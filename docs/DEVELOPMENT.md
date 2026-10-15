# Run ProfitLens locally

## Runtime decisions

The current application uses Python 3.12, FastAPI, SQLAlchemy Core, Alembic, PostgreSQL 17, and Next.js 16 / React 19 / TypeScript on Node.js 24. Python dependencies are pinned in `requirements.lock`; frontend dependencies are pinned in `apps/web/package-lock.json`.

Accounts are provisioned locally. Passwords are hashed with Argon2; opaque session tokens are stored only as SHA-256 hashes in PostgreSQL. The browser receives an HttpOnly, SameSite=Strict cookie. Sessions expire after eight hours and are revoked on logout. A same-origin Next.js proxy connects the browser to FastAPI; no database credentials enter the frontend bundle. No external authentication subscription is required.

## First-time setup

Run commands from the repository root unless a command changes directory. Prerequisites: Python 3.12+, Node.js 24, and PostgreSQL 17 (or Docker Desktop/Engine for the supplied database service).

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
Copy-Item .env.example .env
```

Edit `.env`: choose a local database password, set the matching `DATABASE_URL`, and keep `WEB_ORIGIN=http://localhost:3000`. URL-encode reserved characters if your database password contains them. Do not commit `.env`.

For Docker, the `POSTGRES_PASSWORD` and `DATABASE_URL` values must agree:

```powershell
docker compose up -d db
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m profitlens.manage seed-demo
cd apps/web
npm ci
npm run build
```

The seed command prompts for a password of at least 12 characters. It creates synthetic workspaces and four accounts: `karan@profitlens.local` (admin), `finance@profitlens.local` (finance), `analyst@profitlens.local` (analyst assigned to C001), and `other@profitlens.local` (admin of the isolated second organization). They use the supplied demo password. Re-running seed does not reset existing passwords or restore revoked grants. Use synthetic data only for this setup. The command also preloads the presentation dataset described below.

## Start the application

### Windows launcher

After first-time setup, double-click `dev.cmd` in the repository root. Choose **1 - Start** to apply migrations and start FastAPI and Next.js in development mode with automatic reload. Choose **2 - Stop** to stop both servers, including their reload workers. Choose **0 - Exit** to close only the launcher; servers keep running until you choose Stop. PostgreSQL stays running.

The launcher records process IDs and start times in ignored `.local/dev-processes.json`, so it only stops its own processes. An occupied port produces an error instead of stopping another application. If the older production helper or a manually started server is running, stop it before using this launcher. Logs are in `.local/dev-web.out`, `.local/dev-web.err`, `.local/dev-api.out` and `.local/dev-api.err`. Dependencies, accounts and `.env` must already exist; the launcher does not install or reset them.

For alternate local ports, use `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev.ps1 -Action Start -WebPort 3300 -ApiPort 8300`. The matching local origin and API proxy are set for the child processes. Only one launcher session per checkout is supported.

### Manual startup

