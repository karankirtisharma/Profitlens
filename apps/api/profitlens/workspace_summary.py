"""Deterministic workspace summaries. No external requests or generated queries."""

from decimal import Decimal

from fastapi import HTTPException

from . import profitability
from .finance import money


def summarize(conn, scope, period):
    report = profitability.report(conn, scope, period, limit=200)
    if report["total_customers"] > 200:
        raise HTTPException(
            422,
            "More than 200 visible customers; select a customer. No partial total returned.",
        )
    active = [
        r
        for r in report["items"]
        if r["invoice_lines"]
        or r["expense_lines"]
        or r["calculation_status"] == "blocked"
    ]
    result = {
        "billing_period": report["billing_period"],
        "metrics": {},
        "items": active,
    }
    result["status"] = (
        "no_records"
        if not active
        else "unavailable"
        if any(r["contribution"] is None for r in active)
        else "confirmed"
        if all(r["profitability_status"] == "confirmed" for r in active)
        else "provisional"
    )
    for field in (
        "reported_sales",
        "net_billed_revenue",
        "attributed_cost",
        "contribution",
    ):
        if active and all(r[field] is not None for r in active):
            result["metrics"][field] = {
                "value": money(sum((Decimal(r[field]) for r in active), Decimal(0))),
                "unit": scope.currency,
            }
    metrics = result["metrics"]
    revenue = Decimal(metrics.get("net_billed_revenue", {}).get("value", "0"))
    if "contribution" in metrics and revenue > 0:
        metrics["margin_percent"] = {
            "value": money(Decimal(metrics["contribution"]["value"]) / revenue * 100),
            "unit": "percent",
        }
    metrics["active_customers"] = {"value": str(len(active)), "unit": "customers"}
    metrics["missing_cost_customers"] = {
        "value": str(sum(r["attributed_cost"] is None for r in active)),
        "unit": "customers",
    }
    return result


def presentation(pack, role):
    """UI navigation targets come from authorized records, never generated URLs."""
    customer, period = pack["customer_id"], pack["billing_period"]

    def action(view, label, record=None):
        return dict(
            view=view,
            label=label,
            customer_id=customer,
            billing_period=period,
            record_id=record,
        )

    actions = [action("finance", "Open financial records")]
    if customer:
        actions.append(action("analysis", "Review profitability & issues"))
    for kind, field in (("invoices", "invoice_lines"), ("expenses", "expense_lines")):
        actions.extend(
            action(kind, "Open " + r["id"], r["id"]) for r in pack[field][:3]
        )
    if pack.get("documents"):
        actions.append(action("contracts", "Open contract library"))
    if role in ("admin", "finance"):
        actions.append(action("imports", "Import records"))
    cards = []
    for key, label in (
        ("reported_sales", "Reported sales · tax basis unknown"),
        ("net_billed_revenue", "Net billed revenue"),
        ("attributed_cost", "Attributed cost"),
        ("contribution", "Contribution · not net profit"),
        ("margin_percent", "Contribution margin"),
    ):
        metric = pack["metrics"].get(key)
        if key == "reported_sales" and metric is None:
            continue
        negative = (
            metric
            and key in ("contribution", "margin_percent")
            and Decimal(metric["value"]) < 0
        )
        tone = (
            "negative"
            if negative
            else "warning"
            if metric is None or pack["profitability_status"] != "confirmed"
            else "positive"
            if key in ("contribution", "margin_percent")
            else "neutral"
        )
        cards.append(
            {
                "label": label,
                "value": metric["value"] + " " + metric["unit"]
                if metric
                else "Unavailable",
                "tone": tone,
            }
        )
    pack.update(actions=actions, cards=cards)
    return pack
