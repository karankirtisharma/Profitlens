"""Week 4: exact recorded revenue/costs, with explicit evidence limitations."""

import calendar
from collections import defaultdict
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, select, union_all

from . import database as db
from .ingestion.models import Expense, Invoice, PeriodRecord
from .records import wire
from .security import customer_exists, visible

VERSION = "revenue-cost-v1"
ZERO = Decimal("0.00")
MAX_INPUTS = 10000


def money(value):
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")


def valid_period(value):
    try:
        return PeriodRecord.valid_period(value)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, "billing_period must be a valid YYYY-MM") from exc


def calculate(
    organization_id, customer_id, period, currency, invoices, expenses, contracts
):
    """Pure calculation over one explicitly scoped customer/month; no AI or floats."""
    valid_period(period)
    warnings = []

    def warn(code, message, record_id=None):
        warnings.append(dict(code=code, message=message, record_id=record_id))

    def checked(rows, model, id_key):
        seen, output, blocked = {}, [], False
        for row in rows:
            rid = row.get(id_key, "unknown")
            if (
                row.get("organization_id"),
                row.get("customer_id"),
                row.get("billing_period"),
            ) != (organization_id, customer_id, period):
                warn(
                    "invalid_reference",
                    "Record organization, customer or billing month does not match this calculation.",
                    rid,
                )
                blocked = True
                continue
            if row.get("currency") != currency:
                warn(
                    "mixed_currency",
                    "Currency mismatch; no currency conversion is performed.",
                    rid,
                )
                blocked = True
                continue
            try:
                record = model.model_validate(
                    {k: row[k] for k in model.model_fields if k in row}
                )
                values = record.model_dump()
                if any(
                    isinstance(v, Decimal) and (not v.is_finite() or v >= 10**12)
                    for v in values.values()
                ):
                    raise ValueError("Unsupported amount")
            except (ValidationError, ValueError):
                warn(
                    "invalid_amount",
                    "Invalid financial input; the affected total is unavailable until corrected.",
                    rid,
                )
                blocked = True
                continue
            if rid in seen:
                if seen[rid] == values:
                    warn(
                        "duplicate_record",
                        "Repeated stable record ID counted once.",
                        rid,
                    )
                else:
                    warn(
                        "conflicting_duplicate",
                        "The same record ID has conflicting amounts; its total is unavailable.",
                        rid,
                    )
                    blocked = True
                continue
            seen[rid] = values
            output.append(values | {"source": row.get("source", {})})
        return output, blocked

    inv, revenue_blocked = checked(invoices, Invoice, "invoice_id")
    exp, cost_blocked = checked(expenses, Expense, "expense_id")
    has_reported = any(r["amount_basis"] == "reported_sales" for r in inv)
    if has_reported:
        warn(
            "unknown_invoice_basis",
            "Reported sales amounts have no verified tax, discount or refund breakdown. Net revenue, contribution, margin and pricing comparisons are unavailable.",
        )

    def optional_money(value):
        return money(value) if value is not None else None

    invoice_lines = [
        dict(
            id=r["invoice_id"],
            amount_basis=r["amount_basis"],
            subtotal=optional_money(r["subtotal"]),
            discount=optional_money(r["discount"]),
            refund=optional_money(r["refund"]),
            tax_excluded=optional_money(r["tax"]),
            payable_total=money(r["total"])
            if r["amount_basis"] == "verified"
            else None,
            reported_sales=money(r["total"])
            if r["amount_basis"] == "reported_sales"
            else None,
            net_billed_revenue=money(r["subtotal"] - r["discount"] - r["refund"])
            if r["amount_basis"] == "verified"
            else None,
            source=r["source"],
        )
        for r in inv
    ]
    expense_lines = [
        dict(
            id=r["expense_id"],
            category=r["category"],
            amount=money(r["amount"]),
            source=r["source"],
        )
        for r in exp
    ]
    revenue = (
        None
        if revenue_blocked or not inv or has_reported
        else sum((r["subtotal"] - r["discount"] - r["refund"] for r in inv), ZERO)
    )
    cost = None if cost_blocked or not exp else sum((r["amount"] for r in exp), ZERO)
    if not invoices:
        warn(
            "missing_invoices",
            "No invoices for this customer/month; revenue is unavailable, not assumed zero.",
        )
    if not expenses:
        warn(
            "missing_costs",
            "No attributed expense rows for this customer/month; costs are unknown, not zero.",
        )
    if revenue == ZERO:
        warn(
            "zero_revenue",
            "Net billed revenue is zero. A margin percentage cannot be calculated.",
        )
    if exp:
        warn(
            "cost_completeness_unverified",
            "This is the sum of recorded costs. The dataset has no confirmation that all costs were supplied.",
        )

    start = date.fromisoformat(f"{period}-01")
    end = start.replace(day=calendar.monthrange(start.year, start.month)[1])
    matched, partial, valid_contracts = [], [], []
    for contract in contracts:
        if (contract.get("organization_id"), contract.get("customer_id")) != (
            organization_id,
            customer_id,
        ):
            warn(
                "invalid_contract_reference",
                "Contract does not belong to this organization/customer.",
            )
            continue
        valid_contracts.append(contract)
        if contract["state"] != "reviewed":
            continue
        if contract.get("currency") != currency:
            warn(
                "contract_currency_mismatch",
                "Reviewed contract currency differs from the workspace.",
                contract["id"],
            )
            continue
        first, last = contract.get("effective_from"), contract.get("effective_to")
        if not isinstance(first, date) or not isinstance(last, date) or last < first:
            warn(
                "invalid_contract_period",
                "Reviewed contract dates are invalid.",
                contract["id"],
            )
            continue
        if first <= start and last >= end:
            matched.append(contract)
        elif first <= end and last >= start:
            partial.append(contract)
    if valid_contracts and not matched:
        warn(
            "unmatched_contract_period",
            "No reviewed same-currency contract covers the full billing month. Pricing comparisons are unavailable.",
        )
    if partial:
        warn(
            "partial_contract_period",
            "A contract covers only part of this month. Automatic proration and combining partial contracts are unsupported.",
        )
    if len(matched) > 1 or (matched and partial):
        warn(
            "overlapping_contracts",
            "Multiple reviewed contract periods overlap this month; pricing requires manual review.",
        )
    if any(c["state"] != "reviewed" for c in valid_contracts):
        warn(
            "unreviewed_contract",
            "Unreviewed documents are excluded from effective-period matching.",
        )
    return dict(
        customer_id=customer_id,
        billing_period=period,
        currency=currency,
        reported_sales=money(
            sum(
                (r["total"] for r in inv if r["amount_basis"] == "reported_sales"), ZERO
            )
        )
        if has_reported and not revenue_blocked
        else None,
        contract_status="applicable"
        if len(matched) == 1 and not partial
        else "unavailable"
        if valid_contracts
        else "not_provided",
        net_billed_revenue=money(revenue) if revenue is not None else None,
        attributed_cost=money(cost) if cost is not None else None,
        cost_completeness="unverified" if cost is not None else "unavailable",
        calculation_status="blocked"
        if revenue_blocked or cost_blocked
        else "recorded_only",
        invoice_lines=invoice_lines,
        expense_lines=expense_lines,
        warnings=warnings,
        contracts=[
            dict(
                id=c["id"],
                filename=c["filename"],
                state=c["state"],
                source_page=c.get("source_page"),
                effective_from=c.get("effective_from"),
                effective_to=c.get("effective_to"),
                full_month_match=c in matched,
            )
            for c in valid_contracts
        ],
    )


