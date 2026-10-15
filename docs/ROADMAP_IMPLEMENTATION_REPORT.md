# ProfitLens roadmap implementation report

> Latest minor-project fixes and fresh verification: [release report](MINOR_SCOPE_RELEASE_REPORT.md). Earlier dated results below retain their historical scope.

**Snapshot:** 15 October 2026. Baseline audited: Git commit `fa1e0f2`. This report describes local implementation and testing; it does not claim a deployed service.

**Pre-publication verification, 15 October 2026:** All 114 backend tests passed in the dedicated test database (one existing Starlette/httpx deprecation warning). Ruff lint/format passed for 43 Python files; TypeScript, ESLint and frontend formatting passed. The latest dataset workspaces and new-import preview also passed a separate live browser check. The earlier full-browser/build results below retain their original scope. Private datasets, credentials, local planning notes and presentation artifacts are excluded from the code publication.

## Audit and scope

The audit inspected repository instructions, the private plan/progress notes, README, architecture/data/security/development documentation, SQLAlchemy schema, Alembic migrations, FastAPI routes, financial and ingestion modules, Next.js screens, test fixtures and CI. Code confirmed Weeks 1–4: persistent authorized workspaces, validated imports, private PDFs, manual term review and exact revenue/cost reports. Contribution, margin, retrieval and AI investigations did not exist at the baseline.

The existing `/finance` endpoint and working CRUD/import/authentication routes were preserved. A separate `/profitability` endpoint and analysis screen extend them. No multi-industry expansion, model training, OCR or autonomous financial action was added. Earlier guides/slides remain historical snapshots and were not overwritten.

## Completed, partial and unimplemented work

| Phase | Delivered | Completion boundary |
| --- | --- | --- |
| Week 5 | Decimal contribution/margin, unavailable/provisional/confirmed states, expense-hash attestations, configurable pricing/cost/margin rules, prior-month comparison and inspectable sources | **Implemented and locally tested.** Cost completeness is a user attestation. Fixed monthly contracts only; contribution is not net profit. |
| Weeks 6–7 | Overlapping page chunks, stable source IDs, PostgreSQL passage storage, reviewed customer/month filtering, BM25 baseline/context retrieval, protected source links and reindexing | **Lexical retrieval foundation implemented and tested.** Original semantic/pgvector proposal is **not implemented**. Exact lexical search is an explicit bounded prototype choice, not semantic search. |
| Weeks 8–9 | OpenRouter/NVIDIA provider adapter, strict structured output, Decimal/unit and source/quote checks, insufficient evidence, provider errors, checked extractive summaries, history, permission/data rechecks after generation | **Partially verified.** Protocol and rejection behavior pass mocked HTTP/model tests. The initial roadmap verification used mocks. A subsequent GPT-4.1 Mini chat smoke check passed (see follow-up below); systematic answer-quality evaluation remains outstanding. |
| Weeks 10–11 | Fixed synthetic dataset, 30 questions, financial labels, baseline/context ranking, malformed output and authorization regressions | **Local reproducible evaluation complete.** Synthetic labels are constructed, not independently annotated. User benefit, human relevance, end-to-end live AI latency and generalization remain unmeasured. Quantization is deferred because BM25 has no pretrained weights. |
| Week 12 | Additive migration, backup/restore rehearsal, separate demo workspace, upload pack, browser integration, standalone build, updated docs, CI benchmark command, Dockerfiles/Compose preparation | **Local integration and preparation complete; deployment verification partial.** Docker unavailable, so container builds/startup and public hosting were not tested. No production-security certification is claimed. |

## Chat follow-up verification — 15 October 2026

The later in-popup chat supersedes the earlier launcher shortcut. It uses a configurable real AI provider, bounded conversation history, current authorized financial evidence and source excerpts. No canned response fallback is used. Financial figures and source IDs are checked; natural-language interpretation is not proven by those checks.

- **96 Python tests passed** after chat integration, including fifteen new chat cases: scope restrictions, permission revocation, changed input, invalid sources/figures, exact literal amount/unit handling, bounded context, provider unavailability and rate limits.
- **Two targeted Chromium tests passed** for the analysis/offline-provider flow and the new chat UI. The latter deliberately mocks replies to test conversation, follow-ups, citations, context clearing, mobile bounds and keyboard behavior.
- A separate **live OpenRouter GPT-4.1 Mini smoke check** succeeded on synthetic evaluation records: contribution/margin, a Hinglish follow-up and contract evidence. A real browser session then received two live replies inside the popup at localhost:3000 and displayed a source PDF link. Desktop/mobile screenshots were inspected. Its temporary session was removed afterward.
- TypeScript, ESLint and Ruff checks passed. Model quality across a representative question set, adversarial language behavior and production performance remain unevaluated. The earlier full browser/build results below predate this chat addition.

## Original roadmap verification results

