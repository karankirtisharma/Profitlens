> **Archived expanded proposal — superseded for COM-711.** This is future research, not the current implementation backlog. Use the [active minor-project SRS](../../../../requirements/SRS.md). Historical claims below retain their original audit context.

# ProfitLens: implementation audit and gap analysis

Snapshot: 15 October 2026; Git `c4abad70b53d934016bf5cb39076bf80edf7b756`. Research only. **The code is beyond Week 4; the flexible organization layer is not implemented.**

## 1. Evidence and audit boundaries

Inspected README, public ROADMAP/ARCHITECTURE/DATA_CONTRACTS/FINANCIAL_RULES/SECURITY_AND_IMPORTS/ANALYSIS_GUIDE/DEPLOYMENT, implementation/evaluation reports, private brain/masterplan, both Alembic revisions, API/schema/security/import/finance/retrieval/AI modules, frontend workspace/types/components, test files, dependency manifests and dataset tooling. Read the revised 25 September synopsis in Downloads and selected status pages of the 32-page `PROFITLENS_KNOWLEDGE_BASE_VIVA_GUIDE.pdf` (10 October snapshot). The earlier conversation supplies historical intent, not implementation evidence.

A read-only PostgreSQL transaction confirmed revision `20261015_roadmap`, all 16 application tables present and only `plpgsql` installed as an extension. This is a table-presence/version check, not a complete schema-drift or data-quality audit. No private rows/credentials were exported. Frontend inspection was static plus TypeScript; no fresh browser acceptance run. Baseline tests and limitations are in [test strategy](../testing/test-strategy.md).

## 2. Current inventory

| Area | Observed implementation / evidence | Status and boundary |
|---|---|---|
| Stack | `apps/web/package.json`: Next.js 16.4.0, React 19.3.0, TypeScript; Python manifest FastAPI/Pydantic/SQLAlchemy/Alembic/psycopg/pypdf | Present. Manifest versions are declarations, not a fresh dependency-security audit |
| Identity | `security.py`, `main.py`: hashed passwords, expiring server sessions, org membership, admin/finance writers, assigned-customer analysts | Implemented; current research did not rerun login/RBAC integration suite |
| Persistence | `database.py`; migrations `47e0ed9226fa` → `20261015_roadmap` | Relational PostgreSQL; not SQLite and not a vector database |
| Business records | `records.py`, `schemas.py`, `ingestion/models.py` | Customers/invoices/expenses create/read/update with same-org customer FK; no vendor/project/payment entities |
| CSV | `ingestion/csv_import.py`, `imports.py` | UTF-8 strict header set, 5 MiB/10,000-row limits; atomic confirm and conflict protection. No flexible mapping/XLSX |
| Contracts | `main.py`, `ingestion/pdf_contract.py` | Private text PDF, 10 MiB/100 pages, manual fixed monthly terms, page source. No OCR or agreement amendment model |
| Finance | `finance.calculate/report`, `profitability.metrics/findings/attest` | Decimal net billed revenue, costs, contribution, margin, completeness and discrepancy rules exist |
| Search | `retrieval.py` | BM25, page chunks, permission-first candidate filtering, reviewed/full-month context mode. No embedding model/pgvector use |
| Investigations | `explanations.py`, `analysis_api.py` | Strict structured claims, exact values/quotes, source history and reauthorization. A verified quote does not establish relevance or causality |
| Popup chat | `chat.py`, `assistant.py`, `workspace_summary.py`, `chatbot-launcher.tsx` | Provider-generated responses, permitted automatic scope, placeholders/cards/source navigation; model semantics not exhaustively validated |
| UI | `app/page.tsx`, `lib/workspace.ts`, overview/finance/analysis components | Working-code surfaces for imports, records, terms, finance, chat; fixed fields and kinds; overview explicitly indicates 200-record preview cap |
| Evaluation | `evaluation.py`, saved JSON, `tests/`, Playwright files | Synthetic checks and baseline exist; new organization schemas/matching require new ground truth |
| Operations | local launcher, Docker/deployment preparation | Local setup exists; no new hosting, restore or container validation in this phase |

## 3. Current data and operation contracts

