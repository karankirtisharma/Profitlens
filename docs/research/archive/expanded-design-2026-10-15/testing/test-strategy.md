> **Archived expanded proposal — superseded for COM-711.** This is future research, not the current implementation backlog. Use the [active minor-project SRS](../../../../requirements/SRS.md). Historical claims below retain their original audit context.

# ProfitLens testing and evaluation strategy

15 October 2026 · research baseline and proposed acceptance plan. [SRS](../requirements/SRS.md), [traceability](../requirements/requirements-traceability.md), [datasets](../research/real-world-data-formats-and-datasets.md).

## 1. Actual checks executed in this research phase

| Check | Command / method | Actual result | Limit |
|---|---|---|---|
| Safe Python baseline | .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests/test_ingestion.py tests/test_finance.py tests/test_retrieval_evaluation.py tests/test_provider.py | **43 passed in 0.92 s**, exit 0 | Four selected files; provider traffic mocked; not all application tests |
| Frontend types | apps/web/node_modules/.bin/tsc.cmd --project apps/web/tsconfig.json --noEmit --incremental false | **Exit 0**, no diagnostics | Type checking, not browser behaviour or production build |
| Database inventory | SQLAlchemy connection, SET TRANSACTION READ ONLY, inspect tables, read alembic_version and pg_extension, rollback | Revision 20261015_roadmap; 16 application tables present; metadata_missing empty; extension plpgsql only | Not full drift comparison, migration execution or row-content validation |
| Documentation QA | Local link/requirement/diagram-fence validation after artifact creation | See final QA note below | Does not substitute for rendering diagrams or external product trials |

No seed, schema migration, database-reset test suite, hosted AI call or application behaviour change. Existing integration tests delete fixture-table contents and therefore were not run against the development database. No new live browser claim. Prior work's 114-test run is historical evidence, not this phase's result.

## 2. Existing saved evaluation: interpret narrowly

Source: docs/evaluation-results-2026-10-15.json and evaluation.py, inspected rather than regenerated as a live-data experiment.

- Synthetic corpus: 20 customers, six months, 120 invoices, 115 expenses, 40 contracts; 30 questions split into 10 development and 20 held-out.
- Financial labels: 20/20 contribution cases correct; 15 true-positive anomalies, zero reported false-positive/false-negative on that fixture.
- Held-out retrieval: 15 answerable and 5 unanswerable questions. Baseline and context both recall@3 0.6667. Baseline returned precision@3 / MRR 0.3333 / 0.3333; context 0.6667 / 0.6667. Both correctly abstained on the five labelled unanswerable questions.
- Context improved ranking/returned precision on this corpus, not recall; lexical paraphrase misses remain. These figures are not a customer study, statistical generalization or proof of live LLM answer correctness. Perfect fixture anomaly detection is not a production accuracy claim.

## 3. Test environments and isolation

Unit tests use pure functions/temp files, fixed clock where relevant and mocked outbound HTTP. Integration tests use an explicit dedicated PostgreSQL name ending _test, temporary private storage and no production credentials/data. Inspect tests/test_workspace.py fixture before running: it deletes all fixture tables. Never point TEST_DATABASE_URL at profitlens.

Migration suite uses a disposable restored legacy fixture snapshot and an empty database. Browser suite uses separate ports/storage/build directory to avoid interfering with a running Next.js dev server. Security tests exercise ordinary login/origin/session behaviour; do not bypass authorization by injecting fake sessions. AI quality tests run only with explicit permission for the selected non-sensitive corpus and provider budget.

Proposed baseline commands after implementation review:

~~~powershell
# Safe baseline (executed in this research phase)
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_ingestion.py tests/test_finance.py tests/test_retrieval_evaluation.py tests/test_provider.py
.\apps\web\node_modules\.bin\tsc.cmd --project apps/web/tsconfig.json --noEmit --incremental false
# Full pytest requires a verified dedicated TEST_DATABASE_URL ending _test.
# Do not paste credentials into reports or command output.
~~~

All future execution records include commit, dependency lock versions, OS/CPU/RAM, database version, seed, corpus/config/calculation hashes, command, time, counts and failures. A skipped test is not a pass.

## 4. Acceptance test matrix

