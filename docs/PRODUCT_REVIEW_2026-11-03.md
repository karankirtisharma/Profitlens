# Evidence-first business review — 3 November 2026

## Product decision
ProfitLens focuses on reviewing scattered exports with inspectable evidence. The proposed advantage is reducing effort and unsupported interpretations during a monthly business review, not replacing accounting software. Zoho already has mapping, profitability, dashboards, AI and document workflows. See the [official-source comparison](research/zoho-books-comparison-2026-11-03.md). No authenticated Zoho session or REA runtime analysis was available; findings are public-documentation research, not reverse-engineered internals. No claim of superior speed, customer savings or unique algorithms has been validated.

## Implemented changes
- Three-step source import; explicit financial meaning instead of silently defaulting to expenditure; conditional mapping fields, ambiguity hints, table previews and retained unknown fields.
- TSV imports alongside CSV, single-sheet XLSX, JSON record arrays and supported text PDFs. Unsupported extensions rejected explicitly. Generic PDF text is not arbitrary financial-table extraction; no OCR, legacy XLS, OFX or QIF parsing.
- Reviewed two-column bank mapping creates separate cash-inflow/outflow observations. It never creates sales, expense or profit entries. Exactly one positive direction required; original values and the reviewed mapping retained. No payment-to-invoice settlement matching is inferred.
- Readable, keyboard-accessible evidence dialogs show original fields, reviewed interpretation and calculation. Source-observation chatbot citations open these dialogs; aggregate citations open the source table with original filters. Existing authorization and private file download apply.
- Monthly business review compares current/prior calendar-month amounts of one financial type. Exact source names, signed credits, unknown dates and missing comparison data remain explicit. At most five comparable changes plus three one-sided groups; no causal/anomaly/profit claim. SQL aggregates use organization currency and existing customer permissions; evidence links retain exact filters. A zero supported by records differs from no records.
- Public `/pricing` page: Explore ₹0, Review ₹299, Collaborate ₹699 per workspace/month, explicitly proposed pilot pricing. No checkout, subscriptions, quota enforcement or charges. Cost/user validation and commercial hosting eligibility remain prerequisites to paid launch.
- Next.js patched from 16.4.0 to 16.4.4 after npm audit confirmed an existing production advisory. Production audit verification is recorded with test results below; development-tool advisories are not silently fixed with breaking upgrades.

## Architecture and operation
No schema migration, new service or provider is required. Original files use the existing private storage adapter (TSV added to the strict extension/MIME allowlist). `source_review.py` supplies GET `/api/workspaces/{organization_id}/source-review?period=YYYY-MM&kind=expenditure`; supported types are reported_sales, expenditure, cash_inflow and cash_outflow. `/facts` adds exact optional counterparty/currency filters. Existing tests cover authorization and source links.

The comparison concerns available observations, not complete accounting periods. It does not normalize aliases, infer why values changed, net loans against sales, perform tax/FX calculations, or classify arbitrary bank formats. Unknown/one-sided groups require review. Optional contract evidence remains necessary only for checks that depend on contracts.

Run the normal `dev.cmd` launcher after installing locked Python dependencies and `npm ci` in `apps/web`. Open Source data & insights; import the [synthetic review fixtures](../demo-files/source-review/README.md), select a recorded month and run review. `/pricing` is public. No production data changes are needed. Deployment uses existing separate API/frontend Vercel projects; any deployment must include both changes, no database migration.

## Verification
Executed on 3 November 2026:

- **181 backend tests passed in 13.87s**, using a dedicated local `profitlens_test` database. Includes actual local licensed UCI/FHDC originals, new bank mapping cases, monthly aggregate/source equality, exact-name separation, blank dates, missing months, analyst scope and cross-tenant rejection. No skipped tests in this run.
- **22 distinct Chromium browser scenarios passed across runs**: initial full run 19 passed/3 failed; after fixes the six relevant scenarios all passed in 48.8s. Initial new failures were a test POST lacking the required Origin header, a locator expecting text without its explanation child, and a filter lacking an explicit stable accessible name. Origin protection stayed enabled; the filter now has an explicit accessible label. Existing import, PDF, finance, permission and accessibility flows passed in the full run.
- TypeScript, ESLint, changed-file Ruff lint/format and isolated production build passed. Build produced `/`, `/_not-found`, `/pricing` on Next.js16.4.4.
- `npm audit --omit=dev`: **zero production vulnerabilities reported**. Full audit still reports 11 moderate and one high development-tool dependency entries (ESLint family/minimatch and zod); no breaking force-update was applied.
- Desktop pricing, monthly review and source evidence screenshots inspected; mobile overflow assertions passed. Local screenshots under `apps/web/test-results` are regenerated by tests, not production/customer evidence.

Browser AI response fixtures test UI behavior without external model calls; they are not live OpenRouter quality evidence. Monthly-review browser fixture tests wiring; backend SQL/calculation correctness is independently exercised on PostgreSQL. No new company datasets or invented relationships were added. No authenticated Zoho benchmark, paid billing test, new live AI inference or hosted deployment was executed. Existing production records and unrelated user files remain unchanged.

Initial verification infrastructure failures were resolved: localhost sandbox access, keeping the local PostgreSQL process alive, and an occupied default browser-test port. Test servers used isolated ports3013/8013. A TSV private-storage allowlist omission was fixed before successful tests. The new confirmation-failure expectation was corrected to existing HTTP409 semantics; an evidence-URL expectation was updated for its explicit currency filter.

## Next validation
Observe five target owner/bookkeeper users importing and investigating the same bounded file. Measure completion time, mapping corrections, help required and ability to verify the answer against originals. Compare with their spreadsheet process and Zoho where account access exists. This is proposed validation, not a measured outcome.
