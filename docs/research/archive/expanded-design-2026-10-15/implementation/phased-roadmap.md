> **Archived expanded proposal — superseded for COM-711.** This is future research, not the current implementation backlog. Use the [active minor-project SRS](../../../../requirements/SRS.md). Historical claims below retain their original audit context.

# ProfitLens dependency-aware implementation roadmap

15 October 2026 · **proposed, not authorized for implementation until research review**. Phases below are dependency order, not promised calendar dates. Current team capacity and remaining college deadline have not been verified. No Plane tasks, application code or deployment were changed by this research.

## 1. Reconcile the historical Week 1–12 plan

The original college list placed persistence in Week 5 and fixtures late in Week 10. The project's revised plan correctly moved database/auth/UI earlier. Later user direction moved profitability to Week 5, retrieval to Weeks 6–7 and explanations to Weeks 8–9. Use current code and test evidence rather than treating either old schedule as a completion certificate.

| Original week/topic | Actual evidence at baseline | Remaining work / mapped phase |
|---|---|---|
| 1 setup / ingestion | Strict CSV and text PDF preview; fixtures/tests | Preserve; mapping and XLSX P2 |
| 2 revenue/cost foundation | Database/auth implemented in revised Week 2; arithmetic now in finance.py | Versioned semantics and compatibility P1/P3 |
| 3 contribution/margin | Revised Week 3 delivered records/imports; contribution now in profitability.py | Incomplete coverage and allocation extension P3/P4 |
| 4 quality/discrepancy | Revenue/cost warnings plus subsequent pricing/cost/margin rules exist | Workflow-specific rules and negative cases P3/P4 |
| 5 database/retrieval in college list; profitability in later request | PostgreSQL and financial engine exist | No reimplementation; flexible canonical foundation P1 |
| 6 permissions/evidence | Org/customer scoping and BM25 present | New entity/shared document policies P1/P4 |
| 7 generative integration | Provider adapter and chat/investigation paths present | Configurable outbound policy and evidence prerequisites P4 |
| 8 verification | Exact numeric/source checks and reauthorization exist | Semantic answer evaluation and shared envelope P4/P5 |
| 9 quantization | No neural model or vector index | Deferred, only after a neural retrieval benchmark demonstrates value |
| 10 synthetic labels | Frozen 20-customer/30-question corpus plus separate public-data demo | Heterogeneous schemas/link labels/real components P5 |
| 11 evaluation | Unit/API/security tests and saved lexical baseline exist | Re-run relevant integration suites; broaden evaluation P5 |
| 12 integration/demo/deployment | Local tooling/docs, deployment preparation | Fresh restore/container/public readiness validation P5; no production-complete claim |

The 10 October viva PDF and September synopsis are historical. After approved implementation, refresh their status and the public roadmap; do not silently replace submitted materials in this planning phase.

## 2. Prioritized phases and review gates

| Phase | Objective and deliverables | Dependencies | Value / complexity / risk | Acceptance gate |
|---|---|---|---|---|
| P0: research review | Agree SRS, first B2B-service workflow, cost boundary and evidence labels; approve scope | This document pack | Highest clarity; low coding cost; unresolved semantics are high risk | Owner reviews config/money/link rules; no unsupported capabilities promised |
| P1: compatible foundation | Versioned profile, field/capability registry, source identity crosswalk, vendor/unallocated visibility design, additive schema and legacy adapter | P0 | High correctness value; medium complexity; high migration/access risk | FR-01–04/12–13/31/33 + NFR-01/03/09 relevant tests; old goldens/permissions unchanged |
| P2: staged imports | Immutable originals, source rows, CSV/XLSX adapters, mapping candidates/review/templates, unknown columns, batch retry, schema-driven UI | P1 | High everyday value; medium/high complexity; loss/security risks | FR-05–11/24/34 + NFR-04/05; realistic exports round-trip with no discarded fields; stale preview blocked |
| P3: typed finance and relationships | Lines/tax/adjustments, credits/refunds, same-currency payment allocation, shared costs, contract versions and link review | P1; P2 for imports | High finance value; high complexity; highest double-counting risk | FR-14–20/35 + NFR-06; golden amounts, conservation, rollback, conflicting matches all pass |
| P4: report/evidence integration | Question-specific prerequisites, expanded completeness, stale snapshots, common evidence envelope, scoped UI/reporting and chat | P2/P3 | High demonstration value; medium complexity; misstatement/privacy risk | FR-21–30 + NFR-08/12; no contract needed for valid revenue question; no false verified compliance |
| P5: core validation and release preparation | Real component datasets, frozen linked synthetic benchmark, baseline/human evaluation, regression/security/restore/performance, deployment runbook | P1–P4 | Required quality evidence; medium effort; external validity/operational risk | FR-32 + NFR-02/07/10/11; published actual results and failures; deployment gate separately checked |
| P6: optional extensions | One justified integration or neural retrieval experiment, then a second preset using shared core | Core release gates, validated user demand | Conditional value; potentially high complexity | FR-36; adapter-specific data/security tests; no industry fork |

P1 may add vendor identity but must not imply full vendor-bill/AP functionality. P3 payment reconciliation is a bounded optional module; if schedule is tight, complete config/imports/meaning/permissions first and explicitly defer payment release. Do not weaken its required tests to fit a deadline.

## 3. Small testable milestones

1. **P1a**: profile validation and immutable version activation on copied legacy fixtures. No UI cutover until migration comparison passes.
2. **P1b**: field registry and unallocated-record scope tests. Validate admin/finance/analyst defaults before new rows can be exposed.
3. **P2a**: immutable file + loss-aware CSV preview. Legacy endpoint remains untouched.
4. **P2b**: mapping review and saved templates with stale-preview conflicts. Add XLSX only after raw/provenance contract is stable.
5. **P3a**: invoice basis/lines and explicit credit semantics. Confirm amounts independently; no payments yet.
6. **P3b**: payment and cost allocations with conserved balances, concurrent-write tests and reversal history.
7. **P3c**: contract versions and reviewed links. Keep unsupported billing/proration unavailable.
8. **P4a**: report coverage and exact source drill-down, then **P4b** shared AI evidence. Do not let a model paper over missing data.
9. **P5a**: frozen evaluation against baselines, then **P5b** restore/deploy rehearsal and revised demo documents.

Each milestone ends with tests, a short change/limitation report and a reversible release boundary. Do not call a milestone complete based on code presence alone. Unit tests may run continuously; database suites only on explicitly isolated test databases.

## 4. Architecture decisions to preserve

- Retain FastAPI/Next.js/PostgreSQL, SQLAlchemy Core and Alembic; avoid rewriting into an ERP framework.
- Retain Decimal checks, scoped FKs/queries, origin/session protections, import idempotency and private PDFs.
- Retain lexical baseline and strict AI verification; semantic retrieval is an optional measured enhancement.
- Keep real component datasets and synthetic linked benchmark in separate namespaces/workspaces, with original IDs and licence evidence.
- Prefer supported same-currency calculations and documented unavailable states over incomplete FX/tax automation.

## 5. Stop conditions and approval questions

Do not cut over if legacy values change without an approved semantic explanation, an analyst can access unallocated/shared data, unknown fields disappear, or a similarity match creates an authoritative link. Do not host publicly without recovery and upload-security evidence. Freeze advanced integration work if the first service-business workflow is not usable.

Review needed before implementation: confirm first source-export convention and reporting cost boundary; confirm whether payments ship in the first core increment; provide permission-safe pilot data or approve component-only evaluation. Until then, defaults in the SRS remain proposals, not configuration changes.
