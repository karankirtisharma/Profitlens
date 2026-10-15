# ProfitLens delivery progress

> Latest minor-project fixes and fresh verification: [release report](MINOR_SCOPE_RELEASE_REPORT.md). Earlier dated results below retain their historical scope.

The project has a twelve-week development period. This page records verified implementation, not college approval or assumed completion based on dates.

**15 October update:** Weeks 5–12 now have a bounded local implementation and evaluation. Live hosted-model validation and Docker deployment verification remain incomplete; semantic embeddings/pgvector are deferred. The detailed [implementation report](ROADMAP_IMPLEMENTATION_REPORT.md) supersedes older future-tense entries below.

| Milestone | Verified evidence | Status |
| --- | --- | --- |
| Week 1: foundation and ingestion preview | CSV/PDF validation, customer-period linking, source references and nine original tests | Complete — 27 September 2026 |
| Week 2: database, API foundation and secure workspace | PostgreSQL schema/migration, FastAPI, server-side sessions, preset roles, organization/customer access checks, Next.js login and workspace | Complete — 10 October 2026 |
| Week 3: business data management and persistent imports | Customer/invoice/expense create/read/update, atomic preview-confirm imports, retry protection, provenance, private PDFs, manual monthly-term review and team assignments | Complete — 10 October 2026 |
| Week 4: revenue, costs and data quality | Exact customer/month calculations, source inspection, missing-data and contract-period controls, scoped API and browser verification | Complete — 11 October 2026 |

## Weeks 2–3 verification

- Migrated fresh PostgreSQL 17 databases using Alembic; checked schema against SQLAlchemy metadata.
- **29 Python tests**: nine original ingestion checks plus twenty PostgreSQL/API cases, including cross-tenant and assigned-customer access, session expiry/logout, CSRF checks, login throttling, invalid imports, simultaneous retry, failed transaction/commit, decimal precision, private downloads and reviewed contract periods.
- **11 Chromium browser tests**: real sign-in and record editing; CSV errors/confirmation/retry; private PDF evidence and term review; analyst restrictions; mobile layout; intro skip/replay; reduced motion and focus restoration; chart/API consistency; error recovery; and automated accessibility checks.
- Production Next.js build, TypeScript, frontend/Python lint and code formatting checks.
- Small synthetic CSV/PDF fixtures, separate test databases and reproducible setup instructions. [Run the application and checks](DEVELOPMENT.md).

## Week 3 presentation polish — 10 October 2026

A responsive dark-glass frontend now presents the completed data-management features. GSAP provides a short, skippable logo intro; Framer Motion handles component transitions and record-count charts; Tailwind v4 supports the shared styling. The overview fetches real authorized customers, invoices, expenses and contracts. Seeded organizations are labeled synthetic, chart values are record counts, and future financial/AI capabilities remain explicitly outside this release. See the [presentation guide](DEMO.md).

## Week 3 interface refinement - 10 October 2026

Updated the workspace with light and dark themes, record-source previews, a skippable intro on each visit and after sign-in, and optional interface sounds. Input feedback and view loading were refined while keeping existing business workflows connected to the authorized API. Reduced-motion support and keyboard navigation remain available.

The refreshed browser suite passed all 11 cases, including record editing, CSV validation/confirmation/retry, PDF review/download, analyst restrictions, error recovery, mobile layout and automated accessibility checks. Lint, TypeScript and formatting checks passed. The feature boundary remains Weeks 1-3; financial calculations and AI capabilities are still planned.

## Preloaded faculty demo - 10 October 2026

The explicit demo setup now includes twelve months of varying invoice/expense record counts, private PDFs with reviewed and unreviewed examples, and import history. The separate `demo-files/` pack remains available for new imports. Repeat setup preserves existing business edits and revoked customer grants. The current Python suite passes 30 checks, including the new presentation-seed regression case. All 11 browser acceptance tests also pass with the populated seed, including chart/API consistency and the six-/twelve-month selector. No new financial or AI capabilities were added.

## Week 4 financial foundation — 11 October 2026

The **Revenue & costs** screen now calculates net billed revenue (`subtotal - discount - refund`, excluding tax) and recorded attributed costs using server-side Decimal arithmetic. Customer/month filters, customer pagination and exact source-record links make the figures inspectable. Missing records show **Unavailable**; explicit zeros stay zero; cost completeness remains unverified.

Defensive checks cover invalid amounts/references/currencies, stable-ID duplicates, reviewed contract coverage, partial months and overlapping periods. No automatic proration or pricing anomaly is inferred. Calculations enforce existing organization/customer access and reject oversized source sets rather than return partial totals. [Calculation rules and API](FINANCIAL_RULES.md).

Verification on separate local PostgreSQL databases: **53 Python tests** and **13 Chromium acceptance tests** passed. These include independent golden arithmetic, refunds/tax/zero/missing inputs, more than 200 source records, pagination, import retry, revoked access, exact-record navigation, expanded mobile sources and automated accessibility checks. Frontend build, TypeScript, lint and formatting checks passed. These results describe tested scenarios, not production certification.

Four reproducible `W4-` synthetic customers are added by explicit presentation seeding, with expected amounts documented in [data/week4](../data/week4/README.md). Existing imported data and edits are preserved; the separate teacher upload pack remains available for fresh imports.

## Current completion boundary — 15 October 2026

| Phase | Current evidence | Status |
| --- | --- | --- |
| Week 5 | Contribution/margin, hash-bound cost reviews, pricing/cost/margin findings, scoped API and working screen | Implemented and locally tested |
| Weeks 6–7 | Page chunks, provenance, BM25 ranking, reviewed-period filtering, permission-preserving baseline | Implemented lexical RAG foundation; neural embeddings/pgvector deferred |
| Weeks 8–9 | Strict OpenRouter/NVIDIA adapter, exact metric/quote verification, abstention/failure states, reauthorization, stale-aware history | Code and mocked-provider tests complete; live model behavior/quality unverified |
| Weeks 10–11 | Frozen synthetic corpus, 30 questions, financial labels, retrieval baseline and regression/security tests | Local evaluation complete; external/human validation not performed |
| Week 12 | Additive migration, local backup, separate seeded demo, integration tests, docs, Docker preparation | Local integration complete; Docker images/public hosting unverified |

Quantization is intentionally deferred because lexical retrieval has no pretrained weights. A future neural retrieval decision should first address the measured paraphrase misses; any memory/quality comparison would then be a separate experiment. No multi-industry expansion was implemented.

Operational limits are documented in [Development](DEVELOPMENT.md) and [Workspace access and imports](SECURITY_AND_IMPORTS.md). PDF OCR, automatic contract-term extraction, public registration, cloud object storage and public deployment are not part of the completed Weeks 2–3 scope.
