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
    counts["reviewed_contracts"] = conn.scalar(
        select(func.count())
        .select_from(db.contracts)
        .where(visible(db.contracts, scope), db.contracts.c.state == "reviewed")
    )
    record_months = {}
    for table, key in ((db.invoices, "invoice_count"), (db.expenses, "expense_count")):
        for period, count in conn.execute(
            select(table.c.billing_period, func.count())
            .where(visible(table, scope))
            .group_by(table.c.billing_period)
        ):
            row = record_months.setdefault(
                period,
                {"billing_period": period, "invoice_count": 0, "expense_count": 0},
            )
            row[key] = count
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
    counts["source_counterparties"] = conn.scalar(
        select(func.count(func.distinct(db.financial_facts.c.counterparty))).where(
            visible(db.financial_facts, scope), db.financial_facts.c.counterparty != ""
        )
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
    # Separate semantic series; source observations never become ledger revenue/costs.
    source_series = [
        dict(r)
        for r in conn.execute(
            select(
                func.to_char(db.financial_facts.c.occurred_on, "YYYY-MM").label(
                    "period"
                ),
                db.financial_facts.c.kind,
                func.sum(db.financial_facts.c.amount).label("amount"),
                func.count().label("records"),
            )
            .where(
                visible(db.financial_facts, scope),
                db.financial_facts.c.currency == scope.currency,
            )
            .group_by("period", db.financial_facts.c.kind)
            .order_by("period")
        ).mappings()
    ]
    cost_series = [
        dict(r)
        for r in conn.execute(
            select(
                db.expenses.c.billing_period.label("period"),
                func.sum(db.expenses.c.amount).label("amount"),
            )
            .where(visible(db.expenses, scope))
            .group_by(db.expenses.c.billing_period)
            .order_by(db.expenses.c.billing_period)
        ).mappings()
    ]
    return wire(
        {
            "source_series": source_series,
            "cost_series": cost_series,
            "currency": scope.currency,
            "counts": counts,
            "months": [dict(r) for r in months],
            "record_months": [record_months[key] for key in sorted(record_months)],
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
