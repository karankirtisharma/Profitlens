"""Small operational subledgers; money is deterministic, posting is never inferred."""

from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import and_, func, select

from . import database as db
from .records import log_event, wire
from .security import connection, lock_workspace, writer

router = APIRouter(
    prefix="/api/workspaces/{organization_id}/operations", tags=["Operations"]
)
Money = Annotated[Decimal, Field(ge=0, lt=10**12, max_digits=14, decimal_places=2)]
PositiveMoney = Annotated[
    Decimal, Field(gt=0, lt=10**12, max_digits=14, decimal_places=2)
]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")]
Currency = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Vendor(Payload):
    vendor_id: Identifier
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(default="", max_length=254)
    notes: str = Field(default="", max_length=1000)


class Item(Payload):
    item_id: Identifier
    name: str = Field(min_length=1, max_length=200)
    unit_price: Money
    currency: Currency
    description: str = Field(default="", max_length=1000)


class Bill(Payload):
    bill_id: Identifier
    vendor_id: Identifier
    issued_on: date
    due_on: date | None = None
    currency: Currency
    total: PositiveMoney
    opening_paid: Money
    payments_complete: Literal[True]
    description: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def dates(self):
        if self.opening_paid > self.total:
            raise ValueError("Opening paid cannot exceed bill total")
        if self.due_on is not None and self.due_on < self.issued_on:
            raise ValueError("Due date cannot precede issue date")
        if self.issued_on > date.today():
            raise ValueError("Future bills are not supported")
        return self


class Terms(Payload):
    due_on: date | None = None
    opening_paid: Money
    payments_complete: Literal[True]


class VoidPayment(Payload):
    reason: str = Field(min_length=1, max_length=1000)


class Allocation(Payload):
    document_id: Identifier
    amount: PositiveMoney


class Payment(Payload):
    payment_id: Identifier
    direction: Literal["received", "made"]
    paid_on: date
    currency: Currency
    reference: str = Field(default="", max_length=200)
    allocations: list[Allocation] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def valid(self):
        if self.paid_on > date.today():
            raise ValueError("Future payments are not supported")
        if len({x.document_id for x in self.allocations}) != len(self.allocations):
            raise ValueError("Each document may appear only once per payment")
        if sum(x.amount for x in self.allocations) >= 10**12:
            raise ValueError("Payment total exceeds supported amount")
        return self


def org_key(table, s, id_column=None, record_id=None):
    clause = table.c.organization_id == s.org
    if id_column:
        clause = and_(clause, table.c[id_column] == record_id)
    return clause


def check_currency(s, currency):
    if currency != s.currency:
        raise HTTPException(
            422,
            f"Workspace accepts {s.currency} only; no automatic currency conversion",
        )


def insert_record(conn, s, table, key, payload, *, update_id=None):
    lock_workspace(conn, s)
    data = payload.model_dump(exclude={"payments_complete"})
    if "currency" in data:
        check_currency(s, data["currency"])
    clause = org_key(table, s, key, data[key])
    old = conn.execute(select(table).where(clause)).mappings().first()
    if update_id is not None and update_id != data[key]:
        raise HTTPException(422, "Identifiers cannot change")
    if update_id is not None and not old:
        raise HTTPException(404, "Record not found")
    if update_id is None and old:
        raise HTTPException(409, "This record ID already exists")
    if old:
        conn.execute(table.update().where(clause).values(**data))
    else:
        conn.execute(table.insert().values(organization_id=s.org, **data))
    audit_data = data | (
        {"payments_complete": True} if isinstance(payload, Bill) else {}
    )
    log_event(
        conn, s, table.name, data[key], "updated" if old else "created", audit_data
    )
    return wire(dict(conn.execute(select(table).where(clause)).mappings().one()))


@router.get("/vendors")
def vendors(s=Depends(writer), conn=Depends(connection, scope="function")):
    return wire(
        [
            dict(r)
            for r in conn.execute(
                select(db.vendors)
                .where(org_key(db.vendors, s))
                .order_by(db.vendors.c.name)
            ).mappings()
        ]
    )


@router.post("/vendors")
def create_vendor(
    payload: Vendor, s=Depends(writer), conn=Depends(connection, scope="function")
):
    return insert_record(conn, s, db.vendors, "vendor_id", payload)


