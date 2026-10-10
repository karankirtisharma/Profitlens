# Week 3 presentation guide

The current release demonstrates an authenticated business-data workspace. All business actions use FastAPI and PostgreSQL; the sample organizations contain synthetic data.

## Start the prepared Windows demo

From `D:\Profitlens`:

```powershell
.\scripts\start-local.ps1
```

Open **http://localhost:3000**. Use the provisioned account and its password saved privately in `.local/demo-access.txt` on the prepared machine. Keep that file off screen while presenting. On a new machine, follow [Development](DEVELOPMENT.md) to set up PostgreSQL, migrations and accounts first.

The helper starts an existing production build. After frontend changes, stop the project's frontend process, run `npm --prefix apps/web run build`, then restart it with the helper. Avoid running development and production servers on the same port. The local startup helper does not install dependencies or provision accounts.

## Already populated when you sign in

The explicit demo setup now includes twelve months of synthetic records, confirmed/invalid import history, one prepared reviewed PDF and one PDF awaiting review. On a fresh setup the inventory is 6 customers, 54 invoices, 80 expenses and 2 contracts; existing records can increase these totals. Refresh the app after running `python -m profitlens.manage seed-presentation` in the prepared environment.

Begin with **Overview**: switch between six and twelve recorded months, select a month, open the invoice/expense counters and inspect source rows. Then open **Contracts**, inspect the reviewed C001 terms and review C002 live (INR 20000, discount 0, 2026-09-01 through 2027-02-28, source page 1). The analyst's original C001 assignment includes twelve months of records. Prepared terms are synthetic fixture values checked against their PDFs, not an automated interpretation of a real contract.

## Ready-to-upload teacher pack

Open **`demo-files`** in the repository, then follow its [upload guide](../demo-files/README.md). In an INR workspace, import `01-valid-data` in this order: **customers, invoices, expenses**. A first import adds 5 customers, 30 invoices and 60 expenses across April–September 2026. These IDs are separate from the original seed records.

Upload the three PDFs from `02-contracts` against their matching customer IDs and review the terms using the guide. Use `03-validation-errors` to show rejected inputs, then `04-retry-and-conflict` to demonstrate safe retries and conflicting record IDs. All files contain fictional data. The file picker supports browsing; dropping a file onto its native input depends on the browser. There is no whole-page drop zone.

## Suggested faculty walkthrough — 5 to 7 minutes

| Step | Show | Explain |
| --- | --- | --- |
| 1. Enter | Short logo introduction, then the sign-in screen. | The intro plays on each visit and after sign-in; **Skip intro** or Escape dismisses it. System reduced-motion settings bypass it. |
| 2. Overview | Sign in as `karan@profitlens.local`; inspect record counts and monthly record activity. | Values come from the authorized API. The chart counts invoices and expenses; it does not calculate revenue or profit. The selector shows the latest six or twelve months that contain records. |
| 3. Records | Open Customers, then Invoices; inspect or edit a synthetic record. | Customer IDs link the data. Amounts, invoice totals and required fields are validated by the backend. Source references remain inspectable. |
| 4. Validation | Open Imports and preview `data/demo/invalid_invoices.csv`. | Invalid rows cannot be confirmed. The preview explains the validation problem without adding business records. |
| 5. Import | Preview and confirm a valid fixture such as `data/demo/expenses.csv`; repeat it. | Confirmation is transactional. An already imported file does not duplicate records; identical seeded records can be skipped. Use a new synthetic ID if demonstrating a newly inserted row. |
| 6. Evidence | Upload `data/demo/contract_C001.pdf` for C001; open the source page and review its terms. | The sample is a text PDF: rate INR 10,000, discount 0, effective 1 September 2026 through 28 February 2027, source page 1. Review against the PDF before saving. The authorized download also works. |
| 7. Access | Sign out and sign in as `analyst@profitlens.local`. | Only assigned customer C001 and its records are visible. Import, editing and team administration controls are unavailable to this role. |

The seed also provisions `finance@profitlens.local` and `other@profitlens.local`; the latter belongs to an isolated second organization. Account creation is a local administration command, not a public registration flow.

## Presentation behavior

- The interface is a liquid-glass design in light and dark themes (system default, manual toggle) with self-hosted Geist fonts, a custom WebGL background that stays still inside the workspace, responsive tables and native modal dialogs. The intro plays on every visit and after sign-in; sound effects are off until the visitor turns them on. Password visibility, keyboard focus, loading, error recovery and empty states are supported.
- GSAP controls the finite logo and glass-tile entrance. Framer Motion controls short page, dialog, button and chart transitions. Tailwind v4 utilities complement shared CSS tokens.
- Movement is reduced for keyboard navigation and disabled with the system's reduced-motion preference. Decorative graphics are hidden from assistive technology. No animation is necessary to complete a task.
- Charts use only the records accessible to the current account. The overview loads at most 200 records per type and 200 contracts; a limit note appears when a list reaches that cap. It is a preview of loaded records, not an unlimited analytics report.
- The presentation seed provides twelve recorded months and reviewed/unreviewed contract examples. Importing or reviewing data updates the overview after navigation or **Refresh**. Graphs show actual stored record counts; financial profitability and AI features remain later milestones.

The bottom-right mascot is a chatbot placeholder. Clicking it toggles a small **Under development** bubble; Escape or clicking elsewhere dismisses it. It does not send data or provide AI answers.

## Verified scope and limits

The checked flows cover sign-in/out, customer/invoice/expense management, CSV preview/confirmation/retry, private PDF upload/download, manually reviewed monthly terms, and assigned-customer access. The presentation checks cover intro skip, repeat visits and sign-in, reduced motion, focus restoration, chart/API consistency, failure recovery, narrow layouts and automated WCAG checks for sign-in, overview and an invoice dialog. Automated accessibility checks supplement manual keyboard and visual inspection; they are not a complete accessibility certification.

**Not yet implemented:** profitability aggregation, margin calculations, anomaly detection, semantic search, AI explanations, model quantization, OCR, automatic contract extraction, social login, public registration and password recovery. These remain subsequent milestones. The local demo is not a public deployment.

For verification commands and database isolation rules, see [Development](DEVELOPMENT.md). Browser tests use ports 3001/8001 by default. If another application owns those ports, set `E2E_WEB_PORT` and `E2E_API_PORT` to free ports before running `npm run test:e2e`; do not stop unrelated applications.
