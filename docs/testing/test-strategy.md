# ProfitLens — focused minor-project testing strategy

> **Implementation follow-up — 15 October 2026:** the team authorized core fixes after this planning snapshot. Evidence-specific investigations and date precision are now fixed. [Current implementation and acceptance results](../MINOR_SCOPE_RELEASE_REPORT.md) supersede pending test/prerequisite statuses below; optional and deferred scope is unchanged.

15 October 2026 · active scope v0.2. This revision narrows the acceptance plan; it does **not** report a new application test run.

## 1. Recorded evidence and limits

The earlier research audit on 15 October 2026 recorded:

| Check | Recorded result | Limit |
|---|---|---|
| Selected ingestion, finance, retrieval and provider pytest files | 43 passed in 0.92 seconds, exit 0 | Four files; provider mocked; not a full regression run |
| TypeScript no-emit check | Exit 0, no diagnostics | Not browser behaviour or production build |
| Read-only database inventory | Revision 20261015_roadmap; 16 application tables; plpgsql only | Not a migration rehearsal or full schema-drift comparison |

No database reset, migration, new import, model call or application change is part of this documentation revision. Existing integration fixtures delete table contents: never point them at the normal development database.

## 2. Saved synthetic evaluation

Source: [saved evaluation JSON](../evaluation-results-2026-10-15.json), not regenerated for this scope change.

- Corpus: 20 customers, six months, 120 invoices, 115 expenses, 40 contracts, 30 questions (10 development and 20 held-out).
- Labelled contribution cases: 20/20 correct. Labelled anomalies: 15 true positives, no reported false positives or false negatives on this fixture.
- Held-out questions: 15 answerable and five unanswerable. Baseline/context recall@3 both 0.6667. Returned precision@3 and MRR are 0.3333/0.3333 for baseline and 0.6667/0.6667 for context. Both abstained on the five labelled unanswerable cases.
- This shows a ranking difference on a small lexical benchmark, not improved recall, live answer quality, real-company savings or production accuracy.

Keep genuine component data separate. FHDC spending has no verified sales/cost/contract chain. No newly discovered complete real dataset is claimed, and no synthetic substitute fulfils the earlier genuine-data-only request.

## 3. Acceptance matrix

These **18 planned acceptance cases** map one-to-one to the [SRS](../requirements/SRS.md). Existing tests cover some primitives; the matrix is not a declaration that every acceptance case passed.

| Test | Requirement | Method | Scenario | Expected evidence |
|---|---|---|---|---|
| MP-T01 | MP-F01 | API integration/security | Two organizations; admin, finance, assigned analyst and outsider; attempt records, files, search and chat. | Reject unauthorized IDs and analyst writes without leaking record existence. |
| MP-T02 | MP-F02 | Unit/API integration | Create valid customer/invoice/expense; wrong currency, missing customer, invalid amount; correction history. | Only valid records persist; source and actor history survive corrections. |
| MP-T03 | MP-F03 | Import integration | Valid/invalid/empty CSV; unknown or duplicate header; duplicate file; conflicting ID; repeat confirmation. | Visible errors; no partial business inserts; repeat creates no duplicate; conflict never overwrites silently. |
| MP-T04 | MP-F04 | PDF/API integration | Readable, scanned, encrypted and oversized PDF; unreviewed/expired/wrong-currency/partial-period terms. | Supported text has page sources; unsupported inputs explain failure; inapplicable terms cannot verify price. |
| MP-T05 | MP-F05 | Unit | Subtotal 1000, discount100, refund50; vary tax; empty expense set; repeated identifiers. | Revenue850; tax excluded; supplied costs sum once; absent costs remain unknown. |
| MP-T06 | MP-F06 | Unit/integration | Revenue1000/cost600; zero revenue; absent costs; provisional costs; review followed by edit. | Contribution400/margin40%; unavailable/provisional/stale states follow current definitions. |
| MP-T07 | MP-F07 | Unit/evaluation | Labelled pricing, cost-increase and margin-decline positives plus normal, missing and conflicting-evidence cases. | Findings cite exact inputs/thresholds; no invented expected amount or invalid-baseline comparison. |
| MP-T08 | MP-F08 | Retrieval/security | Same query and authorized corpus in baseline/context modes; expired terms, hidden customer, irrelevant words. | Measure ranking; no hidden source; context excludes inappropriate periods; sources open under permission. |
| MP-T09 | MP-F09 | Provider/unit/manual | Correct/incorrect numeric facts and source IDs; no evidence; record-only question; provider failure; misleading document text. | Reject unsupported claims; explain insufficiency; adequate financial evidence need not imply contract availability; no AI writes. |
| MP-T10 | MP-F10 | Browser/manual | Login → preview/confirm → records → costs/contract review → discrepancy → source → popup chat; change workspace. | All supported controls work; scope updates correctly; failure/empty/loading states remain understandable. |
| MP-T11 | MP-F11 | Reproducible evaluation | Freeze corpus, labels and split; replay same authorized baseline and context mode; inspect real-data manifest. | Actual counts/metrics and failures reported; no fabricated real links or unsupported production claims. |
| MP-T12 | MP-F12 | Integration/regression | Edit source after cost review/investigation; revoke customer access; reopen historical evidence. | Stale state visible; old result not presented as fresh; current permissions still apply. |
| MP-T13 | MP-N01 | Unit | Discount/refund/tax edge cases, decimal rounding boundaries, zero versus missing, foreign currency. | Documented Decimal arithmetic exactly matches independent goldens; unsupported semantics rejected. |
| MP-T14 | MP-N02 | Security/integration | Cross-tenant IDs/files, revoked grants, untrusted source instructions, outbound context capture with mock provider. | No unauthorized sentinel or secret exposure; instructions in source cannot change permissions or financial records. |
| MP-T15 | MP-N03 | API/provider | Upload cap, invalid file, retry/duplicate confirm, unavailable/timeout provider and capped result. | No partial financial records; errors actionable; non-AI analysis remains available. |
| MP-T16 | MP-N04 | Regression/migration if changed | Existing fixture before/after targeted fix; migrate disposable legacy snapshot only if migration needed. | Old totals, sources and grants preserved; no unexplained drift; migration not required for docs-only update. |
| MP-T17 | MP-N05 | Browser/manual | Keyboard navigation, visible focus, field labels, error/readiness labels, narrow viewport and reduced motion. | Core workflow usable without mouse or color alone; no blocking overflow or hidden action. |
| MP-T18 | MP-N06 | Local smoke/documentation | Use documented launcher/setup with isolated demo; open sources; run documented checks; stop owned services. | Repeatable start/demo/stop; honest current status and limitations; no hosting claim without actual verification. |

