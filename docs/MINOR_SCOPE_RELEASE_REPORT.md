# ProfitLens — minor-project fixes and verification

15 October 2026. Baseline: `c4abad70b53d934016bf5cb39076bf80edf7b756`. Scope: the original COM-711 customer-profitability investigation prototype. No accounting-platform or industry expansion was implemented.

## What changed

1. **Evidence appropriate to the operation.** Formal investigations accept `evidence_scope=financial|contract|combined`. The default remains `combined` for existing clients. Financial questions can use available records without a contract or cost attestation; absent costs remain unavailable. Contract-only questions require reviewed, applicable passages but need no invoice/cost. Combined questions require both evidence types. Unsupported sources and numeric claims are still withheld.
2. **Honest provisional results.** Returned contribution/cost/margin claims are labelled provisional until cost coverage is confirmed. A revenue-only answer is not blocked by missing costs. A combined investigation no longer requires an unrelated cost attestation to quote a contract or inspect revenue.
3. **Scoped history and verification.** Evidence scope is saved in the existing JSON snapshot and used on reread. Permission and input rechecks remain in place. Old snapshots may be marked stale because the evidence format has changed; rerun them. No database migration or record rewrite is needed.
4. **Correct date precision in chat.** The renderer previously expanded month-only text such as “September 2026” into a contract end date. Full dates no longer accept month-only aliases. Explicit coarse month facts preserve month precision while exact day facts retain their day. Unknown dates remain rejected. This was found through a live synthetic smoke check, not guessed from a screenshot.
5. **Small UI and test improvements.** The analysis screen offers the evidence selector and explains prerequisites. An unavailable prior margin no longer renders as “unavailable%”. Browser/build output can use separate directories so verification does not replace a running demo's Next.js build. The synthetic model-evaluation script is repeatable and requires `--live` before external calls.

## Actual checks

| Check | Actual outcome | Boundary |
|---|---|---|
| Full backend pytest | **122 passed in 9.81 seconds** | Dedicated `profitlens_test`; normal database untouched. One existing Starlette/httpx deprecation warning |
| Browser acceptance | **15 scenarios passed across full run + corrected-case rerun** | Full run: 14 pass, one test-fixture mistake; analysis rerun passed after choosing the intended missing-cost customer. Additional mobile scroll/screenshot check passed |
| Browser flows | Login/logout; CRUD; invalid/valid/repeated CSV; private PDF/review/download; exact revenue and missing costs; analyst scope; analysis/history/offline provider; chat navigation; keyboard/reduced motion; narrow screen | Chat interaction test mocks model responses. Real model checks are separately listed below |
| Automated accessibility | Existing login/overview/dialog/finance WCAG checks passed in browser suite | Not a comprehensive accessibility certification |
| Production dependency audit | npm audit --omit=dev --audit-level=high: zero vulnerabilities | Registry result at verification time |
| Python quality | Ruff lint and formatting passed, 45 Python files | Existing configured rules |
| Frontend quality | ESLint, TypeScript no-emit and Prettier checks passed | Production build also completed successfully in `.next-verify` |
| Synthetic financial/retrieval replay | 20/20 contribution cases; 15 anomaly TP, 0 FP, 0 FN | Constructed fixture labels; not a real-world accuracy estimate |
| Saved source inspection | Desktop plus scrolled mobile analysis screenshots inspected | Full-page mobile capture had compositing gaps; viewport captures confirmed fields, controls and amounts visible |
| Local API timings | Ten requests each: profitability median 9.40 ms (8.60–25.60); retrieval median 3.61 ms (3.41–6.87), no errors | Authenticated TestClient + local PostgreSQL; excludes browser, socket-network and model latency; not a production SLA |

The test databases and synthetic private storage are separate from normal demo records. Existing real-data workspaces were not replaced, imported into or relabelled. Existing presentation files and local credentials remain outside publication.

## Model and retrieval evaluation

Saved evidence:

- [Financial/retrieval benchmark](evaluation-results-minor-scope-2026-10-15.json)
- [24-case explanation evaluation](explanation-evaluation-minor-scope-2026-10-15.json)
- [Live API chat smoke, including initial failures and final date fix](chat-smoke-minor-scope-2026-10-15.json)
- [Local API timing samples](local-timing-minor-scope-2026-10-15.json)

The frozen retrieval corpus has 20 customers, six months, 120 invoices, 115 expenses, 40 contracts and 30 questions. On the 20 held-out questions (15 answerable, five unsupported), baseline/context recall@3 both remain 0.6667. Returned precision@3 and MRR are 0.3333/0.3333 versus 0.6667/0.6667. Both retrieval modes abstain on five unsupported queries. Context improves ranking here, not recall.

The live explanation evaluation used the configured OpenRouter `openai/gpt-4.1-mini` with generated synthetic evidence only: 20 held-out contract questions plus four explicit financial checks. Of 24 cases, **13 returned checked evidence and 11 returned insufficient evidence**. Ten lexical contract answers quoted the relevant service clauses. Three financial answers gave the expected confirmed/provisional contribution or revenue despite missing costs. Five paraphrase questions were answerable in the corpus but missed by BM25; five unsupported-topic questions had no evidence. Those ten cases did not call the provider. The remaining future-revenue question reached the provider and abstained. Thus there were 14 provider calls in this evaluation, not 24 successful model answers.

