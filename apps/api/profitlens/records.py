"""Validated writes and immutable provenance shared by manual edits and CSV imports."""

import re
from decimal import Decimal

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy import select

from . import database as db
from .ingestion.models import Customer, Expense, Invoice
from .security import customer_exists, lock_workspace

KINDS = {
    "customers": (db.customers, Customer, "customer_id"),
    "invoices": (db.invoices, Invoice, "invoice_id"),
    "expenses": (db.expenses, Expense, "expense_id"),
}


def spec(kind):
    if kind not in KINDS:
        raise HTTPException(404, "Record type not found")
    return KINDS[kind]


def validate(kind, payload, s):
    _, model, _ = spec(kind)
    if "organization_id" in payload:
        raise HTTPException(422, "Organization scope must not be supplied in records")
    try:
        record = model.model_validate({**payload, "organization_id": s.org})
    except ValidationError as exc:
        raise HTTPException(
            422,
            [
                {"field": ".".join(map(str, e["loc"])), "message": e["msg"]}
                for e in exc.errors()
            ],
        ) from exc
    if kind != "customers" and record.currency != s.currency:
        raise HTTPException(
            422,
            f"Workspace accepts {s.currency} only; convert currencies before import",
        )
    data = record.model_dump()
    for key in ("customer_id", "invoice_id", "expense_id"):
        if key in data and not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", data[key]
        ):
            raise HTTPException(
                422,
                f"{key} must be 1-80 letters, digits, dots, underscores or hyphens; start with a letter or digit",
            )
    for key, val in data.items():
        if isinstance(val, str) and len(val) > (
            200 if key in ("name", "industry", "category") else 80
        ):
            raise HTTPException(422, f"{key} is too long")
    for key in ("subtotal", "discount", "tax", "refund", "total", "amount"):
        if key in data and data[key] >= 10**12:
            raise HTTPException(422, f"{key} exceeds supported amount")
    return data


def wire(value):
    return jsonable_encoder(value, custom_encoder={Decimal: str})


def log_event(conn, s, kind, record_id, action, snapshot):
    conn.execute(
        db.audit.insert().values(
            organization_id=s.org,
            kind=kind,
            record_id=record_id,
            actor_id=s.user["id"],
            action=action,
            snapshot=wire(snapshot),
        )
    )


def write_record(conn, s, kind, payload, record_id=None):
    lock_workspace(conn, s)
    table, _, id_key = spec(kind)
    data = validate(kind, payload, s)
    if kind != "customers":
        customer_exists(conn, s, data["customer_id"])
    if record_id and data[id_key] != record_id:
        raise HTTPException(422, "Record IDs cannot be changed")
    key = data[id_key]
    where = (table.c.organization_id == s.org) & (table.c[id_key] == key)
    old = conn.execute(select(table).where(where)).mappings().first()
    if record_id and not old:
        raise HTTPException(404, "Record not found")
    if not record_id and old:
        raise HTTPException(409, "This record ID already exists")
    if old:
        # Keep original import source; append audit event for every correction.
        conn.execute(table.update().where(where).values(**data))
    else:
        conn.execute(
            table.insert().values(
                **data, source={"type": "manual", "actor_id": s.user["id"]}
            )
        )
    log_event(conn, s, kind, key, "updated" if old else "created", data)
    return wire(dict(conn.execute(select(table).where(where)).mappings().one()))
