> **Archived expanded proposal — superseded for COM-711.** This is future research, not the current implementation backlog. Use the [active minor-project SRS](../../../../requirements/SRS.md). Historical claims below retain their original audit context.

# ProfitLens Software Requirements Specification

Version 0.1 · 15 October 2026 · **review draft; proposed requirements are not implemented features**.
Code baseline: c4abad70b53d934016bf5cb39076bf80edf7b756. This SRS supersedes proposed flexible-schema behaviour only after project-owner review; it does not change the existing software or submitted college documents.

## Document pack

1. [Market and case-study review](../research/market-and-case-study-review.md)
2. [Real-world formats and datasets](../research/real-world-data-formats-and-datasets.md)
3. [Current implementation and gaps](../architecture/gap-analysis.md)
4. [Canonical data model and ER diagram](../architecture/canonical-data-model.md)
5. This SRS: requirements, actors, API contracts and release gates
6. [Target architecture and sequence diagrams](../architecture/target-architecture.md)
7. [Phased implementation roadmap](../implementation/phased-roadmap.md)
8. [Testing strategy and acceptance matrix](../testing/test-strategy.md)
9. [Requirement-to-code/test traceability](requirements-traceability.md)

## 1. Purpose, scope and stakeholders

ProfitLens is an investigation companion for small B2B service businesses. It shall preserve heterogeneous source data, compute recorded customer-period contribution under explicit rules, and present reviewable exceptions with authorized evidence. It is not a general ledger, tax filing service, payment execution system or legal contract authority.

Stakeholders: project team, finance reviewer, organization administrator, customer-restricted analyst, faculty evaluator and future pilot users. A data provider controls permission to ingest/reuse source material. The model provider is an external processor, not a trusted source of financial facts.

Evidence-backed need: official vendor schemas distinguish invoice lines, receipts, credits and configurable imports; documented cases describe fragmented evidence and allocation/reconciliation work. Sources and qualification appear in the [market review](../research/market-and-case-study-review.md). H1–H4 in that review are unvalidated product hypotheses. No client study or measured business savings is claimed.

## 2. Current baseline and scope boundaries

Implemented bounded prototype: strict CSV records, PostgreSQL persistence, private text contracts, manual monthly terms, session/RBAC/customer grants, Decimal finance and profitability, BM25 evidence, structured investigation and popup chat. See [gap analysis](../architecture/gap-analysis.md). This is newer than the Week 4 and 10 October handbook descriptions.

Next core: organization profiles and field policies; source staging; CSV/XLSX mapping/review; independent unallocated expenses/vendors; optional projects/contracts; invoice lines and explicit credits; payment/cost allocations; workflow-specific reporting/evidence. Implement in phases, not as a simultaneous ERP rewrite.

Deferred: payroll processing, inventory valuation, automated bank execution, statutory revenue recognition, jurisdiction-specific tax calculation, autonomous financial writes, OCR at scale, cloud-drive/accounting connectors, neural retrieval and industry packages. Reserved modules cannot be enabled as working features.

Assumptions: authorized local development access; small datasets; finance reviewer can resolve semantics; source reuse rights established; hosted AI optional. One-currency calculations remain initial policy even when source storage preserves several currencies. Currency conversion requires separate rate-source/effective-date/rounding decisions. No automatic conversion is authorized.

## 3. Actors, permissions and journeys

| Actor | Permitted operations | Explicit restrictions |
|---|---|---|
| Admin | Profile/module/field policy activation, membership grants, finance workflows | Cannot disable tenant integrity, fabricate sources or bypass approval prerequisites |
| Finance | Import/mapping review, business corrections, terms/allocation/cost review | Cannot grant roles or silently activate new org semantic defaults |
| Analyst | Read/ask about assigned customers and authorized evidence | No imports/settings/writes; no unallocated pool or full shared document without sufficient grants |
| Background parser (future) | Process one authorized scoped job | No broad database/model credentials or network fetch from document content |
| AI provider | Return constrained response from minimized permitted evidence | No database writes, dynamic SQL, link confirmation or authority to grant access |

