import hashlib
import tempfile
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select

from . import database as db
from .ingestion.csv_import import load_csv
from .records import log_event, spec, validate
from .security import lock_workspace


def batch_view(row):
    return {k: v for k, v in dict(row).items() if k != "rows"} | {
        "row_count": len(row["rows"]),
        "preview_rows": row["rows"][:10],
    }


def check_rows(conn, s, kind, rows):
    table, _, id_key = spec(kind)
    issues, seen = [], set()
    for row in rows:
        try:
            data = validate(kind, row["data"], s)
            key = data[id_key]
            if key in seen:
                raise HTTPException(422, f"Duplicate {id_key}: {key}")
            seen.add(key)
            if (
                kind != "customers"
                and not conn.execute(
                    select(db.customers.c.customer_id).where(
                        db.customers.c.organization_id == s.org,
                        db.customers.c.customer_id == data["customer_id"],
                    )
                ).first()
            ):
                raise HTTPException(
                    422,
                    f"Unknown customer: {data['customer_id']}. Import customers first.",
                )
            old = (
                conn.execute(
                    select(table).where(
                        table.c.organization_id == s.org, table.c[id_key] == key
                    )
                )
                .mappings()
                .first()
            )
            if old and any(old[k] != v for k, v in data.items()):
                raise HTTPException(
                    409,
                    f"ID {key} already exists with different values; use the record editor",
                )
        except HTTPException as exc:
            issues.append(
                {
                    "code": "invalid_record",
                    "source_row": row["source_row"],
                    "message": exc.detail,
                }
            )
    return issues


def preview(conn, s, kind, filename, content):
    spec(kind)
    lock_workspace(conn, s)
    fingerprint = hashlib.sha256(content).hexdigest()
    previous = (
        conn.execute(
            select(db.batches).where(
                db.batches.c.organization_id == s.org,
                db.batches.c.kind == kind,
                db.batches.c.fingerprint == fingerprint,
            )
        )
        .mappings()
        .first()
    )
    if previous and previous["state"] == "confirmed":
        return batch_view(previous)
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "upload.csv"
        path.write_bytes(content)
        result = load_csv(path, kind, s.org)
    rows = [
        {
            "data": row.record.model_dump(mode="json", exclude={"organization_id"}),
            "source_row": row.source_row,
            "original": row.original,
        }
        for row in result.rows
    ]
    issues = [{**i.as_dict(), "source_file": filename} for i in result.issues]
    issues.extend(check_rows(conn, s, kind, rows))
    if not rows and not issues:
        issues.append({"code": "empty", "message": "CSV contains no records"})
    values = dict(
        kind=kind,
        filename=filename,
        fingerprint=fingerprint,
        rows=rows,
        issues=issues,
        state="invalid" if issues else "ready",
        created_by=s.user["id"],
        result={},
    )
    if previous:
        batch_id = previous["id"]
        conn.execute(
            db.batches.update()
            .where(db.batches.c.organization_id == s.org, db.batches.c.id == batch_id)
            .values(**values)
        )
    else:
        batch_id = db.uid()
        conn.execute(
            db.batches.insert().values(id=batch_id, organization_id=s.org, **values)
        )
    return batch_view(
        conn.execute(
            select(db.batches).where(
                db.batches.c.organization_id == s.org, db.batches.c.id == batch_id
            )
        )
        .mappings()
        .one()
    )


def confirm(conn, s, batch_id):
    lock_workspace(conn, s)
    where = (db.batches.c.organization_id == s.org) & (db.batches.c.id == batch_id)
    batch = (
        conn.execute(select(db.batches).where(where).with_for_update())
        .mappings()
        .first()
    )
    if not batch:
        raise HTTPException(404, "Import not found")
    if batch["state"] == "confirmed":
        return batch_view(batch)
    if batch["state"] != "ready":
        raise HTTPException(
            409, "Resolve validation errors and upload the corrected CSV"
        )
    issues = check_rows(conn, s, batch["kind"], batch["rows"])
    if issues:
        raise HTTPException(409, issues)
    table, _, id_key = spec(batch["kind"])
    added = skipped = 0
    for row in batch["rows"]:
        data = validate(batch["kind"], row["data"], s)
        exists = conn.execute(
            select(table.c[id_key]).where(
                table.c.organization_id == s.org, table.c[id_key] == data[id_key]
            )
        ).first()
        if exists:
            skipped += 1
            continue
        source = {
            "type": "csv",
            "batch_id": batch_id,
            "filename": batch["filename"],
            "row": row["source_row"],
            "sha256": batch["fingerprint"],
            "original": row.get("original", {}),
        }
        conn.execute(table.insert().values(**data, source=source))
        log_event(
            conn,
            s,
            batch["kind"],
            data[id_key],
            "imported",
            {**row["data"], "source": source},
        )
        added += 1
    conn.execute(
        db.batches.update()
        .where(where)
        .values(state="confirmed", result={"inserted": added, "skipped": skipped})
    )
    return batch_view(conn.execute(select(db.batches).where(where)).mappings().one())
