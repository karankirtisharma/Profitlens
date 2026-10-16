"""Additive financial analysis and evidence endpoints; legacy routes stay intact."""

from datetime import timedelta
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from . import (
    assistant,
    chat,
    explanations,
    profitability,
    retrieval,
    source_chat,
    workspace_summary,
)
from . import database as db
from .records import wire
from .security import (
    connection,
    current_user,
    digest,
    lock_workspace,
    scope,
    visible,
    writer,
)

router = APIRouter(prefix="/api/workspaces/{organization_id}")


class CostReview(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    input_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    note: str = Field(min_length=10, max_length=500)


class Question(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    customer_id: str = Field(min_length=1, max_length=80)
    billing_period: str = Field(pattern=r"^\d{4}-\d{2}$")
    question: str = Field(min_length=5, max_length=1000)
    evidence_scope: explanations.EvidenceScope = "combined"


@router.get("/profitability")
def report(
    billing_period: str | None = None,
    customer_id: str | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    cost_increase_percent: Decimal = Query(Decimal("25"), ge=0, le=1000),
    margin_decline_points: Decimal = Query(Decimal("10"), ge=0, le=100),
    pricing_tolerance: Decimal = Query(Decimal("1"), ge=0, le=100000),
    s=Depends(scope),
    conn=Depends(connection, scope="function"),
):
    return profitability.report(
        conn,
        s,
        billing_period,
        customer_id,
        limit,
        offset,
        cost_increase_percent,
        margin_decline_points,
        pricing_tolerance,
    )


@router.put("/profitability/{customer_id}/{billing_period}/cost-review")
def review(
    customer_id: str,
    billing_period: str,
    payload: CostReview,
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    lock_workspace(conn, s)
    return profitability.attest(
        conn, s, customer_id, billing_period, payload.input_hash, payload.note.strip()
    )


@router.get("/evidence/search")
def search(
    customer_id: str,
    billing_period: str,
    q: str = Query(min_length=2, max_length=1000),
    mode: Literal["context", "baseline"] = "context",
    k: int = Query(5, ge=1, le=10),
    s=Depends(scope),
    conn=Depends(connection, scope="function"),
):
    return wire(retrieval.search(conn, s, customer_id, billing_period, q, mode, k))


@router.post("/evidence/reindex")
def reindex(s=Depends(writer), conn=Depends(connection, scope="function")):
    lock_workspace(conn, s)
    rows = list(
        conn.execute(
            select(db.contracts).where(visible(db.contracts, s)).limit(201)
        ).mappings()
    )
    if len(rows) > 200:
        raise HTTPException(422, "Reindex limit is 200 documents per workspace")
    count = sum(retrieval.index_contract(conn, row) for row in rows)
    return {"documents": len(rows), "passages": count, "version": retrieval.VERSION}


@router.get("/ai/status")
def ai_status(s=Depends(scope)):
    return explanations.provider_status()


def throttle(conn, s, bucket="investigation", limit=5):
    key = digest(bucket + ":" + s.org)
    conn.execute(
        insert(db.login_limits)
        .values(key=key, attempts=0, reset_at=db.now() + timedelta(minutes=1))
        .on_conflict_do_nothing()
    )
    row = (
        conn.execute(
            select(db.login_limits)
            .where(db.login_limits.c.key == key)
            .with_for_update()
        )
        .mappings()
        .one()
    )
    count = row["attempts"] if row["reset_at"] > db.now() else 0
    if count >= limit:
        raise HTTPException(
            429, f"Workspace {bucket} limit: {limit} requests per minute"
        )
    conn.execute(
        db.login_limits.update()
        .where(db.login_limits.c.key == key)
        .values(
            attempts=count + 1,
            reset_at=row["reset_at"]
            if row["reset_at"] > db.now()
            else db.now() + timedelta(minutes=1),
        )
    )


@router.post("/chat")
def converse(organization_id: str, payload: chat.ChatRequest, request: Request):
    if not payload.message.strip():
        raise HTTPException(422, "Enter a message")
    with db.engine.begin() as conn:
        s = scope(organization_id, current_user(request, conn), conn)
        throttle(conn, s, "chat", 20)
        choices = (
            assistant.catalog(conn, s)
            if payload.automatic or not payload.customer_id
            else None
        )
    query = (
        assistant.plan(payload, choices)
        if payload.automatic
        else (
            assistant.Plan(
                intent="overview",
                customer_id=None,
                billing_period=payload.billing_period
                or (
                    choices["available_periods"][0]
                    if choices["available_periods"]
                    else choices["today"][:7]
                ),
                record_id=None,
                clarification="",
                resolution="resolved",
            )
            if choices
            else None
        )
    )
    with db.engine.begin() as conn:
        s = scope(organization_id, current_user(request, conn), conn)
        if choices is not None and assistant.catalog(conn, s) != choices:
            raise HTTPException(
                409, "Available data or permissions changed. Please retry."
            )
        pack = (
            assistant.evidence(conn, s, payload, query)
            if query
            else source_chat.enrich(
                conn,
                s,
                workspace_summary.presentation(chat.evidence(conn, s, payload), s.role),
            )
        )
    result = chat.respond(pack, payload)
    with db.engine.begin() as conn:
        s = scope(organization_id, current_user(request, conn), conn)
        latest = (
            assistant.evidence(conn, s, payload, query)
            if query
            else source_chat.enrich(
                conn,
                s,
                workspace_summary.presentation(chat.evidence(conn, s, payload), s.role),
            )
        )
        if explanations.pack_hash(latest) != explanations.pack_hash(pack):
            raise HTTPException(
                409,
                "Records changed while the AI was answering. Please send your question again.",
            )
    return result


@router.post("/investigations", status_code=201)
def investigate(organization_id: str, payload: Question, request: Request):
    # Do not keep a DB connection/lock open during the hosted model request.
    with db.engine.begin() as conn:
        s = scope(organization_id, current_user(request, conn), conn)
        throttle(conn, s)
        pack = explanations.evidence(
            conn,
            s,
            payload.customer_id,
            payload.billing_period,
            payload.question,
            payload.evidence_scope,
        )
    result = explanations.explain(pack)
    with db.engine.begin() as conn:
        # Permission/session revocation and changed inputs during model latency invalidate the result.
        s = scope(organization_id, current_user(request, conn), conn)
        latest = explanations.evidence(
            conn,
            s,
            payload.customer_id,
            payload.billing_period,
            payload.question,
            payload.evidence_scope,
        )
        if explanations.pack_hash(latest) != explanations.pack_hash(pack):
            raise HTTPException(
                409, "Source data changed during analysis. Refresh and try again."
            )
        identifier = db.uid()
        conn.execute(
            db.investigations.insert().values(
                organization_id=s.org,
                id=identifier,
                customer_id=payload.customer_id,
                billing_period=payload.billing_period,
                created_by=s.user["id"],
                question=payload.question,
                status=result["status"],
                snapshot={
                    "evidence": pack,
                    "result": result,
                    "provider": explanations.provider_status(),
                    "version": profitability.VERSION,
                },
            )
        )
        return {"id": identifier, "result": result, "evidence": pack}


@router.get("/investigations")
def history(
    customer_id: str | None = None,
    s=Depends(scope),
    conn=Depends(connection, scope="function"),
):
    stmt = select(
        db.investigations.c.id,
        db.investigations.c.customer_id,
        db.investigations.c.billing_period,
        db.investigations.c.question,
        db.investigations.c.status,
        db.investigations.c.created_at,
    ).where(visible(db.investigations, s))
    if customer_id:
        stmt = stmt.where(db.investigations.c.customer_id == customer_id)
    return wire(
        [
            dict(r)
            for r in conn.execute(
                stmt.order_by(db.investigations.c.created_at.desc()).limit(50)
            ).mappings()
        ]
    )


@router.get("/investigations/{identifier}")
def detail(
    identifier: str, s=Depends(scope), conn=Depends(connection, scope="function")
):
    row = (
        conn.execute(
            select(db.investigations).where(
                visible(db.investigations, s), db.investigations.c.id == identifier
            )
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(404, "Investigation not found")
    latest = explanations.evidence(
        conn,
        s,
        row["customer_id"],
        row["billing_period"],
        row["question"],
        row["snapshot"]["evidence"].get("evidence_scope", "combined"),
    )
    if explanations.pack_hash(latest) != explanations.pack_hash(
        row["snapshot"]["evidence"]
    ):
        return {
            "id": identifier,
            "stale": True,
            "result": None,
            "reason": "Inputs or document evidence changed; rerun this investigation.",
        }
    return {"id": identifier, "stale": False, **row["snapshot"]}