Question/quote inspection found the ten returned contract selections relevant to the fixture question and the three financial selections correct. This is a small developer review, not independent expert annotation, a customer study or a broad conversational-quality score. Original results are retained, not silently replaced after fixes.

Separate normal-login API smoke checks used `evaluation-demo` in the test database. They confirmed automatic customer/month selection, missing-cost revenue and the current calendar month's no-data state. Initial and prompt-only follow-up replies exposed the month/date rendering error. After the code fix, the actual reply used **2026-09**, contribution **800.00 INR**, margin **66.67 percent**. The “no active customers” prose should be understood as no recorded financial activity that month; free-text interpretation is still not a verified business fact. Deterministic cards and the displayed scope remain the primary reference.

## Requirement coverage and remaining limits

The [SRS](requirements/SRS.md) is the scope authority. Passing tests are evidence for the listed cases, not universal correctness.

| Requirement / acceptance case | Current evidence and disposition |
|---|---|
| MP-F01 / T01 | Session, CSRF, tenant/customer read/write and analyst restriction regressions pass; browser analyst flow passes |
| MP-F02 / T02 | Record create/update, invalid values and audit/source tests pass; browser editing passes |
| MP-F03 / T03 | Preview/confirm, rollback, conflict, concurrent/repeated confirmation, unknown/currency input tests pass; browser import flow passes |
| MP-F04 / T04 | Private upload/download, terms, scope, invalid PDF and overlap tests pass; browser PDF review passes |
| MP-F05 / T05 | Exact financial/duplicate/refund/tax tests and golden browser report pass |
| MP-F06 / T06 | Confirmed/provisional/zero/missing/stale-cost tests pass; missing values visible in browser |
| MP-F07 / T07 | Three rule/threshold tests and 15 labelled positives pass; supported fixed monthly terms only |
| MP-F08 / T08 | Scoped/period retrieval tests pass; five held-out paraphrase misses remain documented |
| MP-F09 / T09 | Scope-specific prerequisites, withheld unsupported claims, provider errors, revocation and live synthetic evidence-selection checks pass; unrestricted semantic quality remains partial |
| MP-F10 / T10 | Supported core browser journeys pass; offline-provider path tested; chat UI model output mocked separately from live API smoke |
| MP-F11 / T11 | Deterministic replay plus saved model outputs/timings provided; complete linked genuine dataset still unverified |
| MP-F12 / T12 | Changed-input/revocation/stale-history tests pass; old evidence-version snapshots may need rerun |
| MP-N01 / T13 | Decimal and explicit money conventions tested; no currency conversion or full credit-note accounting |
| MP-N02 / T14 | Auth, private-file, unauthorized model context, post-generation revocation and hostile/unsupported output cases tested; no external penetration audit |
| MP-N03 / T15 | Size/row limits, safe retry, rollback and mocked provider failure paths pass; non-AI functionality independent |
| MP-N04 / T16 | Existing migration-to-head and regression tests pass on isolated DB; no new migration introduced; no backup-restore rehearsal this turn |
| MP-N05 / T17 | Existing automated accessibility/keyboard/mobile cases pass; analysis viewport inspection completed |
| MP-N06 / T18 | Isolated web/API startup and production build verified; existing launcher preserved, its menu start/stop not freshly rerun; public deployment/restore remain unverified |

## Faculty demonstration — about five minutes

1. Start using `dev.cmd` and use the explicitly synthetic evaluation workspace. Explain one supported service-business customer/month; contribution is not net profit.
2. Preview one invalid CSV, then a valid demo import. Confirm once and retry to show duplicate protection. Inspect source row provenance.
3. For EVAL-01 in September 2026, inspect revenue 1200, costs 400 and contribution 800. Inspect reviewed contract terms and the pricing discrepancy; demonstrate cost/margin findings with EVAL-06 and source records.
4. For EVAL-11 in September, show revenue 1000 with unavailable costs/contribution. Choose **Financial records** and ask about revenue. Missing costs must not become zero.
5. Select **Reviewed contract terms** for a contract question, or **Financial records and contract terms** for a combined explanation. Open the cited page. An unavailable provider displays an explicit error, not a fabricated answer.
6. Show the restricted analyst account, then popup chat's displayed month and source links. State that lexical search can miss paraphrases and AI interpretation requires review.

Use the existing real-data expense workspace only to demonstrate genuine spending ingestion and honest data gaps. It is not a complete customer-profitability dataset.

## Reproduce

Follow [development setup](DEVELOPMENT.md) for dedicated `_test` database URLs. Never run resetting integration fixtures against the normal database.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m profitlens.evaluation --output data/exports/evaluation.json
# Inventory only: no model traffic
.\.venv\Scripts\python.exe scripts/evaluate_explanations.py
# Optional live test: generated synthetic cases only; requires configured provider
.\.venv\Scripts\python.exe scripts/evaluate_explanations.py --live
```

Run browser tests from `apps/web` with `E2E_DATABASE_URL` set. Set `E2E_WEB_PORT` / `E2E_API_PORT` if default ports are busy; this verification used 3002/8002. Browser output uses `.next-e2e`; `NEXT_DIST_DIR=.next-verify` isolates a production-build check. Existing local services were left running.

No XLSX/mapping engine, payment reconciliation, shared-cost engine, industry presets, OCR, embeddings or quantization were added. These do not block this bounded minor-project demonstration. The remaining priorities are faculty preparation, explaining the documented data boundary and any separately requested retrieval/usability improvements—not a larger SaaS build.
