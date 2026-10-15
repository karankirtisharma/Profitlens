# ProfitLens — minor-project requirement traceability

> **Implementation follow-up — 15 October 2026:** the team authorized core fixes after this planning snapshot. Evidence-specific investigations and date precision are now fixed. [Current implementation and acceptance results](../MINOR_SCOPE_RELEASE_REPORT.md) supersede pending test/prerequisite statuses below; optional and deferred scope is unchanged.

15 October 2026 · active scope v0.2. The [SRS](SRS.md) contains 12 functional and six quality requirements. The [test strategy](../testing/test-strategy.md) defines 18 corresponding acceptance cases. All case execution statuses below remain **pending final acceptance**; current implementation observations are not new test passes.

Backend paths below are relative to apps/api/profitlens unless otherwise stated; frontend paths are within apps/web. Test files are under tests. Entries identify the components to inspect, not promises of a new service layer.

| Requirement | Existing component / evidence | Current status | Acceptance case |
|---|---|---|---|
| MP-F01 — Authenticated workspaces | security.py; main.py; test_workspace.py | Implemented; regression verification needed | MP-T01 |
| MP-F02 — Customer and financial records | records.py; ingestion/models.py; database.py | Implemented bounded schema | MP-T02 |
| MP-F03 — Validated CSV imports | imports.py; ingestion/csv_import.py; test_ingestion.py; test_workspace.py | Implemented strict templates; flexible mapping optional | MP-T03 |
| MP-F04 — Private contract evidence | main.py; ingestion/pdf_contract.py; schemas.Terms | Implemented monthly-only workflow | MP-T04 |
| MP-F05 — Revenue and recorded costs | finance.py; test_finance.py | Implemented | MP-T05 |
| MP-F06 — Contribution and margin | profitability.metrics/attest; test_analysis.py | Implemented; strengthen explanation of limitations | MP-T06 |
| MP-F07 — Three explainable rules | profitability.findings; test_analysis.py; evaluation.py | Implemented bounded rules | MP-T07 |
| MP-F08 — Authorized contextual retrieval | retrieval.py; test_retrieval_evaluation.py | Implemented; no embeddings or pgvector | MP-T08 |
| MP-F09 — Evidence-grounded explanations | explanations.py; chat.py; assistant.py; analysis_api.py | Implemented in part; broad investigation prerequisites need focused review | MP-T09 |
| MP-F10 — Complete demonstration workflow | app/page.tsx; finance-panel.tsx; analysis-panel.tsx; chatbot-launcher.tsx | Existing UI; final acceptance rerun needed | MP-T10 |
| MP-F11 — Reproducible evaluation | evaluation.py; scripts/datasets; docs/evaluation-results-2026-10-15.json | Existing benchmark; relevance evaluation incomplete | MP-T11 |
| MP-F12 — Traceable changes and results | records.log_event; profitability.fingerprint; analysis_api.py | Implemented bounded history; regression needed | MP-T12 |
| MP-N01 — Exact arithmetic and meaning | finance.py; ingestion/models.py; test_finance.py | Implemented within declared scope | MP-T13 |
| MP-N02 — Data and provider security | security.py; analysis_api.py; explanations.py; provider/security tests | Existing safeguards; not a production-security certification | MP-T14 |
| MP-N03 — Bounded and recoverable operations | main.py; imports.py; finance.py; test_provider.py | Implemented limits; final failure-flow verification needed | MP-T15 |
| MP-N04 — Compatibility and maintainability | database.py; migrations; existing test suite | Delivery constraint | MP-T16 |
| MP-N05 — Readable accessible interface | apps/web/components; apps/web/tests | Existing UI; final checks pending | MP-T17 |
| MP-N06 — Repeatable local delivery | dev.cmd; docs/DEVELOPMENT.md; docs/DEMO.md | Local tooling exists; public hosting not required | MP-T18 |

## Acceptance criteria

The SRS row supplies the observable criterion; its matching test row supplies inputs, method and expected evidence. Final results must record actual command or manual steps, snapshot/fixture version and outcome. The 43-test historical selection covers only a subset and must not be attributed to all 18 cases.

## Scope transition

The expanded v0.1 FR/NFR requirements are archived rather than partially relabelled as completed.

| Earlier theme | Current disposition |
|---|---|
| Deterministic calculations, incomplete data and source evidence | Retained in MP-F05–F09, F12 and MP-N01 |
| Authentication, tenant/customer permissions and provider boundary | Retained in MP-F01, F08–F09 and MP-N02 |
| Imports, idempotence, validation and provenance | Bounded supported-schema core in MP-F02–F04 and F12 |
| General schema inference, import templates and locale configurator | Optional two-layout reviewed mapping only; full platform deferred |
| Payments, credits, many-to-many settlement and shared allocations | Future accounting expansion; not minor-project requirements |
| Organization module/custom-field/form/role engines and industry presets | Future platform research |
| OCR, external connectors, queues and deployment expansion | Future extensions; repeatable local demonstration retained |
| Evaluation, regression and documentation | Retained as bounded MP-F10–F11 and MP-N03–N06 |

The [archived traceability](../research/archive/expanded-design-2026-10-15/requirements/requirements-traceability.md) documents the broader proposal. It does not authorize implementation or increase the minor-project definition of done.

## Ownership and sign-off

The team assigns work using the existing college process; no names or responsibilities are invented here. Check core readiness against the [roadmap](../implementation/phased-roadmap.md), document any failed or unexecuted case, and keep public progress claims aligned with actual results.
