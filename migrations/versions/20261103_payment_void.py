"""Allow audited voiding of mistaken payment entries without deleting evidence."""

import sqlalchemy as sa
from alembic import op

revision = "20261103_payment_void"
down_revision = "20261103_operations"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "payments",
        sa.Column("state", sa.String(10), nullable=False, server_default="active"),
    )
    op.add_column(
        "payments",
        sa.Column("void_reason", sa.String(1000), nullable=False, server_default=""),
    )
    op.add_column("payments", sa.Column("voided_at", sa.DateTime(timezone=True)))
    op.create_check_constraint(
        "payment_state", "payments", "state IN ('active', 'void')"
    )
    op.create_check_constraint(
        "payment_void_evidence",
        "payments",
        "(state = 'active' AND void_reason = '' AND voided_at IS NULL) OR (state = 'void' AND length(trim(void_reason)) > 0 AND voided_at IS NOT NULL)",
    )


def downgrade():
    if op.get_bind().scalar(
        sa.text("SELECT count(*) FROM payments WHERE state='void'")
    ):
        raise RuntimeError(
            "Voided payments exist; downgrade would lose reversal history"
        )
    op.drop_constraint("payment_void_evidence", "payments", type_="check")
    op.drop_constraint("payment_state", "payments", type_="check")
    for name in ("voided_at", "void_reason", "state"):
        op.drop_column("payments", name)
