# ProfitLens — gaps relevant to the college minor project

> **Implementation follow-up — 15 October 2026:** the team authorized core fixes after this planning snapshot. Evidence-specific investigations and date precision are now fixed. [Current implementation and acceptance results](../MINOR_SCOPE_RELEASE_REPORT.md) supersede pending test/prerequisite statuses below; optional and deferred scope is unchanged.

15 October 2026 · active scope v0.2. This revises priorities from the preceding audit; it is **not a fresh application audit or new test run**. Baseline: c4abad70b53d934016bf5cb39076bf80edf7b756.

## 1. Actual status

The repository is beyond Week 4. It contains customer/invoice/expense management, secure CSV imports, reviewed monthly PDF contracts, revenue/cost and contribution/margin calculations, three discrepancy rules, BM25 retrieval, provider integration and popup AI chat.

The previous audit inspected code, migrations, UI source, tests, public/private project notes, the revised synopsis and selected viva-guide pages. A read-only check found revision 20261015_roadmap and all 16 application tables; only plpgsql was installed. No vector search is implemented. Preserve that evidence; do not reset the project to an outdated milestone.

## 2. Keep / finish / defer

| Area | Current evidence | Minor-project action |
|---|---|---|
| Auth, roles and tenant/customer access | security.py; main.py; integration tests | Preserve and rerun relevant security regressions before demonstration |
| CSV persistence and private PDFs | imports.py; ingestion/; contract routes | Keep documented templates, atomic confirmation and source pages |
| Revenue, costs, contribution, margin | finance.py; profitability.py | Verify goldens and explain provisional/missing values clearly |
| Pricing mismatch, cost increase, margin decline | profitability.findings | Demonstrate one supported case and one insufficient-data case per rule |
| BM25 context filtering | retrieval.py; frozen baseline | Retain; clearly distinguish lexical from semantic retrieval |
| Grounded investigation/chat | explanations.py; chat.py; assistant.py | Test question relevance and failure states; fix only demonstrated issues |
| Broad evidence prerequisite | explain() currently requires confirmed costs and contract passages for formal investigation | Review narrowly: records-only questions should not invent or require unrelated contract evidence |
| Real-data coverage | Genuine public expense component; no complete verified linked real corpus | Document honest gaps; keep synthetic ground-truth demo separate |
| Overview capped lists | UI explicitly labels 200-record preview cap | Keep cap visible; do not imply full financial totals from preview counts |
| Runtime/deployment | Local tooling exists; hosted/restore proof incomplete | Complete local demonstration; public hosting optional |
| General mapping/configuration platform | Not implemented | Defer; only bounded alias/XLSX conveniences may be added after core |
| Payments, vendors, project costing and allocation | Not implemented | Future scope, not a minor-project defect requiring implementation |
| Contract amendment/FX/tax/OCR workflows | Not implemented | State unsupported cases; do not weaken validation to simulate support |

## 3. What still matters for correctness

- Strict schemas are acceptable when clearly documented. Silent field loss, wrong totals, invented links or misleading verified states are not.
- Existing invoices use subtotal - discount + tax - refund = total. This is a bounded import convention, not every company's accounting system.
- Expense records require a known customer. General unallocated spending cannot honestly demonstrate customer contribution; labelled technical buckets in a component demo do not prove allocation.
- Contract pricing is limited to reviewed fixed full-month terms. Revised/overlapping/usage-based contracts may be unsupported, with comparison unavailable.
- Costs are recorded attributed costs. An attestation and a correct formula do not turn the result into audited net profit.
- Exact quote/numeric checks do not prove semantic relevance. Evaluate the actual answer and retain limitations.
- File/DB recovery, parser resource use and public deployment deserve targeted checks if they affect the demo or hosting. They do not justify building an enterprise operations platform.

No new broken user flow has been reproduced in this documentation turn. Risks are not proven exploits, and absent future modules are not implemented functionality.

## 4. Documentation corrections

The 10 October viva guide and September synopsis predate later code. Preserve their historical dates; update teaching material when the final demo snapshot is verified. Semantic retrieval/pgvector and quantization remain unimplemented despite older proposals. Live provider smoke success is different from systematic answer-quality evaluation. The team project lasts 12 development weeks, with no new enterprise phase added to the deadline.

The expanded 48-requirement proposal over-scoped the current task. Its design remains in the [archive](../research/archive/expanded-design-2026-10-15/requirements/SRS.md). The active [SRS](../requirements/SRS.md) now has 18 core requirements. Missing platform features do not block college readiness.

## 5. Validation evidence retained

Previous research run: 43 selected Python tests passed in 0.92 s; TypeScript exited 0; read-only schema inventory passed. No database-reset tests, fresh browser suite or live model evaluation were run in that research phase. This scope-only revision does not claim fresh application passes.

Next work: verify the existing core journey, address specific failures, evaluate results and prepare the report/demo. See [focused roadmap](../implementation/phased-roadmap.md) and [test strategy](../testing/test-strategy.md).
