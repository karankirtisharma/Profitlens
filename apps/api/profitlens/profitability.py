"""Recorded contribution, attestations and reviewable financial discrepancies."""

import hashlib
import json
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from . import database as db
from . import finance
from .records import log_event, wire
from .security import visible

VERSION = "profitability-v1"


def previous_period(period):
    finance.valid_period(period)
    return (date.fromisoformat(period + "-01") - timedelta(days=1)).strftime("%Y-%m")


def fingerprint(item):
    # Include values and identities: a changed amount or newly imported row invalidates review.
    value = [
        item["customer_id"],
        item["billing_period"],
        item["currency"],
        sorted(item["expense_lines"], key=lambda row: row["id"]),
    ]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def metrics(item, review=None):
    result = dict(item)
    result["cost_input_hash"] = fingerprint(item)
    confirmed = bool(review and review["input_hash"] == result["cost_input_hash"])
    if confirmed:
        result["warnings"] = [
            w for w in item["warnings"] if w["code"] != "cost_completeness_unverified"
        ]
        result["cost_completeness"] = "confirmed"
    result["completeness"] = (
        "confirmed" if confirmed else "stale" if review else "unverified"
    )
    revenue, cost = item["net_billed_revenue"], item["attributed_cost"]
    if revenue is None or cost is None or item["calculation_status"] == "blocked":
        result.update(
            contribution=None, margin_percent=None, profitability_status="unavailable"
        )
    else:
        contribution = Decimal(revenue) - Decimal(cost)
        result.update(
            contribution=finance.money(contribution),
            margin_percent=finance.money(contribution / Decimal(revenue) * 100)
            if Decimal(revenue) > 0
            else None,
            profitability_status="confirmed" if confirmed else "provisional",
        )
    return result


def findings(
    current,
    previous,
    contracts,
    cost_threshold=Decimal("25"),
    margin_threshold=Decimal("10"),
    pricing_tolerance=Decimal("1"),
):
    """Economic rules stay separate from quality warnings; no claim of causation."""
    output = []

    def add(rule, actual, expected, delta, unit, evidence, formula):
        output.append(
            dict(
                id=f"{current['customer_id']}:{current['billing_period']}:{rule}",
                rule=rule,
                severity="review",
                actual=finance.money(actual),
                expected=finance.money(expected),
                difference=finance.money(delta),
                unit=unit,
                source_ids=evidence,
                formula=formula,
                limitation="Candidate discrepancy for human review; does not establish cause or savings.",
            )
        )

    codes = {w["code"] for w in current["warnings"]}
    matched = [c for c in current["contracts"] if c["full_month_match"]]
    if (
        current["net_billed_revenue"] is not None
        and len(matched) == 1
        and not codes.intersection(
            {
                "overlapping_contracts",
                "partial_contract_period",
                "unreviewed_contract",
                "invalid_contract_reference",
            }
        )
    ):
        terms = next((c for c in contracts if c["id"] == matched[0]["id"]), None)
        if terms and terms["monthly_rate"] is not None:
            expected = terms["monthly_rate"] - terms["monthly_discount"]
            # Pricing compares pre-refund billed charges to reviewed fixed monthly terms.
            actual = sum(
                (
                    Decimal(r["subtotal"]) - Decimal(r["discount"])
                    for r in current["invoice_lines"]
                ),
                Decimal(0),
            )
            if abs(actual - expected) > pricing_tolerance:
                add(
                    "pricing_mismatch",
                    actual,
                    expected,
                    actual - expected,
                    current["currency"],
                    ["invoice:" + r["id"] for r in current["invoice_lines"]]
                    + ["contract:" + terms["id"]],
                    "sum(subtotal - discount) - (reviewed monthly rate - monthly discount); refunds excluded from price comparison",
                )
    if previous and all(
        r["profitability_status"] == "confirmed" for r in (current, previous)
    ):
        now, before = (
            Decimal(current["attributed_cost"]),
            Decimal(previous["attributed_cost"]),
        )
        sources = [
            "expense:" + r["id"]
            for item in (current, previous)
            for r in item["expense_lines"]
        ]
        if before > 0 and (now - before) / before * 100 > cost_threshold:
            add(
                "cost_increase",
                now,
                before,
                now - before,
                current["currency"],
                sources,
                f"(current cost - prior cost) / prior cost * 100 > {cost_threshold}%",
            )
        if (
            current["margin_percent"] is not None
            and previous["margin_percent"] is not None
        ):
            now_margin, old_margin = (
                Decimal(current["margin_percent"]),
                Decimal(previous["margin_percent"]),
            )
            if old_margin - now_margin > margin_threshold:
                sources += [
                    "invoice:" + r["id"]
                    for item in (current, previous)
                    for r in item["invoice_lines"]
                ]
                add(
                    "margin_decline",
                    now_margin,
                    old_margin,
                    now_margin - old_margin,
                    "percentage_points",
                    sources,
                    f"prior margin - current margin > {margin_threshold} percentage points",
                )
    return output


