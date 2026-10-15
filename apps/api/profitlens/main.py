"""Authenticated API for the ProfitLens business-data workspace."""

import hashlib
import secrets
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import JSONResponse
from sqlalchemy import delete, select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from . import database as db
from . import finance, imports, records, retrieval, schemas, storage
from .analysis_api import router as analysis_router
from .config import settings
from .ingestion.pdf_contract import extract_contract_text
from .security import (
    COOKIE,
    DUMMY_HASH,
    admin,
    connection,
    current_user,
    customer_exists,
    digest,
    lock_workspace,
    passwords,
    scope,
    visible,
    writer,
)

app = FastAPI(
    title="ProfitLens API",
    version="0.3.0",
    description="Organization-scoped business records, imports and reviewed contracts.",
)
PREFIX = "/api/workspaces/{organization_id}"
app.include_router(analysis_router)


@app.middleware("http")
async def guard(request, call_next):
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if request.headers.get("origin") != settings.web_origin:
            return JSONResponse({"detail": "Untrusted request origin"}, status_code=403)
    length = request.headers.get("content-length")
    if length and (not length.isdigit() or int(length) > settings.request_limit):
        return JSONResponse(
            {"detail": "Request exceeds the configured upload limit"}, status_code=413
        )
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@app.exception_handler(IntegrityError)
async def conflict(request, exc):
    return JSONResponse(
        {"detail": "Record conflicts with existing data; refresh and try again"},
        status_code=409,
    )


@app.get("/api/health")
def health(conn=Depends(connection, scope="function")):
    conn.execute(text("SELECT 1"))
    return {"status": "ok", "database": "postgresql"}


@app.exception_handler(OperationalError)
@app.exception_handler(storage.StorageUnavailable)
async def dependency_unavailable(request, exc):
    return JSONResponse(
        {"detail": "A required service is unavailable. Try again later."},
        status_code=503,
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/live")
def live():
    return {"status": "ok"}


@app.get("/api/config")
def public_config():
    return {
        "csv_max_bytes": settings.file_limit("csv"),
        "pdf_max_bytes": settings.file_limit("pdf"),
    }


@app.post("/api/auth/login")
def login(payload: schemas.Login, request: Request, response: Response):
    email = payload.email.strip().lower()
    # Persist limits even when authentication fails, and serialize attempts for a key.
    key = digest(email)
    from sqlalchemy.dialects.postgresql import insert

    with db.engine.begin() as conn:
        conn.execute(
            insert(db.login_limits)
            .values(key=key, attempts=0, reset_at=db.now() + timedelta(minutes=15))
            .on_conflict_do_nothing()
        )
        limit = (
            conn.execute(
                select(db.login_limits)
                .where(db.login_limits.c.key == key)
                .with_for_update()
            )
            .mappings()
            .one()
        )
        attempts = limit["attempts"] if limit["reset_at"] > db.now() else 0
        if attempts >= 5:
            raise HTTPException(429, "Too many attempts. Try again in 15 minutes.")
        user = (
            conn.execute(select(db.users).where(db.users.c.email == email))
            .mappings()
            .first()
        )
        valid = passwords.verify(
            payload.password, user["password_hash"] if user else DUMMY_HASH
        )
        conn.execute(
            db.login_limits.update()
            .where(db.login_limits.c.key == key)
            .values(
                attempts=0 if valid else attempts + 1,
                reset_at=limit["reset_at"]
                if limit["reset_at"] > db.now()
                else db.now() + timedelta(minutes=15),
            )
        )
        if valid and user:
            old = request.cookies.get(COOKIE)
            if old:
                conn.execute(
                    delete(db.sessions).where(db.sessions.c.token_hash == digest(old))
                )
            conn.execute(
                delete(db.sessions).where(db.sessions.c.expires_at <= db.now())
            )
            token = secrets.token_urlsafe(32)
            conn.execute(
                db.sessions.insert().values(
                    token_hash=digest(token),
                    user_id=user["id"],
                    expires_at=db.now() + timedelta(hours=settings.session_hours),
                )
            )
    if not valid or not user:
        raise HTTPException(401, "Email or password is incorrect")
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.session_hours * 3600,
        path="/",
    )
    return {"id": user["id"], "email": user["email"], "name": user["name"]}


@app.post("/api/auth/logout")
def logout(
    request: Request, response: Response, conn=Depends(connection, scope="function")
):
    conn.execute(
        delete(db.sessions).where(
            db.sessions.c.token_hash == digest(request.cookies.get(COOKIE, ""))
        )
    )
    response.delete_cookie(
        COOKIE,
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="strict",
    )
    return {"ok": True}


@app.get("/api/auth/me")
def me(user=Depends(current_user), conn=Depends(connection, scope="function")):
    workspaces = (
        conn.execute(
            select(db.organizations, db.memberships.c.role)
            .join(
                db.memberships,
                db.memberships.c.organization_id == db.organizations.c.id,
            )
            .where(db.memberships.c.user_id == user["id"])
        )
        .mappings()
        .all()
    )
    return {**user, "workspaces": [dict(w) for w in workspaces]}


