"""Review-first recurring billing and purchase commitments. No payments or mail sent."""

from calendar import monthrange
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field, model_validator
from sqlalchemy import select

from . import database as db
from .operations import (
    Bill,
    Currency,
    Identifier,
    Money,
    Payload,
    PositiveMoney,
    Terms,
    check_currency,
    create_bill,
    enroll_invoice,
    org_key,
)
from .records import log_event, wire, write_record
from .security import connection, customer_exists, lock_workspace, writer

router = APIRouter(
    prefix="/api/workspaces/{organization_id}/planning", tags=["Planning"]
)


def next_date(anchor, current, interval):
    offset = (current.year - anchor.year) * 12 + current.month - anchor.month + interval
    year, month = divmod(anchor.year * 12 + anchor.month - 1 + offset, 12)
    return date(year, month + 1, min(anchor.day, monthrange(year, month + 1)[1]))


class Schedule(Payload):
    id: Identifier
    name: str = Field(min_length=1, max_length=200)
    customer_id: Identifier
    start_on: date
    end_on: date | None = None
    interval_months: Literal[1, 3, 12] = 1
    due_days: int = Field(default=30, ge=0, le=365)
    currency: Currency
    subtotal: PositiveMoney
    discount: Money = Decimal("0")
    tax: Money = Decimal("0")

    @model_validator(mode="after")
    def valid(self):
        if (
            self.discount > self.subtotal
            or self.subtotal - self.discount + self.tax >= 10**12
        ):
            raise ValueError("Invalid discount or total")
        if self.subtotal - self.discount + self.tax <= 0:
            raise ValueError("Invoice total must be positive")
        if self.end_on and self.end_on < self.start_on:
            raise ValueError("End date must follow start date")
        if not 2000 <= self.start_on.year <= 2090 or (
            self.end_on and self.end_on.year > 2090
        ):
            raise ValueError("Supported schedule years: 2000–2090")
        return self


class State(Payload):
    state: Literal["active", "paused"]


class Line(Payload):
    item_id: Identifier | None = None
    description: str = Field(min_length=1, max_length=300)
    quantity: Decimal = Field(gt=0, lt=10**8, max_digits=12, decimal_places=3)
    unit_price: Money
    tax: Money = Decimal("0")


class Order(Payload):
    id: Identifier
    vendor_id: Identifier
    ordered_on: date
    expected_on: date | None = None
    currency: Currency
    notes: str = Field(default="", max_length=1000)
    lines: list[Line] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def valid(self):
        if self.ordered_on > date.today() or (
            self.expected_on and self.expected_on < self.ordered_on
        ):
            raise ValueError("Check order and expected dates")
        return self


class Convert(Payload):
    bill_id: Identifier
    issued_on: date
    due_on: date | None = None
    opening_paid: Money
    payments_complete: Literal[True]
    invoice_matches_order: Literal[True]


def row(conn, s, table, key):
    result = (
        conn.execute(select(table).where(org_key(table, s, "id", key)))
        .mappings()
        .first()
    )
    if not result:
        raise HTTPException(404, "Record not found")
    return dict(result)


def listing(conn, s, table):
    return [
        dict(x)
        for x in conn.execute(
            select(table).where(org_key(table, s)).order_by(table.c.id)
        ).mappings()
    ]


@router.get("/recurring")
def recurring(s=Depends(writer), conn=Depends(connection, scope="function")):
    return wire(
        {
            "schedules": listing(conn, s, db.recurring_schedules),
            "drafts": listing(conn, s, db.recurring_drafts),
        }
    )


@router.post("/recurring")
def create_schedule(
    payload: Schedule, s=Depends(writer), conn=Depends(connection, scope="function")
):
    lock_workspace(conn, s)
    customer_exists(conn, s, payload.customer_id)
    check_currency(s, payload.currency)
    if conn.execute(
        select(db.recurring_schedules.c.id).where(
            org_key(db.recurring_schedules, s, "id", payload.id)
        )
    ).first():
        raise HTTPException(409, "Schedule ID already exists")
    data = payload.model_dump() | {"state": "active", "next_on": payload.start_on}
    conn.execute(db.recurring_schedules.insert().values(organization_id=s.org, **data))
    log_event(conn, s, "recurring_schedules", payload.id, "created", data)
    return wire(data)