Every case below is a **proposed target acceptance scenario**. Some underlying primitives have existing tests; none of the new flexible-schema acceptance requirements is claimed fully verified. Each case links directly to the SRS row and phase. Use table-driven variations and integration tests for cross-record/transaction behaviour.

| Test ID | Requirement / subject | Setup and expected observable result | Phase |
|---|---|---|---|
| T01 | FR-01 — Versioned organization profiles | Two concurrent edits yield one activation and one 409; prior records retain their interpretation version. | P1 |
| T02 | FR-02 — Optional modules | Contract-free organization imports valid invoices; compliance displays not applicable; unsupported inventory enablement returns 422. | P1 |
| T03 | FR-03 — Field policies and forms | Missing optional field succeeds; missing workflow prerequisite produces named error; ownership/amount invariants cannot be relaxed by config. | P1 |
| T04 | FR-04 — Custom fields | Invalid enum/type rejected; removing a definition preserves prior values and historical schema; sensitive values excluded from unauthorized views. | P1 |
| T05 | FR-05 — Source inventory and originals | A PDF named .csv is identified for review; duplicate bytes reference the existing blob within the org without suppressing distinct source occurrences. | P2 |
| T06 | FR-06 — CSV/XLSX extraction | Leading-zero ID survives; formulas/external links never execute; unsupported/encrypted files fail clearly; oversized workbook rejected before unbounded expansion. | P2 |
| T07 | FR-07 — Mapping candidates | Ambiguous Amount or Date is not auto-applied; a uniquely validated template mapping may be applied only under an explicit org rule. | P2 |
| T08 | FR-08 — Reusable mapping profiles | Reordered known headers work; changed meaning/type flags review; no profile from another tenant is discoverable or reusable. | P2 |
| T09 | FR-09 — Loss-aware normalization | Ambiguous date rejected pending format choice; tax/discount blanks stay unknown; unmapped column count equals source count minus mapped/explicitly excluded columns. | P2 |
| T10 | FR-10 — Preview/review/confirm | Bad row blocks default batch commit; stale preview returns 409; failed commit leaves no partial records; business totals exclude staged rows. | P2 |
| T11 | FR-11 — Batch/folder recovery | One failed file is visible without hiding others; no dependent invoice confirms before its valid customer; retry adds no duplicate transactions. | P2 |
| T12 | FR-12 — Business identity and duplicates | Same ID/different amount conflicts; same amount/different IDs remain separate; identical invoice ID in another tenant cannot link. | P1 |
| T13 | FR-13 — Independent entities | Unallocated expense persists with private finance visibility and no customer profit attribution; staging unknown customer does not create a customer. | P1 |
| T14 | FR-14 — Invoice amounts and lines | Two lines group once; header/line discounts are not doubled; known gross with unknown tax cannot become verified net revenue. | P3 |
| T15 | FR-15 — Credits and refunds | Invoice net 100, revenue credit 20, subsequent cash refund 20 results in net billed revenue 80, not 60; no fake new cash movement during migration. | P3 |
| T16 | FR-16 — Payments and allocations | Payment 150 applied 100+50 leaves second invoice of 80 outstanding 30; concurrent over-allocation blocked; unallocated remainder visible. | P3 |
| T17 | FR-17 — Shared cost allocation | Expense 1000 allocated 600+300 leaves 100 residual; 101 additional fails; project-to-customer rollup contributes 900 once. | P3 |
| T18 | FR-18 — Contract versions and review | Retrospective amendment changes a new recomputation but not a historical snapshot; ambiguous same-scope overlap blocks price verification. | P3 |
| T19 | FR-19 — Relationship matching | Same name/amount cannot create a link; exact reference with wrong currency is rejected; two eligible candidates require review. | P3 |
| T20 | FR-20 — Relationship audit and reversal | Rejected candidate remains inspectable; reversed allocation restores balances once; future reports exclude superseded link. | P3 |
| T21 | FR-21 — Financial availability and aggregation | Zero stays numeric; no costs means unavailable contribution; partial costs mean clearly provisional result; disabled compliance is not applicable. | P4 |
| T22 | FR-22 — Cost coverage review | Expense or allocation/config change makes review stale; a review cannot convert unknown values to zero. | P4 |
| T23 | FR-23 — Explainable discrepancies | No contract yields no invented price; no baseline yields unavailable change; nonapplicable pricing cannot appear as compliant. | P4 |
| T24 | FR-24 — Source inspection | Reviewer opens both original and normalized value; revoked user receives no source bytes; missing stored file is explicit error. | P2 |
| T25 | FR-25 — Permission-first retrieval | Hidden customer/tenant sentinel never appears in candidates, prompt, counts, citation or cached answer; revoked access invalidates pending result. | P4 |
| T26 | FR-26 — Question-specific evidence | Known revenue can be explained without a contract; contract compliance still abstains without reviewed applicable terms. | P4 |
| T27 | FR-27 — Structured AI verification | Wrong number/source rejected; quote-only relevance failure remains a review limitation; injected document instruction cannot invoke a write or broaden scope. | P4 |
| T28 | FR-28 — Evidence staleness and audit | Changed terms or allocation produce new hash; old snapshot remains labeled with its basis and current permissions. | P4 |
| T29 | FR-29 — Non-AI failure path | Timeout/schema failure returns bounded safe error; deterministic reports still succeed; keys/provider response bodies never exposed. | P4 |
| T30 | FR-30 — Scoped complete reports | 201-row overview reports cap or server count; >calculation limit returns explicit limitation; next page cannot alter an alleged full-workspace total. | P4 |
| T31 | FR-31 — Migration compatibility | Fresh install and copied-fixture upgrade produce identical legacy goldens; new data remains readable if a module is disabled; rollback rehearsal preserves originals. | P1 |
| T32 | FR-32 — Reproducible evaluation | Separate workspaces never merge unrelated sources; baseline and candidate use same authorized corpus; all failures and exclusions reported. | P5 |
| T33 | FR-33 — Module administration and record access | Unallocated/vendor data hidden from analyst; shared document requiring two customers is denied if only one grant exists, unless reviewed redaction is separately stored. | P1 |
| T34 | FR-34 — API error and concurrency contract | Two reviewers cannot both approve an outdated preview; errors contain no database details or secret values. | P2 |
| T35 | FR-35 — Safe correction lifecycle | Same source ID/revised amount enters conflict review; accepted correction invalidates derived snapshots while retaining original evidence. | P3 |
| T36 | FR-36 — Deferred integration boundaries | Capability endpoint returns unsupported instead of accepting arbitrary format; no external fetch or AI upload occurs merely from document text. | P6 |
| T37 | NFR-01 — Tenant and privilege integrity | Cross-tenant negative suite has zero unauthorized records/bytes/side effects; direct cross-tenant relation insert fails. | P1 |
| T38 | NFR-02 — Transport, sessions and secrets | Browser bundle/log scan finds no keys; session/logout/origin tests pass; production cookie flags checked. | P5 |
| T39 | NFR-03 — Privacy and retention | Provider mock receives only permitted minimal fields; deletion is blocked or redacted under defined retention; audit explains outcome. | P1 |
| T40 | NFR-04 — Upload and parser containment | Traversal, zip-bomb, malformed PDF, oversized request and spreadsheet formula fixtures fail without unbounded resources or data writes. | P2 |
| T41 | NFR-05 — Reliability and idempotency | Forced commit/file failure and concurrent retry leave no duplicate financial events; recovery finds orphan/missing blobs. | P2 |
| T42 | NFR-06 — Deterministic integrity | Golden cases match exactly at supported scale; splitting allocations conserves amount; reordering input changes no totals. | P3 |
| T43 | NFR-07 — Performance budget | Proposed targets: p95 ordinary list/report <2 s; 2,000-row CSV preview <10 s; provider timeout <=60 s. Record actual values and failures; no silent truncation. | P5 |
| T44 | NFR-08 — Accessibility | Keyboard-only import and source inspection complete; automated serious/critical findings zero, plus manual focus/contrast/reduced-motion checks. | P4 |
| T45 | NFR-09 — Maintainability and contracts | Unknown config keys fail; adapter contract test proves same normalized semantics; pinned version and upgrade notes exist. | P1 |
| T46 | NFR-10 — Operational recovery | Restore fixture DB/files to isolated target; verify hashes, sources and login. Proposed local-demo recovery target <=1 hour measured in rehearsal. | P5 |
| T47 | NFR-11 — Observability | A failed import can be traced across stages; log/metric access tenant-safe; provider costs tracked without raw prompts. | P5 |
| T48 | NFR-12 — No unsupported financial claims | Incomplete-cost example never appears as confirmed profit; an anomaly is not presented as proven fraud or guaranteed savings. | P4 |

