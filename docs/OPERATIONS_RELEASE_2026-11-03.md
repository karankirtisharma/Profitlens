# Operations and navigation release — 3 November 2026

## Delivered locally

- Searchable, grouped navigation with mobile support; document library and report/task shortcuts.
- Separate vendors and item catalogue; bill entry with reviewed opening-paid amount.
- Explicit verified-invoice enrollment, partial and multi-document same-party payments, and current/overdue/undated balances.
- Audited payment void/re-entry; original allocations remain in history.
- Dashboard charts/counts use full authorized database summaries instead of the first 200 loaded rows.
- Two frozen, additive PostgreSQL migrations. Existing source data is not converted or enrolled automatically.
- Chat guidance explicitly distinguishes existing source/invoice evidence from the new operational subledgers. No unsupported balance claims are promised from chat.

## Executed verification

| Check | Observed result |
| --- | --- |
| Full backend suite | 196 passed in 30.01 seconds, dedicated local test database |
| Follow-up assistant/chat regressions after prompt guidance | 35 passed in 5.77 seconds |
| Browser suite | 22/26 passed on first full run; four failures were accessible-label mismatches introduced by this change |
| Corrected browser rerun | All five affected/navigation scenarios passed in 47.8 seconds; all 26 distinct scenarios passed across runs |
| Production build | Passed, Next.js 16.4.4; routes `/`, `/_not-found`, `/pricing` |
| TypeScript, ESLint, Prettier, Ruff | Passed |
| Fresh migration | Base to head and Alembic schema check passed on a separate migration test database |
| Rollback guard | Empty downgrade/re-upgrade passed; populated downgrade refused and retained its test record |
| Browser screenshots | Operations balance table inspected; recorded 100 bill minus 30 allocation = 70 outstanding, and 50 minus 20 = 30 |

Backend cases cover permission/tenant isolation, exact amounts, positive allocation rules, opening-paid bounds, missing attestation, unknown references, mixed parties/currencies, overpayment, duplicate IDs, tracked-invoice immutability and payment void history. The browser workflow creates synthetic records only and exercises vendor/item edits, bill entry, split payment, invoice enrollment and void/re-entry semantics. Existing source imports, PDF downloads, financial investigation, chat rendering, accessibility and mobile regressions also ran.

The two first-run navigation failures were caused by a group named Workspace colliding with the workspace selector. Two new-flow failures came from select labels containing option text. Unique accessible names corrected these failures; they were not suppressed or skipped.

## Limitations

This is not all of Zoho Books. Quotes, orders, recurring automation, tax filing, banking feeds, GL, inventory and portals are unimplemented. Items are a catalogue, not transaction-line or inventory integration. Bills and tracked invoices lack an amendment/reversal workflow and remain immutable. Payment voiding is an internal correction only, not a refund. No large-volume benchmark or independent security audit was performed. AI was disabled in browser tests; no paid external model calls were made for this release.

No new real company data or financial relationships were fabricated. Operations demo/test records are synthetic. Existing public-data workspaces retain their original financial meaning and missing-information disclosures.

## Hosting

Local implementation and checks above are complete. Production requires the additive migrations before the updated API is deployed. The private backup/migration request was initially blocked by automatic approval review pending explicit authorization for the local backup destination. Do not infer a completed hosted rollout from this report; GitHub deployment status and a subsequent live smoke check are the release evidence.

See [Operations guide](OPERATIONS_GUIDE.md) for setup/rollback and [public demo research](research/zoho-demo-workflow-audit-2026-11-03.md) for the feature comparison.