Organizations have only ID/name/currency. Global users join organizations via memberships; grants link membership to customer. Business PKs include organization. Session/login-limit tables are application-wide. Customers have ID/name/industry/source/created time. Invoices require customer, `YYYY-MM`, workspace currency, subtotal/discount/tax/refund/total; five amount columns are nonnegative `NUMERIC(14,2)` and constrained to `total = subtotal - discount + tax - refund`, with discount + refund no greater than subtotal. Expenses require customer, month, category and nonnegative amount. There are no invoice lines, issue/due dates, settlement balances, vendors or shared-cost allocations.

`record_events` stores actor/action/snapshot; `import_batches` stores validated rows/issues and a fingerprint unique by org/kind. It does not retain original CSV bytes or a complete original-cell representation: temporary upload files are removed, and invalid/unknown cells are not a reusable staging model. Contracts combine private PDF identity/text and mutable reviewed terms in one entity. `document_passages` has an unused JSONB embedding column, not a vector index. `cost_reviews` binds an attestation to expense-input hash. `investigations` snapshots evidence/results.

The scalar invoice `refund` is a **legacy billed-revenue adjustment**, not a general cash-refund or credit-note ledger. Cost arithmetic can be provisional if recorded expenses exist but completeness is unverified. No costs produces unavailable contribution; explicit zero-cost rows can represent attested zero. Pricing compares pre-refund billed charges with one applicable fixed monthly agreement. Cost/margin alerts require confirmed current/prior costs. These safeguards should survive migration.

### Existing API surface (not the proposed v2 contract)

All workspace routes below use `/api/workspaces/{organization_id}`. Session routes are `/api/auth/login`, `/api/auth/logout`, `/api/auth/me`; health is `/api/health`.

| Current route | Behaviour / boundary |
|---|---|
| GET `/records/{kind}` and `/records/{kind}/{record_id}`; registered POST/PUT kind routes | Three allowed kinds; trusted org scope; writer validation and source/audit retention |
| POST `/imports/{kind}/preview`, POST `/imports/{batch_id}/confirm`, GET `/imports` | Writer-only preview/confirm/history; repeated confirmed batch idempotent |
| GET/POST `/contracts`, GET `/contracts/{id}/file`, PUT `/contracts/{id}/terms` | Scoped text PDF and monthly review; incompatible currency/page/overlap rejected |
| GET `/members`, PUT `/members/{user_id}/customers` | Admin-only membership view and analyst customer assignment |
| GET `/finance`, GET `/profitability`, PUT `/profitability/{customer_id}/{billing_period}/cost-review` | Customer/month calculations, bounded pagination, input-bound cost confirmation |
| GET `/evidence/search`, POST `/evidence/reindex`, GET `/ai/status` | Scoped lexical evidence and provider readiness; reindex writer-only |
| POST/GET `/investigations`, GET `/investigations/{identifier}`, POST `/chat` | Evidence-backed investigation history and bounded live-provider chat; reauthorization |

Current errors use FastAPI `detail` payloads (strings or field/row issue lists), not the proposed unified v2 envelope. Invalid input uses 422, conflicts 409, missing/hidden resources 404, missing session 401 and forbidden action/origin 403. Existing middleware limits requests, disables caching and sets response safety headers. CI declares isolated PostgreSQL, Python checks, frontend checks and Playwright; the hosted CI run status was not checked.

## 4. Prioritized gaps

Priority: P0 meaning/security integrity; P1 core usability/correctness; P2 later capability. “Risk” is a finding from inspection, not a demonstrated exploit.