## 5. Layered execution plan

**Unit:** money parsing/rounding, dates/currency scale, conditional requirement predicates, field mapping features, duplicate header ordinals, amount-basis transforms, allocation residuals, effective-version selection, report quality axes, canonical hashing, evidence validators. Golden expected numbers must be calculated independently of production helpers.

**Integration/database:** migration fresh/upgrade/rollback, composite tenant FKs, null optional links, namespaced identities, constraints, source-file recovery, immutable profile/contract versions, concurrent allocation and import confirmation, audit rollback, stale reviews after edits. Include failure at each write/commit/finalization boundary.

**API:** all proposed endpoints tested for valid/invalid input, unsupported module, 401/403/404/409/413/422/429/503, decimal string serialization, date formats, paging/cursor scoping, expected revisions, source download and idempotency. Test unauthenticated and revoked access at both beginning and completion of long operations.

**RBAC and tenant isolation:** at least three organizations with colliding source IDs; admin/finance/assigned analyst/unassigned analyst/outsider. Probe source files, raw rows, suggestions, errors, counts, exports, evidence, chat catalogue and saved results. Two customers sharing a source/cost pool must not leak through an authorized allocation slice.

**Imports and relationships:** duplicate bytes under different names; same transaction in different exports; same ID with conflicting values; missing optional/conditional fields; unknown extra fields; header synonyms and misleading synonyms; partial/multiple payments; overpayment/unallocated amounts; discounts at header and line level; credits/refunds; revised and overlapping contracts; missing currencies/dates; incomplete shared-cost allocation.

