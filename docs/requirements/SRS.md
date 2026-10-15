# ProfitLens — COM-711 Minor Project SRS

> **Implementation follow-up — 15 October 2026:** the team authorized core fixes after this planning snapshot. Evidence-specific investigations and date precision are now fixed. [Current implementation and acceptance results](../MINOR_SCOPE_RELEASE_REPORT.md) supersede pending test/prerequisite statuses below; optional and deferred scope is unchanged.

Version 0.2 · 15 October 2026 · **active planning scope: original 12-week team minor project**.

This revision replaces the expanded SaaS-oriented v0.1 requirements. It changes planning documents only. Existing working features are preserved; scope revision does not imply new implementation, faculty acceptance or fresh test passes.

## 1. Project in one paragraph

ProfitLens helps a small B2B service business investigate changes in customer profitability. It combines customer records, invoices, attributed expenses and readable PDF contracts; calculates net billed revenue, recorded contribution and margin in Python; flags three reviewable discrepancies; and uses authorized document evidence to support AI explanations. Its contribution is the tested integration of these steps, not inventing accounting or AI.

Formal title: **ProfitLens: An AI-Driven Context-Aware Business Profitability and Decision Intelligence System**. Course: COM-711. Team project; 12 development weeks. No new industry expansion is part of this deliverable.

## 2. Scope decision

| Must deliver | Optional only after core passes | Future work — not required for the minor project |
|---|---|---|
| Current authenticated organizations and preset roles | Reviewed column aliases for at most two well-defined CSV export layouts | General module marketplace or industry presets |
| Customer/invoice/attributed-expense CSV preview and confirmation | XLSX using exactly the same validated record semantics | Payment/bank reconciliation and many-to-many settlements |
| Private text PDF contracts and manual monthly-term review | Small convenience export or one scoped usability improvement | Separate accounting credit/refund ledgers, tax engine, FX conversion |
| Deterministic contribution/margin and three discrepancy rules | One small neural retrieval comparison only if time and evidence justify it | Vendors/AP, inventory, purchase orders, payroll, timesheets, project accounting |
| BM25 contextual retrieval and checked AI investigation | Hosted demo if backend/storage requirements can be met safely | Shared-cost allocation engine, custom role/form builder, arbitrary custom records |
| Dashboard/source drill-down and existing popup chat | Quantization only if a chosen pretrained retrieval model exists | OCR, accounting/Drive/OneDrive connectors, microservices, model training |
| Reproducible tests, evaluation, report and local faculty demo | None of these options blocks submission readiness | Enterprise onboarding, billing/subscriptions, high-scale operations |

Existing financial correctness and permission safeguards remain mandatory. Removing a payment module from scope does not allow calling an invoice a payment. Missing data must remain missing.

## 3. Supported assumptions and flexibility

- Small service-business customer/month analysis; one declared currency per workspace and supported two-decimal amounts. No implicit conversion.
- The existing invoice convention is subtotal - discount + tax - refund = total. The legacy refund field is a billed-revenue adjustment, not a cash-refund ledger.
- Costs supplied are already attributed to customers. ProfitLens does not invent customer allocations for generic spending; unsupported/unallocated input stays outside customer profitability.
- Contracts are optional evidence: invoice/revenue reporting can work without one. Pricing compliance requires reviewed applicable terms; absent evidence is unavailable/unverified, never “verified”.
- Customer industry may be blank. Customer, period, currency and amount fields required for a selected calculation cannot be made optional to force an import through.
- Strict template rejection is acceptable for the core. Unknown columns must be identified, not silently dropped. Any optional mapping enhancement must preserve raw values/unknown columns and require review of ambiguity.
- Fixed full-month fees are supported; usage-based billing, proration, contract amendments and overlapping service agreements are documented limitations.
- Public component datasets can demonstrate imports and missing-data handling; synthetic linked fixtures demonstrate the complete workflow. These remain visibly separate.

These boundaries support legitimate differences without promising arbitrary-company compatibility. See the [bounded data model](../architecture/canonical-data-model.md).

## 4. Users and workflow