| ID | Priority / finding | Evidence and consequence | Preserve / proposed improvement |
|---|---|---|---|
| G01 | P0 rigid expense ownership | `record_columns` requires customer; genuine public spending needed technical grouping records | Keep old records intact; permit unallocated expenses and real vendor references; never manufacture customers |
| G02 | P0 fixed monetary meaning | Invoice five-field equation and two-decimal storage cannot represent every export, currency or credit lifecycle | Retain legacy adapter; add explicit amount basis, line/tax/credit semantics and unknown states |
| G03 | P0 unknown/raw data not preserved | Strict headers reject extras; normalized batch rows omit source-cell detail | Immutable source files, staged cells, reviewed mappings and transformation versions |
| G04 | P0 absent config contract | Organization has only name/currency; form fields static in `lib/workspace.ts` | Versioned validated profile and generated form schema; mandatory invariants cannot be relaxed |
| G05 | P0 access model assumes customer ownership | `visible(table,s)` accesses `customer_id` | Define visibility for unallocated/vendor/payment rows before exposing them; no “all org members” fallback |
| G06 | P1 contracts mix file and agreement | Terms mutable; overlapping reviewed customer contracts rejected | Separate agreement, version, billing scope and source evidence; overlapping distinct services may be legitimate |
| G07 | P1 payment/credit/allocation lifecycle absent | No tables or APIs | Add separate entities after canonical identity/mapping; never equate cash receipt with revenue |
| G08 | P1 duplicate protection narrower than identity reconciliation | Fingerprint org/kind + stable IDs; same-ID edits conflict | Preserve exact protections; add source namespace and reviewed probable-duplicate queue |
| G09 | P1 synchronous coarse-grained writes | Workspace row lock spans import validation/insertion; PDF parsing occurs during write transaction | Keep atomicity; stage parsing before short confirm transaction; background worker only after measurement |
| G10 | P1 file/DB atomicity risk | PDF written before DB commit; error cleanup inside upload function may not cover later commit failure | Quarantine/manifest state + recovery sweep; paired DB/file backup/restore test |
| G11 | P1 evidence requirements too coarse | `explanations.explain` requires confirmed costs AND contract passages for every investigation | Per-question prerequisites: revenue questions need not require a contract; contract compliance must require one |
| G12 | P1 duplicated context paths | `finance`, `profitability`, `workspace_summary`, `chat.documents`, `retrieval.search` build different bounded contexts | Shared typed evidence envelope; preserve intentional distinction between unreviewed document chat and verified pricing |
| G13 | P1 operational/security validation incomplete | Plain local cookies configurable; upload parser in process; no demonstrated malware isolation/restore monitoring | Production HTTPS, tested storage policy/resource caps, redacted telemetry and restore exercise before hosting |
| G14 | P1 UI preview coverage | Overview first 200 records with explicit cap; customer selection bounded | Preserve cap disclosure; server count/aggregation endpoints and pagination before large real datasets |
| G15 | P1 benchmark narrow | Frozen synthetic 30-question evaluation; lexical paraphrase misses | Hold-out real component schemas, new relation labels, human explanation relevance; quantify failure types |
| G16 | P2 integrations/modules absent | No XLSX/OCR/drive/bank/API import implementation; no module registry | CSV/XLSX first; adapters later; unsupported modules cannot be enabled as if functional |

## 5. Documentation discrepancies

- User's “approximately Week 4” and 10 October viva guide describe older snapshots. Current finance, retrieval, chat and migration code proves subsequent work exists; it does not prove all original research aims are complete.
- Synopsis proposed semantic retrieval/pgvector and quantization; current BM25 implementation does neither. Its references to solo feasibility and a sixteen-week figure conflict with current team/twelve-week instructions. Do not edit the submitted synopsis in this research phase; flag for later revision.
- Public roadmap retains historical “future AI” wording alongside a later implementation override. Its live-provider unverified wording and README's smoke-test statement need reconciliation: a smoke test is not systematic quality evaluation.
- `pyproject.toml` supports Python >=3.11 while README suggests 3.12+. Treat this as setup-document inconsistency, not proven runtime failure.
- No newly reproduced broken user flow was established. Known limitations and suspected risks above must not be described as confirmed outages. Historical test counts are separate from this phase's results.

## 6. Evidence of testing

Fresh safe run: **43 passed in 0.92 s**, `pytest -q -p no:cacheprovider tests/test_ingestion.py tests/test_finance.py tests/test_retrieval_evaluation.py tests/test_provider.py`. Provider calls mocked. TypeScript `--noEmit --incremental false` exited 0. Read-only live schema check succeeded. No migration, seed, data import, live model call, database-reset suite or application change was performed.

Saved evaluation (not rerun as an external benchmark): 20/20 synthetic contribution cases and 15 labelled anomalies detected without extra flags; held-out context/BM25 recall@3 0.6667, same as baseline, with improved ranking/returned precision. See [testing](../testing/test-strategy.md) for exact interpretation and limitations.

## 7. Recommended next decision

Review [SRS](../requirements/SRS.md) and [phased roadmap](../implementation/phased-roadmap.md). First authorize config/identity/raw-source foundations and compatibility tests. Do not loosen required financial fields, remap live data or expand industries until workflow prerequisites and migration behaviour are agreed.
