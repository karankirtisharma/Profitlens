"""Separate planned commitments and recurring drafts from posted financial records."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


def define(metadata):
    def org():
        return sa.Column(
            "organization_id",
            sa.String(36),
            sa.ForeignKey("organizations.id"),
            primary_key=True,
        )

    def fk(local, target, remote):
        return sa.ForeignKeyConstraint(
            ["organization_id", local],
            [f"{target}.organization_id", f"{target}.{remote}"],
        )

    schedules = sa.Table(
        "recurring_schedules",
        metadata,
        org(),
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("customer_id", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("start_on", sa.Date, nullable=False),
        sa.Column("end_on", sa.Date),
        sa.Column("interval_months", sa.Integer, nullable=False),
        sa.Column("next_on", sa.Date, nullable=False),
        sa.Column("due_days", sa.Integer, nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        *[
            sa.Column(k, sa.Numeric(14, 2), nullable=False)
            for k in ("subtotal", "discount", "tax")
        ],
        fk("customer_id", "customers", "customer_id"),
        sa.CheckConstraint(
            "state IN ('active','paused','completed')", name="schedule_state"
        ),
        sa.CheckConstraint(
            "interval_months IN (1,3,12) AND due_days BETWEEN 0 AND 365",
            name="schedule_interval",
        ),
        sa.CheckConstraint(
            "subtotal > 0 AND discount >= 0 AND discount <= subtotal AND tax >= 0",
            name="schedule_amounts",
        ),
        sa.CheckConstraint(
            "end_on IS NULL OR end_on >= start_on", name="schedule_dates"
        ),
    )
    drafts = sa.Table(
        "recurring_drafts",
        metadata,
        org(),
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("schedule_id", sa.String(80), nullable=False),
        sa.Column("issued_on", sa.Date, nullable=False),
        sa.Column("snapshot", JSONB, nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("invoice_id", sa.String(80)),
        fk("schedule_id", "recurring_schedules", "id"),
        fk("invoice_id", "invoices", "invoice_id"),
        sa.UniqueConstraint(
            "organization_id",
            "schedule_id",
            "issued_on",
            name="uq_recurring_drafts_organization_id",
        ),
        sa.CheckConstraint(
            "(state='draft' AND invoice_id IS NULL) OR (state='issued' AND invoice_id IS NOT NULL) OR (state='skipped' AND invoice_id IS NULL)",
            name="draft_state",
        ),
    )
    orders = sa.Table(
        "purchase_orders",
        metadata,
        org(),
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("vendor_id", sa.String(80), nullable=False),
        sa.Column("ordered_on", sa.Date, nullable=False),
        sa.Column("expected_on", sa.Date),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("notes", sa.String(1000), nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("total", sa.Numeric(14, 2), nullable=False),
        sa.Column("bill_id", sa.String(80)),
        fk("vendor_id", "vendors", "vendor_id"),
        fk("bill_id", "bills", "bill_id"),
        sa.CheckConstraint(
            "state IN ('draft','approved','cancelled','billed')", name="order_state"
        ),
        sa.CheckConstraint(
            "(state='billed') = (bill_id IS NOT NULL)", name="order_bill_state"
        ),
        sa.CheckConstraint("total > 0", name="order_positive"),
    )
    lines = sa.Table(
        "purchase_order_lines",
        metadata,
        org(),
        sa.Column("order_id", sa.String(80), primary_key=True),
        sa.Column("line", sa.Integer, primary_key=True),
        sa.Column("item_id", sa.String(80)),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("tax", sa.Numeric(14, 2), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        fk("order_id", "purchase_orders", "id"),
        fk("item_id", "items", "item_id"),
        sa.CheckConstraint(
            "quantity > 0 AND unit_price >= 0 AND tax >= 0 AND amount > 0",
            name="order_line_amounts",
        ),
    )
    return schedules, drafts, orders, lines