@app.get(PREFIX + "/members")
def members(s=Depends(admin), conn=Depends(connection, scope="function")):
    rows = (
        conn.execute(
            select(
                db.users.c.id, db.users.c.name, db.users.c.email, db.memberships.c.role
            )
            .join(db.memberships, db.memberships.c.user_id == db.users.c.id)
            .where(db.memberships.c.organization_id == s.org)
        )
        .mappings()
        .all()
    )
    return [
        {
            **r,
            "customer_ids": list(
                conn.execute(
                    select(db.grants.c.customer_id).where(
                        db.grants.c.organization_id == s.org,
                        db.grants.c.user_id == r["id"],
                    )
                ).scalars()
            ),
        }
        for r in rows
    ]


@app.put(PREFIX + "/members/{user_id}/customers")
def assign(
    user_id: str,
    payload: schemas.GrantInput,
    s=Depends(admin),
    conn=Depends(connection, scope="function"),
):
    lock_workspace(conn, s)
    member = (
        conn.execute(
            select(db.memberships).where(
                db.memberships.c.organization_id == s.org,
                db.memberships.c.user_id == user_id,
            )
        )
        .mappings()
        .first()
    )
    if not member:
        raise HTTPException(404, "Member not found")
    if member["role"] != "analyst":
        raise HTTPException(422, "Customer assignments apply to analysts")
    for cid in payload.customer_ids:
        customer_exists(conn, s, cid)
    conn.execute(
        delete(db.grants).where(
            db.grants.c.organization_id == s.org, db.grants.c.user_id == user_id
        )
    )
    for cid in set(payload.customer_ids):
        conn.execute(
            db.grants.insert().values(
                organization_id=s.org, user_id=user_id, customer_id=cid
            )
        )
    return {"customer_ids": sorted(set(payload.customer_ids))}


@app.get(PREFIX + "/records/{kind}")
def list_records(
    kind: Literal["customers", "invoices", "expenses"],
    customer_id: str | None = None,
    limit: int = 200,
    offset: int = 0,
    s=Depends(scope),
    conn=Depends(connection, scope="function"),
):
    table, _, id_key = records.spec(kind)
    query = select(table).where(visible(table, s))
    if customer_id:
        query = query.where(table.c.customer_id == customer_id)
    if not 1 <= limit <= 200 or offset < 0:
        raise HTTPException(422, "Invalid pagination")
    return records.wire(
        [
            dict(r)
            for r in conn.execute(
                query.order_by(table.c[id_key]).limit(limit).offset(offset)
            ).mappings()
        ]
    )


