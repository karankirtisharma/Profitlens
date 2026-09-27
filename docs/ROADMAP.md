# Twelve-week delivery plan and progress

The repository started in **Week 1**. Status labels below describe implementation state, not college approval. A week is complete only when its acceptance evidence exists in code or documentation and has been checked.

| Week | Focus | Acceptance evidence | Status |
| --- | --- | --- | --- |
| 1 | Project foundation and ingestion | Repository guide, data contracts, validated customer/invoice/expense CSV preview, PDF text extraction, tests | Complete (2026-09-27) |
| 2 | Storage | PostgreSQL schema and migrations for organizations, customers, periods, invoices, expenses, contracts, imports; idempotent import persistence | Planned |
| 3 | API and access | FastAPI endpoints, authentication, organization membership and role checks, cross-tenant denial tests | Planned |
| 4 | Business workflows | Create/list/detail workflows for core records and contract upload; import errors visible to users | Planned |
| 5 | Profitability | Code-based net revenue, attributed costs, contribution, margin; tax/discount/refund/duplicate/zero-revenue/missing-cost tests | Planned |
| 6 | Findings | Explainable pricing mismatch, cost-spike, and margin-decline rules with traceable records | Planned |
| 7 | Contract retrieval | Page-linked PDF passages, embeddings, pgvector index, semantic baseline | Planned |
| 8 | Context engine | Customer and period filters, role-aware retrieval, context-pack provenance and denial tests | Planned |
| 9 | AI investigation | Provider abstraction, evidence-linked answers, abstention on insufficient data, prompt/evidence logging | Planned |
| 10 | Product UI | Next.js dashboard, customer profitability, finding detail, investigation view, responsive and accessible states | Planned |
| 11 | Evaluation | Synthetic cases, retrieval baseline comparison, anomaly/answer metrics, quantized versus unquantized embedding study | Planned |
| 12 | Integration and presentation | End-to-end demo, security/regression checks, deployable prototype, project report and limitations | Planned |

## Week 1 progress

- [x] Define the 12-week scope and current repository structure.
- [x] Document CSV fields, validation rules, provenance, and financial edge cases.
- [x] Add a local CSV/PDF ingestion preview and focused tests.
- [x] Verify the first GitHub push and repository description.

**2026-09-27 evidence:** Initial `main` push succeeded; the GitHub About description was set. The local preview passed its synthetic example and focused CSV/PDF tests. The preview links records by customer and billing period and warns about unmatched periods; it does not persist data or calculate profitability.

Do not mark a future week complete merely because it has design notes. Record date, evidence, and any plan change here when a milestone is completed.
