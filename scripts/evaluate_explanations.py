"""Bounded synthetic-only explanation evaluation; no database or real records.

Default writes a case inventory. --live sends only generated fixture evidence to
the configured provider (at most 24 calls, no retries). Never logs API keys.
This evaluates evidence selection, not unrestricted chat interpretation or RBAC.
"""

import argparse
import json
import time
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path

from profitlens import evaluation, explanations, finance, profitability, retrieval
from profitlens.records import wire


def cases():
    data = evaluation.dataset()
    questions = [
        q | {"scope": "contract"} for q in data["questions"] if q["split"] == "held_out"
    ]
    for identifier, customer, question, reviewed in [
        ("F01", "EVAL-01", "What is the recorded contribution and margin?", True),
        ("F02", "EVAL-01", "What is the provisional recorded contribution?", False),
        ("F03", "EVAL-11", "What is the net billed revenue? Costs are missing.", False),
        ("F04", "EVAL-01", "What will next year's revenue be?", True),
    ]:
        questions.append(
            dict(
                id=identifier,
                customer_id=customer,
                billing_period="2026-09",
                question=question,
                scope="financial",
                reviewed=reviewed,
                relevant_contracts=[],
                category="financial",
                expected_answerable=identifier != "F04",
            )
        )
    for q in questions:
        cid = q["customer_id"]
        terms = [c for c in data["contracts"] if c["customer_id"] == cid]
        raw = finance.calculate(
            "evaluation",
            cid,
            "2026-09",
            "INR",
            [
                r
                for r in data["invoices"]
                if r["customer_id"] == cid and r["billing_period"] == "2026-09"
            ],
            [
                r
                for r in data["expenses"]
                if r["customer_id"] == cid and r["billing_period"] == "2026-09"
            ],
            terms,
        )
        item = profitability.metrics(
            raw,
            {"input_hash": profitability.fingerprint(raw)}
            if q.get("reviewed")
            else None,
        )
        metrics = {
            k: {"value": item[k], "unit": "percent" if k == "margin_percent" else "INR"}
            for k in (
                "net_billed_revenue",
                "attributed_cost",
                "contribution",
                "margin_percent",
            )
            if item[k] is not None
        }
        current = [
            c
            for c in terms
            if c["state"] == "reviewed"
            and c["currency"] == "INR"
            and c["effective_from"] <= date(2026, 9, 1)
            and c["effective_to"] >= date(2026, 9, 30)
        ]
        hits = retrieval.rank(
            q["question"], [p for c in current for p in retrieval.chunks(c)], 3
        )
        pack = wire(
            dict(
                customer_id=cid,
                billing_period="2026-09",
                question=q["question"],
                evidence_scope=q["scope"],
                metrics=metrics if q["scope"] == "financial" else {},
                findings=[],
                passages=[p | {"source_id": "passage:" + p["id"]} for p in hits]
                if q["scope"] == "contract"
                else [],
                profitability_status=item["profitability_status"],
                warnings=item["warnings"],
                invoice_lines=item["invoice_lines"]
                if q["scope"] == "financial"
                else [],
                expense_lines=item["expense_lines"]
                if q["scope"] == "financial"
                else [],
            )
        )
        yield q, pack


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--output", default="data/exports/explanation-evaluation.json")
    args = parser.parse_args()
    status = explanations.provider_status()
    if args.live and not status["configured"]:
        raise SystemExit("Configure a provider before --live; no request sent.")
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset": "synthetic-evaluation-v1",
        "live": args.live,
        "provider": status["provider"],
        "model": status["model"],
        "cases": [],
        "limits": [
            "Synthetic-only; not a real-company or user study.",
            "Function-level evidence selection; API permissions and UI tested separately.",
            "Deterministic checks do not establish semantic relevance; inspect saved questions and quotes.",
            "Retrieval misses are retained, not repaired using labels.",
        ],
    }
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    for q, pack in cases():
        start = time.perf_counter()
        result = explanations.explain(pack) if args.live else {"status": "not_run"}
        row = {
            "id": q["id"],
            "question": q["question"],
            "scope": q["scope"],
            "expected_answerable": q.get(
                "expected_answerable", bool(q["relevant_contracts"])
            ),
            "evidence_available": bool(pack["metrics"] or pack["passages"]),
            "result": result,
            "elapsed_seconds": round(time.perf_counter() - start, 3),
        }
        report["cases"].append(row)
        report["status_counts"] = dict(
            Counter(r["result"]["status"] for r in report["cases"])
        )
        destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(q["id"], result["status"], flush=True)
        if result["status"] == "provider_unavailable":
            print("Stopped after provider failure; partial results retained.")
            break
    print("Saved:", destination)


if __name__ == "__main__":
    main()