@app.get(PREFIX + "/records/{kind}/{record_id}")
def get_record(
    kind: str,
    record_id: str,
    s=Depends(scope),
    conn=Depends(connection, scope="function"),
):
    table, _, id_key = records.spec(kind)
    row = (
        conn.execute(
            select(table).where(visible(table, s), table.c[id_key] == record_id)
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(404, "Record not found")
    return records.wire(dict(row))


# Separate typed request schemas keep OpenAPI useful while sharing write logic.
def register_record_routes(kind, model):
    def create(payload, s=Depends(writer), conn=Depends(connection, scope="function")):
        return records.write_record(conn, s, kind, payload.model_dump())

    def update(
        record_id: str,
        payload,
        s=Depends(writer),
        conn=Depends(connection, scope="function"),
    ):
        return records.write_record(conn, s, kind, payload.model_dump(), record_id)

    create.__annotations__["payload"] = model
    update.__annotations__["payload"] = model
    app.add_api_route(
        PREFIX + f"/records/{kind}",
        create,
        methods=["POST"],
        status_code=201,
        name=f"create_{kind}",
    )
    app.add_api_route(
        PREFIX + f"/records/{kind}" + "/{record_id}",
        update,
        methods=["PUT"],
        name=f"update_{kind}",
    )


for kind, model in [
    ("customers", schemas.CustomerInput),
    ("invoices", schemas.InvoiceInput),
    ("expenses", schemas.ExpenseInput),
]:
    register_record_routes(kind, model)


@app.get(PREFIX + "/imports")
def history(s=Depends(writer), conn=Depends(connection, scope="function")):
    return [
        imports.batch_view(r)
        for r in conn.execute(
            select(db.batches)
            .where(db.batches.c.organization_id == s.org)
            .order_by(db.batches.c.created_at.desc())
            .limit(100)
        ).mappings()
    ]


def safe_filename(name):
    return Path((name or "upload").replace("\\", "/")).name[:200]


@app.post(PREFIX + "/imports/{kind}/preview")
def preview_import(
    kind: Literal["customers", "invoices", "expenses"],
    file: UploadFile = File(...),
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    limit = settings.file_limit("csv")
    content = file.file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(413, f"CSV exceeds the {limit:,} byte upload limit")
    return imports.preview(conn, s, kind, safe_filename(file.filename), content)


@app.post(PREFIX + "/imports/{batch_id}/confirm")
def confirm_import(
    batch_id: str, s=Depends(writer), conn=Depends(connection, scope="function")
):
    return imports.confirm(conn, s, batch_id)


def contract_view(row):
    return records.wire({k: v for k, v in dict(row).items() if k != "file_key"})


@app.get(PREFIX + "/contracts")
def list_contracts(
    customer_id: str | None = None,
    s=Depends(scope),
    conn=Depends(connection, scope="function"),
):
    query = select(db.contracts).where(visible(db.contracts, s))
    if customer_id:
        query = query.where(db.contracts.c.customer_id == customer_id)
    return [
        contract_view(r)
        for r in conn.execute(
            query.order_by(db.contracts.c.created_at.desc()).limit(200)
        ).mappings()
    ]


def contract_row(conn, s, contract_id):
    row = (
        conn.execute(
            select(db.contracts).where(
                visible(db.contracts, s), db.contracts.c.id == contract_id
            )
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(404, "Contract not found")
    return row


@app.post(PREFIX + "/contracts", status_code=201)
def upload_contract(
    customer_id: str = Form(...),
    file: UploadFile = File(...),
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    lock_workspace(conn, s)
    customer_exists(conn, s, customer_id)
    limit = settings.file_limit("pdf")
    content = file.file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(413, f"PDF exceeds the {limit:,} byte upload limit")
    fingerprint = hashlib.sha256(content).hexdigest()
    prior = (
        conn.execute(
            select(db.contracts).where(
                db.contracts.c.organization_id == s.org,
                db.contracts.c.customer_id == customer_id,
                db.contracts.c.fingerprint == fingerprint,
            )
        )
        .mappings()
        .first()
    )
    if prior:
        return contract_view(prior)
    key = db.uid() + ".pdf"
    # Parser scratch space is temporary; durable files use the private store.
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / key
        path.write_bytes(content)
        result = extract_contract_text(path, s.org, customer_id)
    if result.issues:
        raise HTTPException(422, [i.as_dict() for i in result.issues])
    storage.put(s.org, key, content)
    try:
        cid = db.uid()
        conn.execute(
            db.contracts.insert().values(
                organization_id=s.org,
                id=cid,
                customer_id=customer_id,
                filename=safe_filename(file.filename),
                file_key=key,
                fingerprint=fingerprint,
                pages=[{"page": p.page_number, "text": p.text} for p in result.pages],
                state="unreviewed",
            )
        )
        records.log_event(
            conn,
            s,
            "contracts",
            cid,
            "uploaded",
            {"filename": safe_filename(file.filename), "sha256": fingerprint},
        )
        row = contract_row(conn, s, cid)
        retrieval.index_contract(conn, row)
        return contract_view(row)
    except Exception:
        storage.remove(s.org, key)
        raise


@app.get(PREFIX + "/contracts/{contract_id}/file")
def contract_file(
    contract_id: str, s=Depends(scope), conn=Depends(connection, scope="function")
):
    row = contract_row(conn, s, contract_id)
    try:
        content = storage.read(s.org, row["file_key"])
    except FileNotFoundError:
        raise HTTPException(404, "Stored file is unavailable") from None
    if hashlib.sha256(content).hexdigest() != row["fingerprint"]:
        raise storage.StorageUnavailable("Stored file integrity check failed")
    return Response(
        content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=utf-8''{quote(row['filename'], safe='')}"
        },
    )


@app.put(PREFIX + "/contracts/{contract_id}/terms")
def review_terms(
    contract_id: str,
    payload: schemas.Terms,
    s=Depends(writer),
    conn=Depends(connection, scope="function"),
):
    lock_workspace(conn, s)
    row = contract_row(conn, s, contract_id)
    if payload.currency != s.currency:
        raise HTTPException(422, "Currency must match workspace")
    if payload.source_page not in [p["page"] for p in row["pages"]]:
        raise HTTPException(422, "Source page has no extracted text")
    overlap = conn.execute(
        select(db.contracts.c.id).where(
            db.contracts.c.organization_id == s.org,
            db.contracts.c.customer_id == row["customer_id"],
            db.contracts.c.id != contract_id,
            db.contracts.c.state == "reviewed",
            db.contracts.c.effective_from <= payload.effective_to,
            db.contracts.c.effective_to >= payload.effective_from,
        )
    ).first()
    if overlap:
        raise HTTPException(409, "Reviewed contract periods overlap for this customer")
    values = payload.model_dump(exclude={"billing_frequency"})
    conn.execute(
        db.contracts.update()
        .where(
            db.contracts.c.organization_id == s.org, db.contracts.c.id == contract_id
        )
        .values(
            **values, state="reviewed", reviewed_by=s.user["id"], reviewed_at=db.now()
        )
    )
    records.log_event(conn, s, "contracts", contract_id, "terms_reviewed", values)
    return contract_view(contract_row(conn, s, contract_id))


@app.get(PREFIX + "/finance")
def financial_report(
    billing_period: str | None = None,
    customer_id: str | None = None,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    s=Depends(scope),
    conn=Depends(connection, scope="function"),
):
    return finance.report(conn, s, billing_period, customer_id, limit, offset)
