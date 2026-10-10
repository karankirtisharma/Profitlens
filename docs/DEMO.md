# Week 3 presentation guide

The current release demonstrates an authenticated business-data workspace. All business actions use FastAPI and PostgreSQL; the sample organizations contain synthetic data.

## Start the prepared Windows demo

From `D:\Profitlens`:

```powershell
.\scripts\start-local.ps1
```

Open **http://localhost:3000**. Use the provisioned account and its password saved privately in `.local/demo-access.txt` on the prepared machine. Keep that file off screen while presenting. On a new machine, follow [Development](DEVELOPMENT.md) to set up PostgreSQL, migrations and accounts first.

The helper starts an existing production build. After frontend changes, stop the project's frontend process, run `npm --prefix apps/web run build`, then restart it with the helper. Avoid running development and production servers on the same port. The local startup helper does not install dependencies or provision accounts.

## Suggested faculty walkthrough — 5 to 7 minutes

| Step | Show | Explain |
| --- | --- | --- |
| 1. Enter | Short logo introduction, then the sign-in screen. | The intro plays once per browser session; **Play intro** replays it, **Skip intro** or Escape dismisses it. System reduced-motion settings bypass it. |
| 2. Overview | Sign in as `karan@profitlens.local`; inspect record counts and monthly record activity. | Values come from the authorized API. The chart counts invoices and expenses; it does not calculate revenue or profit. The selector shows the latest six or twelve months that contain records. |
| 3. Records | Open Customers, then Invoices; inspect or edit a synthetic record. | Customer IDs link the data. Amounts, invoice totals and required fields are validated by the backend. Source references remain inspectable. |
| 4. Validation | Open Imports and preview `data/demo/invalid_invoices.csv`. | Invalid rows cannot be confirmed. The preview explains the validation problem without adding business records. |
| 5. Import | Preview and confirm a valid fixture such as `data/demo/expenses.csv`; repeat it. | Confirmation is transactional. An already imported file does not duplicate records; identical seeded records can be skipped. Use a new synthetic ID if demonstrating a newly inserted row. |
| 6. Evidence | Upload `data/demo/contract_C001.pdf` for C001; open the source page and review its terms. | The sample is a text PDF: rate INR 10,000, discount 0, effective 1 September 2026 through 28 February 2027, source page 1. Review against the PDF before saving. The authorized download also works. |
| 7. Access | Sign out and sign in as `analyst@profitlens.local`. | Only assigned customer C001 and its records are visible. Import, editing and team administration controls are unavailable to this role. |

The seed also provisions `finance@profitlens.local` and `other@profitlens.local`; the latter belongs to an isolated second organization. Account creation is a local administration command, not a public registration flow.

## Presentation behavior

- The interface uses dark glass surfaces, local fonts, responsive tables and native modal dialogs. Password visibility, keyboard focus, loading, error recovery and empty states are supported.
- GSAP controls the finite logo and glass-tile entrance. Framer Motion controls short page, dialog, button and chart transitions. Tailwind v4 utilities complement shared CSS tokens.
- Movement is reduced for keyboard navigation and disabled with the system's reduced-motion preference. Decorative graphics are hidden from assistive technology. No animation is necessary to complete a task.
- Charts use only the records accessible to the current account. The overview loads at most 200 records per type and 200 contracts; a limit note appears when a list reaches that cap. It is a preview of loaded records, not an unlimited analytics report.
- The small seed has a limited set of records and may show one billing month and an empty contract library. Importing or reviewing data updates the overview after navigation or **Refresh**. No extra trends or financial results are fabricated for the presentation.

## Verified scope and limits

The checked flows cover sign-in/out, customer/invoice/expense management, CSV preview/confirmation/retry, private PDF upload/download, manually reviewed monthly terms, and assigned-customer access. The presentation checks cover intro skip/replay, reduced motion, focus restoration, chart/API consistency, failure recovery, narrow layouts and automated WCAG checks for sign-in, overview and an invoice dialog. Automated accessibility checks supplement manual keyboard and visual inspection; they are not a complete accessibility certification.

**Not yet implemented:** profitability aggregation, margin calculations, anomaly detection, semantic search, AI explanations, model quantization, OCR, automatic contract extraction, social login, public registration and password recovery. These remain subsequent milestones. The local demo is not a public deployment.

For verification commands and database isolation rules, see [Development](DEVELOPMENT.md). Browser tests use ports 3001/8001 by default. If another application owns those ports, set `E2E_WEB_PORT` and `E2E_API_PORT` to free ports before running `npm run test:e2e`; do not stop unrelated applications.
