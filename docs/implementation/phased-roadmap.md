# ProfitLens — 12-week minor-project roadmap and completion plan

> **Implementation follow-up — 15 October 2026:** the team authorized core fixes after this planning snapshot. Evidence-specific investigations and date precision are now fixed. [Current implementation and acceptance results](../MINOR_SCOPE_RELEASE_REPORT.md) supersede pending test/prerequisite statuses below; optional and deferred scope is unchanged.

15 October 2026 · active scope v0.2. The user has narrowed the project to its original COM-711 goal. This plan replaces the expanded P0–P6 platform programme. **This update changes documentation, not application behaviour.**

## 1. Original target

A secure customer-profitability investigation prototype: import customer/invoice/attributed-expense data and readable contracts, calculate contribution/margin, flag three discrepancies, retrieve authorized evidence and explain it with checked AI output. Deliver a repeatable faculty demonstration and honest evaluation.

## 2. Week mapping

Week numbers describe the intended academic sequence; actual code/test evidence determines completion. Earlier Plane task ordering and the revised development ordering differ. Do not rebuild completed functionality to match an old task title.

| Week | Focused deliverable | Current evidence / remaining work |
|---|---|---|
| 1 | Setup, supported CSV/PDF preview and input contracts | Implemented; preserve source/validation checks |
| 2 | PostgreSQL, migrations, API, authentication and organization access | Implemented; maintain isolated regression tests |
| 3 | Customer/invoice/expense UI, preview-confirm import and private contracts | Implemented; verify demo controls and provenance |
| 4 | Revenue, recorded costs and data-quality warnings | Implemented; retain missing-versus-zero and period checks |
| 5 | Contribution, margin, cost review and three discrepancy rules | Implemented bounded logic; demonstrate accurate outputs and limits |
| 6 | Page-based document retrieval and source references | BM25 implemented; no semantic-search claim |
| 7 | Customer/period-aware evidence and permission-equivalent baseline | Implemented; retain access and context tests |
| 8 | Pretrained AI provider and structured explanations | Provider/code paths exist; live answer quality needs evaluation |
| 9 | Numeric/source verification, insufficient evidence and UI integration | Implemented guards; review question-specific prerequisite/failure issues |
| 10 | Freeze synthetic fixtures and real component provenance | Existing 20-customer/six-month/30-question corpus; real data stays separate |
| 11 | Calculation, anomaly, retrieval, access and answer-quality evaluation | Existing benchmark; rerun relevant checks and document actual failures |
| 12 | Regression, local demo, report, slides and viva preparation | Complete final verified demonstration and status documentation; hosting optional |

Quantization is not mandatory. There is no pretrained retrieval model to quantize today. If the college asks, explain that the measured baseline is lexical BM25; neural retrieval/efficiency is future work unless separately completed and evaluated.

## 3. Remaining work in priority order

| Step | Action | Evidence of completion |
|---|---|---|
| A — verify core | Run existing finance/import/access regressions on isolated fixtures; walk through dashboard and sources | Actual commands/results; issues listed, no claims based solely on screenshots |
| B — fix specific gaps | Resolve incorrect/overbroad evidence prerequisites, confusing incomplete-data states or failed core controls if reproduced | Focused regression plus successful affected user flow; no model/schema rewrite |
| C — evaluate | Freeze questions/labels; compare BM25 and context-aware BM25; assess a small set of model answers and failures | Reproducible results, denominators, unsupported/unanswerable cases and limits |
| D — prepare faculty demo | Valid/invalid/repeated import; contribution; three rules; source drill-down; restricted account; AI failure/uncertainty | Demonstration checklist, known expected numbers, updated report/slides/viva notes |
| E — optional convenience | At most two reviewed CSV alias layouts OR XLSX on the same schemas, only if A–D are on track | Explicit scope decision; original values/unknowns preserved; validation unchanged |

The schedule does not restart twelve weeks or promise new calendar dates. Existing work is reused. Stop optional work when it threatens core correctness, testing or presentation readiness.

## 4. Explicitly deferred

General organization modules/settings engine; arbitrary custom fields/forms/roles; payment/bank reconciliation; vendor/AP accounting; shared-cost allocations; projects/timesheets/payroll/inventory/POs; contract amendment automation; FX/tax engines; OCR; cloud connectors; microservices; industry-specific applications. Their research is archived, not deleted, and is not part of the grading deliverable.

## 5. Ready-for-review definition

The team can explain the problem, demonstrate the complete supported journey, show exact arithmetic and evidence, prove the basic permission boundary, reproduce evaluation and state limitations. No unsupported links, invented data or hidden calculation failure. Public deployment, customer adoption, business savings and general-company compatibility are not claimed without evidence.

See [SRS](../requirements/SRS.md), [testing](../testing/test-strategy.md) and [gap analysis](../architecture/gap-analysis.md). Implement only separately requested core work; this documentation revision does not authorize the archived platform build.
