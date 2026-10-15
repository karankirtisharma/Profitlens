> **Archived expanded proposal — superseded for COM-711.** This is future research, not the current implementation backlog. Use the [active minor-project SRS](../../../../requirements/SRS.md). Historical claims below retain their original audit context.

# Requirements traceability and review register

15 October 2026 · SRS v0.1 · **implementation plan, not a test pass register**.

Read the [SRS](SRS.md) for exact SHALL behaviour and acceptance criteria. The [test strategy](../testing/test-strategy.md) defines each T-case and its evidence requirements. [P0–P6](../implementation/phased-roadmap.md) are proposed dependency phases, not new calendar weeks.

## Traceability matrix

Paths below are under apps/api/profitlens unless a frontend/config path is named. “New/proposed” names designate future components; their appearance here does not imply files exist. Existing modules are extension/preservation targets. No proposed test file or function has been added in this phase.

| Requirement | Existing evidence / current coverage | Implementation target | Phase | Acceptance test |
|---|---|---|---|---|
| [FR-01](SRS.md) Versioned organization profiles | Absent | database.py; security.admin | P1 | [T01](../testing/test-strategy.md) |
| [FR-02](SRS.md) Optional modules | Absent | new profile service; lib/workspace.ts | P1 | [T02](../testing/test-strategy.md) |
| [FR-03](SRS.md) Field policies and forms | Absent | schemas.py; ingestion/models.py; lib/workspace.ts | P1 | [T03](../testing/test-strategy.md) |
| [FR-04](SRS.md) Custom fields | Absent | new custom field registry | P1 | [T04](../testing/test-strategy.md) |
| [FR-05](SRS.md) Source inventory and originals | Partial | main.upload_contract; imports.preview | P2 | [T05](../testing/test-strategy.md) |
| [FR-06](SRS.md) CSV/XLSX extraction | CSV only | ingestion/csv_import.py; proposed workbook adapter | P2 | [T06](../testing/test-strategy.md) |
| [FR-07](SRS.md) Mapping candidates | Absent | new mapping service and review UI | P2 | [T07](../testing/test-strategy.md) |
| [FR-08](SRS.md) Reusable mapping profiles | Absent | new mapping service | P2 | [T08](../testing/test-strategy.md) |
| [FR-09](SRS.md) Loss-aware normalization | Absent | imports.py; new source_records | P2 | [T09](../testing/test-strategy.md) |
| [FR-10](SRS.md) Preview/review/confirm | Partial | imports.preview/confirm; security.lock_workspace | P2 | [T10](../testing/test-strategy.md) |
| [FR-11](SRS.md) Batch/folder recovery | Absent | new import manifest orchestration | P2 | [T11](../testing/test-strategy.md) |
| [FR-12](SRS.md) Business identity and duplicates | Partial | records.py; imports.check_rows; database.py | P1 | [T12](../testing/test-strategy.md) |
| [FR-13](SRS.md) Independent entities | Partial | database.record_columns; security.visible | P1 | [T13](../testing/test-strategy.md) |
| [FR-14](SRS.md) Invoice amounts and lines | Legacy only | ingestion.models.Invoice; finance.calculate | P3 | [T14](../testing/test-strategy.md) |
| [FR-15](SRS.md) Credits and refunds | Absent | new credits service; legacy finance adapter | P3 | [T15](../testing/test-strategy.md) |
| [FR-16](SRS.md) Payments and allocations | Absent | new payments/payment_allocations | P3 | [T16](../testing/test-strategy.md) |
| [FR-17](SRS.md) Shared cost allocation | Absent | new cost_allocations; profitability.py | P3 | [T17](../testing/test-strategy.md) |
| [FR-18](SRS.md) Contract versions and review | Monthly review only | main.review_terms; contracts; proposed version tables | P3 | [T18](../testing/test-strategy.md) |
| [FR-19](SRS.md) Relationship matching | Only explicit customer FKs | new matching service; typed relationship tables | P3 | [T19](../testing/test-strategy.md) |
| [FR-20](SRS.md) Relationship audit and reversal | Absent | record_events; proposed relationship_evidence | P3 | [T20](../testing/test-strategy.md) |
| [FR-21](SRS.md) Financial availability and aggregation | Partial | finance.py; profitability.py; finance-panel.tsx | P4 | [T21](../testing/test-strategy.md) |
| [FR-22](SRS.md) Cost coverage review | Expense hash exists | profitability.attest/fingerprint | P4 | [T22](../testing/test-strategy.md) |
| [FR-23](SRS.md) Explainable discrepancies | Bounded rules exist | profitability.findings | P4 | [T23](../testing/test-strategy.md) |
| [FR-24](SRS.md) Source inspection | Partial | records.source; contract_file; proposed provenance service | P2 | [T24](../testing/test-strategy.md) |
| [FR-25](SRS.md) Permission-first retrieval | Customer-level implemented | security.visible; retrieval.search; analysis_api.py | P4 | [T25](../testing/test-strategy.md) |
| [FR-26](SRS.md) Question-specific evidence | Partial; investigation gate too broad | explanations.evidence/explain; chat.evidence | P4 | [T26](../testing/test-strategy.md) |
| [FR-27](SRS.md) Structured AI verification | Partial existing guardrails | explanations.verify; chat.respond; assistant.plan | P4 | [T27](../testing/test-strategy.md) |
| [FR-28](SRS.md) Evidence staleness and audit | Partial | investigations; explanations.pack_hash | P4 | [T28](../testing/test-strategy.md) |
| [FR-29](SRS.md) Non-AI failure path | Implemented bounded path | explanations.structured_completion; analysis_api.py | P4 | [T29](../testing/test-strategy.md) |
| [FR-30](SRS.md) Scoped complete reports | Partial caps exist | main.list_records; finance.report; overview.tsx | P4 | [T30](../testing/test-strategy.md) |
| [FR-31](SRS.md) Migration compatibility | Proposed extension | migrations; database.py; legacy adapter | P1 | [T31](../testing/test-strategy.md) |
| [FR-32](SRS.md) Reproducible evaluation | Existing narrow benchmark | evaluation.py; scripts/datasets; proposed eval manifests | P5 | [T32](../testing/test-strategy.md) |
| [FR-33](SRS.md) Module administration and record access | Partial existing RBAC | security.py; new scope resolver | P1 | [T33](../testing/test-strategy.md) |
| [FR-34](SRS.md) API error and concurrency contract | Partial current errors | main.py; new API models | P2 | [T34](../testing/test-strategy.md) |
| [FR-35](SRS.md) Safe correction lifecycle | Partial manual edit audit | records.write_record; import review | P3 | [T35](../testing/test-strategy.md) |
| [FR-36](SRS.md) Deferred integration boundaries | Not implemented | new capability registry | P6 | [T36](../testing/test-strategy.md) |
| [NFR-01](SRS.md) Tenant and privilege integrity | Partial | security.py; database constraints | P1 | [T37](../testing/test-strategy.md) |
| [NFR-02](SRS.md) Transport, sessions and secrets | Partial local controls | config.py; main.login/guard; deployment | P5 | [T38](../testing/test-strategy.md) |
| [NFR-03](SRS.md) Privacy and retention | Absent per-org policy | profile; source storage; provider adapter | P1 | [T39](../testing/test-strategy.md) |
| [NFR-04](SRS.md) Upload and parser containment | Partial PDF/CSV limits | ingestion; storage service; ingress | P2 | [T40](../testing/test-strategy.md) |
| [NFR-05](SRS.md) Reliability and idempotency | Partial | imports.confirm; storage manifest | P2 | [T41](../testing/test-strategy.md) |
| [NFR-06](SRS.md) Deterministic integrity | Legacy Decimal exists | finance/profitability; new calculation services | P3 | [T42](../testing/test-strategy.md) |
| [NFR-07](SRS.md) Performance budget | Unmeasured targets | API/import/report/query planning | P5 | [T43](../testing/test-strategy.md) |
| [NFR-08](SRS.md) Accessibility | Historical frontend checks only | review UI; existing components | P4 | [T44](../testing/test-strategy.md) |
| [NFR-09](SRS.md) Maintainability and contracts | Partial typed stack | schemas; new registry; CI | P1 | [T45](../testing/test-strategy.md) |
| [NFR-10](SRS.md) Operational recovery | Not freshly verified | deployment and storage tooling | P5 | [T46](../testing/test-strategy.md) |
| [NFR-11](SRS.md) Observability | Partial audit only | record_events; proposed telemetry | P5 | [T47](../testing/test-strategy.md) |
| [NFR-12](SRS.md) No unsupported financial claims | Partial existing warnings | report/evidence/UI contracts | P4 | [T48](../testing/test-strategy.md) |