## 4. Practical execution order

1. Run pure-function/import/provider checks, then TypeScript checking. Investigate failures before broadening.
2. Use a dedicated disposable PostgreSQL test database, temporary private storage and non-sensitive fixtures for API, auth, tenant, transaction and regression tests. Inspect fixture deletion behaviour first.
3. Test existing migrations against an empty database and a disposable older fixture only when schema changes are actually proposed. No new canonical-model migration is necessary for this scope.
4. Walk through the faculty demo in a test workspace with the admin and assigned analyst. Use valid, invalid and repeated imports; show unknown costs and unavailable contract compliance as meaningful states.
5. Compare baseline/context retrieval on the same frozen authorized corpus. Inspect model answers separately using approved non-sensitive inputs and a bounded provider budget.
6. Record commit, command, dataset version/hash, configuration, counts, failures and environment. A skipped or mocked live-provider check is not proof of real-provider quality.

Previously executed safe baseline commands:

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_ingestion.py tests/test_finance.py tests/test_retrieval_evaluation.py tests/test_provider.py
.\apps\web\node_modules\.bin\tsc.cmd --project apps/web/tsconfig.json --noEmit --incremental false
~~~

## 5. Measures appropriate to the project

| Area | Method / denominator | Interpretation |
|---|---|---|
| Financial correctness | Independently worked expected amounts for every labelled case; include zero/missing/tax/discount/refund | Exact equality under the declared money convention; no percentage alone hides failures |
| Three discrepancy rules | TP, FP, FN and precision/recall per rule on labelled positives and negatives | Include missing/ambiguous evidence; fixture results are not real-world rates |
| Retrieval | Recall@3, returned precision@3, MRR on frozen answerable questions; abstentions separately | Same authorized corpus and query split; do not compare an unrestricted baseline |
| Answer quality | Review all 20 held-out questions if live evaluation is authorized; record correct, relevant, supported, incomplete and withheld answers | Report successful/failed/abstained denominators and citation validity separately; exact-value checks do not prove semantic truth |
| Provenance | Check each demonstrated financial result against row IDs and each contract citation against page IDs | Source coverage does not establish that a source is current or true |
| Reliability/security | Repeat imports, invalid batches, revocation and cross-tenant sentinel attempts | Zero unauthorized disclosure expected; any observed breach blocks core readiness |
| Responsiveness | On declared local hardware, repeat ten representative financial/retrieval requests; record median/range and errors | Descriptive local measurements only; no enterprise SLA or universal speed claim |

No mandatory user-research recruitment, stress-testing programme, model training or quantization benchmark. A small optional usability trial can supplement the faculty demo.

## 6. Optional import flexibility

Only after the core is stable: choose two known CSV layouts OR XLSX with the same semantics. Label every source column manually, preserve raw/unknown fields, test missing optional and required values, ambiguous dates/decimals and duplicate IDs. Measure correctly proposed mappings / reviewed proposals and exact-ID relationship correctness against labels; review ambiguity instead of guessing. These are conditional tests for a separately approved enhancement, not present capabilities.

Payment allocations, shared-cost allocation engines, arbitrary modules and industry presets are outside the current acceptance matrix. Their test ideas remain in the [expanded archive](../research/archive/expanded-design-2026-10-15/testing/test-strategy.md).

## 7. Completion record

For each MP-T case, record pass/fail/not run, evidence location and limitation during final acceptance. Resolve core correctness/security blockers before presentation; document lesser limitations. See the [completion roadmap](../implementation/phased-roadmap.md) and [traceability](../requirements/requirements-traceability.md).