Core journeys:
1. Admin chooses supported modules and semantics, validates profile, previews impact, activates a version.
2. Finance uploads source files, checks inventory, selects sheets/type, reviews mappings and unresolved fields, previews errors, confirms valid batch.
3. Finance inspects probable links/duplicates, accepts only supported associations; records allocations and reasons.
4. Analyst chooses customer/period, sees available totals and missing prerequisites, opens a finding and its row/page.
5. User asks a question; server scopes and builds evidence, calculates facts, optionally calls provider, checks response and reauthorizes before display.
6. Finance corrects a source interpretation; dependent reviews/reports become stale; historical evidence remains accessible within current permission.

## 4. Functional and non-functional requirements

Priority P0 = integrity/security/dependency gate; P1 = core completion; P2 = deferred extension. “Current” is inspection status, not proof that every acceptance criterion has passed. Each row has observable acceptance criteria and a matching test case in [traceability](requirements-traceability.md).

| ID | Requirement / priority | Required behaviour | Acceptance criteria | Current |
|---|---|---|---|---|
| FR-01 | Versioned organization profiles (P0) | Only an administrator shall activate a validated immutable profile revision with an expected-current-version check. | Two concurrent edits yield one activation and one 409; prior records retain their interpretation version. | Absent |
| FR-02 | Optional modules (P0) | The server shall advertise implemented modules and enforce their dependencies; disabled modules shall not be required by unrelated workflows. | Contract-free organization imports valid invoices; compliance displays not applicable; unsupported inventory enablement returns 422. | Absent |
| FR-03 | Field policies and forms (P0) | A shared field registry shall classify every supported field as required, optional, conditional or generated and expose the same policy to forms and imports. | Missing optional field succeeds; missing workflow prerequisite produces named error; ownership/amount invariants cannot be relaxed by config. | Absent |
| FR-04 | Custom fields (P1) | Admins shall define typed, bounded custom fields with sensitivity, allowed values and versioned requirements; unmapped source columns shall remain distinct. | Invalid enum/type rejected; removing a definition preserves prior values and historical schema; sensitive values excluded from unauthorized views. | Absent |
| FR-05 | Source inventory and originals (P0) | Uploads shall retain immutable original bytes, hash, detected type, origin and source occurrence in private staging; names shall not determine actual format. | A PDF named .csv is identified for review; duplicate bytes reference the existing blob within the org without suppressing distinct source occurrences. | Partial |
| FR-06 | CSV/XLSX extraction (P1) | Bounded CSV and selected-sheet XLSX extraction shall preserve raw strings, cell positions and headers including duplicate-header ordinals. | Leading-zero ID survives; formulas/external links never execute; unsupported/encrypted files fail clearly; oversized workbook rejected before unbounded expansion. | CSV only |
| FR-07 | Mapping candidates (P0) | The mapper shall propose targets using header, sampled type/value, source metadata and profile evidence; each candidate shall show confidence band and reason. | Ambiguous Amount or Date is not auto-applied; a uniquely validated template mapping may be applied only under an explicit org rule. | Absent |
| FR-08 | Reusable mapping profiles (P1) | Authorized writers shall save reviewed mapping versions scoped to organization/source signature; activation requiring new semantic defaults shall require admin policy. | Reordered known headers work; changed meaning/type flags review; no profile from another tenant is discoverable or reusable. | Absent |
| FR-09 | Loss-aware normalization (P0) | Each transformed value shall retain original value, target value, transform/version and assumptions; unknown columns shall remain queryable in restricted staging. | Ambiguous date rejected pending format choice; tax/discount blanks stay unknown; unmapped column count equals source count minus mapped/explicitly excluded columns. | Absent |
| FR-10 | Preview/review/confirm (P0) | Confirm shall require the exact reviewed source, mapping, config and candidate hashes, reauthorize and revalidate before one atomic business-data commit. | Bad row blocks default batch commit; stale preview returns 409; failed commit leaves no partial records; business totals exclude staged rows. | Partial |
| FR-11 | Batch/folder recovery (P1) | Multi-file intake shall inventory relative paths, per-file states and dependencies, reject unsafe paths, and allow idempotent retry of failed stages. | One failed file is visible without hiding others; no dependent invoice confirms before its valid customer; retry adds no duplicate transactions. | Absent |
| FR-12 | Business identity and duplicates (P0) | Records shall have tenant-scoped internal identity and namespaced source IDs; exact duplicates, conflicting revisions and similar candidates shall have different outcomes. | Same ID/different amount conflicts; same amount/different IDs remain separate; identical invoice ID in another tenant cannot link. | Partial |
| FR-13 | Independent entities (P0) | Customers, vendors, invoices, expenses and documents shall remain typed entities; absent optional customer/vendor/project relationships shall not require invented records. | Unallocated expense persists with private finance visibility and no customer profit attribution; staging unknown customer does not create a customer. | Partial |
| FR-14 | Invoice amounts and lines (P0) | Adapters shall preserve aggregate-only or line-based invoices and explicit tax/discount basis; derived totals shall use Decimal and reconcile under a versioned rounding policy. | Two lines group once; header/line discounts are not doubled; known gross with unknown tax cannot become verified net revenue. | Legacy only |
| FR-15 | Credits and refunds (P0) | Credit notes, credit allocations and cash refunds shall be distinct; legacy refund semantics shall remain versioned. | Invoice net 100, revenue credit 20, subsequent cash refund 20 results in net billed revenue 80, not 60; no fake new cash movement during migration. | Absent |
| FR-16 | Payments and allocations (P1) | Confirmed same-customer/same-currency allocations shall support one payment across invoices and several payments per invoice. | Payment 150 applied 100+50 leaves second invoice of 80 outstanding 30; concurrent over-allocation blocked; unallocated remainder visible. | Absent |
| FR-17 | Shared cost allocation (P0) | Expense allocations shall retain target, driver/rule version, amount, review evidence and unallocated residual; project rollup shall not double-count. | Expense 1000 allocated 600+300 leaves 100 residual; 101 additional fails; project-to-customer rollup contributes 900 once. | Absent |
| FR-18 | Contract versions and review (P0) | Agreement identity, source files, immutable reviewed versions and service schedules shall be separate; effective and recorded times shall be retained. | Retrospective amendment changes a new recomputation but not a historical snapshot; ambiguous same-scope overlap blocks price verification. | Monthly review only |
| FR-19 | Relationship matching (P0) | Link creation shall validate exact IDs, party, tenant, currency, dates, scope and cardinality; weaker methods shall create reviewed candidates only. | Same name/amount cannot create a link; exact reference with wrong currency is rejected; two eligible candidates require review. | Only explicit customer FKs |
| FR-20 | Relationship audit and reversal (P0) | Each material link shall record method, evidence, policy/version, review state and actor; reversal shall invalidate dependent results without erasing history. | Rejected candidate remains inspectable; reversed allocation restores balances once; future reports exclude superseded link. | Absent |
| FR-21 | Financial availability and aggregation (P0) | Reports shall separate value availability, verification and completeness and aggregate only compatible currency/period/basis records. | Zero stays numeric; no costs means unavailable contribution; partial costs mean clearly provisional result; disabled compliance is not applicable. | Partial |
| FR-22 | Cost coverage review (P0) | Completeness attestation shall bind to source, allocation, configuration and cost-boundary versions and require reviewer explanation. | Expense or allocation/config change makes review stale; a review cannot convert unknown values to zero. | Expense hash exists |
| FR-23 | Explainable discrepancies (P1) | Pricing/cost/margin findings shall expose rule/version, inputs, formula, threshold, evidence and limitations; applicability shall be checked before evaluation. | No contract yields no invented price; no baseline yields unavailable change; nonapplicable pricing cannot appear as compliant. | Bounded rules exist |
| FR-24 | Source inspection (P0) | Every displayed financial assertion and confirmed mapping/link shall resolve to authorized original row/cell/page or manual audit evidence. | Reviewer opens both original and normalized value; revoked user receives no source bytes; missing stored file is explicit error. | Partial |
| FR-25 | Permission-first retrieval (P0) | Search, candidate matching, model context and histories shall be scoped before retrieval and reauthorized before delivery. | Hidden customer/tenant sentinel never appears in candidates, prompt, counts, citation or cached answer; revoked access invalidates pending result. | Customer-level implemented |
| FR-26 | Question-specific evidence (P0) | Evidence builder shall select prerequisites by question/workflow and attach currency/period/quality, not require contracts for every finance question. | Known revenue can be explained without a contract; contract compliance still abstains without reviewed applicable terms. | Partial; investigation gate too broad |
| FR-27 | Structured AI verification (P0) | Hosted answers shall use schema-constrained source IDs and deterministic facts; unsupported claims shall be withheld or marked insufficient; models shall have no financial write tools. | Wrong number/source rejected; quote-only relevance failure remains a review limitation; injected document instruction cannot invoke a write or broaden scope. | Partial existing guardrails |
| FR-28 | Evidence staleness and audit (P0) | Saved reports/investigations shall record source/config/calculation/provider versions and display stale results as historical. | Changed terms or allocation produce new hash; old snapshot remains labeled with its basis and current permissions. | Partial |
| FR-29 | Non-AI failure path (P1) | Finance, imports and source inspection shall remain usable with provider disabled/down; AI failure shall disclose state without inventing an answer. | Timeout/schema failure returns bounded safe error; deterministic reports still succeed; keys/provider response bodies never exposed. | Implemented bounded path |
| FR-30 | Scoped complete reports (P1) | Reports shall disclose coverage and truncation; financial totals shall never silently sum only a display page. | 201-row overview reports cap or server count; >calculation limit returns explicit limitation; next page cannot alter an alleged full-workspace total. | Partial caps exist |
| FR-31 | Migration compatibility (P0) | Additive migrations and explicit adapters shall preserve existing IDs, amounts, sources, permissions and legacy-v1 formula results; no invented dates/lines/credits. | Fresh install and copied-fixture upgrade produce identical legacy goldens; new data remains readable if a module is disabled; rollback rehearsal preserves originals. | Proposed extension |
| FR-32 | Reproducible evaluation (P1) | Dataset manifests shall label genuine/synthetic provenance, licence, hashes, selection and limitations; benchmark questions and relationship labels shall be frozen before tuning. | Separate workspaces never merge unrelated sources; baseline and candidate use same authorized corpus; all failures and exclusions reported. | Existing narrow benchmark |
| FR-33 | Module administration and record access (P0) | Administrative settings shall require admin rights; finance may review/import; analysts read only explicitly granted scope. Shared documents shall use a defined least-privilege policy. | Unallocated/vendor data hidden from analyst; shared document requiring two customers is denied if only one grant exists, unless reviewed redaction is separately stored. | Partial existing RBAC |
| FR-34 | API error and concurrency contract (P1) | New APIs shall expose stable error codes, field/source locations, retryability and request IDs; version conflicts shall not silently overwrite data. | Two reviewers cannot both approve an outdated preview; errors contain no database details or secret values. | Partial current errors |
| FR-35 | Safe correction lifecycle (P0) | Confirmed financial records shall be corrected by audited revisions or reversals; imports shall not silently upsert conflicting confirmed data. | Same source ID/revised amount enters conflict review; accepted correction invalidates derived snapshots while retaining original evidence. | Partial manual edit audit |
| FR-36 | Deferred integration boundaries (P2) | Reserved OCR, XML/JSON, cloud-drive, bank and industry adapters shall remain disabled until each has a schema, authorization, licence/consent and acceptance suite. | Capability endpoint returns unsupported instead of accepting arbitrary format; no external fetch or AI upload occurs merely from document text. | Not implemented |
| NFR-01 | Tenant and privilege integrity (P0) | All data reads/writes, FKs, file paths, caches and background jobs shall use validated organization scope; no client-set organization field shall override it. | Cross-tenant negative suite has zero unauthorized records/bytes/side effects; direct cross-tenant relation insert fails. | Partial |
| NFR-02 | Transport, sessions and secrets (P0) | Production shall require HTTPS/secure cookies, server-only secrets, allowed origin, bounded sessions and redacted logs; deployments with insecure settings shall fail readiness checks. | Browser bundle/log scan finds no keys; session/logout/origin tests pass; production cookie flags checked. | Partial local controls |
| NFR-03 | Privacy and retention (P0) | Profiles shall define retention and outbound AI policy; restricted fields shall be excluded from external contexts; deletion/archive shall account for evidence dependencies. | Provider mock receives only permitted minimal fields; deletion is blocked or redacted under defined retention; audit explains outcome. | Absent per-org policy |
| NFR-04 | Upload and parser containment (P0) | Enforce byte/page/row/cell/time limits, safe paths, file signatures and isolated risky parsing; no macro/formula/external-entity execution. | Traversal, zip-bomb, malformed PDF, oversized request and spreadsheet formula fixtures fail without unbounded resources or data writes. | Partial PDF/CSV limits |
| NFR-05 | Reliability and idempotency (P0) | Retryable import/reconciliation steps shall be idempotent and final financial transitions atomic; partial failures shall be discoverable. | Forced commit/file failure and concurrent retry leave no duplicate financial events; recovery finds orphan/missing blobs. | Partial |
| NFR-06 | Deterministic integrity (P0) | Calculations shall use Decimal, documented precision/rounding, explicit basis and conserved allocation balances; snapshots shall identify algorithm versions. | Golden cases match exactly at supported scale; splitting allocations conserves amount; reordering input changes no totals. | Legacy Decimal exists |
| NFR-07 | Performance budget (P1) | Before pilot, benchmark on a declared 4-core/8-GB local environment with 2,000 records, 100 PDF pages and five concurrent users. | Proposed targets: p95 ordinary list/report <2 s; 2,000-row CSV preview <10 s; provider timeout <=60 s. Record actual values and failures; no silent truncation. | Unmeasured targets |
| NFR-08 | Accessibility (P1) | Mapping, review, errors and reporting shall be keyboard-operable with labeled controls, visible focus and non-color status cues; target WCAG 2.2 AA for core journeys. | Keyboard-only import and source inspection complete; automated serious/critical findings zero, plus manual focus/contrast/reduced-motion checks. | Historical frontend checks only |
| NFR-09 | Maintainability and contracts (P1) | Shared field/business contracts shall drive API and UI semantics; CI shall validate types, migrations and legacy compatibility without a model key. | Unknown config keys fail; adapter contract test proves same normalized semantics; pinned version and upgrade notes exist. | Partial typed stack |
| NFR-10 | Operational recovery (P0) | Before hosting, provide synchronized DB/private-file backup, restoration, migration rollback strategy and incident procedure. | Restore fixture DB/files to isolated target; verify hashes, sources and login. Proposed local-demo recovery target <=1 hour measured in rehearsal. | Not freshly verified |
| NFR-11 | Observability (P1) | Emit structured request/import/review/error events with correlation IDs and timings, excluding document contents and secrets by default. | A failed import can be traced across stages; log/metric access tenant-safe; provider costs tracked without raw prompts. | Partial audit only |
| NFR-12 | No unsupported financial claims (P0) | UI/export/model context shall retain quality labels and distinguish recorded contribution, net profit, cash and recoverable loss. | Incomplete-cost example never appears as confirmed profit; an anomaly is not presented as proven fraud or guaranteed savings. | Partial existing warnings |

