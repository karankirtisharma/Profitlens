"""Preserve unknown invoice breakdowns without changing existing verified records."""

import sqlalchemy as sa
from alembic import op

revision = "20261016_reported_sales"
down_revision = "20261015_roadmap"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "invoices",
        sa.Column(
            "amount_basis", sa.String(20), nullable=False, server_default="verified"
        ),
    )
    for name in ("subtotal", "discount", "tax", "refund"):
        op.alter_column("invoices", name, nullable=True)
    op.drop_constraint("invoice_amounts", "invoices", type_="check")
    op.create_check_constraint(
        "invoice_amounts",
        "invoices",
        "total >= 0 AND ((amount_basis = 'reported_sales' AND subtotal IS NULL AND discount IS NULL AND tax IS NULL AND refund IS NULL) OR (amount_basis = 'verified' AND subtotal IS NOT NULL AND discount IS NOT NULL AND tax IS NOT NULL AND refund IS NOT NULL AND subtotal >= 0 AND discount >= 0 AND tax >= 0 AND refund >= 0 AND discount + refund <= subtotal AND total = subtotal - discount + tax - refund))",
    )


def downgrade():
    if (
        op.get_bind()
        .execute(
            sa.text("SELECT 1 FROM invoices WHERE amount_basis <> 'verified' LIMIT 1")
        )
        .first()
    ):
        raise RuntimeError(
            "Export and explicitly remove reported-sales records before downgrade; never invent breakdowns"
        )
    op.drop_constraint("invoice_amounts", "invoices", type_="check")
    for name in ("subtotal", "discount", "tax", "refund"):
        op.alter_column("invoices", name, nullable=False)
    op.drop_column("invoices", "amount_basis")
    op.create_check_constraint(
        "invoice_amounts",
        "invoices",
        "subtotal >= 0 AND discount >= 0 AND tax >= 0 AND refund >= 0 AND total >= 0 AND discount + refund <= subtotal AND total = subtotal - discount + tax - refund",
    )
