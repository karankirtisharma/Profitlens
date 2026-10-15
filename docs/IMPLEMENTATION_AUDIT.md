# ProfitLens roadmap audit

Audit date: 15 October 2026. Baseline: `fa1e0f2` (Weeks 1–4).

## Observed before implementation

| Area | Evidence | Actual status |
| --- | --- | --- |
| CSV and PDF ingestion | `ingestion/`, `imports.py`, ingestion and workspace tests | Implemented, bounded validation and preview/confirm |
| Persistence and security | `database.py`, `security.py`, initial Alembic revision | PostgreSQL, organization/customer authorization, sessions, private PDF routes |
| Business workflows | `main.py`, Next.js workspace, browser tests | Record create/read/update, atomic imports, reviewed monthly contract terms |
| Financial foundation | `finance.py`, `test_finance.py` | Decimal revenue and recorded cost, quality warnings, source lines |
| Contribution and margin | No implementation in baseline | Week 5 missing |
| Economic discrepancies | No pricing/cost/margin rules in baseline | Week 5 missing; quality warnings are not economic findings |
| Search and RAG | PDF pages exist, no retrieval/index modules | Weeks 6–7 missing |
| AI investigations | Mascot says under development, no provider | Weeks 8–9 missing |
| Evaluation and deployment | Unit/API/browser suites and local launcher exist | Existing checks reused; retrieval comparison and production packaging missing |

The existing roadmap records 53 Python and 13 browser checks on 11 October. These are historical results until rerun. Presentation files are unrelated untracked user artifacts and are preserved.

## Implementation decisions

- Extend the existing modular FastAPI/Next.js/PostgreSQL application, retaining the Week 4 revenue/cost endpoint.
- Add profitability separately so existing callers and tests retain their contracts.
- Record cost-completeness attestations against a hash of the expense inputs. Editing or importing costs invalidates old attestations automatically. Unknown costs never become zero.
- Separate quality warnings, provisional calculations and explainable economic findings.
- Retrieve only authorized source pages. Record passage hashes, model versions and effective periods; check historical evidence against current permissions and content.
- Financial numbers remain deterministic. AI output is bounded, schema-validated and checked against the exact authorized context. Valid citation IDs alone do not establish semantic support.
- Compare contextual retrieval with an equally permission-scoped baseline on frozen synthetic questions. Quantization is conditional on a real model/resource need, per the latest request.
- No multi-industry expansion, service purchases or public deployment is included.

New verification and remaining limitations will be recorded in `COMPLETION_REPORT.md` after the milestones are exercised.


Implementation and verification outcome: see [Roadmap implementation report](ROADMAP_IMPLEMENTATION_REPORT.md). This audit records the pre-change baseline; it is not the final feature status.
