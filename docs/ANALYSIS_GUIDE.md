# Profitability and evidence investigations

Updated 15 October 2026. These additions preserve the Week 4 `/finance` API and existing import/edit workflows.

## Run and demonstrate

The bottom-right ProfitLens bot opens an actual AI conversation inside the popup. Automatic scope is the default: ask across accessible customers, name a customer, or specify a month naturally. “This month” uses the current calendar month in India; missing records never cause a silent fallback to an older month. Ask explicitly for the latest available month when needed. **Use manual filters** is a separate optional mode; a blank month there uses the latest available reporting period. Changing customer/month or workspace clears the conversation. Closing/reopening the popup retains it; refreshing or signing out clears it. Conversations are not saved in local storage or the database.

Chat requires a configured provider: there are no canned business answers or offline AI substitutes. Failed requests show an error and restore the draft for retry. Enter sends; Shift+Enter adds a line; Escape closes and returns focus to the mascot. Replies support bold headings, bullets and labelled green/red/amber financial cards. Related buttons open existing financial, analysis, invoice, expense, contract and import screens; permissions still apply. Source excerpts, private PDF links, invoice/expense IDs and findings appear under **View supporting records**. Chat does not edit data or confirm costs itself.

1. Install the locked Python dependencies and web dependencies using the existing development guide. Run `python -m alembic upgrade head` before starting the API.
2. Existing PDFs need a one-time **Index existing contracts** action in **Profitability & evidence**. New uploads are indexed automatically. Indexing does not review contract terms.
3. Optional reproducible data: `python -m profitlens.evaluation_demo --seed`. It requires the previously provisioned synthetic demo owner and creates a separate **ProfitLens Evaluation (synthetic)** workspace. A repeated seed preserves all existing edits. It does not change the original demo workspace.
4. Choose that workspace, open **Profitability & evidence**, select `EVAL-01`, month `2026-09`, and **Load analysis**. Expected revenue 1200, direct costs 400, contribution 800, margin 66.67%; a pricing mismatch references the reviewed 1000 monthly charge.
5. `EVAL-06` shows a cost increase and margin decline; `EVAL-11` has missing costs and unavailable contribution; `EVAL-16` is a control. April–September costs are explicitly attested only where the synthetic fixture contains expenses.
6. Search “What does the payroll monthly delivery agreement cover?” for `EVAL-01`. The current PDF should be cited with its page. Expired terms are excluded in context mode.
7. With AI disabled, **Generate with configured AI** shows an explicit provider-unavailable state; it does not invent a response. Missing costs or contract evidence produce insufficient-evidence without calling a provider.

Ready-to-import CSVs/PDFs and labels are in `demo-files/evaluation/`. Import customers, then invoices and expenses. Attach each PDF to its matching customer; manually review current terms before context retrieval. Importing into a different workspace does not transfer the seed's cost attestations.

## Optional OpenRouter / NVIDIA configuration

Edit the repository-root **ignored `.env` locally**. Do not put credentials in chat, screenshots, source control or any `NEXT_PUBLIC_` variable.

```dotenv
AI_PROVIDER=openrouter
AI_MODEL=openai/gpt-4.1-mini
OPENROUTER_API_KEY=your-new-local-secret
AI_TIMEOUT_SECONDS=30
```

Choose a model that supports strict JSON-schema output. For NVIDIA hosted NIM use `AI_PROVIDER=nvidia`, its model ID and `NVIDIA_API_KEY`. NeMo training tooling is not integrated. Restart the API after configuration changes. `GET /api/workspaces/{org}/ai/status` reports configuration only; it never exposes the key or proves a live connection.

Provider hosts are fixed to OpenRouter and NVIDIA's hosted endpoint. No user-supplied URL is fetched. OpenRouter requests require parameter support and deny routing through providers marked as collecting data. This is not a guarantee of zero retention: review the chosen provider's policies before using non-synthetic records. No credentials are needed for calculations or local retrieval.

Only authorized, bounded evidence is sent. The model returns metric claims, finding IDs and verbatim quotes. The backend verifies Decimal values and units, source membership and quote substrings. It renders a summary from verified metrics and shows cited quotes. Unchecked free-form model prose is deliberately excluded. Successful checks establish provenance/arithmetic, **not relevance, causation or business truth**. Live quality remains unverified in this delivery.

## Financial semantics