def report(conn, scope, billing_period=None, customer_id=None, limit=25, offset=0):
    if billing_period is not None:
        valid_period(billing_period)
    if customer_id:
        customer_exists(conn, scope, customer_id)
    # Writers take an exclusive lock on this same workspace row: keep the read coherent.
    conn.execute(
        select(db.organizations.c.id)
        .where(db.organizations.c.id == scope.org)
        .with_for_update(read=True)
    ).first()
    predicates = {
        t.name: visible(t, scope)
        for t in (db.customers, db.invoices, db.expenses, db.contracts)
    }
    if customer_id:
        predicates = {
            t.name: predicates[t.name] & (t.c.customer_id == customer_id)
            for t in (db.customers, db.invoices, db.expenses, db.contracts)
        }
    if billing_period is None:
        periods = union_all(
            *[
                select(t.c.billing_period).where(predicates[t.name])
                for t in (db.invoices, db.expenses)
            ]
        ).subquery()
        billing_period = conn.execute(
            select(func.max(periods.c.billing_period))
        ).scalar_one_or_none()
    total = conn.execute(
        select(func.count())
        .select_from(db.customers)
        .where(predicates[db.customers.name])
    ).scalar_one()
    customers = list(
        conn.execute(
            select(db.customers.c.customer_id, db.customers.c.name)
            .where(predicates[db.customers.name])
            .order_by(db.customers.c.customer_id)
            .limit(limit)
            .offset(offset)
        ).mappings()
    )
    if billing_period is None:
        return dict(
            billing_period=None,
            currency=scope.currency,
            total_customers=total,
            offset=offset,
            limit=limit,
            items=[],
            calculation_version=VERSION,
        )
    valid_period(billing_period)
    ids = [r["customer_id"] for r in customers]
    grouped = {}
    for table in (db.invoices, db.expenses, db.contracts):
        columns = (
            table
            if table is not db.contracts
            else [
                table.c[k]
                for k in (
                    "id",
                    "organization_id",
                    "customer_id",
                    "filename",
                    "state",
                    "source_page",
                    "effective_from",
                    "effective_to",
                    "currency",
                )
            ]
        )
        query = select(*columns) if isinstance(columns, list) else select(columns)
        query = query.where(predicates[table.name], table.c.customer_id.in_(ids))
        if table is not db.contracts:
            query = query.where(table.c.billing_period == billing_period)
        id_key = (
            "id"
            if table is db.contracts
            else ("invoice_id" if table is db.invoices else "expense_id")
        )
        rows = list(
            conn.execute(
                query.order_by(table.c[id_key]).limit(MAX_INPUTS + 1)
            ).mappings()
        )
        if len(rows) > MAX_INPUTS:
            raise HTTPException(
                422,
                "Too many source records for one calculation; select a customer or a smaller customer page. No partial total was returned.",
            )
        groups = defaultdict(list)
        for row in rows:
            groups[row["customer_id"]].append(dict(row))
        grouped[table.name] = groups
    return wire(
        dict(
            billing_period=billing_period,
            currency=scope.currency,
            total_customers=total,
            offset=offset,
            limit=limit,
            calculation_version=VERSION,
            items=[
                calculate(
                    scope.org,
                    c["customer_id"],
                    billing_period,
                    scope.currency,
                    grouped[db.invoices.name][c["customer_id"]],
                    grouped[db.expenses.name][c["customer_id"]],
                    grouped[db.contracts.name][c["customer_id"]],
                )
                | {"customer_name": c["name"]}
                for c in customers
            ],
        )
    )
