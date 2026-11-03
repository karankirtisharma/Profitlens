# Zoho Books comparison and ProfitLens product decisions

Research checked: **3 November 2026**. Publisher of all external sources below: **Zoho**. These pages do not display a reliable publication date; the check date is not a publication date. Prices are India-edition prices and can change.

## Evidence boundary

This is a public-documentation study using the REA skill's observation/inference distinction. No REA MCP runtime was connected, no authenticated Zoho account was inspected, and no proprietary server implementation was reverse engineered. Listed capabilities are documented capabilities, not our executed tests. Lack of documentation in this bounded review is not proof that Zoho lacks a feature. ProfitLens's current code and release verification reports establish its implementation status separately.

## What Zoho already does

| Area | Documented observation | Consequence for ProfitLens |
| --- | --- | --- |
| General record imports | CSV, TSV and XLS; encoding/delimiter selection, mapping and preview. [Import guide](https://www.zoho.com/in/books/help/import-export/import.html) | Guided mapping is expected usability, not a unique invention. Do not say Zoho only accepts one rigid CSV. |
| Bank statements | India troubleshooting guide lists PDF, CSV, TSV, XLS, OFX and QIF; requires mapped fields and unchanged bank-downloaded PDFs. Processing can take up to 48 hours in the described delayed-import case. [India banking guidance](https://www.zoho.com/in/books/kb/banking/unable-to-import-statements.html) | Document uploads and structured financial imports are different workflows. A text-PDF extractor does not establish equivalent bank-statement support. |
| Regional format differences | Bahrain guidance additionally lists CAMT.053 and CAMT.054. [Bank-format reference](https://www.zoho.com/bh/books/kb/banking/file-format.html) | Check edition and actual file layout; do not generalize a regional format list to every account. |
| Documents | Private organization document workflows include folders, folder permissions, email/cloud uploads, autoscan states, extracted fields and attaching files to transactions. The page lists an India 50-scan add-on at INR499/month or INR419/month billed annually after included scans. [Documents](https://www.zoho.com/in/books/help/documents/documents.html) | Traceability, document storage and OCR are not novel on their own. Generic document upload is not proof that every file type can be financially parsed. |
| Dashboard | Receivables/payables, time-filtered cash flow, income/expense views with cash/accrual choices, top-expense drilldowns and project information. [India dashboard](https://www.zoho.com/in/books/help/home/) | Clickable numbers and accounting-basis labels are established patterns worth learning from. Avoid calling an incomplete export a complete P&L. |
| AI | Ask Zia retrieves information and creates transactions; CoCreate offers reviewable transaction creation; reports offer forecasts/anomalies. AI fields and bank-categorization suggestions are labelled early access on the help page. [India AI guide](https://www.zoho.com/in/books/help/ai-features/ai-features.html) | A chatbot, charts or anomaly flags are not differentiation. Availability still depends on edition/configuration; never claim every account has every advertised feature. |

### Pricing facts

The official India page lists Free, Standard INR899/month (INR749/month billed annually), Professional INR1,799 (INR1,499 annually), Premium INR3,599 (INR2,999 annually), Elite INR5,999 (INR4,999 annually), and Ultimate INR9,599 (INR7,999 annually), per organization and excluding local taxes. Standard lists three users; Professional five. Project profitability is listed under Professional, dashboard customization under Elite, and combining other data sources through the Zoho Analytics add-on under Ultimate. [Official India pricing](https://www.zoho.com/in/books/pricing/).

This is not a comprehensive entitlement audit. Free-plan eligibility and limits must be checked before comparing a particular customer. ProfitLens cannot truthfully claim to be cheaper than free, or functionally equivalent at a lower price.

## A defensible product direction

**Recommended positioning:** ProfitLens is a lightweight financial review companion for small teams with scattered business exports. It preserves original evidence, distinguishes the meaning of imported values, explains only supported figures and makes missing information actionable.

**Hypothesis to test:** a reviewer can answer a bounded question about a sales or spending export with less preparation and fewer interpretation errors than their existing spreadsheet/folder workflow. Zoho can remain their accounting system. This is a workflow advantage to validate, not a proven capability gap in Zoho.

Small B2B service firms and their bookkeepers remain the intended primary audience. Retail sales and public expenditure examples demonstrate heterogeneous inputs, not validation of every industry's accounting workflow.

### Recommended implementation priorities

1. **Guided import:** upload, select financial meaning, review suggested fields, preview, then confirm. Never interpret a bank debit as a business expense automatically. Keep unmatched and unknown values visible.
2. **Readable evidence:** show the source filename, row/page, original fields, normalized values and transformation next to a number. Use a readable drawer rather than a raw API response as the main destination.
3. **Data readiness:** explain what the current export supports. Sales-only and expenditure-only workspaces remain useful; costs, contracts and tax basis must not be invented. Contracts are optional unless the requested check needs them.
4. **Meaning-aware extensions:** prioritize delimited exports and explicit bank cash movements, followed by reviewed templates. Cash movements, sales, procurement commitments and balance snapshots remain separate. No arbitrary spreadsheet can be safely understood merely because it opens.
5. **Bounded assistant:** answers reference authorized source evidence. Financial amounts come from deterministic code; the model explains them. Missing evidence produces a clear reason and next action.

Do not add tax filing, payroll, bank payment execution, inventory costing, generic OCR or a full accounting ledger to win a comparison table. They exceed the college scope and introduce obligations not addressed by the current prototype.

## Three proposed pricing plans

These are **pricing hypotheses for a pilot**, not existing subscriptions, enforced entitlements or a checkout offer. The public UI must say this clearly. No customer should be charged or lose existing access through a presentation-only plan selection.

| Plan | Proposed price per organization/month | Intended use | Proposed future allowance, not an implemented quota |
| --- | --- | --- | --- |
| Explore | INR0 | Student/demo and occasional file review | One reviewer; 500 new source rows/month; no included hosted AI questions |
| Review | INR299 | Owner/bookkeeper reviewing monthly exports | Three reviewers; 2,000 new source rows/month; 100 AI questions/month |
| Collaborate | INR699 | Small review team with customer-scoped access | Five reviewers; 5,000 new source rows/month; 300 AI questions/month |

Evidence, numeric integrity, tenant isolation and missing-data disclosure belong in every plan. More expensive tiers should buy usage/collaboration, never permission to see trustworthy totals. Existing per-file/server limits still apply independently. No unlimited AI, all-format import, automatic tax compliance, guaranteed savings or SLA promises.

Before paid launch, measure actual provider input/output tokens, storage, database, compute, support and tax costs; validate willingness to pay; add authenticated usage metering, idempotent billing/webhooks, cancellation, invoice/refund handling and enforceable entitlements. The existing hosted faculty deployment is not evidence that a commercial service can run sustainably on free plans. Pricing and hosting eligibility need review before accepting money.

## Validation before superiority claims

Recruit five target reviewers for an initial usability study (recommended sample, not a completed study). Use the same licensed files and known answers for each workflow. Counterbalance task order when comparing tools. Record first-import time, field corrections, task success, unsupported interpretations, help requests, and time to locate an original source. Include a sales-only dataset, a signed expenditure dataset, duplicate re-import and an ambiguous amount/date layout. If Zoho access is unavailable, report the spreadsheet comparison only.

No market interviews, head-to-head timing, willingness-to-pay results or verified commercial savings were produced by this documentation research. Success means improving a specific measured review task; it does not establish ProfitLens as a replacement for Zoho Books.