- **81 Python tests passed** on the dedicated `profitlens_test` database. Includes the original 53 regression tests plus 14 analysis/API tests, eight retrieval/evaluation/verifier tests and six mocked provider-protocol/error cases.
- **14 Chromium tests passed** on separate `profitlens_e2e_test` and ports 3201/8201. Existing editing/import/PDF/authentication/accessibility flows remained functional; the new case covers calculated contribution, discrepancy display, current-contract retrieval, explicit offline-provider status, history and mobile overflow. A final targeted analysis test checks the subsequent small mobile readability correction.
- Ruff lint and formatting checks passed; TypeScript, ESLint and Prettier passed. A Next.js standalone production build succeeded. These are local results, not a GitHub Actions run.
- Alembic upgraded the existing local database and `alembic check` detected no schema drift. A pre-upgrade custom-format dump was restored to the **dedicated test database**; upgrade → downgrade to the Week 4 revision → upgrade preserved all 16 restored customer rows. No development database downgrade occurred.
- **43 private PDF backup copies** matched their source SHA-256 hashes. The PDF copy includes the new synthetic evaluation files; the earlier pre-upgrade database dump intentionally does not. Treat that dump as a pre-upgrade recovery point, not a synchronized post-seed snapshot.
- Initial test execution could not reach the old PostgreSQL port. Windows rejected its bind; the local configuration was repaired to port **55433**. The launcher now reads the configured port and waits only for `pg_ctl`, avoiding the previous descendant-process wait issue.
- One existing Starlette/TestClient `httpx` deprecation warning remains. It does not fail these tests. The future `httpx2` migration was not folded into this feature change.

## Measured synthetic evaluation

Dataset v1: 20 customers, six months, 120 invoices, 115 expenses, 20 current/20 expired contracts, 30 questions; five pricing changes, five cost-increase/margin-decline pairs and five missing-cost cases. The 15 financial discrepancy labels count cost increase and margin decline separately.

| Metric | Observed result |
| --- | --- |
| September contribution golden cases | 20 / 20 correct, including unavailable results |
| Financial rule detections | 15 true positives, 0 false positives, 0 false negatives |
| Rule precision / recall on this fixture | 1.0 / 1.0; not a real-world accuracy claim |
| Held-out answerable questions | 15 (ten lexical, five paraphrases) |
| Baseline BM25 recall@3 / MRR | 0.6667 / 0.3333 |
| Period-aware BM25 recall@3 / MRR | 0.6667 / 0.6667 |
| Baseline / context precision of returned results, up to 3 | 0.3333 / 0.6667 |
| Unsupported-topic empty retrieval | 5 / 5 in both modes |

The context filter improves ranking and excludes expired contracts in this deliberately constructed corpus. It does **not** improve recall: both approaches miss five paraphrase queries. A neural retrieval experiment may be justified by this gap, but no embedding improvement or quantization benefit has been claimed. Per-query ranking times are in the result JSON; they exclude database/network/provider costs and are not application latency measurements.

Reproduce with `python -m profitlens.evaluation --output data/exports/evaluation.json`. [Recorded run](evaluation-results-2026-10-15.json). [Dataset and demonstration guide](ANALYSIS_GUIDE.md).

## Important implementation decisions

1. **Completeness before confirmed profitability.** Recorded values can be shown provisionally; confirmed period comparisons require cost attestations. Updates to expense IDs, amounts or provenance invalidate the stored review hash.
2. **Separate price from refunds.** A contractual pricing mismatch compares pre-refund billed charges, avoiding a false price alarm merely because a refund reduced net revenue.
3. **Permissions before ranking and generation.** Both retrieval modes retain customer/organization authorization. Saved history is authorized on every read. Revoked access or changed evidence during generation prevents a stale/private result being returned.
4. **Constrained explanations.** Models select supplied metrics, findings and exact quotes. No unchecked free-form prose is promoted to a financial conclusion. Exact substring checks cannot establish relevance; user review remains required.
5. **No decorative quantization claim.** There is no embedding model/GPU dependency in the delivered retrieval path. The unused nullable `embedding` schema field reserves a possible extension but is not used by indexing or search.
6. **Safe local evolution.** Three additive tables and a separate evaluation workspace preserve existing business records. The prior presentation artifacts and historical viva PDF were left unchanged.

## Known limitations and next actions

- Keep provider credentials only in ignored backend `.env`. The later chat follow-up used a configured model for a small synthetic smoke check; the publishable environment example retains empty key fields.
- Live model relevance/selection quality is unverified. Validate normal questions, unsupported questions, prompt injection, provider timeout and malformed output with the selected real model; retain exact evidence and human judgments.
- Run Docker build/Compose/HTTPS smoke tests on the intended host. Verify persistent file permissions and recovery as a complete database-plus-files backup pair. Container files and operational instructions are preparation, not a successful deployment.
- BM25 misses paraphrases. If adding neural embeddings, evaluate on the unchanged held-out questions and record hardware, memory, latency, relevance and failure cases before considering quantization.
- Existing authentication is local accounts/sessions; no SSO/MFA/reset workflow. Private storage is local, bounded and single-node. No production load, retention policy, cloud object storage or independent penetration test was completed.
- The UI exposes default thresholds; custom thresholds are API parameters, not persisted user settings. Search is capped at 2000 candidate passages, investigations at 100 financial source rows, reindex at 200 documents, history at 50 entries, customer pickers at 200 customers.
- Source links authorize at click time. Evidence already sent to a provider before a later permission revocation cannot be recalled. The application never claims otherwise.

The local demo supports a defensible presentation of deterministic financial analysis, permission-scoped retrieval and output verification. Full production readiness and real-model effectiveness remain separate, explicitly unverified claims.
