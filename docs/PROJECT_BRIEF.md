# Project brief

**Title:** ProfitLens: An AI-Driven Context-Aware Business Profitability and Decision Intelligence System

**Course:** COM-711 Minor Project

**Duration:** 12 weeks
**Team:** Group project; team membership is managed through the college process

## Problem and proposed solution

Small businesses often keep contracts, invoices, customer records, and costs in separate files. This makes it hard to explain a falling customer margin or detect a contract price that was not reflected in billing. ProfitLens will join these sources by organization, customer, and billing period; compute profitability in code; flag reviewable anomalies; and present evidence-linked AI explanations to authorized users.

## Academic contribution

The project combines four engineering threads: validated multi-format ingestion, robust deterministic financial analysis, tenant- and role-aware retrieval, and evaluated evidence-grounded generation. A controlled comparison will test whether customer/period-aware retrieval improves relevance and answer support over a basic semantic baseline. A quantized embedding option will be compared with an unquantized counterpart for memory use and retrieval quality, subject to a feasible model and hardware setup.

## 12-week deliverable

The target prototype supports synthetic organization data, roles, customers, invoices, expenses, PDF contracts, profitability views, rule-based findings, and evidence-linked investigations. Evaluation will use a prepared synthetic dataset and known answers. It is not an accounting authority; results and opportunity estimates require human review.

## Out of scope

Banking/payment execution, payroll, production accounting compliance, autonomous decisions, real-time enterprise connectors, custom model training, and forecasting are outside this project.

## Acceptance evidence

- Repeatable import and validation of representative CSVs and text-based PDFs.
- Verified contribution and margin calculations, including documented edge cases.
- Cross-organization and role-access tests that prevent unauthorized retrieval and AI context exposure.
- Traceable rule alerts and AI explanations with source references or explicit uncertainty.
- Reproducible evaluation on synthetic cases: calculation accuracy, anomaly precision/recall, retrieval relevance, answer support, and response time; quantization comparison where feasible.
- Working end-to-end demonstration and clear limitations.