def report(
    conn,
    scope,
    period,
    customer_id=None,
    limit=25,
    offset=0,
    cost_threshold=Decimal("25"),
    margin_threshold=Decimal("10"),
    pricing_tolerance=Decimal("1"),
):
    raw = finance.report(conn, scope, period, customer_id, limit, offset)
    period = raw["billing_period"]
    if not period:
        return raw | {"items": [], "version": VERSION}
    prior = finance.report(
        conn, scope, previous_period(period), customer_id, limit, offset
    )
    reviews = {
        (r["customer_id"], r["billing_period"]): r
        for r in conn.execute(
            select(db.cost_reviews).where(
                visible(db.cost_reviews, scope),
                db.cost_reviews.c.customer_id.in_(
                    [r["customer_id"] for r in raw["items"]]
                ),
                db.cost_reviews.c.billing_period.in_([period, previous_period(period)]),
            )
        ).mappings()
    }
    previous = {
        r["customer_id"]: metrics(
            r, reviews.get((r["customer_id"], r["billing_period"]))
        )
        for r in prior["items"]
    }
    items = []
    for row in raw["items"]:
        item = metrics(row, reviews.get((row["customer_id"], period)))
        contracts = list(
            conn.execute(
                select(db.contracts).where(
                    visible(db.contracts, scope),
                    db.contracts.c.id.in_([c["id"] for c in row["contracts"]]),
                )
            ).mappings()
        )
        before = previous.get(row["customer_id"])
        item["previous"] = (
            {
                k: before[k]
                for k in (
                    "billing_period",
                    "net_billed_revenue",
                    "attributed_cost",
                    "contribution",
                    "margin_percent",
                    "profitability_status",
                )
            }
            if before
            else None
        )
        item["findings"] = findings(
            item, before, contracts, cost_threshold, margin_threshold, pricing_tolerance
        )
        item["comparison_limitation"] = (
            "Cost and margin findings require current and prior costs to be confirmed. A zero prior cost has no percentage increase."
        )
        items.append(item)
    return wire(
        raw
        | {
            "items": items,
            "version": VERSION,
            "thresholds": {
                "cost_increase_percent": str(cost_threshold),
                "margin_decline_points": str(margin_threshold),
                "pricing_tolerance": str(pricing_tolerance),
            },
        }
    )


def attest(conn, scope, customer, period, input_hash, note):
    item = finance.report(conn, scope, period, customer, 1, 0)["items"][0]
    if item["attributed_cost"] is None or item["calculation_status"] == "blocked":
        raise HTTPException(
            409,
            "Valid expense records are required; add an explicit zero-cost record if appropriate.",
        )
    if fingerprint(item) != input_hash:
        raise HTTPException(
            409, "Costs changed. Refresh and review the current inputs."
        )
    values = dict(
        organization_id=scope.org,
        customer_id=customer,
        billing_period=period,
        input_hash=input_hash,
        reviewed_by=scope.user["id"],
        note=note,
        created_at=db.now(),
    )
    conn.execute(
        insert(db.cost_reviews)
        .values(**values)
        .on_conflict_do_update(
            index_elements=["organization_id", "customer_id", "billing_period"],
            set_=values,
        )
    )
    log_event(conn, scope, "cost_review", customer, "confirmed", values)
    return {"status": "confirmed"}