## 5. Data contract and validation policy

The [canonical data dictionary](../architecture/canonical-data-model.md) is normative for proposed entities, fields, requirement levels, cardinalities, money/date semantics, lifecycle and ownership. No optional source field becomes a mandatory globally fabricated value. Minimum operation prerequisites are stricter than raw staging requirements.

Examples:
- Raw invoice with no customer ID may be staged; it is not counted as a confirmed customer sale.
- Expense without a customer is a legitimate unallocated expense, not an invalid company record.
- Absent tax allows gross-only storage where amount basis is explicit; it prevents a verified net-revenue calculation.
- Disabled contract module allows invoicing but yields not-applicable compliance; enabled module with no applicable evidence yields unavailable comparison.
- Confirmed cost coverage does not prove audited net profit; shared overhead exclusions remain disclosed.

Statuses are separate axes: availability (known/unknown/unavailable/not_applicable), verification (verified/unverified/not_required), completeness (complete/partial/unknown). Zero is a value. UI/export/AI must preserve these axes and reasons.

## 6. API contracts — proposed additive v2

All paths below begin /api/workspaces/{organization_id}/v2. They are **proposals**; current /records, /imports, /contracts, /finance, /profitability, /evidence and /chat endpoints remain compatible until a separately reviewed migration. Authentication uses existing session/origin controls. Organization in path is resolved against membership, never accepted as sufficient authorization.