@router.put("/vendors/{record_id}")
def update_vendor(
    record_id: str,
    payload: Vendor,
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    return insert_record(conn, s, db.vendors, "vendor_id", payload, update_id=record_id)


@router.get("/items")
def items(s=Depends(writer), conn=Depends(connection, scope="function")):
    return wire(
        [
            dict(r)
            for r in conn.execute(
                select(db.items).where(org_key(db.items, s)).order_by(db.items.c.name)
            ).mappings()
        ]
    )


@router.post("/items")
def create_item(
    payload: Item, s=Depends(writer), conn=Depends(connection, scope="function")
):
    return insert_record(conn, s, db.items, "item_id", payload)


@router.put("/items/{record_id}")
def update_item(
    record_id: str,
    payload: Item,
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    return insert_record(conn, s, db.items, "item_id", payload, update_id=record_id)


@router.get("/bills")
def bills(s=Depends(writer), conn=Depends(connection, scope="function")):
    return wire(
        [
            dict(r)
            for r in conn.execute(
                select(db.bills)
                .where(org_key(db.bills, s))
                .order_by(db.bills.c.issued_on.desc(), db.bills.c.bill_id)
            ).mappings()
        ]
    )


@router.post("/bills")
def create_bill(
    payload: Bill, s=Depends(writer), conn=Depends(connection, scope="function")
):
    if not conn.execute(
        select(db.vendors.c.vendor_id).where(
            org_key(db.vendors, s, "vendor_id", payload.vendor_id)
        )
    ).first():
        raise HTTPException(404, "Vendor not found")
    return insert_record(conn, s, db.bills, "bill_id", payload)


def assert_invoice_editable(conn, s, invoice_id):
    if conn.execute(
        select(db.invoice_terms.c.invoice_id).where(
            org_key(db.invoice_terms, s, "invoice_id", invoice_id)
        )
    ).first():
        raise HTTPException(
            409,
            "Tracked invoices are immutable; changing them would invalidate payment balances",
        )


@router.get("/invoice-candidates")
def invoice_candidates(s=Depends(writer), conn=Depends(connection, scope="function")):
    join = and_(
        db.invoices.c.organization_id == db.invoice_terms.c.organization_id,
        db.invoices.c.invoice_id == db.invoice_terms.c.invoice_id,
    )
    rows = conn.execute(
        select(
            db.invoices.c.invoice_id,
            db.invoices.c.customer_id,
            db.invoices.c.total,
            db.invoice_terms.c.invoice_id.label("tracked_id"),
        )
        .outerjoin(db.invoice_terms, join)
        .where(org_key(db.invoices, s), db.invoices.c.amount_basis == "verified")
        .order_by(db.invoices.c.invoice_id)
    ).mappings()
    return wire(
        [
            {k: r[k] for k in ("invoice_id", "customer_id", "total")}
            | {"tracked": r["tracked_id"] is not None}
            for r in rows
        ]
    )


@router.put("/invoice-terms/{invoice_id}")
def enroll_invoice(
    invoice_id: str,
    payload: Terms,
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    lock_workspace(conn, s)
    row = (
        conn.execute(
            select(db.invoices).where(org_key(db.invoices, s, "invoice_id", invoice_id))
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(404, "Invoice not found")
    if row["amount_basis"] != "verified":
        raise HTTPException(422, "Reported sales are not verified invoice obligations")
    check_currency(s, row["currency"])
    if payload.opening_paid > row["total"]:
        raise HTTPException(422, "Opening paid cannot exceed invoice total")
    assert_invoice_editable(conn, s, invoice_id)
    data = {
        "invoice_id": invoice_id,
        "due_on": payload.due_on,
        "opening_paid": payload.opening_paid,
        "attested_by": s.user["id"],
    }
    conn.execute(db.invoice_terms.insert().values(organization_id=s.org, **data))
    log_event(
        conn,
        s,
        "invoice_terms",
        invoice_id,
        "enrolled",
        data | {"payments_complete": True},
    )
    return wire(data)


def active_allocations():
    return db.payment_allocations.join(
        db.payments,
        and_(
            db.payment_allocations.c.organization_id == db.payments.c.organization_id,
            db.payment_allocations.c.payment_id == db.payments.c.payment_id,
            db.payments.c.state == "active",
        ),
    )


def paid_amount(conn, s, document_id, direction):
    column = (
        db.payment_allocations.c.invoice_id
        if direction == "received"
        else db.payment_allocations.c.bill_id
    )
    return conn.scalar(
        select(func.coalesce(func.sum(db.payment_allocations.c.amount), 0))
        .select_from(active_allocations())
        .where(org_key(db.payment_allocations, s), column == document_id)
    )


@router.get("/payments")
def payments(s=Depends(writer), conn=Depends(connection, scope="function")):
    rows = [
        dict(r)
        for r in conn.execute(
            select(db.payments)
            .where(org_key(db.payments, s))
            .order_by(db.payments.c.paid_on.desc(), db.payments.c.payment_id)
        ).mappings()
    ]
    allocations = conn.execute(
        select(db.payment_allocations).where(org_key(db.payment_allocations, s))
    ).mappings()
    grouped = {}
    for row in allocations:
        grouped.setdefault(row["payment_id"], []).append(
            {
                "document_id": row["invoice_id"] or row["bill_id"],
                "amount": row["amount"],
            }
        )
    return wire([r | {"allocations": grouped.get(r["payment_id"], [])} for r in rows])


@router.post("/payments")
def create_payment(
    payload: Payment, s=Depends(writer), conn=Depends(connection, scope="function")
):
    lock_workspace(conn, s)
    check_currency(s, payload.currency)
    if conn.execute(
        select(db.payments.c.payment_id).where(
            org_key(db.payments, s, "payment_id", payload.payment_id)
        )
    ).first():
        raise HTTPException(
            409, "Payment ID already exists; no duplicate payment recorded"
        )
    target = db.invoices if payload.direction == "received" else db.bills
    id_key = "invoice_id" if payload.direction == "received" else "bill_id"
    party_key = "customer_id" if payload.direction == "received" else "vendor_id"
    parties = set()
    for allocation in payload.allocations:
        row = (
            conn.execute(
                select(target).where(org_key(target, s, id_key, allocation.document_id))
            )
            .mappings()
            .first()
        )
        if not row:
            raise HTTPException(404, "Payment document not found in this workspace")
        check_currency(s, row["currency"])
        parties.add(row[party_key])
        opening = row["opening_paid"] if payload.direction == "made" else Decimal("0")
        if payload.direction == "received":
            terms = (
                conn.execute(
                    select(db.invoice_terms).where(
                        org_key(
                            db.invoice_terms, s, "invoice_id", allocation.document_id
                        )
                    )
                )
                .mappings()
                .first()
            )
            if not terms:
                raise HTTPException(
                    422,
                    "Enroll the invoice and attest opening payments before receiving payment",
                )
            opening = terms["opening_paid"]
        elif payload.paid_on < row["issued_on"]:
            raise HTTPException(
                422,
                "Payment cannot precede bill issue date; prepayments are unsupported",
            )
        outstanding = (
            row["total"]
            - opening
            - paid_amount(conn, s, allocation.document_id, payload.direction)
        )
        if allocation.amount > outstanding:
            raise HTTPException(
                422,
                f"Allocation exceeds outstanding amount for {allocation.document_id}",
            )
    if len(parties) != 1:
        raise HTTPException(422, "One payment must belong to one customer or vendor")
    data = payload.model_dump(exclude={"allocations"}) | {
        "total": sum(a.amount for a in payload.allocations)
    }
    conn.execute(db.payments.insert().values(organization_id=s.org, **data))
    for allocation in payload.allocations:
        conn.execute(
            db.payment_allocations.insert().values(
                organization_id=s.org,
                payment_id=payload.payment_id,
                **{id_key: allocation.document_id},
                amount=allocation.amount,
            )
        )
    log_event(
        conn,
        s,
        "payments",
        payload.payment_id,
        "created",
        data | {"allocations": [a.model_dump() for a in payload.allocations]},
    )
    return wire(data | {"allocations": [a.model_dump() for a in payload.allocations]})


@router.post("/payments/{payment_id}/void")
def void_payment(
    payment_id: str,
    payload: VoidPayment,
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    lock_workspace(conn, s)
    clause = org_key(db.payments, s, "payment_id", payment_id)
    row = conn.execute(select(db.payments).where(clause)).mappings().first()
    if not row:
        raise HTTPException(404, "Payment not found")
    if row["state"] == "void":
        raise HTTPException(409, "Payment is already void")
    changed = {"state": "void", "void_reason": payload.reason, "voided_at": db.now()}
    conn.execute(db.payments.update().where(clause).values(**changed))
    log_event(
        conn,
        s,
        "payments",
        payment_id,
        "voided",
        {"before": dict(row), "after": dict(row) | changed},
    )
    return wire(dict(row) | changed)


def bucket(rows, today):
    totals = {key: Decimal("0") for key in ("total", "current", "overdue", "undated")}
    for row in rows:
        remaining = row["total"] - row["paid"]
        row["outstanding"] = remaining
        due = row["due_on"]
        status = (
            "paid"
            if remaining == 0
            else "undated"
            if due is None
            else "overdue"
            if due < today
            else "current"
        )
        row["status"] = status
        totals["total"] += remaining
        if status != "paid":
            totals[status] += remaining
    return totals | {"rows": rows}


@router.get("/summary")
def summary(s=Depends(writer), conn=Depends(connection, scope="function")):
    lock_workspace(conn, s)
    allocations = conn.execute(
        select(db.payment_allocations)
        .select_from(active_allocations())
        .where(org_key(db.payment_allocations, s))
    ).mappings()
    paid = {}
    for row in allocations:
        key = (
            ("invoice", row["invoice_id"])
            if row["invoice_id"]
            else ("bill", row["bill_id"])
        )
        paid[key] = paid.get(key, Decimal("0")) + row["amount"]
    invoice_rows = conn.execute(
        select(
            db.invoices,
            db.invoice_terms.c.due_on,
            db.invoice_terms.c.opening_paid,
            db.customers.c.name,
        )
        .join(
            db.invoice_terms,
            and_(
                db.invoices.c.organization_id == db.invoice_terms.c.organization_id,
                db.invoices.c.invoice_id == db.invoice_terms.c.invoice_id,
            ),
        )
        .join(
            db.customers,
            and_(
                db.invoices.c.organization_id == db.customers.c.organization_id,
                db.invoices.c.customer_id == db.customers.c.customer_id,
            ),
        )
        .where(org_key(db.invoices, s))
    ).mappings()
    receivables = [
        {
            "document_id": r["invoice_id"],
            "party_id": r["customer_id"],
            "party_name": r["name"],
            "total": r["total"],
            "paid": r["opening_paid"]
            + paid.get(("invoice", r["invoice_id"]), Decimal("0")),
            "due_on": r["due_on"],
        }
        for r in invoice_rows
    ]
    bill_rows = conn.execute(
        select(db.bills, db.vendors.c.name)
        .join(
            db.vendors,
            and_(
                db.bills.c.organization_id == db.vendors.c.organization_id,
                db.bills.c.vendor_id == db.vendors.c.vendor_id,
            ),
        )
        .where(org_key(db.bills, s))
    ).mappings()
    payables = [
        {
            "document_id": r["bill_id"],
            "party_id": r["vendor_id"],
            "party_name": r["name"],
            "total": r["total"],
            "paid": r["opening_paid"] + paid.get(("bill", r["bill_id"]), Decimal("0")),
            "due_on": r["due_on"],
        }
        for r in bill_rows
    ]
    total_invoices = conn.scalar(
        select(func.count()).select_from(db.invoices).where(org_key(db.invoices, s))
    )
    today = date.today()
    return wire(
        {
            "currency": s.currency,
            "as_of": today,
            "receivables": bucket(receivables, today)
            | {"untracked_count": total_invoices - len(receivables)},
            "payables": bucket(payables, today) | {"untracked_count": 0},
            "limitations": [
                "Receivables cover only explicitly enrolled verified invoices; historic payments require human attestation.",
                "Bills and payments are operational records, not automatic revenue/expense postings or a bank balance.",
                "No FX, refunds, prepayments, or statutory accounting. Payments can be voided with an audit reason; original records and allocations remain preserved.",
                "Payments must be fully allocated to one customer or vendor; due dates may be unknown.",
            ],
        }
    )