From the root, start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn profitlens.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd apps/web
npm run dev
```

Open **http://localhost:3000** (use this exact origin, rather than 127.0.0.1, for browser requests). API documentation is at **http://127.0.0.1:8000/docs**; read endpoints can be explored there, but writes require the configured origin and a session. Health is at `/api/health`. For production-build verification, use `npm run build` and `npm start` instead of `npm run dev`.

On the prepared Windows development machine, `scripts/start-local.ps1` starts the existing private portable database when available and launches both servers in the background. It does not install PostgreSQL or create credentials. The portable data directory, runtime logs and local demo access file are excluded from Git. Other machines should use Docker or an installed PostgreSQL server. On macOS/Linux use `.venv/bin/python` in place of the Windows Python path.

To provision another member in an existing organization:

```powershell
.\.venv\Scripts\python.exe -m profitlens.manage add-user --organization demo-org --email teammate@example.test --name "Project teammate" --role analyst
```

Provide the password when prompted. An admin can then assign customers in **Team access**. Email invitations, password recovery, custom roles and organization creation screens are outside this release.

## Preloaded presentation workspace

Fresh `seed-demo` setup creates ten customers, twelve recorded months (October 2025–September 2026), 57 invoices, 84 expenses, two private PDFs and confirmed/invalid import history. Counts include the original small seed. Monthly record counts vary so both chart ranges are useful. One PDF has prepared, source-checked synthetic terms and the other is available for a live review. These are synthetic demonstration records, not financial analysis results.

For a previously provisioned local workspace, add this dataset without entering or changing account passwords:

```powershell
.\.venv\Scripts\python.exe -m profitlens.manage seed-presentation
```

Then click **Refresh** in the workspace. Existing user data adds to the totals. The command targets only the prepared `demo-org` INR workspace; it does not seed arbitrary workspaces. It preserves edits, previously reviewed contracts and revoked grants on repeat runs. Conflicting new IDs cause a database rollback. A process failure after writing a PDF can leave an unreferenced private file, as with the normal upload workflow.

`READY-` IDs identify the additional baseline records; original C001/C002 remain so the existing analyst assignment has twelve months of examples. `demo-files/` uses separate `DEMO3-` IDs and is **not imported by setup**. Keep it for live CSV/PDF uploads. If already uploaded manually, matching files deduplicate as usual. No database dump, password or private PDF storage is published to GitHub; the seed code recreates the synthetic workspace on another machine after setup.

## Week 4 financial report

Open **Revenue & costs**, choose a customer and billing month, then expand **Calculation and sources**. [Rules, API and limits](FINANCIAL_RULES.md) and [golden demo cases](../data/week4/README.md) describe the expected amounts. Existing installations can add these cases with `python -m profitlens.manage seed-presentation`; no migration or new dependencies are required.

## Try the Week 3 workflow

For a timed faculty walkthrough, intro controls and visual-demo limits, see [the presentation guide](DEMO.md).

1. Sign in as admin. Inspect the seeded customer directory, invoice and expense records.
2. Open **Imports**. Upload customer CSVs before their invoices or expenses; preview, resolve errors and confirm.
3. Upload `data/demo/invalid_invoices.csv` to see row errors. Confirmation is unavailable; no business records are created.
4. Re-upload a previously confirmed file to see the same result without duplicate records. Matching records in different files are skipped; conflicting IDs require an explicit edit.
5. Open **Contracts**, associate `data/demo/contract_C001.pdf` with C001, and inspect its source page. Confirm the effective dates, fixed monthly rate, discount, currency and source page from the document. Download uses the authorized API.
6. Sign in as the analyst. Only C001 and its related records/documents are visible. Use the admin account to revoke that assignment; subsequent API requests are denied.

Contract PDFs are synthetic. `python scripts/generate_demo.py` recreates the small fixture set; this requires the test dependencies. The broader evaluation dataset belongs to subsequent milestones.

## Verification

The PostgreSQL integration suite requires a **separate database whose name ends in `_test`**. Create `profitlens_test` and `profitlens_e2e_test`, owned by your test database role, and set their full connection strings locally. Do not point tests at the development database. API tests clear their dedicated database tables between cases. Browser tests add synthetic records to their separate database.

```powershell
# Set TEST_DATABASE_URL and E2E_DATABASE_URL to your dedicated test databases first.
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check apps/api tests scripts migrations
.\.venv\Scripts\python.exe -m ruff format --check apps/api tests scripts migrations
.\.venv\Scripts\python.exe -m alembic check
cd apps/web
npm run lint
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

Without `TEST_DATABASE_URL`, the 29 local ingestion and financial calculation tests run and the database tests are explicitly skipped. The browser harness starts its own API on port 8001 and Next.js on port 3001; it requires `E2E_DATABASE_URL`. In CI, both suites use fresh PostgreSQL databases. Test credentials are synthetic and must never be reused elsewhere.

## Current operational boundaries

- Development prototype; Internet deployment and the deployment review belong to Week 12. Before deployment, use HTTPS, secure cookies, a private API/database network, backups and an appropriate account recovery flow.
- PDF storage is a private local directory, not object storage. Back up it and PostgreSQL together. Unexpected process/commit failure can leave an unreferenced file; never expose the directory as a static web folder.
- One workspace currency, fixed monthly contract terms, text-based PDFs, and customer-attributed expenses. No OCR, automated term verification or currency conversion.
- Lists are bounded: 200 records per page; customer pickers cover the first 200 customers; latest 100 imports and 200 contracts. This supports the planned 20-customer evaluation, not an unlimited enterprise deployment.
- The new analysis module adds contribution/margin, reviewable discrepancies, BM25 evidence retrieval and verified extractive provider integration. Semantic search is not implemented; live AI requires configuration. See [Analysis setup](ANALYSIS_GUIDE.md) and [verification report](ROADMAP_IMPLEMENTATION_REPORT.md).

Browser-test ports default to 3001 (web) and 8001 (API). Optional `E2E_WEB_PORT` and `E2E_API_PORT` environment variables let the isolated harness use free ports while other projects are running. The harness derives the API origin and allowed browser origin from those values.

## Isolated build verification

Browser tests use `.next-e2e` to avoid replacing `.next` for a running development session. `NEXT_DIST_DIR` optionally selects a separate Next.js build directory; `.next-verify` is ignored for production-build checks. Browser test ports remain independently configurable. The latest [minor-project verification report](MINOR_SCOPE_RELEASE_REPORT.md) distinguishes real provider checks, mocked flows and remaining limits.