| Method / path | Input / output | Authorization and errors |
|---|---|---|
| GET /capabilities | Implemented modules, supported kinds/limits, active config version | Member; no private profile fields |
| GET /configuration | Redacted profile + version; admin sees editable settings | Member/admin view separation |
| POST /configuration/versions | expected_version, full validated settings, reason → draft version | Admin; 422 invalid/unsupported policy |
| POST /configuration/versions/{version}/activate | expected_active_version, impact_acknowledgement → active version | Admin; 409 stale; old previews invalidated |
| GET /schemas/{kind} | field types/policies, allowed transforms, layout and active version | Finance/admin; analysts read only authorized display schema |
| POST /source-files | Multipart file + declared kind/source metadata → inventory ID, hash, detected type | Writer; 413 cap, 422 unsupported/corrupt; no financial insertion |
| POST /import-batches | source IDs, selected sheet, kind, config_version → staged batch | Writer; source ownership verified |
| GET /import-batches/{id} | states, mapping suggestions/reasons, paginated rows/issues/unknown fields | Writer; full raw source not exposed to analyst |
| PUT /import-batches/{id}/mapping | expected_revision, mappings/transforms, explicit review choices → new preview hash | Writer; 409 stale, 422 ambiguous/incompatible |
| POST /mapping-profiles | name, source signature, reviewed mapping, auto-apply rules → version | Writer within admin policy; cannot cross org |
| POST /import-batches/{id}/confirm | preview_hash, expected_config_version, expected_revision → inserted/skipped/conflicted counts | Writer; 409 stale/conflict, 422 unresolved required field; atomic |
| GET /relationships/candidates | typed relation, permitted source filters, cursor → candidates + evidence | Writer for material review; never use candidate as confirmed data |
| POST /relationships/{candidate_id}/decision | expected_revision, accept/reject, reason → typed link/review event | Writer; 409 competing decision; 422 invalid date/currency/cardinality |
| POST /payments/{id}/allocations | invoice IDs + decimal amounts + evidence + expected_revision → balances | Writer; lock allocation parents; reject over/foreign allocation |
| POST /expenses/{id}/allocations | typed targets + amount/driver + review evidence + expected_revision → residual | Writer; no duplicate project/customer rollup |
| POST /contracts/{id}/versions | source evidence, dates, terms/scope, supersedes reference → draft version | Writer; review endpoint required before compliance |
| POST /contracts/{id}/versions/{version}/review | expected_revision, reviewer decision/reason → reviewed/declined | Writer; same-scope ambiguity fails 409 |
| GET /reports/customer-period | customer, period, basis, optional as_of → metrics/coverage/findings/source refs | Scoped member; no mixed-currency implicit total |
| GET /sources/{id} | authorized original file/record/locator | Scope-aware file access; 404 hidden/missing; safe attachment |
| POST /investigations | question + optional scope + report version → structured evidence response | Member; exact reauthorization and configurable outbound policy |

