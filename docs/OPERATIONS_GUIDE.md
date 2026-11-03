# Business operations and review workspace

ProfitLens now separates **Sales & purchases**, **Money tracking**, and **Review & evidence**. Search the sidebar by task words such as billing, costs or documents. The Reports page explains which records each report uses. Documents collects the latest 100 source files and 200 accessible contracts, with filters and authorized original-file downloads.

## Typical workflow

1. **Vendors:** create a supplier with a stable vendor ID. A supplier is not automatically a customer.
2. **Items:** optionally maintain goods/service names and unit prices. This catalogue does not track stock or create invoice/bill lines.
3. **Bills:** enter a vendor's exact reference, issue date, optional due date, currency and total. Supply the amount already paid and explicitly confirm you reviewed its payment history. Zero must be entered deliberately. Bills do not automatically become customer delivery costs.
4. **Receivables & payables:** enroll a verified invoice only after reviewing its opening-paid amount. Imported reported-sales records are ineligible. Untracked invoices are counted separately, not assumed unpaid. Unknown due dates remain undated, not overdue.
5. **Payments:** record money already received or paid, using a unique payment reference. Allocate it to one or several tracked documents belonging to the same customer/vendor and workspace. Partial payments work; overpayments, mixed parties, unsupported currencies and duplicate IDs are rejected.
6. **Correct a mistaken payment:** open the payment, choose Void recorded payment, enter a reason and confirm. The original record/allocation stays in history. Its allocation stops reducing outstanding balances. Record a replacement with a new ID if needed. This does not cancel a bank transfer or issue a refund.
7. **Reports:** continue using Monthly business review for source observations, Revenue & costs for the verified customer ledger, and Profitability & evidence for source-grounded investigation.

## What balances mean

`Outstanding = recorded document total − reviewed opening-paid amount − active payment allocations`.

Receivables/payables cover tracked documents only. They do not claim complete company accounts, bank balances, cash flow or profit. The original profit calculation is unchanged. Future-dated payments/bills, prepayments, FX, refunds and credit notes are not supported. Invoice issue dates are not available in the original ledger, so chronological validation of invoice receipts is limited; billing month is not substituted for issue date.

Vendors/items can be edited. Bills and enrolled invoices are immutable in this release; correcting their monetary inputs needs a future audited amendment/reversal workflow. Review inputs carefully. Payments support audited void/re-entry. This limitation makes the module a review prototype, not complete production bookkeeping.

## Access and reliability

- Admin and finance roles can use operations. Analysts retain existing assigned-customer analysis and contract access; they cannot access supplier/payment subledgers or full raw source files.
- Foreign keys include organization IDs. A workspace transaction lock serializes balance-changing operations. Financial values use Decimal/NUMERIC, not AI or binary floating-point calculation.
- Changes append audit events. No payment execution, email sending, statutory filing or external banking connection occurs.
- Chat retains its existing invoice/cost/source-evidence scope. Operational balances are available through Money tracking, not yet through AI chat.

## Deployment and rollback

Use the configured PostgreSQL environment, then run:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic check
```

Two additive revisions add the operational tables and payment-void metadata: `20261103_operations` and `20261103_payment_void`. Back up the database before production migration. Existing source records are not converted, enrolled or overwritten. No new environment variables or paid services are required.

For rollback, redeploy the prior frontend/API commit and leave the additive tables in place. Do not drop business data. The migrations reject a downgrade that would discard operational records or void history. A restored backup should first be tested in a separate database; restoring over production needs a separate deliberate decision.

## Scope still missing compared with Zoho Books

Quotes, purchase/sales orders, retainers, recurring billing, inventory, bank feeds, general ledger, tax filing, timesheets, portals and automated payment collection remain unimplemented. The [demo audit](research/zoho-demo-workflow-audit-2026-11-03.md) separates observed competitor capabilities from delivered work.
