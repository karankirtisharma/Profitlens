"""Explicit synthetic presentation seed; never run automatically on API startup."""

import csv
import io
from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select

from . import database as db
from . import imports
from .schemas import Terms
from .security import Scope, lock_workspace


def csv_bytes(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def presentation_rows():
    customers = [
        dict(
            customer_id=f"READY-C{i:03}", name=f"{name} (synthetic)", industry=industry
        )
        for i, name, industry in [
            (3, "Cedar Learning", "Education"),
            (4, "Orchid Events", "Events"),
            (5, "Maple Support", "Support services"),
            (6, "Aster Digital", "Software services"),
        ]
    ]
    ids = ["C001", "C002"] + [r["customer_id"] for r in customers]
    invoices, expenses = [], []
    for month_index in range(12):
        absolute = 2025 * 12 + 9 + month_index
        period = f"{absolute // 12:04}-{absolute % 12 + 1:02}"
        for index, customer in enumerate(ids[: min(6, 2 + month_index // 2)]):
            subtotal = Decimal(10000 + index * 2000 + month_index * 150)
            discount = Decimal(250 if index % 2 else 0)
            refund = Decimal(500 if month_index == 7 and index == 0 else 0)
            tax = (subtotal - discount - refund) * Decimal("0.18")
            key = f"{index + 1:02}-{period}"
            invoices.append(
                dict(
                    invoice_id=f"READY-I-{key}",
                    customer_id=customer,
                    billing_period=period,
                    currency="INR",
                    subtotal=str(subtotal),
                    discount=str(discount),
                    tax=str(tax),
                    refund=str(refund),
                    total=str(subtotal - discount + tax - refund),
                )
            )
            for n in range(1 + month_index % 2):
                expenses.append(
                    dict(
                        expense_id=f"READY-E-{key}-{n + 1}",
                        customer_id=customer,
                        billing_period=period,
                        currency="INR",
                        category="Service delivery" if n == 0 else "Cloud tools",
                        amount=str(
                            Decimal(4000 + index * 300 + month_index * 75)
                            if n == 0
                            else Decimal("650.50")
                        ),
                    )
                )
    return {"customers": customers, "invoices": invoices, "expenses": expenses}


def seed_presentation():
    # Reuse the actual upload/review handlers, including their validation and audit trail.
    from .main import review_terms, upload_contract

    with db.engine.begin() as conn:
        owner = (
            conn.execute(
                select(db.users)
                .join(db.memberships, db.memberships.c.user_id == db.users.c.id)
                .where(
                    db.users.c.email == "karan@profitlens.local",
                    db.memberships.c.organization_id == "demo-org",
                    db.memberships.c.role == "admin",
                )
            )
            .mappings()
            .first()
        )
        org = (
            conn.execute(
                select(db.organizations).where(db.organizations.c.id == "demo-org")
            )
            .mappings()
            .first()
        )
        if not owner or not org or org["currency"] != "INR":
            raise SystemExit("Run seed-demo first in the synthetic INR demo workspace")
        scope = Scope("demo-org", dict(owner), "admin", "INR")
        lock_workspace(conn, scope)
        for kind, rows in presentation_rows().items():
            batch = imports.preview(
                conn, scope, kind, f"synthetic-preloaded-{kind}.csv", csv_bytes(rows)
            )
            if batch["state"] == "ready":
                imports.confirm(conn, scope, batch["id"])
            elif batch["state"] != "confirmed":
                raise SystemExit(
                    f"Presentation seed conflicts with {kind}; database changes rolled back"
                )
        for kind in ("customers", "invoices", "expenses"):
            source = Path("data/week4") / f"{kind}.csv"
            batch = imports.preview(
                conn, scope, kind, f"synthetic-week4-{kind}.csv", source.read_bytes()
            )
            if batch["state"] == "ready":
                imports.confirm(conn, scope, batch["id"])
            elif batch["state"] != "confirmed":
                raise SystemExit(
                    f"Week 4 seed conflicts with {kind}; database changes rolled back"
                )
        folder = Path("data/demo")
        for customer in ("C001", "C002"):
            source = folder / f"contract_{customer}.pdf"
            existing = set(
                conn.execute(
                    select(db.contracts.c.id).where(
                        db.contracts.c.organization_id == scope.org
                    )
                ).scalars()
            )
            with source.open("rb") as stream:
                doc = upload_contract(
                    customer, UploadFile(file=stream, filename=source.name), scope, conn
                )
            # Only prepare newly created C001 terms. Preserve all later human reviews/edits.
            if customer == "C001" and doc["id"] not in existing:
                overlap = conn.execute(
                    select(db.contracts.c.id).where(
                        db.contracts.c.organization_id == scope.org,
                        db.contracts.c.customer_id == customer,
                        db.contracts.c.state == "reviewed",
                        db.contracts.c.effective_from <= date(2027, 2, 28),
                        db.contracts.c.effective_to >= date(2026, 9, 1),
                    )
                ).first()
                if not overlap:
                    review_terms(
                        doc["id"],
                        Terms(
                            effective_from="2026-09-01",
                            effective_to="2027-02-28",
                            currency="INR",
                            monthly_rate="10000",
                            monthly_discount="0",
                            source_page=1,
                        ),
                        scope,
                        conn,
                    )
        imports.preview(
            conn,
            scope,
            "invoices",
            "synthetic-preloaded-invalid.csv",
            (folder / "invalid_invoices.csv").read_bytes(),
        )
    print(
        "Synthetic presentation data ready: 12 months, private PDFs and import history. Existing edits and access grants preserved."
    )