Admin manages existing access grants and can use finance features. Finance can import/correct records and review evidence/cost coverage. Analyst reads and investigates only assigned customers.

Faculty demonstration: sign in → preview/confirm CSV → inspect invoice/cost records → review contract page/terms → view contribution and warning → open discrepancy sources → ask an evidence-backed question → repeat with a restricted user.

## 5. Requirements and acceptance criteria

MP identifiers replace the archived FR/NFR identifiers. There are **12 functional and 6 quality requirements**, rather than 48 expanded-platform requirements. Status refers to the previously audited repository, not a new execution result.

| ID | Requirement | Behaviour | Acceptance criterion | Current status |
|---|---|---|---|---|
| MP-F01 | Authenticated workspaces | Users shall sign in and access only their organization and permitted customers; retain admin, finance and analyst roles. | An outsider cannot read records/files/search/chat evidence; an analyst cannot write or see unassigned customers. | Implemented; regression verification needed |
| MP-F02 | Customer and financial records | Create, inspect and correct customers, invoices and customer-attributed expenses using documented fields and audit/source references. | Valid records persist; invalid customer/currency/amount is rejected; correcting a record retains source history. | Implemented bounded schema |
| MP-F03 | Validated CSV imports | Preview and explicitly confirm supported CSV schemas; reject unknown/incompatible fields clearly rather than silently discarding or inventing values. | Invalid batch has no business inserts; repeated confirmed file creates no duplicates; same ID with different values conflicts; missing financial prerequisites fail. | Implemented strict templates; flexible mapping optional |
| MP-F04 | Private contract evidence | Upload selectable-text PDFs with customer association; inspect pages and manually review fixed monthly terms and effective dates. | Scanned/encrypted/oversized input is rejected clearly; unreviewed or inapplicable terms never establish an expected price. | Implemented monthly-only workflow |
| MP-F05 | Revenue and recorded costs | Calculate customer/month net billed revenue and attributed recorded costs using the documented legacy amount convention, excluding tax from revenue. | Golden invoice subtotal 1000 − discount 100 − refund 50 gives revenue 850 regardless of tax; absent costs remain unknown. | Implemented |
| MP-F06 | Contribution and margin | Calculate contribution and margin with explicit cost coverage; retain unverified/provisional/stale states. | Revenue 1000 and costs 600 give contribution 400 / margin 40%; missing costs give unavailable contribution; zero revenue gives unavailable margin. | Implemented; strengthen explanation of limitations |
| MP-F07 | Three explainable rules | Flag supported pricing mismatch, unusual cost increase and margin decline with formula, threshold and sources. | Pricing requires reviewed applicable fixed terms; cost/margin comparison requires confirmed comparable costs; unavailable baseline produces no invented finding. | Implemented bounded rules |
| MP-F08 | Authorized contextual retrieval | Retrieve contract passages using BM25 plus customer/period context, preserving page IDs; retain a permission-equivalent baseline. | Hidden passages never enter candidates; expired terms excluded in context mode; source links resolve; lexical misses reported. | Implemented; no embeddings or pgvector |
| MP-F09 | Evidence-grounded explanations | Use the configured pretrained model through the existing adapter, check structured facts/citations and expose insufficient-evidence/provider-failure states. | Wrong numeric/source claims withheld; no model-written financial records; interpretations remain reviewable; revenue-only questions need no fabricated contract evidence. | Implemented in part; broad investigation prerequisites need focused review |
| MP-F10 | Complete demonstration workflow | Provide import→record→financial finding→source inspection→AI investigation through existing UI; retain scoped popup chat. | Teacher can complete the journey with labelled fixtures; filters/links work; empty/error/permission states explain the issue. | Existing UI; final acceptance rerun needed |
| MP-F11 | Reproducible evaluation | Use the frozen synthetic corpus and separate licensed real component data; compare contextual retrieval with the same authorized lexical baseline. | Report actual counts, correctness, anomaly precision/recall, retrieval ranking, failures and provenance; never join unrelated real datasets as one company. | Existing benchmark; relevance evaluation incomplete |
| MP-F12 | Traceable changes and results | Retain source row/page, correction audit and evidence versions; detect stale cost reviews/investigations after relevant changes. | Edited input invalidates its review/result or marks it historical; users can inspect supporting records under current permissions. | Implemented bounded history; regression needed |
| MP-N01 | Exact arithmetic and meaning | Use Decimal and explicit amount/currency/month conventions; distinguish zero from missing and recorded contribution from net profit. | Money goldens pass exactly; no implicit currency conversion, tax-zero default or second discount/refund subtraction. | Implemented within declared scope |
| MP-N02 | Data and provider security | Enforce authorization before retrieval and after generation; keep keys server-side and files private; treat document text as untrusted. | Unauthorized sentinel absent from files/prompts/results; revoked access denied; source instructions cannot trigger writes; no key in browser/log output. | Existing safeguards; not a production-security certification |
| MP-N03 | Bounded and recoverable operations | Keep upload/query/provider limits, explicit errors and safe import retry; deterministic functions remain usable without AI. | Oversized/invalid input fails without partial records; provider failure does not break finance; displayed caps are visible. | Implemented limits; final failure-flow verification needed |
| MP-N04 | Compatibility and maintainability | Reuse existing stack, tests and migrations; make only focused changes needed for the core and preserve old records/semantics. | Affected regressions pass; any migration is tested on isolated fixtures; no schema redesign solely to support a speculative industry. | Delivery constraint |
| MP-N05 | Readable accessible interface | Keep key journeys keyboard-operable, labelled, readable and responsive; status must not rely on color. | Manual keyboard demo and relevant existing browser/accessibility checks pass; no critical navigation/error blocker. | Existing UI; final checks pending |
| MP-N06 | Repeatable local delivery | Provide local launcher/setup, synthetic demo, test instructions, final report and viva materials with accurate status. | From documented setup the team can start frontend/API/PostgreSQL, demonstrate and stop; list unverified hosting/model limitations. | Local tooling exists; public hosting not required |