@router.put("/recurring/{key}/state")
def schedule_state(
    key: str,
    payload: State,
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    lock_workspace(conn, s)
    old = row(conn, s, db.recurring_schedules, key)
    if old["state"] == "completed":
        raise HTTPException(
            409, "Completed schedules cannot resume; create a new schedule"
        )
    conn.execute(
        db.recurring_schedules.update()
        .where(org_key(db.recurring_schedules, s, "id", key))
        .values(state=payload.state)
    )
    log_event(
        conn, s, "recurring_schedules", key, "state_changed", payload.model_dump()
    )
    return {"state": payload.state}


@router.post("/recurring/generate")
def generate(s=Depends(writer), conn=Depends(connection, scope="function")):
    lock_workspace(conn, s)
    count = 0
    for schedule in listing(conn, s, db.recurring_schedules):
        if schedule["state"] != "active":
            continue
        due = schedule["next_on"]
        while (
            due <= date.today()
            and (not schedule["end_on"] or due <= schedule["end_on"])
            and count < 120
        ):
            key = str(uuid4())
            snapshot = {
                k: schedule[k]
                for k in (
                    "customer_id",
                    "currency",
                    "subtotal",
                    "discount",
                    "tax",
                    "due_days",
                    "name",
                )
            }
            conn.execute(
                db.recurring_drafts.insert().values(
                    organization_id=s.org,
                    id=key,
                    schedule_id=schedule["id"],
                    issued_on=due,
                    snapshot=wire(snapshot),
                    state="draft",
                )
            )
            log_event(
                conn,
                s,
                "recurring_drafts",
                key,
                "generated",
                snapshot | {"issued_on": due},
            )
            due = next_date(schedule["start_on"], due, schedule["interval_months"])
            count += 1
        completed = bool(schedule["end_on"] and due > schedule["end_on"])
        conn.execute(
            db.recurring_schedules.update()
            .where(org_key(db.recurring_schedules, s, "id", schedule["id"]))
            .values(next_on=due, state="completed" if completed else "active")
        )
    return {
        "generated": count,
        "limit": 120,
        "message": "Review drafts before issuing. Run again if more than 120 periods are due.",
    }


@router.post("/drafts/{key}/issue")
def issue(key: str, s=Depends(writer), conn=Depends(connection, scope="function")):
    lock_workspace(conn, s)
    draft = row(conn, s, db.recurring_drafts, key)
    if draft["state"] == "issued":
        return {"invoice_id": draft["invoice_id"], "already_issued": True}
    if draft["state"] != "draft":
        raise HTTPException(409, "Only pending drafts can be issued")
    snap = draft["snapshot"]
    total = Decimal(snap["subtotal"]) - Decimal(snap["discount"]) + Decimal(snap["tax"])
    invoice_id = "RI-" + key
    payload = {
        k: snap[k] for k in ("customer_id", "currency", "subtotal", "discount", "tax")
    }
    write_record(
        conn,
        s,
        "invoices",
        payload
        | {
            "invoice_id": invoice_id,
            "billing_period": draft["issued_on"].strftime("%Y-%m"),
            "refund": "0",
            "total": str(total),
        },
    )
    conn.execute(
        db.invoices.update()
        .where(org_key(db.invoices, s, "invoice_id", invoice_id))
        .values(
            source={
                "type": "recurring",
                "schedule_id": draft["schedule_id"],
                "draft_id": key,
                "issued_on": str(draft["issued_on"]),
            }
        )
    )
    enroll_invoice(
        invoice_id,
        Terms(
            due_on=draft["issued_on"] + timedelta(days=snap["due_days"]),
            opening_paid=0,
            payments_complete=True,
        ),
        s,
        conn,
    )
    conn.execute(
        db.recurring_drafts.update()
        .where(org_key(db.recurring_drafts, s, "id", key))
        .values(state="issued", invoice_id=invoice_id)
    )
    log_event(conn, s, "recurring_drafts", key, "issued", {"invoice_id": invoice_id})
    return {"invoice_id": invoice_id, "already_issued": False}


@router.post("/drafts/{key}/skip")
def skip(key: str, s=Depends(writer), conn=Depends(connection, scope="function")):
    lock_workspace(conn, s)
    draft = row(conn, s, db.recurring_drafts, key)
    if draft["state"] != "draft":
        raise HTTPException(409, "Only pending drafts can be skipped")
    conn.execute(
        db.recurring_drafts.update()
        .where(org_key(db.recurring_drafts, s, "id", key))
        .values(state="skipped")
    )
    log_event(conn, s, "recurring_drafts", key, "skipped", {})
    return {"state": "skipped"}


@router.get("/orders")
def orders(s=Depends(writer), conn=Depends(connection, scope="function")):
    result = listing(conn, s, db.purchase_orders)
    lines = list(
        conn.execute(
            select(db.purchase_order_lines)
            .where(org_key(db.purchase_order_lines, s))
            .order_by(db.purchase_order_lines.c.line)
        ).mappings()
    )
    return wire(
        [
            x | {"lines": [dict(y) for y in lines if y["order_id"] == x["id"]]}
            for x in result
        ]
    )


@router.post("/orders")
def create_order(
    payload: Order, s=Depends(writer), conn=Depends(connection, scope="function")
):
    lock_workspace(conn, s)
    check_currency(s, payload.currency)
    if not conn.execute(
        select(db.vendors.c.vendor_id).where(
            org_key(db.vendors, s, "vendor_id", payload.vendor_id)
        )
    ).first():
        raise HTTPException(404, "Vendor not found")
    if conn.execute(
        select(db.purchase_orders.c.id).where(
            org_key(db.purchase_orders, s, "id", payload.id)
        )
    ).first():
        raise HTTPException(409, "Order ID already exists")
    lines = []
    for index, line in enumerate(payload.lines, 1):
        if line.item_id:
            item = (
                conn.execute(
                    select(db.items).where(
                        org_key(db.items, s, "item_id", line.item_id)
                    )
                )
                .mappings()
                .first()
            )
            if not item or item["currency"] != payload.currency:
                raise HTTPException(422, "Item is missing or its currency differs")
        amount = (line.quantity * line.unit_price + line.tax).quantize(
            Decimal(".01"), rounding=ROUND_HALF_UP
        )
        if amount <= 0 or amount >= 10**12:
            raise HTTPException(422, "Line total outside supported range")
        lines.append(line.model_dump() | {"line": index, "amount": amount})
    total = sum(x["amount"] for x in lines)
    if total >= 10**12:
        raise HTTPException(422, "Order total outside supported range")
    data = payload.model_dump(exclude={"lines"}) | {"total": total, "state": "draft"}
    conn.execute(db.purchase_orders.insert().values(organization_id=s.org, **data))
    for line in lines:
        conn.execute(
            db.purchase_order_lines.insert().values(
                organization_id=s.org, order_id=payload.id, **line
            )
        )
    log_event(
        conn, s, "purchase_orders", payload.id, "created", data | {"lines": lines}
    )
    return wire(data)


@router.post("/orders/{key}/{action}")
def transition(
    key: str,
    action: Literal["approve", "cancel"],
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    lock_workspace(conn, s)
    old = row(conn, s, db.purchase_orders, key)
    allowed = {"approve": ("draft",), "cancel": ("draft", "approved")}
    if old["state"] not in allowed[action]:
        raise HTTPException(409, "This transition is not allowed")
    state = "approved" if action == "approve" else "cancelled"
    conn.execute(
        db.purchase_orders.update()
        .where(org_key(db.purchase_orders, s, "id", key))
        .values(state=state)
    )
    log_event(conn, s, "purchase_orders", key, state, {})
    return {"state": state}


@router.put("/orders/{key}/bill")
def convert(
    key: str,
    payload: Convert,
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    lock_workspace(conn, s)
    order = row(conn, s, db.purchase_orders, key)
    if order["state"] == "billed" and order["bill_id"] == payload.bill_id:
        return {"bill_id": order["bill_id"], "already_converted": True}
    if order["state"] != "approved":
        raise HTTPException(409, "Only approved orders can be converted once")
    if payload.issued_on < order["ordered_on"]:
        raise HTTPException(422, "Bill date cannot precede purchase order")
    bill = Bill(
        **payload.model_dump(exclude={"invoice_matches_order"}),
        vendor_id=order["vendor_id"],
        currency=order["currency"],
        total=order["total"],
        description=f"Purchase order {key}: {order['notes']}"[:1000],
    )
    create_bill(bill, s, conn)
    conn.execute(
        db.purchase_orders.update()
        .where(org_key(db.purchase_orders, s, "id", key))
        .values(state="billed", bill_id=payload.bill_id)
    )
    log_event(conn, s, "purchase_orders", key, "billed", payload.model_dump())
    return {"bill_id": payload.bill_id, "already_converted": False}
