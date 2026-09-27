# ProfitLens coding-agent guide

This file is for contributors and coding agents working in this repository. It describes the current plan; it does not override a direct request from the project team.

## Read first

If local `brain.md` exists, read it for dated session context. It is Git-ignored agent memory, not the source of truth; verify it against the working tree and current user instructions.

1. Read `README.md` for the public product description and truthful implementation status.
2. Read `docs/ROADMAP.md` before selecting work. Week numbers are milestones, not evidence of completion.
3. Read `docs/PROJECT_BRIEF.md`, `docs/ARCHITECTURE.md`, and `docs/DATA_CONTRACTS.md` for current scope and contracts.
4. The original `profitlens_brain.md` is background inspiration. Its solo/two-week schedule and unimplemented feature list are superseded by the current team and 12-week plan. Do not copy its instructions uncritically.

## Engineering rules

- Build a modular full-stack application: Next.js/TypeScript web app, FastAPI/Python API, PostgreSQL, and pgvector only where useful. Keep deployment complexity proportionate to a minor project.
- Keep organization IDs on every business record. Authorize before database retrieval and again before evidence is sent to an AI provider. Never rely on an LLM to enforce access.
- Use decimal or integer-minor-unit arithmetic for money. Document invoice totals, tax, discounts, refunds, missing costs, zero revenue, duplicates, and period mismatches. AI must never be the source of financial calculations.
- Keep imported source references so a user can inspect each finding. Treat extracted PDF terms as candidates until verified.
- Isolate any AI provider behind an interface. Ground generated findings in retrieved evidence; label incomplete evidence and unsupported claims rather than fabricating certainty.
- Use synthetic data in the public repository. Never commit real customer files, credentials, or `.env` values.
- Add focused tests for financial rules, import validation, tenant isolation, and retrieval. Avoid tests that simply mirror implementation details.
- Update README status and the weekly progress log only after the corresponding work is implemented and verified.

## Week 1 boundaries

The Week 1 ingestion code is a **preview**, not persistent storage or a deployed service. Keep its input contracts explicit, retain row/page provenance, and make validation errors inspectable. Database migrations and API endpoints belong to Weeks 2–3.