## Existing-test anchors

| Existing file | Supported baseline area | What it does not establish |
|---|---|---|
| tests/test_ingestion.py | Strict CSV/PDF/record preview | Flexible mapping, XLSX, unknown-column preservation |
| tests/test_finance.py | Decimal arithmetic, missing/zero, duplicate/conflict/period checks | Payments, credits, shared-cost allocations or multiple currency bases |
| tests/test_retrieval_evaluation.py | Chunk IDs/page provenance, frozen synthetic labels, verification negatives | Human answer relevance or real-world retrieval quality |
| tests/test_provider.py | Mocked OpenRouter/NVIDIA protocol/failure handling | Live model compatibility, billing or security of vendor infrastructure |
| tests/test_workspace.py | Existing PostgreSQL/API/session/import/grant cases | Freshly passed in this research phase; new entity visibility |
| tests/test_analysis.py | Existing profitability/evidence API cases | New contract-version and allocation workflows |
| tests/test_chat.py; test_assistant.py; test_workspace_summary.py | Existing scoped chat/planning/summary cases | General reliable reasoning on arbitrary exports |
| apps/web/tests/*.spec.ts | Existing workspace/presentation/finance/analysis/chat journeys | Newly proposed mapping/settings UI or fresh browser validation |

Fresh baseline: 43 unit/fixture/mocked-provider cases and TypeScript passed. Other test files were inspected, not executed in this phase. [Exact commands/results](../testing/test-strategy.md).

## Research-to-design trace

| Research finding or internal gap | Requirements / consequence |
|---|---|
| Existing customer-required expense schema; FHDC technical buckets (G01) | FR-13, FR-17, FR-33: legitimate unallocated records with safe access |
| Fixed invoice equation, two-decimal assumption (G02; M03/M09/M10) | FR-14–16, NFR-06: typed amounts, independent settlement, preserved legacy formula |
| Strict schema/unknown data loss (G03; M06/M13) | FR-05–11: raw staging, mapping review, explicit transform evidence |
| Optional workflows and configuration (G04; M05/M07) | FR-01–04: supported modules/conditional policies rather than industry forks |
| Contract history and applicability (G06; M11/M14) | FR-18–20/23: versioned reviewed evidence and auditable typed links |
| Invoice/receipt and operational allocations (M09/M15/M16) | FR-16/17/19/20: conservation, review and explicit correction history |
| Broad evidence gate and duplicated context (G11–12) | FR-25–29: shared envelope with question-specific prerequisites |
| Missing operational proof (G10/G13; M18) | NFR-02/04/05/10/11: parser/transport/recovery/telemetry gates |
| Narrow synthetic metrics and partial genuine data (G15; D01–05) | FR-32: separate real-component and labelled-linked evaluation |

Source IDs Mxx are defined in [market review](../research/market-and-case-study-review.md); Dxx in [dataset review](../research/real-world-data-formats-and-datasets.md).

## Completion evidence required per requirement

Record requirement ID/version, implementing commit, config/schema version, actual test command, environment, fixture hash, result/count, failures, evidence path and reviewer. Mark implemented only after the acceptance case is demonstrated; mark tested only for executed cases. Any waiver must name the limitation and release impact. No acceptance check is automatically satisfied by having a similarly named endpoint.

A proposed traceability row may become complete only when its tests cover both successful use and relevant failure/permission paths. Requirements covering deferred modules remain deferred; do not inflate the completed Week 1–12 count by including design documents as feature implementation.
