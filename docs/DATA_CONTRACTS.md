# Week 1 data contracts

These are the **initial demo CSV schemas**, not a promise that arbitrary accounting exports already work. Files must be UTF-8 with headers. All row identifiers are case-sensitive and unique within one import. The organization ID is supplied by the caller, never by a CSV column.

| File | Required columns | Meaning |
| --- | --- | --- |
| Customers | `customer_id,name,industry` | Customer identifier within one organization; industry may be blank. |
| Invoices | `invoice_id,customer_id,billing_period,currency,subtotal,discount,tax,refund,total` | One invoice for a customer and period. Amounts use decimal major units (e.g. `1250.00`). |
| Expenses | `expense_id,customer_id,billing_period,category,amount,currency` | Direct or attributed customer cost in a period. |

`billing_period` is `YYYY-MM`. `currency` is a three-letter uppercase code; a single evaluation run uses one currency because cross-currency conversion is not in scope. A contract PDF is supplied with a customer ID as metadata; text is extracted by page, with no automatic claim that extracted amounts are contract terms.

## Financial and quality rules

- `subtotal`, `discount`, `tax`, `refund`, and `total` are nonnegative. For this initial input format, `refund` is a pre-tax reduction linked to the invoice in the same billing period. Prior-period credit notes and refunds that include tax need separate explicit handling later. Discount and refund are not subtracted twice.
- The expected payable invoice total is `subtotal - discount + tax - refund`. Week 1 validates this identity and reports mismatches. Tax is excluded from future revenue calculations.
- Planned net billed revenue for this supported format is `subtotal - discount - refund`; this calculation is not yet implemented in Week 1.
- Negative net revenue, impossible discounts/refunds, invalid months, duplicate IDs, unknown customer references, and mixed currencies are import errors.
- A present expense row is an attributed cost. An absent expense row is **not evidence of zero cost**; completeness must be established separately before showing a final margin.
- The Week 1 preview groups invoice and expense IDs by `(customer_id, billing_period)` and warns when only one side is present. It does not calculate a margin from incomplete groups.
- A zero-revenue period has no margin percentage. Missing or conflicting source data blocks a confident finding.
- Invoice and expense rows retain their CSV filename and row number; PDF passages retain page numbers.

## PDF limitations

Week 1 accepts text-based PDFs. Scans requiring OCR, password-protected files, and automatic interpretation of contract clauses are outside the current parser. Extraction output must be reviewed before any pricing comparison is considered reliable.
