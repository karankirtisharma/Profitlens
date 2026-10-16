"""Add source documents, raw rows and typed financial observations; no data rewrite."""

from alembic import op
from profitlens import database as db

revision = "20261016_sources"
down_revision = "20261016_reported_sales"
branch_labels = None
depends_on = None

TABLES = (
    db.source_documents,
    db.raw_records,
    db.financial_facts,
    db.mapping_profiles,
    db.entity_aliases,
    db.cost_allocations,
)


def upgrade():
    for table in TABLES:
        table.create(op.get_bind())


def downgrade():
    import sqlalchemy as sa

    if any(
        op.get_bind().scalar(sa.select(sa.func.count()).select_from(table))
        for table in TABLES
    ):
        raise RuntimeError(
            "Source data exists: export and explicitly clear it before downgrade"
        )
    for table in reversed(TABLES):
        table.drop(op.get_bind())