Future vendor/project/credit CRUD uses separate typed resources, never arbitrary table names or free-form SQL. Paginated reads return items, next_cursor and coverage; cursor bound to org/filter/order, stable-ID tie-breaking. Money JSON values are strings, not floats. Date-only fields use ISO date; timestamps include offset and normalize to UTC; month basis stays explicit.

Example proposed mapping decision (illustrative, not an executable endpoint today):

~~~json
{
  "expected_revision": 2,
  "config_version": 3,
  "mappings": [
    {"source_column": 0, "source_name": "Client Code", "target": "customer_external_id", "transform": "identity"},
    {"source_column": 4, "source_name": "Gross", "target": "source_gross", "transform": "decimal_en_GB"}
  ],
  "unmapped_columns": [5],
  "amount_basis": "gross_tax_unknown",
  "review_reason": "Source contains gross billed amount without a tax breakdown"
}
~~~

Proposed error envelope:

~~~json
{
  "error": {
    "code": "mapping_ambiguous",
    "message": "Choose the date format before confirming.",
    "field": "issue_date",
    "source": {"file_id": "example", "sheet": "Sales", "row": 7, "column": 2},
    "retryable": false,
    "request_id": "example-request"
  }
}
~~~

401 invalid session; 403 forbidden operation; 404 absent or inaccessible object without enumeration details; 409 stale/conflict; 413 size cap; 422 semantic validation; 429 throttled; 503 provider/storage unavailable. Current API uses older detail payloads; compatibility adapter required, not an unannounced breaking replacement.

