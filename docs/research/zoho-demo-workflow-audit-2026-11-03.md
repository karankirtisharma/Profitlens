# Zoho demo workflow audit and ProfitLens overhaul

Observed 3 November 2026. Source: [Zoho Books India public demo](https://www.zoho.com/in/books/accounting-software-demo/#/home/dashboard), browser inspection of dashboard, menus, documents and bills. Official reference: [Zoho Bills help](https://www.zoho.com/in/books/help/bills/). This is an independent implementation from observed workflows, not copied source code or a claim of feature parity.

## Evidence and limits

The demo explicitly says actions are limited. Its menus expose features; their presence does not prove every workflow was tested. The document library exposed file/status filters, downloads/upload controls and transaction associations. Bills exposed supplier, due date, total, balance and status. The dashboard exposed receivables/payables, cash flow, income/expense, top expenses and projects. Some demo amounts/statuses were inconsistent; these sample values are not a specification for financial rules.

REA skill guidance was followed for evidence boundaries. No REA MCP operations are connected in this session. Observations came from browser accessibility/DOM output and official documentation; there are no invented REA Evidence IDs. No private Zoho account, server internals, proprietary source, or financial submission was accessed.

## Workflow comparison

| Observed Zoho capability | ProfitLens implementation in this change | Remaining gap |
| --- | --- | --- |
| Grouped navigation, search | Grouped task navigation; business-term section search; mobile layout | No global cross-record search |
| Documents library | Unified original-source/contract library, type/status/name filters, authorized downloads | No OCR, nested folders, email inbox or cloud-drive connector |
| Reports | Report hub linking financial, evidence, monthly source and balance reports | No statutory financial statements or custom report builder |
| Vendors | Separate organization-scoped vendor identities, create/edit | No supplier portal or bank details |
| Items | Goods/services catalogue and prices | No inventory, stock movements, pricing rules or transaction line linkage |
| Bills | Explicit vendor bills and reviewed opening payment history | No recurring bills, tax engine, credit notes or reversals |
| Payments received/made | Record existing payments; partial and same-party multi-document allocations | No payment execution, gateway, prepayment or bank feed |
| Receivables/payables | Enrolled verified invoices and bills; current/overdue/unknown-date balances | No inferred historical settlement or FX |
| Sales/PO/quotes/retainers/challans | Existing invoice records remain supported | Quotes, purchase/sales orders, retainers and challans not implemented |
| Accountant/tax/projects | Existing financial investigation retained | GL journals, chart of accounts, GST filing, e-Way bills, timesheets and projects not implemented |

## Design decisions

1. An invoice import does not establish that it remains unpaid. Invoice tracking requires a reviewed opening-paid amount and explicit payment-history attestation. Reported-sales observations cannot become receivables.
2. A vendor bill is a payable, not automatically an attributed customer expense. Operational bills/payments do not silently enter existing profitability calculations.
3. Every payment must allocate its exact amount to existing documents in the same organization, currency and customer/vendor. Duplicate payment IDs and excess allocations are rejected under a workspace transaction lock.
4. Money uses server-side Decimal and database NUMERIC. Browser formatting is presentation only.
5. Posted payment/bill/tracked-invoice corrections need a future explicit reversal workflow; editing is restricted to avoid corrupting balances.
6. Existing document access remains permission-scoped. Analysts cannot browse full raw source files or operational supplier/payment records.

## Positioning

ProfitLens is a financial review workspace with source traceability and a small operational payment tracker. Its practical differentiator remains handling incomplete source evidence honestly and explaining recorded changes. This release does not establish that ProfitLens is a cheaper or functionally superior replacement for Zoho Books. Such a claim requires customer validation and materially broader accounting coverage.

## Usability changes

| Before | After | Why |
| --- | --- | --- |
| Flat navigation | Labelled business groups and search | Find frequent tasks quickly |
| Files split across imports and contracts | Document library with direct authorized downloads | Locate evidence without knowing implementation terminology |
| Reports spread across panels | Report hub explaining each report's basis | Avoid confusing sales, cash and profit |
| Preview-sized activity charts | Server summaries over accessible records | Avoid presenting the first 200 records as the whole workspace |
| Imported invoices without settlement history | Explicit enrollment and opening balance review | Do not assume unpaid balances |

See the release verification report for executed checks. Unimplemented rows above remain explicit follow-up scope, not working menu placeholders.
