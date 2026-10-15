"""PostgreSQL schema. Every business relationship includes its organization key."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB

from .config import settings

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)
engine = create_engine(settings.database_url, pool_pre_ping=True)


def now():
    return datetime.now(UTC)


def uid():
    return str(uuid.uuid4())


def orgcol():
    return Column(
        "organization_id", String(36), ForeignKey("organizations.id"), primary_key=True
    )


def timestamp():
    return Column("created_at", DateTime(timezone=True), nullable=False, default=now)


organizations = Table(
    "organizations",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("name", String(120), nullable=False),
    Column("currency", String(3), nullable=False, default="INR"),
)
users = Table(
    "users",
    metadata,
    Column("id", String(36), primary_key=True, default=uid),
    Column("email", String(254), unique=True, nullable=False),
    Column("name", String(120), nullable=False),
    Column("password_hash", String(255), nullable=False),
)
memberships = Table(
    "memberships",
    metadata,
    orgcol(),
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("role", String(20), nullable=False),
    CheckConstraint("role IN ('admin', 'finance', 'analyst')", name="valid_role"),
)
sessions = Table(
    "sessions",
    metadata,
    Column("token_hash", String(64), primary_key=True),
    Column("user_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
)
login_limits = Table(
    "login_limits",
    metadata,
    Column("key", String(64), primary_key=True),
    Column("attempts", Integer, nullable=False),
    Column("reset_at", DateTime(timezone=True), nullable=False),
)

customers = Table(
    "customers",
    metadata,
    orgcol(),
    Column("customer_id", String(80), primary_key=True),
    Column("name", String(200), nullable=False),
    Column("industry", String(200), nullable=False, default=""),
    Column("source", JSONB, nullable=False, default=dict),
    timestamp(),
)
grants = Table(
    "customer_grants",
    metadata,
    orgcol(),
    Column("user_id", String(36), primary_key=True),
    Column("customer_id", String(80), primary_key=True),
    ForeignKeyConstraint(
        ["organization_id", "user_id"],
        ["memberships.organization_id", "memberships.user_id"],
    ),
    ForeignKeyConstraint(
        ["organization_id", "customer_id"],
        ["customers.organization_id", "customers.customer_id"],
    ),
)


def record_columns(id_name):
    return [
        orgcol(),
        Column(id_name, String(80), primary_key=True),
        Column("customer_id", String(80), nullable=False, index=True),
        Column("billing_period", String(7), nullable=False),
        Column("currency", String(3), nullable=False),
        Column("source", JSONB, nullable=False, default=dict),
        timestamp(),
        ForeignKeyConstraint(
            ["organization_id", "customer_id"],
            ["customers.organization_id", "customers.customer_id"],
        ),
    ]


invoices = Table(
    "invoices",
    metadata,
    *record_columns("invoice_id"),
    *[
        Column(key, Numeric(14, 2), nullable=False)
        for key in ("subtotal", "discount", "tax", "refund", "total")
    ],
    CheckConstraint(
        "subtotal >= 0 AND discount >= 0 AND tax >= 0 AND refund >= 0 AND total >= 0 AND discount + refund <= subtotal AND total = subtotal - discount + tax - refund",
        name="invoice_amounts",
    ),
)
expenses = Table(
    "expenses",
    metadata,
    *record_columns("expense_id"),
    Column("category", String(200), nullable=False),
    Column("amount", Numeric(14, 2), nullable=False),
    CheckConstraint("amount >= 0", name="expense_amount"),
)
batches = Table(
    "import_batches",
    metadata,
    orgcol(),
    Column("id", String(36), primary_key=True, default=uid),
    Column("kind", String(20), nullable=False),
    Column("fingerprint", String(64), nullable=False),
    Column("filename", String(200), nullable=False),
    Column("state", String(20), nullable=False),
    Column("rows", JSONB, nullable=False),
    Column("issues", JSONB, nullable=False),
    Column("result", JSONB, nullable=False, default=dict),
    Column("created_by", String(36), ForeignKey("users.id"), nullable=False),
    timestamp(),
    UniqueConstraint("organization_id", "kind", "fingerprint"),
)
contracts = Table(
    "contracts",
    metadata,
    orgcol(),
    Column("id", String(36), primary_key=True, default=uid),
    Column("customer_id", String(80), nullable=False),
    Column("filename", String(200), nullable=False),
    Column("file_key", String(40), nullable=False),
    Column("fingerprint", String(64), nullable=False),
    Column("pages", JSONB, nullable=False),
    Column("state", String(20), nullable=False, default="unreviewed"),
    Column("effective_from", Date),
    Column("effective_to", Date),
    Column("currency", String(3)),
    Column("monthly_rate", Numeric(14, 2)),
    Column("monthly_discount", Numeric(14, 2)),
    Column("source_page", Integer),
    Column("reviewed_by", String(36), ForeignKey("users.id")),
    Column("reviewed_at", DateTime(timezone=True)),
    timestamp(),
    ForeignKeyConstraint(
        ["organization_id", "customer_id"],
        ["customers.organization_id", "customers.customer_id"],
    ),
    UniqueConstraint("organization_id", "customer_id", "fingerprint"),
    CheckConstraint("state IN ('unreviewed','reviewed')", name="contract_state"),
    CheckConstraint(
        "state <> 'reviewed' OR (effective_from IS NOT NULL AND effective_to IS NOT NULL AND effective_to >= effective_from AND monthly_rate IS NOT NULL AND monthly_discount IS NOT NULL AND monthly_rate >= monthly_discount AND monthly_discount >= 0 AND source_page IS NOT NULL AND currency IS NOT NULL AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)",
        name="reviewed_terms",
    ),
)
audit = Table(
    "record_events",
    metadata,
    orgcol(),
    Column("id", String(36), primary_key=True, default=uid),
    Column("kind", String(30), nullable=False),
    Column("record_id", String(80), nullable=False),
    Column("actor_id", String(36), ForeignKey("users.id"), nullable=False),
    Column("action", String(30), nullable=False),
    Column("snapshot", JSONB, nullable=False),
    timestamp(),
)

# Additive roadmap tables; existing financial/import records remain unchanged.
cost_reviews = Table(
    "cost_reviews",
    metadata,
    orgcol(),
    Column("customer_id", String(80), primary_key=True),
    Column("billing_period", String(7), primary_key=True),
    Column("input_hash", String(64), nullable=False),
    Column("reviewed_by", String(36), ForeignKey("users.id"), nullable=False),
    Column("note", String(500), nullable=False),
    timestamp(),
    ForeignKeyConstraint(
        ["organization_id", "customer_id"],
        ["customers.organization_id", "customers.customer_id"],
    ),
)
passages = Table(
    "document_passages",
    metadata,
    orgcol(),
    Column("id", String(64), primary_key=True),
    Column("contract_id", String(36), nullable=False),
    Column("customer_id", String(80), nullable=False),
    Column("page", Integer, nullable=False),
    Column("content", String(2400), nullable=False),
    Column("content_hash", String(64), nullable=False),
    Column("index_version", String(160), nullable=False),
    Column("embedding", JSONB),
    ForeignKeyConstraint(
        ["organization_id", "contract_id"],
        ["contracts.organization_id", "contracts.id"],
    ),
    ForeignKeyConstraint(
        ["organization_id", "customer_id"],
        ["customers.organization_id", "customers.customer_id"],
    ),
    CheckConstraint("page > 0", name="passage_page"),
)
investigations = Table(
    "investigations",
    metadata,
    orgcol(),
    Column("id", String(36), primary_key=True, default=uid),
    Column("customer_id", String(80), nullable=False),
    Column("billing_period", String(7), nullable=False),
    Column("created_by", String(36), ForeignKey("users.id"), nullable=False),
    Column("question", String(1000), nullable=False),
    Column("status", String(32), nullable=False),
    Column("snapshot", JSONB, nullable=False),
    timestamp(),
    ForeignKeyConstraint(
        ["organization_id", "customer_id"],
        ["customers.organization_id", "customers.customer_id"],
    ),
)
