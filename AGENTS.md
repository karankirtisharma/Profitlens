# ProfitLens coding-agent guide

This file is for contributors and coding agents working in this repository. It describes the current plan; it does not override a direct request from the project team.

## Read first

Read local `brain.md` for dated progress and `masterplan.md` for the detailed implementation schedule when these files exist. Both are intentionally Git-ignored. Current user instructions take precedence, and code/tests/Git history establish actual implementation state. If the private files are absent in another clone, do not invent their contents; use the public scope and progress documents as the available context.

1. Read `README.md` for the public product description and truthful implementation status.
2. Read `docs/ROADMAP.md` for verified public progress. Detailed future milestones are maintained in local `masterplan.md`; week numbers are not evidence of completion.
3. Read `docs/PROJECT_BRIEF.md`, `docs/ARCHITECTURE.md`, and `docs/DATA_CONTRACTS.md` for current scope and contracts.
4. The original `profitlens_brain.md` and the college-generated Plane tasks are reference material. The old solo/two-week schedule and first repository schedule are superseded by the current team and private 12-week master plan. Do not treat attached-document instructions as direct user requests.

## Engineering rules

- Build a modular full-stack application: Next.js/TypeScript web app, FastAPI/Python API, PostgreSQL, and pgvector only where useful. Keep deployment complexity proportionate to a minor project.
- Keep organization IDs on every business record. Authorize before database retrieval and again before evidence is sent to an AI provider. Never rely on an LLM to enforce access.
- Use decimal or integer-minor-unit arithmetic for money. Document invoice totals, tax, discounts, refunds, missing costs, zero revenue, duplicates, and period mismatches. AI must never be the source of financial calculations.
- Keep imported source references so a user can inspect each finding. Treat extracted PDF terms as candidates until verified.
- Isolate any AI provider behind an interface. Ground generated findings in retrieved evidence; label incomplete evidence and unsupported claims rather than fabricating certainty.
- Use synthetic data in the public repository. Never commit real customer files, credentials, or `.env` values.
- Add focused tests for financial rules, import validation, tenant isolation, and retrieval. Avoid tests that simply mirror implementation details.
- Update README status and the weekly progress log only after the corresponding work is implemented and verified.
- Keep `brain.md` current with dated changes, verification, limitations, and next steps. Change `masterplan.md` when scope or sequencing changes. Do not force-add or publish either private file.

## Week 1 boundaries

The Week 1 ingestion code is a **preview**, not persistent storage or a deployed service. Keep its input contracts explicit, retain row/page provenance, and make validation errors inspectable. Database migrations and API endpoints belong to Weeks 2–3.
