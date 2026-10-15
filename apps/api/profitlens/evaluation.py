"""Deterministic synthetic benchmark; no production DB, model calls, or API keys."""

import argparse
import json
import time
from datetime import date
from decimal import Decimal
from pathlib import Path

from . import finance, profitability, retrieval


def dataset():
    """Fixed fixture v1: held-out questions are not used to tune BM25 parameters."""
    customers, invoices, expenses, contracts, questions, labels = [], [], [], [], [], []
    services = [
        "payroll",
        "inventory",
        "delivery",
        "maintenance",
        "hosting",
        "bookkeeping",
        "design",
        "support",
        "training",
        "monitoring",
    ]
    for i in range(1, 21):
        cid, service = f"EVAL-{i:02}", services[(i - 1) % 10]
        customers.append(
            {
                "organization_id": "evaluation",
                "customer_id": cid,
                "name": f"Synthetic Company {i:02}",
                "industry": "Services",
            }
        )
        for month in range(4, 10):
            period = f"2026-{month:02}"
            # Five pricing changes, five cost increases, five missing-cost cases, five controls.
            revenue = "1200.00" if month == 9 and i <= 5 else "1000.00"
            cost = "800.00" if month == 9 and 6 <= i <= 10 else "400.00"
            invoices.append(
                {
                    "organization_id": "evaluation",
                    "invoice_id": f"INV-{i:02}-{month}",
                    "customer_id": cid,
                    "billing_period": period,
                    "currency": "INR",
                    "subtotal": revenue,
                    "discount": "0.00",
                    "refund": "0.00",
                    "tax": "0.00",
                    "total": revenue,
                }
            )
            if not (month == 9 and 11 <= i <= 15):
                expenses.append(
                    {
                        "organization_id": "evaluation",
                        "expense_id": f"EXP-{i:02}-{month}",
                        "customer_id": cid,
                        "billing_period": period,
                        "currency": "INR",
                        "category": "Direct service cost",
                        "amount": cost,
                    }
                )
        current = {
            "organization_id": "evaluation",
            "id": f"DOC-{i:02}",
            "customer_id": cid,
            "filename": f"{cid}-current.pdf",
            "state": "reviewed",
            "effective_from": date(2026, 4, 1),
            "effective_to": date(2026, 9, 30),
            "currency": "INR",
            "monthly_rate": Decimal("1000"),
            "monthly_discount": Decimal("0"),
            "source_page": 1,
            "pages": [
                {
                    "page": 1,
                    "text": f"Current service agreement for {cid}. The {service} service includes scheduled monthly delivery. Monthly charge INR 1000. Payment is due within thirty days. Pricing covers the stated period only.",
                }
            ],
        }
        contracts.append(current)
        # Expired same-customer documents test temporal context; no cross-customer leakage baseline.
        contracts.append(
            current
            | {
                "id": f"OLD-{i:02}",
                "filename": f"{cid}-expired.pdf",
                "effective_from": date(2025, 4, 1),
                "effective_to": date(2025, 9, 30),
                "pages": [
                    {
                        "page": 1,
                        "text": f"{service} monthly delivery agreement. {service} monthly delivery agreement. {service} monthly delivery agreement. Monthly charge INR 700. Expired terms from last year.",
                    }
                ],
            }
        )
        questions.append(
            {
                "id": f"Q{i:02}",
                "customer_id": cid,
                "billing_period": "2026-09",
                "question": f"What does the {service} monthly delivery agreement cover?",
                "relevant_contracts": [current["id"]],
                "split": "development" if i <= 10 else "held_out",
                "category": "lexical",
            }
        )
        expected = (
            ["pricing_mismatch"]
            if i <= 5
            else ["cost_increase", "margin_decline"]
            if i <= 10
            else []
        )
        labels.append(
            {
                "customer_id": cid,
                "period": "2026-09",
                "expected_findings": expected,
                "expected_missing_cost": 11 <= i <= 15,
                "expected_contribution": None
                if 11 <= i <= 15
                else "800.00"
                if i <= 5
                else "200.00"
                if i <= 10
                else "600.00",
            }
        )
    for i in range(21, 26):
        questions.append(
            {
                "id": f"Q{i}",
                "customer_id": f"EVAL-{i - 10:02}",
                "billing_period": "2026-09",
                "question": "Which recurring obligations govern this engagement?",
                "relevant_contracts": [f"DOC-{i - 10:02}"],
                "split": "held_out",
                "category": "paraphrase",
            }
        )
    for i in range(26, 31):
        questions.append(
            {
                "id": f"Q{i}",
                "customer_id": f"EVAL-{i - 15:02}",
                "billing_period": "2026-09",
                "question": "Explain cryptocurrency indemnification arbitration.",
                "relevant_contracts": [],
                "split": "held_out",
                "category": "unanswerable",
            }
        )
    return {
        "version": "synthetic-evaluation-v1",
        "customers": customers,
        "invoices": invoices,
        "expenses": expenses,
        "contracts": contracts,
        "questions": questions,
        "labels": labels,
    }