**Regression:** keep original strict templates and all existing fixture values. Fresh migration must not invent contracts, invoice lines, issue dates or payment/refund records. Compare original source hashes, scoped row counts and financial results before/after migration. Run existing backend suite and relevant Playwright workspace/finance/analysis/chat flows on isolated stores.

**Performance:** declared 4-core/8-GB local baseline, 2,000 records, 100 PDF pages, 5 concurrent users, separate cold/warm runs. Measure p50/p95/max and peak memory for preview, confirm, report and search; record SQL counts/lock wait. Proposed budgets: p95 list/report <2 s, CSV preview <10 s, provider timeout <=60 s. Run at least 30 measured requests per operation after 5 warmups; do not publish these targets as achieved. Load above limits must fail explicitly, not return partial totals.

**End-to-end:** admin configures contract-free org; finance maps unfamiliar CSV/XLSX, reviews unknowns, confirms, repeats safely; imports linked contract-org case; resolves an ambiguous relationship; applies partial payment and shared cost; analyst investigates and opens evidence; revoke permission during response; change config and prove stale preview; restore backup and repeat one read-only report.

**Accessibility:** keyboard-only mapping/edit/review/confirm/source navigation; focus restoration after modal, error announcements, readable non-color states, reduced motion; axe plus manual contrast and assistive-technology review. Automated tools alone cannot establish WCAG conformance.

## 6. Benchmark design and ground truth

All following sample sizes and thresholds are **proposed**, not completed experiments.

### Mapping and extraction
- 12 labelled export layouts across three organization profiles: contract-free services, recurring-contract services and project-cost services. At least 600 labelled source-column decisions, including unknown and deliberately ambiguous fields.
- Split by layout/source system: 8 development, 4 held-out; no template from a held-out export in the development registry.
- Baseline A: exact canonical header match. Candidate B: normalized header + declared type/sample validation + org profile. Report per-field precision/recall, exact full-record mapping rate, ambiguity abstention and auto-apply coverage.
- Mapping accuracy = correct labelled decisions / all labelled decisions; report separately for material amount/party/date fields. Count incorrect automatic mappings separately; high overall accuracy must not conceal unsafe money mapping.
- Extraction subset: 100 manually labelled rows/cells across CSV/XLSX plus 20 selectable PDF pages where permitted. Score exact amount/date/ID and evidence-locator accuracy. Preserve expected unknowns rather than forcing every field to have a value.

