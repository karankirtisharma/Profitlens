"""Command-line preview of a synthetic import bundle; writes nothing to storage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .csv_import import ImportIssue, preview_bundle
from .pdf_contract import extract_contract_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ProfitLens demo inputs without persisting data")
    parser.add_argument("--organization-id", required=True)
    parser.add_argument("--customers", required=True, type=Path)
    parser.add_argument("--invoices", required=True, type=Path)
    parser.add_argument("--expenses", required=True, type=Path)
    parser.add_argument("--contract-pdf", type=Path)
    parser.add_argument("--contract-customer-id")
    args = parser.parse_args()

    bundle = preview_bundle(args.customers, args.invoices, args.expenses, args.organization_id)
    issues: list[ImportIssue] = list(bundle.issues)
    pages = 0
    if args.contract_pdf:
        if not args.contract_customer_id:
            parser.error("--contract-customer-id is required with --contract-pdf")
        if args.contract_customer_id not in {row.record.customer_id for row in bundle.customers.rows}:
            issues.append(ImportIssue("unknown_customer", "Contract customer is not in customer CSV", args.contract_pdf.name))
        else:
            contract = extract_contract_text(args.contract_pdf, args.organization_id, args.contract_customer_id)
            issues.extend(contract.issues)
            pages = len(contract.pages)
    elif args.contract_customer_id:
        parser.error("--contract-pdf is required with --contract-customer-id")

    report = {
        "valid": not issues,
        "organization_id": args.organization_id,
        "counts": {
            "customers": len(bundle.customers.rows),
            "invoices": len(bundle.invoices.rows),
            "expenses": len(bundle.expenses.rows),
            "contract_text_pages": pages,
        },
        "currency": bundle.currency,
        "billing_periods": sorted(
            {row.record.billing_period for row in [*bundle.invoices.rows, *bundle.expenses.rows]}
        ),
        "period_links": [
            {
                "customer_id": link.customer_id,
                "billing_period": link.billing_period,
                "invoice_ids": link.invoice_ids,
                "expense_ids": link.expense_ids,
            }
            for link in bundle.period_links
        ],
        "warnings": [warning.as_dict() for warning in bundle.warnings],
        "issues": [issue.as_dict() for issue in issues],
        "persisted": False,
    }
    print(json.dumps(report, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
