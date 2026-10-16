"""Permission-scoped summaries over all stored records, not a UI preview page."""

from sqlalchemy import case, func, select

from . import database as db
from .records import wire
from .security import visible


def summary(conn, scope):
    conn.execute(
        select(db.organizations.c.id)
        .where(db.organizations.c.id == scope.org)
        .with_for_update(read=True)
    ).first()
    counts = {
        table.name: conn.scalar(
            select(func.count()).select_from(table).where(visible(table, scope))
        )
        for table in (db.customers, db.invoices, db.expenses, db.contracts)
    }
    i = db.invoices
    reported = i.c.amount_basis == "reported_sales"
    net = i.c.subtotal - i.c.discount - i.c.refund
    months = (
        conn.execute(
            select(
                i.c.billing_period,
                func.count().label("invoice_count"),
                func.sum(case((reported, 1), else_=0)).label("reported_count"),
                func.sum(case((reported, i.c.total))).label("reported_sales"),
                func.sum(case((~reported, net))).label("verified_net_revenue"),
            )
            .where(visible(i, scope))
            .group_by(i.c.billing_period)
            .order_by(i.c.billing_period)
        )
        .mappings()
        .all()
    )
    top = (
        conn.execute(
            select(
                i.c.customer_id,
                func.sum(i.c.total).label("reported_sales"),
                func.count().label("invoice_count"),
            )
            .where(visible(i, scope), reported)
            .group_by(i.c.customer_id)
            .order_by(func.sum(i.c.total).desc(), i.c.customer_id)
            .limit(5)
        )
        .mappings()
        .all()
    )
    totals = (
        conn.execute(
            select(
                func.sum(case((reported, i.c.total))).label("reported_sales"),
                func.sum(case((~reported, net))).label("verified_net_revenue"),
                func.sum(case((reported, 1), else_=0)).label("reported_count"),
            ).where(visible(i, scope))
        )
        .mappings()
        .one()
    )
    counts["financial_facts"] = conn.scalar(
        select(func.count())
        .select_from(db.financial_facts)
        .where(visible(db.financial_facts, scope))
    )
    counts["source_documents"] = (
        conn.scalar(
            select(func.count())
            .select_from(db.source_documents)
            .where(db.source_documents.c.organization_id == scope.org)
        )
        if scope.role != "analyst"
        else 0
    )
    counts["review_tasks"] = (
        conn.scalar(
            select(func.count())
            .select_from(db.source_documents)
            .where(
                db.source_documents.c.organization_id == scope.org,
                db.source_documents.c.state != "confirmed",
            )
        )
        if scope.role != "analyst"
        else 0
    )
    return wire(
        {
            "currency": scope.currency,
            "counts": counts,
            "months": [dict(r) for r in months],
            "top_reported_customers": [dict(r) for r in top],
            **dict(totals),
            "contract_status": "not_provided"
            if not counts["contracts"]
            else "review_required",
            "limitations": [
                "Reported sales are source amounts, not verified net revenue, cash receipts or profit.",
                "Missing costs remain unknown. Contracts are optional; pricing checks require reviewed applicable terms.",
                "Trends describe only the imported selection, not the complete business.",
            ],
        }
    )
