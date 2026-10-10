"""Explicit local account provisioning; no default passwords or public signup."""

import argparse
import getpass
import os
from pathlib import Path

from sqlalchemy import select

from . import database as db
from . import imports
from .security import Scope, passwords


def get_password():
    value = os.environ.get("DEMO_PASSWORD") or getpass.getpass(
        "New account password (12+ characters): "
    )
    if len(value) < 12:
        raise SystemExit("Use at least 12 characters")
    return value


def seed_demo(password):
    with db.engine.begin() as conn:
        for org, name in [
            ("demo-org", "Northstar Services"),
            ("other-org", "Seabrook Operations"),
        ]:
            if not conn.execute(
                select(db.organizations.c.id).where(db.organizations.c.id == org)
            ).first():
                conn.execute(
                    db.organizations.insert().values(id=org, name=name, currency="INR")
                )
        for email, name, org, role in [
            ("karan@profitlens.local", "Karan Kirti Sharma", "demo-org", "admin"),
            ("finance@profitlens.local", "Demo Finance", "demo-org", "finance"),
            ("analyst@profitlens.local", "Demo Analyst", "demo-org", "analyst"),
            ("other@profitlens.local", "Other Workspace Admin", "other-org", "admin"),
        ]:
            user = (
                conn.execute(select(db.users).where(db.users.c.email == email))
                .mappings()
                .first()
            )
            if not user:
                user = {"id": db.uid(), "email": email, "name": name}
                conn.execute(
                    db.users.insert().values(
                        **user, password_hash=passwords.hash(password)
                    )
                )
            if not conn.execute(
                select(db.memberships).where(
                    db.memberships.c.organization_id == org,
                    db.memberships.c.user_id == user["id"],
                )
            ).first():
                conn.execute(
                    db.memberships.insert().values(
                        organization_id=org, user_id=user["id"], role=role
                    )
                )
        owner = (
            conn.execute(
                select(db.users).where(db.users.c.email == "karan@profitlens.local")
            )
            .mappings()
            .one()
        )
        s = Scope("demo-org", dict(owner), "admin", "INR")
        for kind in ("customers", "invoices", "expenses"):
            source = Path("data/demo") / f"{kind}.csv"
            p = imports.preview(conn, s, kind, source.name, source.read_bytes())
            if p["state"] == "ready":
                imports.confirm(conn, s, p["id"])
            elif p["state"] != "confirmed":
                raise SystemExit(
                    f"Seed conflicts with existing {kind}; no changes committed"
                )
        analyst = conn.execute(
            select(db.users.c.id).where(db.users.c.email == "analyst@profitlens.local")
        ).scalar_one()
        # Do not restore a grant revoked by an administrator on subsequent seeds.
        if not conn.execute(
            select(db.customers.c.customer_id).where(
                db.customers.c.organization_id == "other-org"
            )
        ).first():
            conn.execute(
                db.customers.insert().values(
                    organization_id="other-org",
                    customer_id="PRIVATE-1",
                    name="Seabrook Private Customer",
                    industry="Services",
                    source={"type": "synthetic"},
                )
            )
            conn.execute(
                db.grants.insert().values(
                    organization_id="demo-org", user_id=analyst, customer_id="C001"
                )
            )
    print(
        "Synthetic workspaces provisioned. Existing accounts/passwords and business edits are not overwritten."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed-demo")
    add = sub.add_parser("add-user")
    add.add_argument("--organization", required=True)
    add.add_argument("--email", required=True)
    add.add_argument("--name", required=True)
    add.add_argument("--role", choices=["admin", "finance", "analyst"], required=True)
    args = parser.parse_args()
    password = get_password()
    if args.command == "seed-demo":
        seed_demo(password)
        return
    with db.engine.begin() as conn:
        if not conn.execute(
            select(db.organizations).where(db.organizations.c.id == args.organization)
        ).first():
            raise SystemExit("Workspace not found")
        if conn.execute(
            select(db.users).where(db.users.c.email == args.email.strip().lower())
        ).first():
            raise SystemExit("Account already exists")
        uid = db.uid()
        conn.execute(
            db.users.insert().values(
                id=uid,
                email=args.email.strip().lower(),
                name=args.name,
                password_hash=passwords.hash(password),
            )
        )
        conn.execute(
            db.memberships.insert().values(
                organization_id=args.organization, user_id=uid, role=args.role
            )
        )
    print("Account provisioned. Assign analyst customers in Team access.")


if __name__ == "__main__":
    main()
