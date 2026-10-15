"""Export reproducible fixtures or seed a separate synthetic evaluation workspace."""

import argparse
import csv
import io
import json
from pathlib import Path

from fastapi import UploadFile
from reportlab.pdfgen import canvas
from sqlalchemy import select

from . import database as db
from . import profitability
from .evaluation import dataset
from .ingestion.csv_import import SCHEMAS
from .records import wire, write_record
from .security import Scope, lock_workspace


def pdf_bytes(contract):
    output = io.BytesIO()
    pdf = canvas.Canvas(output, invariant=1)
    for page in contract["pages"]:
        text = pdf.beginText(50, 780)
        words = page["text"].split()
        for start in range(0, len(words), 11):
            text.textLine(" ".join(words[start : start + 11]))
        pdf.drawText(text)
        pdf.showPage()
    pdf.save()
    return output.getvalue()


def export(directory):
    data = dataset()
    directory.mkdir(parents=True, exist_ok=True)
    for kind in ("customers", "invoices", "expenses"):
        with (directory / f"{kind}.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=SCHEMAS[kind][1], extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(data[kind])
    (directory / "labels-and-questions.json").write_text(
        json.dumps(
            wire({k: data[k] for k in ("version", "questions", "labels")}), indent=2
        ),
        encoding="utf-8",
    )
    for contract in data["contracts"]:
        (directory / contract["filename"]).write_bytes(pdf_bytes(contract))


def seed():
    from .main import review_terms, upload_contract
    from .schemas import Terms

    data = dataset()
    with db.engine.begin() as conn:
        owner = (
            conn.execute(
                select(db.users).where(db.users.c.email == "karan@profitlens.local")
            )
            .mappings()
            .first()
        )
        if not owner:
            raise SystemExit(
                "Provision the normal synthetic demo account first with seed-demo."
            )
        # Never overwrite existing business edits or silently restore revoked permissions.
        if conn.execute(
            select(db.organizations.c.id).where(
                db.organizations.c.id == "evaluation-demo"
            )
        ).first():
            print("Evaluation demo already exists; all edits preserved.")
            return
        conn.execute(
            db.organizations.insert().values(
                id="evaluation-demo",
                name="ProfitLens Evaluation (synthetic)",
                currency="INR",
            )
        )
        conn.execute(
            db.memberships.insert().values(
                organization_id="evaluation-demo", user_id=owner["id"], role="admin"
            )
        )
        s = Scope("evaluation-demo", dict(owner), "admin", "INR")
        lock_workspace(conn, s)
        for kind in ("customers", "invoices", "expenses"):
            for row in data[kind]:
                write_record(
                    conn,
                    s,
                    kind,
                    {k: v for k, v in row.items() if k != "organization_id"},
                )
        for contract in data["contracts"]:
            document = upload_contract(
                contract["customer_id"],
                UploadFile(
                    filename=contract["filename"], file=io.BytesIO(pdf_bytes(contract))
                ),
                s,
                conn,
            )
            terms = Terms(
                **{
                    k: contract[k]
                    for k in (
                        "effective_from",
                        "effective_to",
                        "currency",
                        "monthly_rate",
                        "monthly_discount",
                        "source_page",
                    )
                }
            )
            review_terms(document["id"], terms, s, conn)
        for customer in data["customers"]:
            for month in range(4, 10):
                period = f"2026-{month:02}"
                row = profitability.report(conn, s, period, customer["customer_id"], 1)[
                    "items"
                ][0]
                if row["attributed_cost"] is not None:
                    profitability.attest(
                        conn,
                        s,
                        customer["customer_id"],
                        period,
                        row["cost_input_hash"],
                        "Synthetic fixture v1: generated direct costs are complete by construction; not a real business attestation.",
                    )
    print(
        "Created separate evaluation-demo workspace: 20 customers, six months, 40 current/expired contracts."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path)
    parser.add_argument("--seed", action="store_true")
    args = parser.parse_args()
    if args.export:
        export(args.export)
    if args.seed:
        seed()
    if not args.export and not args.seed:
        parser.error("Choose --export DIRECTORY or --seed")


if __name__ == "__main__":
    main()
