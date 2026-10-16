"""Reviewed source imports and typed observations; never an implicit accounting ledger."""

import hashlib
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal
from urllib.parse import quote
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
)
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from . import database as db
from . import source_parser, storage
from .config import settings
from .records import log_event, wire
from .security import (
    connection,
    customer_exists,
    lock_workspace,
    scope,
    visible,
    writer,
)

router = APIRouter(prefix="/api/workspaces/{organization_id}")
KINDS = Literal[
    "reported_sales",
    "expenditure",
    "cash_inflow",
    "cash_outflow",
    "commitment",
    "asset_balance",
    "liability_balance",
]


class Mapping(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: KINDS
    columns: dict[str, str]
    currency: str = Field(pattern="^[A-Z]{3}$")
    date_format: Literal["ISO", "DMY", "MDY"] = "ISO"
    decimal_format: Literal["dot", "comma"] = "dot"
    amount_mode: Literal["direct", "quantity_price"] = "direct"
    namespace: str = Field(default="", max_length=60, pattern=r"^[A-Za-z0-9._-]*$")
    profile_name: str = Field(default="", max_length=80)


def document(conn, s, key):
    row = (
        conn.execute(
            select(db.source_documents).where(
                db.source_documents.c.organization_id == s.org,
                db.source_documents.c.id == str(key),
            )
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(404, "Source document not found")
    return row


def public_doc(row):
    return wire({k: v for k, v in row.items() if k != "file_key"})


@router.get("/sources")
def documents(s=Depends(writer), conn=Depends(connection, scope="function")):
    return [
        public_doc(r)
        for r in conn.execute(
            select(db.source_documents)
            .where(db.source_documents.c.organization_id == s.org)
            .order_by(db.source_documents.c.created_at.desc())
            .limit(100)
        ).mappings()
    ]


@router.get("/mapping-profiles")
def profiles(s=Depends(writer), conn=Depends(connection, scope="function")):
    return wire(
        list(
            conn.execute(
                select(db.mapping_profiles).where(
                    db.mapping_profiles.c.organization_id == s.org
                )
            ).mappings()
        )
    )


@router.post("/sources")
def upload(
    file: UploadFile = File(...),
    adapter: Literal["generic", "fhdc_card"] = Form("generic"),
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    content = file.file.read(settings.file_limit("csv") + 1)
    if len(content) > settings.file_limit("csv"):
        raise HTTPException(413, "Source exceeds upload limit")
    lock_workspace(conn, s)
    sha = hashlib.sha256(content).hexdigest()
    existing = (
        conn.execute(
            select(db.source_documents).where(
                db.source_documents.c.organization_id == s.org,
                db.source_documents.c.sha256 == sha,
            )
        )
        .mappings()
        .first()
    )
    if existing:
        return public_doc(existing)
    name = Path((file.filename or "upload.csv").replace("\\", "/")).name[:200]
    try:
        fmt, headers, rows, pages = source_parser.extract(content, name, adapter)
    except Exception as exc:
        if isinstance(exc, (ValueError, UnicodeError, InvalidOperation)):
            raise HTTPException(422, str(exc)) from None
        raise HTTPException(
            422, "Unsupported or malformed source; no records imported"
        ) from None
    did = db.uid()
    key = did + "." + fmt
    storage.put(s.org, key, content)
    try:
        conn.execute(
            db.source_documents.insert().values(
                organization_id=s.org,
                id=did,
                filename=name,
                file_key=key,
                sha256=sha,
                format=fmt,
                headers=headers,
                pages=pages,
                mapping={"adapter": adapter},
                issues=[],
                created_by=s.user["id"],
            )
        )
        if rows:
            conn.execute(
                db.raw_records.insert(),
                [
                    dict(
                        organization_id=s.org,
                        document_id=did,
                        row_number=i + 1,
                        values=row,
                    )
                    for i, row in enumerate(rows)
                ],
            )
        log_event(
            conn,
            s,
            "source",
            did,
            "uploaded",
            {"sha256": sha, "rows": len(rows), "adapter": adapter},
        )
    except Exception:
        storage.remove(s.org, key)
        raise
    return public_doc(document(conn, s, did))


@router.get("/sources/{document_id}/raw")
def raw(
    document_id: UUID, s=Depends(writer), conn=Depends(connection, scope="function")
):
    doc = document(conn, s, document_id)
    rows = conn.execute(
        select(db.raw_records)
        .where(
            db.raw_records.c.organization_id == s.org,
            db.raw_records.c.document_id == str(document_id),
        )
        .order_by(db.raw_records.c.row_number)
        .limit(2000)
    ).mappings()
    return {
        "document": public_doc(doc),
        "suggestions": source_parser.suggestions(doc["headers"]),
        "rows": [dict(r) for r in rows],
    }


@router.get("/sources/{document_id}/file")
def download(
    document_id: UUID, s=Depends(writer), conn=Depends(connection, scope="function")
):
    doc = document(conn, s, document_id)
    content = storage.read(s.org, doc["file_key"])
    if hashlib.sha256(content).hexdigest() != doc["sha256"]:
        raise storage.StorageUnavailable("Source integrity check failed")
    return Response(
        content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{quote(doc['filename'], safe='')}",
            "X-Content-Type-Options": "nosniff",
        },
    )


def normalized(conn, s, doc, mapping):
    if set(mapping.columns) - {
        "amount",
        "quantity",
        "unit_price",
        "date",
        "counterparty",
        "description",
        "external_id",
        "customer_id",
        "currency",
    }:
        raise HTTPException(422, "Unknown mapping target")
    required = (
        ["amount"] if mapping.amount_mode == "direct" else ["quantity", "unit_price"]
    )
    if any(not mapping.columns.get(k) for k in required) or any(
        v not in doc["headers"] for v in mapping.columns.values() if v
    ):
        raise HTTPException(422, "Choose valid source columns, including amount")
    rows = conn.execute(
        select(db.raw_records)
        .where(
            db.raw_records.c.organization_id == s.org,
            db.raw_records.c.document_id == doc["id"],
        )
        .order_by(db.raw_records.c.row_number)
    ).mappings()
    output, issues, seen = [], [], set()
    existing = list(
        conn.execute(
            select(db.financial_facts)
            .where(db.financial_facts.c.organization_id == s.org)
            .limit(10001)
        ).mappings()
    )
    if len(existing) > 10000:
        raise HTTPException(
            422, "Prototype supports up to 10,000 existing observations per workspace"
        )
    by_key = {r["record_key"]: r for r in existing}
    hashes = {r["raw_hash"] for r in existing}
    customers = set(
        conn.execute(
            select(db.customers.c.customer_id).where(visible(db.customers, s))
        ).scalars()
    )
    aliases = dict(
        conn.execute(
            select(db.entity_aliases.c.alias, db.entity_aliases.c.customer_id).where(
                db.entity_aliases.c.organization_id == s.org
            )
        ).all()
    )
    for row in rows:
        raw = row["values"]

        def val(key, raw=raw):
            return raw.get(mapping.columns.get(key, ""), "").strip()

        try:
            value = val("amount").replace("£", "").strip()
            if mapping.amount_mode == "quantity_price":
                if mapping.kind != "reported_sales" or mapping.decimal_format != "dot":
                    raise ValueError(
                        "Quantity × price is only supported for reported sales with dot decimals"
                    )
                quantity, price = Decimal(val("quantity")), Decimal(val("unit_price"))
                if (
                    not quantity.is_finite()
                    or not price.is_finite()
                    or abs(quantity) >= 10**9
                    or abs(price) >= 10**9
                ):
                    raise ValueError("Unsupported quantity or price")
                from decimal import ROUND_HALF_UP

                value = str(
                    (quantity * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                )
            if value.startswith("(") and value.endswith(")"):
                value = "-" + value[1:-1]
            pattern = (
                r"-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?"
                if mapping.decimal_format == "dot"
                else r"-?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,2})?"
            )
            if not re.fullmatch(pattern, value):
                raise ValueError(
                    "Amount is missing or incompatible with the selected numeric format"
                )
            amount = Decimal(
                value.replace(",", "")
                if mapping.decimal_format == "dot"
                else value.replace(".", "").replace(",", ".")
            )
            if abs(amount) >= 10**12:
                raise ValueError("Amount exceeds supported range")
            currency = val("currency") or mapping.currency
            if currency != s.currency:
                raise ValueError(
                    "Currency differs from workspace; no implicit FX conversion"
                )
            day = None
            if val("date"):
                day = (
                    (
                        date.fromisoformat(val("date"))
                        if len(val("date")) == 10
                        else datetime.fromisoformat(val("date")).date()
                    )
                    if mapping.date_format == "ISO"
                    else datetime.strptime(
                        val("date"),
                        "%d/%m/%Y" if mapping.date_format == "DMY" else "%m/%d/%Y",
                    ).date()
                )
            customer = val("customer_id") or None
            method = "exact_identifier" if customer else "unmatched"
            if not customer and val("counterparty"):
                customer = aliases.get(val("counterparty"))
                if customer:
                    method = "reviewed_alias"
            if customer and customer not in customers:
                raise ValueError("Unknown or unauthorized customer reference")
            if len(val("description")) > 1000 or len(val("counterparty")) > 200:
                raise ValueError(
                    "Description or counterparty exceeds supported length; no truncation performed"
                )
            external = val("external_id")
            if external and not mapping.namespace:
                raise ValueError("External identifiers require a source namespace")
            key = (
                f"{mapping.namespace}:{external}"
                if external
                else f"{doc['sha256']}:{row['row_number']}"
            )
            if len(key) > 200 or key in seen:
                raise ValueError("Repeated or oversized source identifier")
            seen.add(key)
            digest = hashlib.sha256(
                json.dumps(raw, sort_keys=True).encode()
            ).hexdigest()
            fact = dict(
                organization_id=s.org,
                document_id=doc["id"],
                row_number=row["row_number"],
                record_key=key,
                raw_hash=digest,
                kind=mapping.kind,
                amount=amount,
                currency=currency,
                occurred_on=day,
                description=val("description"),
                counterparty=val("counterparty"),
                customer_id=customer,
                link_method=method,
            )
            old = by_key.get(key)
            if old:
                if any(
                    old[k] != fact[k]
                    for k in (
                        "kind",
                        "amount",
                        "currency",
                        "occurred_on",
                        "counterparty",
                        "customer_id",
                        "raw_hash",
                    )
                ):
                    raise ValueError(
                        "Existing source identifier has conflicting values"
                    )
                fact["skip"] = True
            elif digest in hashes:
                raise ValueError(
                    "Possible duplicate source row in another document; review identifiers rather than double-count"
                )
            output.append(fact)
        except (ValueError, InvalidOperation, HTTPException) as exc:
            issues.append(
                {
                    "row": row["row_number"],
                    "message": str(exc.detail)
                    if isinstance(exc, HTTPException)
                    else str(exc),
                }
            )
    if not output and not issues:
        issues.append(
            {
                "message": "Document has no structured records. Read its text; do not invent financial facts."
            }
        )
    return output, issues


@router.post("/sources/{document_id}/preview")
def preview(
    document_id: UUID,
    payload: Mapping,
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    lock_workspace(conn, s)
    doc = document(conn, s, document_id)
    if doc["state"] == "confirmed":
        raise HTTPException(
            409, "Confirmed mappings are immutable; upload a new source version"
        )
    rows, issues = normalized(conn, s, doc, payload)
    mapping = payload.model_dump()
    token = hashlib.sha256(json.dumps(mapping, sort_keys=True).encode()).hexdigest()
    conn.execute(
        db.source_documents.update()
        .where(
            db.source_documents.c.organization_id == s.org,
            db.source_documents.c.id == doc["id"],
        )
        .values(mapping=mapping, issues=issues, state="invalid" if issues else "ready")
    )
    return wire(
        {
            "rows": rows[:20],
            "row_count": len(rows),
            "issues": issues,
            "preview_token": token,
            "unmapped_columns": [
                h for h in doc["headers"] if h not in payload.columns.values()
            ],
            "notice": "All raw columns retained. Review meaning and currency before confirming; these observations are excluded from the verified profitability ledger.",
        }
    )


class Confirm(BaseModel):
    preview_token: str = Field(min_length=64, max_length=64)


@router.post("/sources/{document_id}/confirm")
def confirm(
    document_id: UUID,
    payload: Confirm,
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    lock_workspace(conn, s)
    doc = document(conn, s, document_id)
    if (
        hashlib.sha256(json.dumps(doc["mapping"], sort_keys=True).encode()).hexdigest()
        != payload.preview_token
    ):
        raise HTTPException(409, "Mapping changed; preview again")
    if doc["state"] == "confirmed":
        return {"state": "confirmed", "already_confirmed": True}
    if doc["state"] != "ready":
        raise HTTPException(409, "Resolve import issues first")
    mapping = Mapping.model_validate(doc["mapping"])
    rows, issues = normalized(conn, s, doc, mapping)
    if issues:
        raise HTTPException(409, issues)
    additions = [row for row in rows if not row.pop("skip", False)]
    inserted = len(additions)
    if additions:
        conn.execute(db.financial_facts.insert(), additions)
    conn.execute(
        db.source_documents.update()
        .where(
            db.source_documents.c.organization_id == s.org,
            db.source_documents.c.id == doc["id"],
        )
        .values(state="confirmed")
    )
    if mapping.profile_name:
        stmt = insert(db.mapping_profiles).values(
            organization_id=s.org,
            name=mapping.profile_name,
            version=1,
            mapping=mapping.model_dump(),
        )
        conn.execute(
            stmt.on_conflict_do_update(
                index_elements=["organization_id", "name"],
                set_={
                    "version": db.mapping_profiles.c.version + 1,
                    "mapping": mapping.model_dump(),
                },
            )
        )
    log_event(
        conn,
        s,
        "source",
        str(document_id),
        "confirmed",
        {"mapping": mapping.model_dump(), "inserted": inserted},
    )
    return {"state": "confirmed", "inserted": inserted, "skipped": len(rows) - inserted}


@router.get("/facts")
def facts(
    kind: KINDS | None = None,
    start: date | None = None,
    end: date | None = None,
    offset: int = Query(0, ge=0),
    s=Depends(scope),
    conn=Depends(connection, scope="function"),
):
    table = db.financial_facts
    predicate = visible(table, s)
    if kind:
        predicate &= table.c.kind == kind
    if start:
        predicate &= table.c.occurred_on >= start
    if end:
        predicate &= table.c.occurred_on <= end
    rows = list(
        conn.execute(
            select(table)
            .where(predicate)
            .order_by(table.c.occurred_on, table.c.id)
            .limit(100)
            .offset(offset)
        ).mappings()
    )
    groups = list(
        conn.execute(
            select(
                table.c.kind,
                table.c.currency,
                func.sum(table.c.amount).label("amount"),
                func.count().label("count"),
            )
            .where(predicate)
            .group_by(table.c.kind, table.c.currency)
        ).mappings()
    )
    # Balance snapshots are not additive through time; never return their sum as an insight.
    groups = [
        {**r, "amount": None if r["kind"].endswith("_balance") else r["amount"]}
        for r in groups
    ]
    return wire(
        {
            "rows": rows,
            "groups": groups,
            "months": list(
                conn.execute(
                    select(
                        func.to_char(table.c.occurred_on, "YYYY-MM").label("month"),
                        table.c.kind,
                        table.c.currency,
                        func.sum(table.c.amount).label("amount"),
                        func.count().label("count"),
                    )
                    .where(
                        predicate,
                        table.c.occurred_on.is_not(None),
                        table.c.kind.not_in(["asset_balance", "liability_balance"]),
                    )
                    .group_by("month", table.c.kind, table.c.currency)
                    .order_by("month")
                ).mappings()
            ),
            "total": conn.scalar(
                select(func.count()).select_from(table).where(predicate)
            ),
            "unmatched": conn.scalar(
                select(func.count())
                .select_from(table)
                .where(predicate, table.c.customer_id.is_(None))
            ),
            "notice": "Separate source observations, not net profit. Payments, expenditure and sales are never combined; balances are snapshots, not additive flows.",
        }
    )


@router.get("/facts/{fact_id}")
def fact_source(
    fact_id: UUID, s=Depends(scope), conn=Depends(connection, scope="function")
):
    fact = (
        conn.execute(
            select(db.financial_facts).where(
                visible(db.financial_facts, s), db.financial_facts.c.id == str(fact_id)
            )
        )
        .mappings()
        .first()
    )
    if not fact:
        raise HTTPException(404, "Record not found")
    raw = conn.scalar(
        select(db.raw_records.c["values"]).where(
            db.raw_records.c.organization_id == s.org,
            db.raw_records.c.document_id == fact["document_id"],
            db.raw_records.c.row_number == fact["row_number"],
        )
    )
    doc = document(conn, s, fact["document_id"])
    allocations = list(
        conn.execute(
            select(db.cost_allocations).where(
                visible(db.cost_allocations, s),
                db.cost_allocations.c.fact_id == str(fact_id),
            )
        ).mappings()
    )
    return wire(
        {
            "fact": dict(fact),
            "raw": raw,
            "filename": doc["filename"],
            "sha256": doc["sha256"],
            "mapping": doc["mapping"],
            "allocations": allocations,
            "can_download": s.role in {"admin", "finance"},
        }
    )


class Alias(BaseModel):
    alias: str = Field(min_length=1, max_length=200)
    customer_id: str


class Link(BaseModel):
    customer_id: str
    reason: str = Field(min_length=5, max_length=500)


@router.put("/facts/{fact_id}/link")
def review_link(
    fact_id: UUID,
    payload: Link,
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    lock_workspace(conn, s)
    customer_exists(conn, s, payload.customer_id)
    where = (db.financial_facts.c.organization_id == s.org) & (
        db.financial_facts.c.id == str(fact_id)
    )
    if not conn.scalar(select(db.financial_facts.c.id).where(where)):
        raise HTTPException(404, "Record not found")
    conn.execute(
        db.financial_facts.update()
        .where(where)
        .values(customer_id=payload.customer_id, link_method="human_review")
    )
    log_event(conn, s, "relationship", str(fact_id), "reviewed", payload.model_dump())
    return {
        "status": "reviewed",
        "notice": "Relationship recorded; no financial records merged or amounts changed",
    }


@router.post("/entity-aliases")
def alias(
    payload: Alias, s=Depends(writer), conn=Depends(connection, scope="function")
):
    lock_workspace(conn, s)
    customer_exists(conn, s, payload.customer_id)
    old = conn.scalar(
        select(db.entity_aliases.c.customer_id).where(
            db.entity_aliases.c.organization_id == s.org,
            db.entity_aliases.c.alias == payload.alias,
        )
    )
    if old and old != payload.customer_id:
        raise HTTPException(409, "Alias already points to another customer")
    if not old:
        conn.execute(
            db.entity_aliases.insert().values(
                organization_id=s.org, **payload.model_dump(), reviewed_by=s.user["id"]
            )
        )
        log_event(conn, s, "alias", payload.alias, "reviewed", payload.model_dump())
    return {
        "status": "reviewed",
        "applies_to": "future previews only; existing facts are not silently relinked",
    }


class Allocation(BaseModel):
    customer_id: str
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    reason: str = Field(min_length=5, max_length=500)


@router.put("/facts/{fact_id}/allocations")
def allocate(
    fact_id: UUID,
    payload: list[Allocation],
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    lock_workspace(conn, s)
    fact = (
        conn.execute(
            select(db.financial_facts).where(
                db.financial_facts.c.organization_id == s.org,
                db.financial_facts.c.id == str(fact_id),
            )
        )
        .mappings()
        .first()
    )
    if not fact or fact["kind"] != "expenditure" or fact["amount"] <= 0:
        raise HTTPException(422, "Select a positive expenditure observation")
    if (
        len(payload) > 100
        or len({p.customer_id for p in payload}) != len(payload)
        or sum((p.amount for p in payload), Decimal(0)) > fact["amount"]
    ):
        raise HTTPException(
            422, "Allocations must be unique and cannot exceed source expenditure"
        )
    for item in payload:
        customer_exists(conn, s, item.customer_id)
    conn.execute(
        db.cost_allocations.delete().where(
            db.cost_allocations.c.organization_id == s.org,
            db.cost_allocations.c.fact_id == str(fact_id),
        )
    )
    for item in payload:
        conn.execute(
            db.cost_allocations.insert().values(
                organization_id=s.org,
                fact_id=str(fact_id),
                **item.model_dump(),
                reviewed_by=s.user["id"],
            )
        )
    log_event(
        conn,
        s,
        "allocation",
        str(fact_id),
        "reviewed",
        wire([p.model_dump() for p in payload]),
    )
    return {
        "status": "reviewed",
        "unallocated": str(
            fact["amount"] - sum((p.amount for p in payload), Decimal(0))
        ),
        "notice": "Allocation evidence only; not automatically added to verified expenses or profitability (avoids double counting).",
    }