### Relationship matching
- Freeze 300 labelled candidate pairs: 100 true links, 100 plausible hard negatives, 100 ambiguous/insufficient-evidence examples; include reused invoice numbers, identical names, currencies and amendments.
- Exact-ID-only baseline vs validated deterministic candidates. Similarity is review-only initially. Measure accepted-link precision TP/(TP+FP), recall TP/(TP+FN), candidate recall@k, review rate and abstention by ambiguity class.
- Human acceptance is a separate evaluated action, not part of algorithm accuracy. Reviewer labels require independent second review on all material disagreements.
- Release gate for automated material links: zero wrong auto-links in the safety fixture and report confidence interval; proposed >=99% precision target for a larger pilot. A small all-correct sample cannot prove universal 99% reliability. Keep automation off if evidence is inadequate.

### Finance and discrepancies
- At least 50 independent golden cases: unknown/zero/negative net, 0/2/3-decimal currencies, tax inclusive/exclusive/unknown, discount distribution, credit/refund once, source duplicate vs new identity, partial/multiple payments, shared residual, period changes and contract amendments.
- Decimal goldens must match exactly at specified scale; rounding residual distribution must conserve totals. Reject or flag unsupported cases.
- At least 60 labelled customer-period rule cases: 30 true discrepancies, 20 clean cases, 10 insufficient-evidence cases. Compute anomaly precision/recall only on applicable labelled cases; report abstention separately. A quality warning is not a detected pricing anomaly.
- Compare explicit rules against a simple change-threshold baseline on identical records; no anomaly thresholds tuned on held-out labels.

### Retrieval and explanations
- Retain current frozen 30-question benchmark for regression; add 60 new independently authored questions spanning factual/period/contract/ambiguous/unanswerable/adversarial prompts.
- Compare BM25 baseline and context-filtered BM25 on identical authorized corpora. Optional neural retrieval only after documented lexical failure analysis; quantization only on an actual chosen model with fixed hardware/weights.
- Report recall@3, MRR, returned precision, correct abstention, source coverage and elapsed time. Both variants enforce permissions.
- Explanation review: every numeric claim exact; source IDs valid; judge question relevance and support independently. Unsupported-claim rate = unsupported checkable claims / all checkable claims; show unanswered cases and denominators. Exact quote match alone is not entailment.
- No external AI call on private/sensitive datasets merely to fill a benchmark. Mock provider reliability/security tests; obtain separate consent for live non-sensitive evaluation.

### Import reliability and user value
- Ten repeat imports per fixture plus concurrent retries and injected failures; measure duplicate inserts, partial commits and failed-job recovery, not just HTTP 200 rate.
- If pilot access is approved, use 6–10 participants in counterbalanced tasks against spreadsheet/source folders; measure correct completion, source inspection, elapsed time and usability feedback. Until then, time saved and business benefit remain hypotheses.

## 7. Dataset controls

Real component data stays in isolated workspaces with publisher/licence/date/hash and no invented cross-dataset relationships. Proposed Portland/UCI samples are not yet downloaded. Existing FHDC expenses remain a missing-data demonstration. Use first-party linked synthetic records for complete ground truth, visibly marked. Deterministic sample selection must retain child records required for totals; excluded credits/unknowns are reported and reconciled to source totals.

See [dataset report](../research/real-world-data-formats-and-datasets.md) for acquisition limits and [canonical model](../architecture/canonical-data-model.md) for normalization semantics. A public procurement payment is not both supplier revenue and supplier delivery cost.

## 8. Completion and reporting gates

Per phase: execute its P0 acceptance scenarios plus affected legacy regression tests, report all failures/skips, and attach traceability evidence. No deployment if a cross-tenant data leak, unexplained monetary difference, invented relationship, lost raw field or partial financial commit remains.

Final report must distinguish implemented, tested, partially tested, deferred and unknown. Publish methodology, corpus/version/splits, baseline results and failure examples; do not fabricate missing metrics. Maintain a separate issue for every approved limitation, with next experiment or mitigation. Review is required before implementing this plan.

## 9. Research artifact QA

Checked all nine requested files exist, relative document links resolve, code fences balance and text contains no replacement characters. Verified 48 unique requirement IDs each have a traceability row and one of 48 unique target acceptance cases. Five Mermaid diagrams were structurally reviewed (current architecture, proposed architecture, data flow, sequence and ER); they were not browser-rendered in this phase. No existing tracked application files were changed. External-source access limitations are recorded rather than presented as successful downloads. These checks validate the document pack, not the proposed system.
