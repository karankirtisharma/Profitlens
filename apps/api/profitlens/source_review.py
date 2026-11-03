"""Deterministic monthly comparisons of authorized source observations, not profit."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Literal
from urllib.parse import quote, urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func, select

from . import database as db
from .security import connection, customer_exists, scope, visible

router = APIRouter(prefix="/api/workspaces/{organization_id}")
ReviewKind = Literal["reported_sales", "expenditure", "cash_inflow", "cash_outflow"]


def month_bounds(period):
    """Return prior start, current start and exclusive next start."""
    try:
        current = date.fromisoformat(period + "-01")
        previous = (current - timedelta(days=1)).replace(day=1)
        following = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
    except (ValueError, OverflowError):
        raise HTTPException(
            422, "Choose a valid month between 0001-02 and 9999-11"
        ) from None
    return previous, current, following


def assemble_review(
    groups,
    *,
    period,
    kind,
    currency,
    organization_id,
    missing_dates=0,
    today=None,
    customer_id=None,
):
    """Summarize SQL groups without turning absent observations into zero."""
    previous_start, current_start, following = month_bounds(period)
    today = today or date.today()
    base = f"/api/workspaces/{quote(organization_id, safe='')}/facts"

    def source_url(current, counterparty=None):
        start = current_start if current else previous_start
        end = (following if current else current_start) - timedelta(days=1)
        params = {
            "kind": kind,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "currency": currency,
        }
        if customer_id:
            params["customer_id"] = customer_id
        if counterparty is not None:
            params["counterparty"] = counterparty
        return base + "?" + urlencode(params)

    buckets = {}
    totals = {"current": Decimal("0"), "previous": Decimal("0")}
    counts = {"current": 0, "previous": 0}
    unknown_counterparty_records = 0
    for row in groups:
        side = row["side"]
        raw_name = row["counterparty"]
        amount = Decimal(str(row["amount"]))
        count = int(row["count"])
        totals[side] += amount
        counts[side] += count
        if not raw_name.strip():
            unknown_counterparty_records += count
        buckets.setdefault(raw_name, {})[side] = {"amount": amount, "count": count}

    comparable_drivers, one_sided_drivers = [], []
    for raw_name, sides in buckets.items():
        current, previous = sides.get("current"), sides.get("previous")
        both = current is not None and previous is not None
        difference = current["amount"] - previous["amount"] if both else None
        driver = {
            "counterparty": raw_name,
            "label": raw_name if raw_name.strip() else "Unknown counterparty",
            "status": "comparable"
            if both
            else "current_only"
            if current
            else "previous_only",
            "current": str(current["amount"]) if current else None,
            "previous": str(previous["amount"]) if previous else None,
            "change": str(difference) if difference is not None else None,
            "current_count": current["count"] if current else 0,
            "previous_count": previous["count"] if previous else 0,
            "current_source_url": source_url(True, raw_name),
            "previous_source_url": source_url(False, raw_name),
        }
        (comparable_drivers if both else one_sided_drivers).append(driver)
    comparable_drivers.sort(
        key=lambda row: (-abs(Decimal(row["change"])), row["counterparty"])
    )
    one_sided_drivers.sort(
        key=lambda row: (
            -abs(Decimal(row["current"] or row["previous"])),
            row["counterparty"],
        )
    )
    comparable = bool(counts["current"] and counts["previous"])
    current_month_incomplete = following > today
    return {
        "period": period,
        "previous_period": previous_start.strftime("%Y-%m"),
        "kind": kind,
        "currency": currency,
        "customer_id": customer_id,
        **{
            side: {
                "amount": str(totals[side]) if counts[side] else None,
                "count": counts[side],
                "source_url": source_url(side == "current"),
            }
            for side in ("current", "previous")
        },
        "comparable": comparable,
        "change": str(totals["current"] - totals["previous"]) if comparable else None,
        "drivers": comparable_drivers[:5] + one_sided_drivers[:3],
        "driver_group_count": len(buckets),
        "missing_dates": missing_dates,
        "unknown_counterparty_records": unknown_counterparty_records,
        "current_month_incomplete": current_month_incomplete,
        "notice": (
            "Comparison of recorded observations only, not profit or a complete accounting period. "
            "Different financial meanings are kept separate. Counterparty labels match exactly; "
            "they are not verified company identities. Groups with records in only one month "
            "have no calculated change: absence does not mean zero. Up to five comparable "
            "changes and three one-month groups are shown; they may not explain the full total. "
            "Unknown dates are excluded from both months. No cause or anomaly is inferred."
        ),
        "review_prompts": [
            "Check that both months include all relevant exports before interpreting the change.",
            "Open source records to check credits, duplicates and unusually large entries.",
            "Review unknown dates and counterparties; do not guess missing relationships.",
        ],
    }


@router.get("/source-review")
def monthly_review(
    period: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    kind: ReviewKind = "expenditure",
    customer_id: str | None = None,
    s=Depends(scope),
    conn=Depends(connection, scope="function"),
):
    previous, current, following = month_bounds(period)
    table = db.financial_facts
    predicate = (
        visible(table, s) & (table.c.kind == kind) & (table.c.currency == s.currency)
    )
    if customer_id:
        customer_exists(conn, s, customer_id)
        predicate &= table.c.customer_id == customer_id
    side = case((table.c.occurred_on >= current, "current"), else_="previous")
    groups = list(
        conn.execute(
            select(
                side.label("side"),
                table.c.counterparty,
                func.sum(table.c.amount).label("amount"),
                func.count().label("count"),
            )
            .where(
                predicate,
                table.c.occurred_on >= previous,
                table.c.occurred_on < following,
            )
            .group_by(side, table.c.counterparty)
        ).mappings()
    )
    missing_dates = conn.scalar(
        select(func.count())
        .select_from(table)
        .where(predicate, table.c.occurred_on.is_(None))
    )
    return assemble_review(
        groups,
        period=period,
        kind=kind,
        currency=s.currency,
        organization_id=s.org,
        missing_dates=missing_dates,
        customer_id=customer_id,
    )
