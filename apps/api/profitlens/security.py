import hashlib
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash
from sqlalchemy import and_, select

from . import database as db

passwords = PasswordHash.recommended()
DUMMY_HASH = passwords.hash("unused-account-timing-placeholder")
COOKIE = "profitlens_session"


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def connection():
    with db.engine.begin() as conn:
        yield conn


def current_user(request: Request, conn=Depends(connection, scope="function")):
    token = request.cookies.get(COOKIE, "")
    user = (
        conn.execute(
            select(db.users.c.id, db.users.c.email, db.users.c.name)
            .join(db.sessions, db.sessions.c.user_id == db.users.c.id)
            .where(
                db.sessions.c.token_hash == digest(token),
                db.sessions.c.expires_at > db.now(),
            )
        )
        .mappings()
        .first()
    )
    if not user:
        raise HTTPException(401, "Please sign in")
    return dict(user)


@dataclass
class Scope:
    org: str
    user: dict
    role: str
    currency: str


def scope(
    organization_id: str,
    user=Depends(current_user),
    conn=Depends(connection, scope="function"),
):
    member = conn.execute(
        select(db.memberships.c.role, db.organizations.c.currency)
        .join(
            db.organizations, db.organizations.c.id == db.memberships.c.organization_id
        )
        .where(
            db.memberships.c.organization_id == organization_id,
            db.memberships.c.user_id == user["id"],
        )
    ).first()
    if not member:
        raise HTTPException(404, "Workspace not found")
    return Scope(organization_id, user, member.role, member.currency)


def writer(s: Scope = Depends(scope)):
    if s.role not in ("admin", "finance"):
        raise HTTPException(403, "Your role is read-only")
    return s


def admin(s: Scope = Depends(scope)):
    if s.role != "admin":
        raise HTTPException(403, "Administrator access required")
    return s


def visible(table, s):
    predicate = table.c.organization_id == s.org
    if s.role == "analyst":
        allowed = select(db.grants.c.customer_id).where(
            db.grants.c.organization_id == s.org, db.grants.c.user_id == s.user["id"]
        )
        predicate = and_(predicate, table.c.customer_id.in_(allowed))
    return predicate


def customer_exists(conn, s, customer_id):
    if not conn.execute(
        select(db.customers.c.customer_id).where(
            visible(db.customers, s), db.customers.c.customer_id == customer_id
        )
    ).first():
        raise HTTPException(404, "Customer not found")


def lock_workspace(conn, s):
    # Serializes writes per workspace: confirms, manual edits, and duplicate checks agree.
    conn.execute(
        select(db.organizations.c.id)
        .where(db.organizations.c.id == s.org)
        .with_for_update()
    ).first()
