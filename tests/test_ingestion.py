"""Behavior checks for the Week 1 import preview."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from profitlens.ingestion.csv_import import preview_bundle
from profitlens.ingestion.pdf_contract import extract_contract_text


CUSTOMERS = "customer_id,name,industry\nC001,Northstar Studio,Design\nC002,Harbor Retail,Retail\n"
INVOICES = (
    "invoice_id,customer_id,billing_period,currency,subtotal,discount,tax,refund,total\n"
    "I001,C001,2026-09,INR,100.00,10.00,16.20,5.00,101.20\n"
)
EXPENSES = "expense_id,customer_id,billing_period,category,amount,currency\nE001,C001,2026-09,Support,20.00,INR\n"


def write_text_pdf(path: Path) -> None:
    """Produce a minimal one-page selectable-text PDF without a test-only package."""
    contents = b"BT /F1 12 Tf 72 720 Td (Contract rate INR 10000) Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(contents)).encode() + b" >>\nstream\n" + contents + b"\nendstream",
    ]
    data = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(data))
        data.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref_start = len(data)
    data.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        data.extend(f"{offset:010} 00000 n \n".encode())
    data.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode())
    path.write_bytes(data)


class IngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.customers = self.root / "customers.csv"
        self.invoices = self.root / "invoices.csv"
        self.expenses = self.root / "expenses.csv"
        self.customers.write_text(CUSTOMERS, encoding="utf-8")
        self.invoices.write_text(INVOICES, encoding="utf-8")
        self.expenses.write_text(EXPENSES, encoding="utf-8")

    def preview(self):
        return preview_bundle(self.customers, self.invoices, self.expenses, "org-1")

    def test_valid_bundle_links_customer_and_period(self) -> None:
        result = self.preview()
        self.assertTrue(result.valid, result.issues)
        self.assertEqual(result.currency, "INR")
        self.assertEqual(result.invoices.rows[0].record.billing_period, "2026-09")
        self.assertEqual(result.invoices.rows[0].source_row, 2)
        self.assertEqual(result.invoices.rows[0].record.organization_id, "org-1")

    def test_total_mismatch_is_rejected(self) -> None:
        self.invoices.write_text(INVOICES.replace("101.20", "111.20"), encoding="utf-8")
        result = self.preview()
        self.assertFalse(result.valid)
        self.assertEqual(result.invoices.rows, [])
        self.assertTrue(any("total must equal" in issue.message for issue in result.issues))

    def test_duplicate_and_unknown_customer_are_reported(self) -> None:
        self.customers.write_text(CUSTOMERS + "C001,Repeated,Design\n", encoding="utf-8")
        self.expenses.write_text(EXPENSES.replace("E001,C001", "E001,C999"), encoding="utf-8")
        result = self.preview()
        self.assertEqual({issue.code for issue in result.issues}, {"duplicate_id", "unknown_customer"})

    def test_bad_period_is_rejected(self) -> None:
        self.invoices.write_text(INVOICES.replace("2026-09", "2026-13"), encoding="utf-8")
        result = self.preview()
        self.assertTrue(any(issue.code == "invalid_value" for issue in result.issues))
        self.assertFalse(result.valid)

    def test_mixed_currency_is_rejected(self) -> None:
        self.expenses.write_text(EXPENSES.replace("INR", "USD"), encoding="utf-8")
        result = self.preview()
        self.assertTrue(any(issue.code == "mixed_currency" for issue in result.issues))
        self.assertFalse(result.valid)

    def test_csv_cannot_supply_organization_scope(self) -> None:
        self.customers.write_text(CUSTOMERS.replace("customer_id,name,industry", "organization_id,customer_id,name,industry"), encoding="utf-8")
        result = self.preview()
        self.assertTrue(any(issue.code == "invalid_header" for issue in result.issues))

    def test_pdf_extracts_text_with_page_provenance(self) -> None:
        pdf = self.root / "contract.pdf"
        write_text_pdf(pdf)
        result = extract_contract_text(pdf, "org-1", "C001")
        self.assertFalse(result.issues, result.issues)
        self.assertEqual(result.pages[0].page_number, 1)
        self.assertEqual(result.pages[0].customer_id, "C001")
        self.assertIn("Contract rate INR 10000", result.pages[0].text)

    def test_non_pdf_is_reported(self) -> None:
        pdf = self.root / "bad.pdf"
        pdf.write_text("not a PDF", encoding="utf-8")
        result = extract_contract_text(pdf, "org-1", "C001")
        self.assertFalse(result.pages)
        self.assertEqual(result.issues[0].code, "invalid_pdf")


if __name__ == "__main__":
    unittest.main()
