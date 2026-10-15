# ProfitLens project brief

**Title:** ProfitLens: An AI-Driven Context-Aware Business Profitability and Decision Intelligence System

**Course:** COM-711 Minor Project

**Duration:** 12 development weeks

**Team:** Group project; membership is managed through the college process

**Current implementation (15 October 2026):** the existing workspace now adds contribution/margin, cost review, discrepancy rules, permission-scoped BM25 retrieval and extractive AI integration with deterministic checks. A bounded live synthetic evidence-selection evaluation is recorded; broader conversational quality and container deployment remain unverified. [Current implementation and checks](MINOR_SCOPE_RELEASE_REPORT.md).

## Problem and proposed solution

Small businesses often keep contracts, invoices, customer records, and costs in separate files. This makes it hard to explain a falling customer margin or detect a contract price that was not reflected in billing. ProfitLens will join these sources by organization, customer, and billing period; compute profitability in code; flag reviewable anomalies; and present evidence-linked AI explanations to authorized users through a web application.

## Academic contribution

The contribution is the integration of validated inputs, deterministic financial analysis, permission-aware retrieval and checked explanations. The current benchmark compares period-aware BM25 with the same permission-scoped BM25 search without temporal filtering. It does not establish semantic answer quality. Embeddings and quantization are deferred until a pretrained retrieval model is justified by measured need.

## V.E.T.S. fit

| Dimension | How the project addresses it |
| --- | --- |
| Viability | A bounded 12-week prototype, synthetic data, staged delivery, and a tested application foundation with persistent business workflows. |
| Engineering depth | Exact financial rules, import provenance, database constraints, organization/customer permissions, retrieval, and verifiable AI output. |
| Trend alignment | Document search, context-aware retrieval, grounded generative AI; a model-efficiency experiment is optional and needs a justified retrieval model. |
| Social/industrial impact | Helps smaller businesses investigate pricing and cost issues while keeping decisions and evidence review with people. |

## 12-week deliverable

The target prototype supports authenticated organizations and preset roles; customer, invoice, expense, and PDF contract workflows; a profitability dashboard; three explainable anomaly categories; and evidence-linked investigations. The saved 15 October evaluation uses 20 customers, six billing months, 120 invoices, 115 expenses, 40 contract PDFs and 30 business questions, with 15 labelled anomaly positives. These are saved synthetic-fixture counts, not real-company data or a new test run. Real component data stays separate; live answer quality and final end-to-end acceptance still need evaluation. ProfitLens is not an accounting authority; results and opportunity estimates require human review.

## Out of scope

Payment/bank reconciliation or execution, vendor/AP accounting, payroll, inventory, timesheets/projects, shared-cost allocation engines, arbitrary industry modules/forms/roles, production tax/FX accounting, autonomous decisions, real-time enterprise connectors, OCR, custom model training and forecasting are outside this minor project. Reuse existing authentication, tenant isolation and supported CSV/PDF workflows. Two reviewed CSV layouts OR XLSX may be considered after core readiness; public hosting and quantization are not mandatory.

## Acceptance evidence

- Repeatable import and validation of representative CSVs and text-based PDFs.
- Verified contribution and margin calculations, including documented edge cases.
- Cross-organization and role-access tests that prevent unauthorized retrieval and AI context exposure.
- Traceable rule alerts and AI explanations with source references or explicit uncertainty.
- Reproducible synthetic evaluation: calculation accuracy, anomaly precision/recall, retrieval ranking and verification failure cases. Live answer relevance and full response time require separate measurement. Quantization is conditional on introducing a justified embedding model.
- Working end-to-end demonstration and clear limitations.

## Active scope and remaining work

The [minor-project SRS](requirements/SRS.md) and [completion roadmap](implementation/phased-roadmap.md) replace the expanded platform proposal. Preserve working features; prioritize core regression checks, focused fixes, evaluation and the faculty demo. Larger architecture research is archived for future work. This scope revision changes documentation only.
