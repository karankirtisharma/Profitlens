"""Strict, non-persistent CSV import preview with row-level errors."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel, ValidationError

from .models import Customer, Expense, Invoice

RecordT = TypeVar("RecordT", bound=BaseModel)
MAX_CSV_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10_000


@dataclass(frozen=True)
class ImportIssue:
    code: str
    message: str
    source_file: str
    source_row: int | None = None

    def as_dict(self) -> dict[str, str | int | None]:
        return {
            "code": self.code,
            "message": self.message,
            "source_file": self.source_file,
            "source_row": self.source_row,
        }


@dataclass(frozen=True)
class ImportedRow(Generic[RecordT]):
    record: RecordT
    source_file: str
    source_row: int


@dataclass
class ImportResult(Generic[RecordT]):
    rows: list[ImportedRow[RecordT]] = field(default_factory=list)
    issues: list[ImportIssue] = field(default_factory=list)


SCHEMAS: dict[str, tuple[type[BaseModel], tuple[str, ...]]] = {
    "customers": (Customer, ("customer_id", "name", "industry")),
    "invoices": (
        Invoice,
        ("invoice_id", "customer_id", "billing_period", "currency", "subtotal", "discount", "tax", "refund", "total"),
    ),
    "expenses": (Expense, ("expense_id", "customer_id", "billing_period", "category", "amount", "currency")),
}


def load_csv(path: str | Path, kind: str, organization_id: str) -> ImportResult:
    """Parse one CSV. A caller must supply its trusted organization scope."""
    source = Path(path)
    result = ImportResult()
    if kind not in SCHEMAS:
        raise ValueError(f"unsupported CSV kind: {kind}")
    if not organization_id.strip():
        raise ValueError("organization_id is required")
    model, columns = SCHEMAS[kind]
    try:
        if source.stat().st_size > MAX_CSV_BYTES:
            result.issues.append(ImportIssue("file_too_large", "CSV exceeds 5 MiB preview limit", source.name))
            return result
        with source.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, restkey="__extra__")
            headers = reader.fieldnames
            if not headers:
                result.issues.append(ImportIssue("missing_header", "CSV has no header row", source.name, 1))
                return result
            if len(headers) != len(set(headers)):
                result.issues.append(ImportIssue("duplicate_header", "CSV has duplicate column names", source.name, 1))
                return result
            missing = set(columns) - set(headers)
            unexpected = set(headers) - set(columns)
            if missing or unexpected:
                detail = f"missing={sorted(missing)}, unexpected={sorted(unexpected)}"
                result.issues.append(ImportIssue("invalid_header", detail, source.name, 1))
                return result
            for row_number, raw in enumerate(reader, start=2):
                if row_number - 1 > MAX_ROWS:
                    result.issues.append(ImportIssue("too_many_rows", "CSV exceeds 10,000-row preview limit", source.name, row_number))
                    break
                if not any(value for value in raw.values()):
                    continue
                if "__extra__" in raw or any(value is None for value in raw.values()):
                    result.issues.append(ImportIssue("column_count", "Row has missing or extra columns", source.name, row_number))
                    continue
                try:
                    record = model.model_validate({**raw, "organization_id": organization_id})
                except ValidationError as exc:
                    for error in exc.errors():
                        field_name = ".".join(str(part) for part in error["loc"]) or "row"
                        result.issues.append(
                            ImportIssue("invalid_value", f"{field_name}: {error['msg']}", source.name, row_number)
                        )
                    continue
                result.rows.append(ImportedRow(record, source.name, row_number))
    except (OSError, UnicodeError, csv.Error) as exc:
        result.issues.append(ImportIssue("read_error", str(exc), source.name))
    return result


@dataclass
class BundlePreview:
    customers: ImportResult[Customer]
    invoices: ImportResult[Invoice]
    expenses: ImportResult[Expense]
    issues: list[ImportIssue]
    currency: str | None

    @property
    def valid(self) -> bool:
        return not self.issues


def preview_bundle(
    customers_csv: str | Path,
    invoices_csv: str | Path,
    expenses_csv: str | Path,
    organization_id: str,
) -> BundlePreview:
    customers = load_csv(customers_csv, "customers", organization_id)
    invoices = load_csv(invoices_csv, "invoices", organization_id)
    expenses = load_csv(expenses_csv, "expenses", organization_id)
    issues = [*customers.issues, *invoices.issues, *expenses.issues]

    known_customers: set[str] = set()
    for row in customers.rows:
        key = row.record.customer_id
        if key in known_customers:
            issues.append(ImportIssue("duplicate_id", f"Duplicate customer_id: {key}", row.source_file, row.source_row))
        known_customers.add(key)

    for result, id_field in ((invoices, "invoice_id"), (expenses, "expense_id")):
        seen: set[str] = set()
        for row in result.rows:
            record = row.record
            key = getattr(record, id_field)
            if key in seen:
                issues.append(ImportIssue("duplicate_id", f"Duplicate {id_field}: {key}", row.source_file, row.source_row))
            seen.add(key)
            if record.customer_id not in known_customers:
                issues.append(
                    ImportIssue("unknown_customer", f"Unknown customer_id: {record.customer_id}", row.source_file, row.source_row)
                )

    currencies = {row.record.currency for row in [*invoices.rows, *expenses.rows]}
    if len(currencies) > 1:
        issues.append(ImportIssue("mixed_currency", f"Mixed currencies: {sorted(currencies)}", "bundle"))
    return BundlePreview(customers, invoices, expenses, issues, next(iter(currencies)) if len(currencies) == 1 else None)
