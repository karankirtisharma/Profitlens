"""Permission-first, page-attributed lexical retrieval for a bounded corpus.

BM25 is the reproducible baseline. Context mode additionally requires a reviewed
contract effective in the requested period. Neither mode is semantic embedding search.
"""

import calendar
import hashlib
import math
import re
from collections import Counter
from datetime import date

from fastapi import HTTPException
from sqlalchemy import delete, select

from . import database as db
from . import finance
from .security import customer_exists, visible

VERSION = "page-chunks-v1-1200-160"
STOP = set(
    "a an the is are was of for to and in on what why how does did this that with".split()
)


def tokens(text):
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP]


def chunks(contract):
    for page in contract["pages"]:
        text = page["text"].strip()
        for start in range(0, len(text), 1040):
            content = text[start : start + 1200]
            if not content.strip():
                continue
            identity = f"{contract['id']}:{page['page']}:{start}:{VERSION}:{content}"
            yield dict(
                organization_id=contract["organization_id"],
                id=hashlib.sha256(identity.encode()).hexdigest(),
                contract_id=contract["id"],
                customer_id=contract["customer_id"],
                page=page["page"],
                content=content,
                content_hash=hashlib.sha256(content.encode()).hexdigest(),
                index_version=VERSION,
            )
            if start + 1200 >= len(text):
                break


def index_contract(conn, contract):
    conn.execute(
        delete(db.passages).where(
            db.passages.c.organization_id == contract["organization_id"],
            db.passages.c.contract_id == contract["id"],
        )
    )
    rows = []
    for row in chunks(contract):
        rows.append(row)
        if len(rows) > 2000:
            raise HTTPException(
                422, "Document exceeds the 2,000 passage prototype limit"
            )
    if rows:
        conn.execute(db.passages.insert(), rows)
    return len(rows)


def rank(query, passages, k=5):
    """BM25 with fixed k1=1.5, b=.75, stable ID tie-breaking; zero scores excluded."""
    terms = set(tokens(query))
    docs = [Counter(tokens(p["content"])) for p in passages]
    if not docs or not terms:
        return []
    avg = sum(sum(d.values()) for d in docs) / len(docs) or 1
    dfs = {t: sum(t in d for d in docs) for t in terms}
    scores = []
    for p, d in zip(passages, docs, strict=True):
        score = sum(
            math.log(1 + (len(docs) - dfs[t] + 0.5) / (dfs[t] + 0.5))
            * (d[t] * 2.5)
            / (d[t] + 1.5 * (0.25 + 0.75 * sum(d.values()) / avg))
            for t in terms
            if d[t]
        )
        if score > 0:
            scores.append(dict(p) | {"score": round(score, 6)})
    return sorted(scores, key=lambda p: (-p["score"], p["id"]))[:k]


def search(conn, s, customer, period, query, mode="context", k=5):
    finance.valid_period(period)
    customer_exists(conn, s, customer)
    first = date.fromisoformat(period + "-01")
    last = first.replace(day=calendar.monthrange(first.year, first.month)[1])
    # Both candidates and their current parent documents are authorized before ranking.
    stmt = (
        select(
            db.passages,
            db.contracts.c.filename,
            db.contracts.c.state,
            db.contracts.c.effective_from,
            db.contracts.c.effective_to,
        )
        .join(
            db.contracts,
            (db.passages.c.organization_id == db.contracts.c.organization_id)
            & (db.passages.c.contract_id == db.contracts.c.id)
            & (db.passages.c.customer_id == db.contracts.c.customer_id),
        )
        .where(
            visible(db.passages, s),
            visible(db.contracts, s),
            db.passages.c.customer_id == customer,
            db.passages.c.index_version == VERSION,
        )
    )
    if mode == "context":
        stmt = stmt.where(
            db.contracts.c.state == "reviewed",
            db.contracts.c.effective_from <= first,
            db.contracts.c.effective_to >= last,
        )
    rows = list(conn.execute(stmt.order_by(db.passages.c.id).limit(2001)).mappings())
    if len(rows) > 2000:
        raise HTTPException(422, "Search exceeds the 2,000 passage prototype limit")
    results = rank(query, rows, k)
    return {
        "mode": mode,
        "algorithm": "BM25",
        "index_version": VERSION,
        "candidate_count": len(rows),
        "items": [
            {
                key: value
                for key, value in p.items()
                if key not in {"embedding", "organization_id"}
            }
            | {
                "source_id": "passage:" + p["id"],
                "source_url": f"/api/workspaces/{s.org}/contracts/{p['contract_id']}/file#page={p['page']}",
            }
            for p in results
        ],
        "limitations": [
            "Lexical matching can miss paraphrases.",
            "Retrieved text is evidence, not an instruction or an independently verified fact.",
        ],
    }