| Item | Behavior |
| --- | --- |
| Contribution | Net billed revenue minus recorded direct costs. Missing input → unavailable. Shared overhead allocation is not included. |
| Margin | Contribution / revenue × 100, rounded half-up to two decimals. Zero revenue → unavailable margin, not 0%. |
| Completeness | Provisional until admin/finance reviews the customer/month costs. An expense identity/value/source hash invalidates confirmation after changes. A matching review is an attestation, not an external audit. |
| Pricing mismatch | Compare summed subtotal minus discounts with one full-month reviewed rate minus monthly discount. Refunds are excluded from this price comparison; tax is excluded throughout. Ambiguous, partial or unreviewed evidence suppresses the rule. |
| Cost increase | Both periods confirmed, prior cost positive, increase exceeds configured percentage (default 25%). |
| Margin decline | Both periods confirmed, margins available, decline exceeds configured percentage points (default 10). |
| Tolerance | Pricing default is 1 currency unit; strict greater-than comparison. Thresholds are bounded API query parameters, not saved workspace preferences. |

No inferred zero costs, automatic proration, causal diagnosis, negative net revenue, currency conversion, recovery/savings promise or automatic financial action is supported.

## Added API surface

`POST /api/workspaces/{organization_id}/chat` accepts `automatic` (default false for API compatibility; true in the popup), `message` (1–1000 characters), optional `customer_id` and `billing_period`, and at most six history turns (role `user|assistant`, up to 3000 characters each). Only the last four turns, truncated to 700 characters each, go to the provider. Each turn reads fresh authorized data. The provider receives calculated metrics, up to five findings, ten warning codes and three retrieved excerpts of at most 1200 characters each—not full invoice ledgers or PDFs. Automatic mode adds a bounded query-planning call (350 output tokens) before the answer call (900 output tokens). The planner receives the authorized customer names/IDs (maximum 200), available month names, current date, question and recent history. There are no automatic retries, and twenty requests per workspace per minute limit consumption. A failed/aborted browser request may still incur a provider charge if generation already began.

Chat checks allowed metric placeholders, exact literal amount/unit matches and source/finding IDs; the server substitutes figures and copies source excerpts itself. It rechecks session/permissions and source hashes after the provider returns. Errors: 401/404 authentication/scope, 422 input/evidence limits, 429 rate limit, 409 changed data, 502 rejected evidence, 503 unavailable/unconfigured provider. It does not execute model-authored SQL or perform financial mutations. Natural-language interpretation is **not** verified for semantic correctness; valid numbers or source IDs do not prove the prose is correct. This conversational route differs from the stricter extractive `/investigations` route below.