## 7. Reconciliation, evidence and corrections

Accepting a relationship is a financial state change: validate party/tenant/currency/applicability again within a transaction. Similarity never auto-confirms. Record candidate alternatives, confidence meaning, reviewer and source. Use explicit payment and cost allocation tables with conservation checks; pending candidates have no financial effect.

Deterministic calculations operate on confirmed typed records and approved interpretation versions. Existing legacy equations remain a named adapter. Reviewed contract values are usable only for supported billing scope/period. Pricing flags do not establish loss, fraud, legal enforceability or savings.

Document content is untrusted data. Authorize before search; never follow embedded instructions/URLs automatically. Provider outputs can select supported evidence but cannot establish financial facts. Exact value and substring checks are necessary controls, not proof that an explanation answers the question. Keep a visible limitation and human review.

## 8. Migration, storage and operations

Expand schema with profile/source/mapping/typed relation tables; backfill a legacy profile and identity crosswalk without inventing fields. Compare old/new read paths on copied fixtures. Move unallocated-expense support only after its access rules exist. Store all parser/config/calculation versions. Cut over by organization; disable new writes before rollback; retain new tables/data until a verified downgrade or forward fix. See target architecture and roadmap.

Use private persistent storage paired with PostgreSQL backups. Stage files before confirmation, track finalization state and reconcile orphans. Restrict original/raw data to finance/admin unless a reviewed evidence slice is explicitly accessible. Set retention and provider-consent policies before real-user rollout.

Initial deploy is local/private. Public rollout requires HTTPS, secret provisioning, resource limits, database migrations, restore verification, health/monitoring and tested persistent file storage. A frontend-only host does not supply these backend responsibilities.

## 9. Release gates and unresolved product choices

Release requires all P0 requirements in the phase and its traceability tests passing; no cross-tenant leak, unexplained money difference, unsupported automatic link or partial commit is acceptable. Performance/accessibility targets are proposed acceptance budgets, not measured outcomes.

Review decisions: choose first pilot accounting-export convention and cost boundary; confirm real-data reuse/retention; decide whether payment reconciliation belongs in the first usable release or the next increment. Defaults proposed here: small B2B services, billed-contribution basis, same-currency applications, finance-reviewed relationships and no statutory accounting. These questions do not block the research artifacts.

Full unit/integration/API/RBAC/import/matching/migration/performance/E2E matrix and actual safe baseline outcomes: [test strategy](../testing/test-strategy.md). Requirement-to-code/phase/test ownership: [traceability](requirements-traceability.md).
