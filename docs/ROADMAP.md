# ProfitLens delivery progress

The project has a twelve-week development period. This page records verified implementation, not college approval or assumed completion based on dates.

| Milestone | Verified evidence | Status |
| --- | --- | --- |
| Week 1: foundation and ingestion preview | CSV/PDF validation, customer-period linking, source references and nine original tests | Complete — 27 September 2026 |
| Week 2: database, API foundation and secure workspace | PostgreSQL schema/migration, FastAPI, server-side sessions, preset roles, organization/customer access checks, Next.js login and workspace | Complete — 10 October 2026 |
| Week 3: business data management and persistent imports | Customer/invoice/expense create/read/update, atomic preview-confirm imports, retry protection, provenance, private PDFs, manual monthly-term review and team assignments | Complete — 10 October 2026 |

## Weeks 2–3 verification

- Migrated fresh PostgreSQL 17 databases using Alembic; checked schema against SQLAlchemy metadata.
- **29 Python tests**: nine original ingestion checks plus twenty PostgreSQL/API cases, including cross-tenant and assigned-customer access, session expiry/logout, CSRF checks, login throttling, invalid imports, simultaneous retry, failed transaction/commit, decimal precision, private downloads and reviewed contract periods.
- **Five Chromium browser tests**: real sign-in and record editing; CSV errors/confirmation/retry; private PDF evidence and term review; analyst restrictions; mobile layout.
- Production Next.js build, TypeScript, frontend/Python lint and code formatting checks.
- Small synthetic CSV/PDF fixtures, separate test databases and reproducible setup instructions. [Run the application and checks](DEVELOPMENT.md).

## What remains

The application currently organizes and validates business data. Revenue/cost aggregation and data-quality analysis are next, followed by profitability metrics, rule-based findings, contract retrieval, AI investigations, verification and measured model-efficiency experiments. No profitability result, anomaly score, semantic retrieval benchmark or AI evaluation result is claimed in this release.

Operational limits are documented in [Development](DEVELOPMENT.md) and [Workspace access and imports](SECURITY_AND_IMPORTS.md). PDF OCR, automatic contract-term extraction, public registration, cloud object storage and public deployment are not part of the completed Weeks 2–3 scope.
