"""Add cost attestations, versioned document passages and investigation history."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20261015_roadmap"
down_revision = "47e0ed9226fa"
branch_labels = None
depends_on = None


def customer_fk():
    return sa.ForeignKeyConstraint(
        ["organization_id", "customer_id"],
        ["customers.organization_id", "customers.customer_id"],
    )


def org():
    return sa.Column(
        "organization_id",
        sa.String(36),
        sa.ForeignKey("organizations.id"),
        primary_key=True,
    )


def upgrade():
    op.create_table(
        "cost_reviews",
        org(),
        sa.Column("customer_id", sa.String(80), primary_key=True),
        sa.Column("billing_period", sa.String(7), primary_key=True),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column(
            "reviewed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("note", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        customer_fk(),
    )
    op.create_table(
        "document_passages",
        org(),
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("contract_id", sa.String(36), nullable=False),
        sa.Column("customer_id", sa.String(80), nullable=False),
        sa.Column("page", sa.Integer, nullable=False),
        sa.Column("content", sa.String(2400), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("index_version", sa.String(160), nullable=False),
        sa.Column("embedding", JSONB),
        customer_fk(),
        sa.ForeignKeyConstraint(
            ["organization_id", "contract_id"],
            ["contracts.organization_id", "contracts.id"],
        ),
        sa.CheckConstraint("page > 0", name="passage_page"),
    )
    op.create_table(
        "investigations",
        org(),
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("customer_id", sa.String(80), nullable=False),
        sa.Column("billing_period", sa.String(7), nullable=False),
        sa.Column(
            "created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("question", sa.String(1000), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("snapshot", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        customer_fk(),
    )


def downgrade():
    op.drop_table("investigations")
    op.drop_table("document_passages")
    op.drop_table("cost_reviews")