The local chat uses [GPT-4.1 Mini on OpenRouter](https://openrouter.ai/openai/gpt-4.1-mini), selected for structured outputs and modest token cost. The model remains configurable in backend environment settings. A live synthetic profitability/follow-up/contract smoke check passed on 15 October 2026, including two real replies through the popup and a linked PDF. This is a connectivity/behavior check, not a quality benchmark. No semantic embedding or autonomous financial decision capability is implied.

All paths below start `/api/workspaces/{organization_id}` and require a valid session. Write requests also require the configured Origin.

| Method/path | Inputs and output | Access/errors |
| --- | --- | --- |
| GET `/profitability` | Optional `billing_period`, `customer_id`, limit≤100, offset; `cost_increase_percent`, `margin_decline_points`, `pricing_tolerance`. Returns exact amounts, status, source lines and findings. | Scoped users; 404 unknown/unassigned customer; 422 invalid/oversized inputs. |
| PUT `/profitability/{customer}/{period}/cost-review` | `input_hash`, meaningful `note`. Confirms the current expense inputs. | Admin/finance; 409 changed/absent/invalid costs; 403 analyst. |
| GET `/evidence/search` | `customer_id`, `billing_period`, `q`, `mode=context|baseline`, `k≤10`. Page references and lexical scores. | Both modes preserve organization/customer permissions; 422 >2000 candidate passages. |
| POST `/evidence/reindex` | Rebuild existing page chunks; returns document/passage counts and version. | Admin/finance; ≤200 documents per workspace action. |
| GET `/ai/status` | Provider, model, configured flag; no secret. | Workspace members. |
| POST `/investigations` | Customer, month, question≤1000 characters. Returns ID, evidence and result status. | ≤100 financial source rows; five requests/workspace/minute; 409 changed inputs during generation; no unchecked output. |
| GET `/investigations` | Optional customer filter; latest 50 visible metadata rows. Status is the saved status, not a fresh validity check. | Current permissions enforced. |
| GET `/investigations/{id}` | Revalidates evidence hash; returns result/evidence or a stale marker. | 404 inaccessible; changed evidence hides the old answer. |

Investigation statuses: `verified`, `insufficient_evidence`, `rejected`, `provider_unavailable`. A stale saved result has `stale=true` and `result=null`. Provider failures do not expose raw responses or credentials. Revocation during generation prevents the final answer from being returned; information already sent before revocation cannot be recalled from a provider.

## Evaluation

```powershell
.\.venv\Scripts\python.exe -m profitlens.evaluation --output data/exports/evaluation.json
.\.venv\Scripts\python.exe -m profitlens.evaluation_demo --export demo-files/evaluation
```

The fixed v1 dataset contains 20 customers, 120 invoices, 115 expense rows, six months, 20 current plus 20 expired contracts, 15 financial discrepancy labels, five missing-cost cases and 30 questions. Ten questions are development examples; twenty are held out from parameter tuning. Labels are synthetic, constructed from known fixture rules, not independent expert annotation.

The baseline is BM25 over the same authorized customer's documents; context mode additionally filters contract review/date coverage. This isolates the value of temporal context. Five paraphrase questions expose lexical misses; five unsupported-topic questions test empty retrieval. Precision uses returned results up to k=3, not a fixed denominator of three. Local ranking timing excludes database/network/model latency. No user study, live-model correctness score, production load result, semantic-search result or quantization benefit is claimed.


## Document-context correction — 15 October 2026

The popup chat now separates document summaries from validated monthly pricing. It can read authorized unreviewed or out-of-period PDFs as reference material, with explicit source badges. The stricter investigation retrieval and financial calculation rules still require reviewed, period-matched evidence. No upload, contract date or review flag is modified by chat.

The context includes up to six document metadata summaries and twenty-four available transaction months, plus the existing three-excerpt limit. A generic document question can receive a first excerpt even when its words do not match the PDF; this is document context, not a semantic-search result. Contract-only customers can receive document answers even with no financial records. Documents remain subject to organization/customer authorization, a fifty-document and two-thousand-passage bound, and post-generation snapshot checks.

Known dates, numbered-list markers and exact quoted document values no longer fail the financial-number guard. Quoted facts are distinct from calculated metrics: rates extracted from an unreviewed PDF are accompanied by an explicit unreviewed-pricing notice and linked original text. This verifies provenance, not the AI's interpretation or applicability. Unknown dates, invented amounts and foreign source IDs remain rejected. Chat does not approve terms or infer missing costs. Automatic mode selects the month requested by the question; it does not substitute a different month when data is missing.

Northstar Services examples: Northstar Studio's reviewed contract starts in September 2026 and ends in February 2027; it does not cover February 2026. Harbor Retail's uploaded contract is unreviewed. Both were successfully summarized through live OpenRouter calls with appropriate caveats. Regression verification: 100 Python tests passed; two targeted browser flows passed; TypeScript, ESLint and Ruff passed.


## Automatic workspace chat — 15 October 2026

The model selects an allowlisted read scope; the server validates the customer, month and optional record ID, then runs existing permission-filtered calculations. No generated SQL, ledger writes or new database migrations. Session/membership/customer access and snapshots are checked after planning and after answering. The selected workspace remains a boundary: chat never searches another organization on its own.

Workspace totals cover all visible customers with invoice or expense activity, up to 200 customers and the existing source-record bounds. A missing component makes that aggregate unavailable; contribution is not net profit. Aggregate margin is total contribution / total revenue, not an average of customer percentages. Cost completeness determines confirmed/provisional status. Ten prioritized customer summaries and at most three PDF excerpts keep context bounded; these lists are not exhaustive. Detailed ledger lines remain server-side and are opened through record buttons, not sent as new per-record model context.

Try “How is profit this month?”, “Check the latest available month; what needs review?”, “Explain EVAL-01 in September 2026”, then open a related record. Unsupported multi-month ranges ask for clarification. The planner adds latency and can misunderstand intent; inspect the displayed scope/month and use manual filters if needed. Natural-language interpretation still requires human review.

Verification for this update: 114 backend tests passed; both targeted Chromium flows passed, including automatic-scope payloads, optional filter reset, formatted cards, mobile layout, invoice-detail navigation and customer/month-prefilled analysis navigation. TypeScript, ESLint and Ruff passed. Real OpenRouter checks on the explicitly synthetic evaluation workspace covered current-month no-data, latest-month review, and customer analysis; two live browser replies and a PDF link passed. These are smoke checks, not a correctness benchmark. Northstar was not live-tested in this update.