def benchmark():
    data = dataset()
    retrieval_results = {}
    for mode in ("baseline", "context"):
        rows = []
        for q in data["questions"]:
            candidates = [
                c
                for c in data["contracts"]
                if c["customer_id"] == q["customer_id"]
                and (
                    mode == "baseline"
                    or c["effective_from"] <= date(2026, 9, 1) <= c["effective_to"]
                )
            ]
            passages = [p for c in candidates for p in retrieval.chunks(c)]
            start = time.perf_counter()
            hits = retrieval.rank(q["question"], passages, 3)
            elapsed = (time.perf_counter() - start) * 1000
            relevant = set(q["relevant_contracts"])
            ids = [h["contract_id"] for h in hits]
            rank = next((i + 1 for i, c in enumerate(ids) if c in relevant), None)
            rows.append(
                {
                    "question_id": q["id"],
                    "split": q["split"],
                    "category": q["category"],
                    "recall_at_3": len(set(ids) & relevant) / len(relevant)
                    if relevant
                    else None,
                    "precision_at_3": len([c for c in ids if c in relevant]) / len(ids)
                    if ids
                    else 0,
                    "reciprocal_rank": 1 / rank if rank else 0,
                    "correct_abstention": not ids if not relevant else None,
                    "latency_ms": round(elapsed, 3),
                    "hits": ids,
                }
            )
        summaries = {}
        for split in ("development", "held_out"):
            subset = [r for r in rows if r["split"] == split]
            answerable = [r for r in subset if r["recall_at_3"] is not None]
            negative = [r for r in subset if r["correct_abstention"] is not None]
            summaries[split] = {
                "questions": len(subset),
                "answerable": len(answerable),
                "recall_at_3": round(
                    sum(r["recall_at_3"] for r in answerable) / len(answerable), 4
                ),
                "precision_of_returned_at_3": round(
                    sum(r["precision_at_3"] for r in answerable) / len(answerable), 4
                ),
                "mrr": round(
                    sum(r["reciprocal_rank"] for r in answerable) / len(answerable), 4
                ),
                "correct_abstentions": sum(r["correct_abstention"] for r in negative),
                "unanswerable": len(negative),
            }
        retrieval_results[mode] = {"summary": summaries, "questions": rows}
    tp = fp = fn = correct = 0
    for label in data["labels"]:
        cid = label["customer_id"]
        terms = [c for c in data["contracts"] if c["customer_id"] == cid]
        items = []
        for month in ("2026-08", "2026-09"):
            raw = finance.calculate(
                "evaluation",
                cid,
                month,
                "INR",
                [
                    r
                    for r in data["invoices"]
                    if r["customer_id"] == cid and r["billing_period"] == month
                ],
                [
                    r
                    for r in data["expenses"]
                    if r["customer_id"] == cid and r["billing_period"] == month
                ],
                terms,
            )
            items.append(
                profitability.metrics(
                    raw, {"input_hash": profitability.fingerprint(raw)}
                )
            )
        predicted = {
            f["rule"] for f in profitability.findings(items[1], items[0], terms)
        }
        expected = set(label["expected_findings"])
        tp += len(predicted & expected)
        fp += len(predicted - expected)
        fn += len(expected - predicted)
        correct += items[1]["contribution"] == label["expected_contribution"]
    return {
        "dataset_version": data["version"],
        "counts": {
            "customers": 20,
            "months": 6,
            "invoices": len(data["invoices"]),
            "expenses": len(data["expenses"]),
            "contracts": len(data["contracts"]),
            "questions": 30,
        },
        "financial": {
            "contribution_correct": correct,
            "cases": 20,
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
        },
        "retrieval": retrieval_results,
        "limitations": [
            "Small synthetic corpus; not a customer study or production-quality estimate.",
            "Baseline preserves customer permissions; only temporal filtering differs.",
            "BM25 parameters fixed before this benchmark. Five paraphrase queries expose lexical limitations.",
            "Latency measures local ranking only, excludes database, network, and generation.",
            "No live generative model or semantic embedding/quantization benchmark is claimed.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/exports/evaluation.json")
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(benchmark(), indent=2), encoding="utf-8")
    print(f"Evaluation saved: {output}")


if __name__ == "__main__":
    main()