## 6. Architecture, interfaces and evidence

Keep Next.js/React/TypeScript → FastAPI → PostgreSQL and private PDF storage. Keep current session/origin checks, SQLAlchemy/Alembic, Decimal calculations, BM25 and configurable provider adapter. No generalized v2 API is required.

Current workspace API groups: /records, /imports, /contracts, /finance, /profitability, /evidence, /investigations, /chat and /members under /api/workspaces/{organization_id}. Follow current typed inputs and normal preview-confirm flow. Any targeted bug fix preserves client compatibility. A wider data model is not a prerequisite for completing the prototype.

AI is not a financial calculator or permission authority. Exact values/quotes are checked; semantic relevance still needs evaluation and human review. Source text cannot authorize actions. A financial question with sufficient records should not be forced to have contract evidence, while contract-price claims must have it.

## 7. Evaluation and completion

Use the existing 20-customer, six-month synthetic corpus and 30-question baseline. Inspect actual fixture counts rather than repeating old targets: the saved corpus includes 120 invoices, 115 expenses and 40 current/expired contracts. Keep the real-data demonstration separate; no complete publicly reusable customer-invoice-cost-contract dataset has been verified.

Core readiness means affected automated tests pass, the faculty journey works, evidence/permissions can be demonstrated, evaluation results and failures are reported, and setup/viva documents match the code. No production SLA, customer survey programme, public deployment or universal export compatibility is required. User feedback is welcome but not a mandatory research study.

## 8. Document pack

- [Market research and relevant lessons](../research/market-and-case-study-review.md)
- [Formats and datasets](../research/real-world-data-formats-and-datasets.md)
- [Scoped gap analysis](../architecture/gap-analysis.md)
- [Bounded data model](../architecture/canonical-data-model.md)
- [Architecture and workflow](../architecture/target-architecture.md)
- [Original-week roadmap and completion plan](../implementation/phased-roadmap.md)
- [Focused testing strategy](../testing/test-strategy.md)
- [Requirement traceability](requirements-traceability.md)

The [expanded v0.1 design archive](../research/archive/expanded-design-2026-10-15/requirements/SRS.md) is future reference only. Do not implement its platform requirements as minor-project prerequisites.
