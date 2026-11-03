"""Add separate operational subledgers; frozen PostgreSQL DDL, no existing data rewrite."""

import sqlalchemy as sa
from alembic import op

revision = "20261103_operations"
down_revision = "20261016_sources"
branch_labels = None
depends_on = None

# Frozen at revision creation. Never import the application's evolving metadata.
TABLE_NAMES = (
    "vendors",
    "items",
    "bills",
    "invoice_terms",
    "payments",
    "payment_allocations",
)
DDL = (
    """CREATE TABLE vendors (
	organization_id VARCHAR(36) NOT NULL,
	vendor_id VARCHAR(80) NOT NULL,
	name VARCHAR(200) NOT NULL,
	email VARCHAR(254) NOT NULL,
	notes VARCHAR(1000) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	CONSTRAINT pk_vendors PRIMARY KEY (organization_id, vendor_id),
	CONSTRAINT fk_vendors_organization_id_organizations FOREIGN KEY(organization_id) REFERENCES organizations (id)
)""",
    """CREATE TABLE items (
	organization_id VARCHAR(36) NOT NULL,
	item_id VARCHAR(80) NOT NULL,
	name VARCHAR(200) NOT NULL,
	description VARCHAR(1000) NOT NULL,
	unit_price NUMERIC(14, 2) NOT NULL,
	currency VARCHAR(3) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	CONSTRAINT pk_items PRIMARY KEY (organization_id, item_id),
	CONSTRAINT fk_items_organization_id_organizations FOREIGN KEY(organization_id) REFERENCES organizations (id),
	CONSTRAINT item_price_nonnegative CHECK (unit_price >= 0)
)""",
    """CREATE TABLE bills (
	organization_id VARCHAR(36) NOT NULL,
	bill_id VARCHAR(80) NOT NULL,
	vendor_id VARCHAR(80) NOT NULL,
	issued_on DATE NOT NULL,
	due_on DATE,
	currency VARCHAR(3) NOT NULL,
	total NUMERIC(14, 2) NOT NULL,
	opening_paid NUMERIC(14, 2) NOT NULL,
	description VARCHAR(1000) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	CONSTRAINT pk_bills PRIMARY KEY (organization_id, bill_id),
	CONSTRAINT bill_positive CHECK (total > 0),
	CONSTRAINT fk_bills_organization_id_vendors FOREIGN KEY(organization_id, vendor_id) REFERENCES vendors (organization_id, vendor_id),
	CONSTRAINT bill_opening_paid CHECK (opening_paid >= 0 AND opening_paid <= total),
	CONSTRAINT fk_bills_organization_id_organizations FOREIGN KEY(organization_id) REFERENCES organizations (id),
	CONSTRAINT bill_due_date CHECK (due_on IS NULL OR due_on >= issued_on)
)""",
    """CREATE TABLE invoice_terms (
	organization_id VARCHAR(36) NOT NULL,
	invoice_id VARCHAR(80) NOT NULL,
	due_on DATE,
	opening_paid NUMERIC(14, 2) NOT NULL,
	attested_by VARCHAR(36) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	CONSTRAINT pk_invoice_terms PRIMARY KEY (organization_id, invoice_id),
	CONSTRAINT opening_paid_nonnegative CHECK (opening_paid >= 0),
	CONSTRAINT fk_invoice_terms_attested_by_users FOREIGN KEY(attested_by) REFERENCES users (id),
	CONSTRAINT fk_invoice_terms_organization_id_organizations FOREIGN KEY(organization_id) REFERENCES organizations (id),
	CONSTRAINT fk_invoice_terms_organization_id_invoices FOREIGN KEY(organization_id, invoice_id) REFERENCES invoices (organization_id, invoice_id)
)""",
    """CREATE TABLE payments (
	organization_id VARCHAR(36) NOT NULL,
	payment_id VARCHAR(80) NOT NULL,
	direction VARCHAR(10) NOT NULL,
	paid_on DATE NOT NULL,
	currency VARCHAR(3) NOT NULL,
	total NUMERIC(14, 2) NOT NULL,
	reference VARCHAR(200) NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE NOT NULL,
	CONSTRAINT pk_payments PRIMARY KEY (organization_id, payment_id),
	CONSTRAINT payment_positive CHECK (total > 0),
	CONSTRAINT payment_direction CHECK (direction IN ('received', 'made')),
	CONSTRAINT fk_payments_organization_id_organizations FOREIGN KEY(organization_id) REFERENCES organizations (id)
)""",
    """CREATE TABLE payment_allocations (
	organization_id VARCHAR(36) NOT NULL,
	id VARCHAR(36) NOT NULL,
	payment_id VARCHAR(80) NOT NULL,
	invoice_id VARCHAR(80),
	bill_id VARCHAR(80),
	amount NUMERIC(14, 2) NOT NULL,
	CONSTRAINT pk_payment_allocations PRIMARY KEY (organization_id, id),
	CONSTRAINT fk_payment_allocations_organization_id_organizations FOREIGN KEY(organization_id) REFERENCES organizations (id),
	CONSTRAINT one_allocation_target CHECK ((invoice_id IS NOT NULL AND bill_id IS NULL) OR (invoice_id IS NULL AND bill_id IS NOT NULL)),
	CONSTRAINT uq_payment_bill_allocation UNIQUE (organization_id, payment_id, bill_id),
	CONSTRAINT fk_payment_allocations_organization_id_invoice_terms FOREIGN KEY(organization_id, invoice_id) REFERENCES invoice_terms (organization_id, invoice_id),
	CONSTRAINT fk_payment_allocations_organization_id_bills FOREIGN KEY(organization_id, bill_id) REFERENCES bills (organization_id, bill_id),
	CONSTRAINT allocation_positive CHECK (amount > 0),
	CONSTRAINT uq_payment_invoice_allocation UNIQUE (organization_id, payment_id, invoice_id),
	CONSTRAINT fk_payment_allocations_organization_id_payments FOREIGN KEY(organization_id, payment_id) REFERENCES payments (organization_id, payment_id)
)""",
)


def upgrade():
    for statement in DDL:
        op.execute(sa.text(statement))


def downgrade():
    # Names are fixed migration constants, never user input.
    if any(
        op.get_bind().scalar(sa.text('SELECT count(*) FROM "' + name + '"'))
        for name in TABLE_NAMES
    ):
        raise RuntimeError(
            "Operations records exist: export and explicitly clear them before downgrade"
        )
    for name in reversed(TABLE_NAMES):
        op.drop_table(name)
