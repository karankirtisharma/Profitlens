"""Extract page-attributed text from a text-based contract PDF."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .csv_import import ImportIssue

MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_PAGES = 100


@dataclass(frozen=True)
class ContractPage:
    organization_id: str
    customer_id: str
    source_file: str
    page_number: int
    text: str


@dataclass
class ContractPreview:
    pages: list[ContractPage] = field(default_factory=list)
    issues: list[ImportIssue] = field(default_factory=list)


def extract_contract_text(path: str | Path, organization_id: str, customer_id: str) -> ContractPreview:
    """Extract selectable PDF text; extracted content is not a verified contract term."""
    source = Path(path)
    result = ContractPreview()
    if not organization_id.strip() or not customer_id.strip():
        result.issues.append(ImportIssue("missing_scope", "Organization and customer IDs are required", source.name))
        return result
    try:
        if source.stat().st_size > MAX_PDF_BYTES:
            result.issues.append(ImportIssue("file_too_large", "PDF exceeds 10 MiB preview limit", source.name))
            return result
        with source.open("rb") as stream:
            if stream.read(5) != b"%PDF-":
                result.issues.append(ImportIssue("invalid_pdf", "File is not a PDF", source.name))
                return result
            stream.seek(0)
            reader = PdfReader(stream)
            if reader.is_encrypted:
                result.issues.append(ImportIssue("encrypted_pdf", "Encrypted PDFs are not supported", source.name))
                return result
            if len(reader.pages) > MAX_PAGES:
                result.issues.append(ImportIssue("too_many_pages", "PDF exceeds 100-page preview limit", source.name))
                return result
            for page_number, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                if text:
                    result.pages.append(ContractPage(organization_id, customer_id, source.name, page_number, text))
            if not result.pages:
                result.issues.append(
                    ImportIssue("no_text", "No selectable text found; scanned PDFs need OCR", source.name)
                )
    except (OSError, ValueError, PdfReadError) as exc:
        result.issues.append(ImportIssue("pdf_read_error", f"Could not read PDF: {exc}", source.name))
    return result
