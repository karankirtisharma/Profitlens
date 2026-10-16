# Richer genuine-data demo: verified source selection

Inspected 16 October 2026. **Partial result: a richer real sales dataset is downloaded and sampled; a complete linked customer/invoice/cost/contract dataset is not verified. No hosted records were changed.**

## Selected source

[UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail), Daqing Chen (2015), DOI [10.24432/C5BW33](https://doi.org/10.24432/C5BW33), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). UCI describes transactions of an actual UK non-store retailer, including wholesale customers. Currency is documented as sterling. Customer names are not supplied.

Original download: <https://archive.ics.uci.edu/static/public/352/online%2Bretail.zip>. The original archive is preserved unchanged, with SHA-256, byte size, attribution and download timestamp in the private manifest. Download was capped at 26 MB; actual size is 23,715,478 bytes. No account, payment or external AI upload was used.

## Measured contents

| Measurement | Actual inspected result |
|---|---:|
| Source transaction lines | 541,909 |
| Distinct invoice/cancellation identifiers | 25,900 |
| Distinct known customer identifiers | 4,372 |
| Missing-customer lines | 135,080 |
| Cancellation lines | 9,288 |
| Nonpositive quantity or price lines | 11,805 |
| Invoice groups containing exact duplicate lines | 1,933 |
| Selected complete sales invoices | 110 |
| Selected customers | 104 |
| Selected source lines | 1,364 |
| Selected months | January–November 2011 |

Quality counts overlap; do not add them as disjoint exclusions. The publisher page says no missing values, but the actual workbook contains missing customer IDs. Code/data inspection takes precedence for this audit.

## Reproducible sample and mapping

`scripts/datasets/uci_inspect.py` reads the original XLSX archive without changing it. It selects the first ten eligible complete invoices in each month, restricted to at most thirty lines per invoice. It excludes cancellation/non-numeric invoice identifiers, missing customer IDs, nonpositive quantity/price, duplicate-line ambiguity and inconsistent customer/date within an invoice. This deliberate demo selection is **not a representative sample or a business-growth benchmark**. Equal monthly invoice counts reflect sampling, not real activity.

| Original field | Preserved sample meaning / future mapping |
|---|---|
| InvoiceNo | Original invoice identifier; group all its lines before invoice import |
| CustomerID | Exact anonymous customer identifier; no name-based linking |
| InvoiceDate | Excel serial converted to timestamp; calendar month derived; timezone not supplied |
| Quantity, UnitPrice | Original stored numeric strings retained; their Decimal product is reported line value, not asserted net revenue |
| StockCode, Description, Country | Preserved source context; no guessed industries or vendors |
| Worksheet row | `source_row` points back to original workbook |
| Tax, discount, linked refund | Not provided; no zeros invented |
| Expenses, contracts | Not provided; no synthetic or council records joined |

Some XLSX numeric strings contain binary floating-point storage artifacts. Raw Decimal products preserve those strings; they are not a verified invoice payable amount. Currency rounding policy needs an explicit review before import.

Files are Git-ignored under `D:\Profitlens\data\private\uci-online-retail\`:

- `online-retail.zip`: unchanged original workbook archive.
- `manifest.json`: source, licence, size, download date and original hash.
- `inspection.json`: measured audit and selection rules.
- `source-linked-sales-sample.csv`: the 1,364 preserved source lines. **Not a ProfitLens-ready invoice CSV.**

Run `python scripts/datasets/uci_inspect.py` from the project root after obtaining the original archive. Inspection completed successfully; no dashboard import or financial reconciliation test is claimed.

## Why it cannot honestly fill every existing graph

The current canonical invoice format expects subtotal, discount, tax, refund and total with a known identity. This source supplies quantity and price without that accounting breakdown. Importing it with invented zero tax would misstate certainty. A safe future sales adapter would need a distinct reported-sales basis and explicit unknown-tax status, with net revenue/profit unavailable until supported. That adapter was not implemented in this source-selection task.

No source cost ledger, allocation or contract evidence exists here. Do not create expenses from an arbitrary percentage of sales, treat charged freight as verified supplier cost, attach unrelated council contracts, or rename anonymous IDs into fictitious real businesses. Keep FHDC as a separate public-expense import example, not the main complete financial demo.

## Other sources checked

| Source | Finding and decision |
|---|---|
| [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) | Real two-year retail transactions and CC BY 4.0, but the same missing cost/contract problem; avoided a second larger download. |
| [Olist publisher listing](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) | Candidate linked commerce dataset. Publisher content was not readable through this research tool; no newly verified licence/field semantics or download claimed. Orders/payment/freight are not automatically invoices/attributed costs. |
| [Mendeley invoice clearing](https://data.mendeley.com/datasets/28rbmvwsm9/1) | Real-source pseudonymous debtor/creditor invoices, CC BY 4.0 with publisher data-use caveat. Does not establish customer-attributed costs or contracts; no download. |
| [Open Contracting specification](https://standard.open-contracting.org/latest/en/primer/how/) | Linked procurement stages can support contract investigations. A supplier's internal costs are not established by a buyer's procurement payment. The standard is not a licence for each publisher's records. |
| [Contoso repository](https://github.com/usrbinr/contoso) | Explicitly fictional/synthetic. Not an acceptable substitute for the user's genuine-data requirement. |

The remaining all-feature real-data route is a permissioned, anonymized business export containing sales invoices, attributable costs and actual agreements. It need not be large: a few customers over several periods are enough if relationships and accounting meaning are verifiable. Existing separate synthetic fixtures can test the implementation, but cannot be presented as those real business records.

## Follow-up: explicit linked-data search, 16 October 2026

The user rejected another incomplete substitute and requested an all-feature real dataset before dashboard publication. No replacement workspace was created.

### ACT Government: actual files and link audit

Official sources: [Notifiable Invoices Register](https://www.data.act.gov.au/d/kzmf-7uhp), [Contracts Register](https://www.data.act.gov.au/d/pfs5-8d64). Both official metadata endpoints identify **Creative Commons Attribution 4.0 International**, attributed to ACT Government.

Downloaded original API responses, each capped at 5 MB, to private `data/private/act-linked-source-audit/`:

- Both official dataset metadata JSON responses.
- All 2,374 rows returned by the contract query (limit 3,000).
- An initial historical referenced-payment query returned zero rows; this was not treated as evidence that the entire register is empty.
- A second query without that date restriction returned 1,000 invoice-payment rows with contract references.

Exactly **13 payment rows matched 2 contract records** using equal contract numbers plus supplier ABNs after removing identifier formatting characters. No name similarity was used. These are **link candidates**, not verified contract-compliance conclusions: date applicability, amendments and invoice details still require review. Original response bytes, request URLs, byte counts, hashes and the audit are retained privately in `manifest.json` and `link-audit.json`; the second response's provenance is inside `link-audit.json.second_query`.

The actual invoice-payment schema contains supplier name/ABN, reporting entity, description, received date, payment date, payment amount and contract number. It contains **no supplier delivery costs**, customer cost allocations, original invoice-number field, or invoice tax breakdown. The contract schema includes aggregate contract amounts, dates and GST-inclusion labels, not a reviewed monthly billing schedule. Therefore this source supports a procurement-payment/contract study, **not the full customer-profitability demonstration requested**. Do not turn the same payment into both customer revenue and delivery expense.

### Other newly investigated candidates

| Candidate | Primary evidence | Decision |
|---|---|---|
| SAP SALT | [SAP repository](https://github.com/SAP-samples/salt), [original paper](https://arxiv.org/html/2501.03413v1): authentic enterprise-origin data, scoped to sales orders, order items, customers and addresses; CC BY-NC-SA listed by repository. | Sales orders are not invoices; no verified full cost ledger or contract evidence. No large download or import. |
| BPI Challenge 2019 | [Publisher record](https://figshare.com/articles/dataset/BPI_Challenge_2019/12715853): purchase-order process events and invoice matching; source describes transformed monetary values. Direct page fetch returned 403; no attempt to bypass. | No verified sales/cost/contract-document package suitable for this demo. No download. |
| Open Collective | [Official expense documentation](https://documentation.opencollective.com/advanced/ledger/expenses-in-the-ledger), [public expense privacy notice](https://opencollective.com/ubuntu/expenses): invoices can be expense records; attachments and payment details are private to authorized participants. | Public activity is not a licensed full customer-profitability ledger. Did not access private attachments or recast donations as customer sales. |
| FieldServio | [Official dataset catalogue](https://standpoint.atlassian.net/wiki/spaces/FPK/pages/2369978401/Datasets%2Bfor%2BData%2BAnalytics) describes contract-invoice, invoice-cost/tax, jobs and vendor-bill relationships. | Potentially the right kind of permissioned business export, but this is product documentation, **not a publicly downloadable licensed company dataset**. No access or data availability claimed. |
| San Francisco procurement | [Official federal catalogue: vendor payments](https://catalog.data.gov/dataset/vendor-payments-vouchers), [contracts](https://catalog.data.gov/dataset/supplier-contracts) describe contract/PO/voucher expenditure chains. | Buyer expenditure does not establish supplier delivery costs or margin. Not imported as customer profitability. |

**Result:** More precise linked procurement evidence was found and tested, but no candidate passed all required gates: genuine reusable records, linked sales invoices, independently evidenced customer costs, applicable contract evidence, compatible financial semantics. The full-demo dataset and dashboard-import request remains unfulfilled. No production mutations, external AI calls, invented records or synthetic substitutions were performed.

## Kaggle, GitHub and Hugging Face targeted search

Checked 16 October 2026 at the user's explicit request. Queried public catalog APIs as well as web search. Inspected dataset cards/file listings before considering downloads. No incomplete workspace was added.

| Platform / candidate | Verification | Result |
|---|---|---|
| Kaggle: [Calgary bookstore financial dataset](https://www.kaggle.com/datasets/gabriellecharlton/bookstore-financial-dataset-2019-2024-calgary) | Official Kaggle API description explicitly says fully synthetic. | Reject as genuine company records. |
| Kaggle: [Contracts to Invoices Conversion](https://www.kaggle.com/datasets/eduardbalamatiuc/contracts-to-invoices-conversion-pdf-to-json) | Metadata and first file-list page retrieved. Lists contract PDFs; metadata identifies CC BY-NC-ND 4.0. Description was empty. Attempted individual contract download returned 404, so no PDF inspection claimed. | Genuine-company provenance, expense ledger and all-three links unverified. Title alone does not establish suitability. Did not fetch the full archive. |
| Kaggle: [SAP replicated training dataset](https://www.kaggle.com/datasets/mustafakeser4/sap-dataset-bigquery-dataset) | Description identifies cloud-training-demos and says it mimics/simulates enterprise scenarios. | Not verified genuine company history. |
| GitHub: [Procurement Analytics](https://github.com/Theophilusehimegbe/procurement-analytics) | Read repository README via official GitHub API. Describes purchase-order spend, contract identifiers and invoice status. | No verified provenance/licence for a full real company sales/cost/contract package; purchase-order spend is not a supplier's attributable delivery cost. |
| GitHub: [construction-company operations database](https://github.com/abdullahahmadd/construction-company-operations-database/) | Publisher describes generated data simulating company operations. | Synthetic, not a qualifying replacement. |
| Hugging Face: [US SME Business Dataset](https://huggingface.co/datasets/vedrowjee/us-sme-business-dataset) | Dataset card says generated by simulating a retailer over two years; commercial licensing noted. | Synthetic, despite realistic relational tables. |
| Hugging Face: [VynFi audit P2P](https://huggingface.co/datasets/VynFi/vynfi-audit-p2p) | Card explicitly identifies synthetic general-ledger data. | Reject as genuine company records. |
| Hugging Face: [Finch](https://huggingface.co/datasets/FinWorkBench/Finch) | Card lists CC BY 3.0. Downloaded and searched 172 task descriptors. Inspected three source workbooks: task 25 (62,908 bytes), 131 (23,512 bytes), 169 (56,387 bytes). | Promising real-world-derived financial workflows, but no verified complete linked case. See below. |
| Hugging Face: [document-processing benchmark](https://huggingface.co/datasets/thoughtworks/document-processing-benchmark) | Card describes combining separate invoice, receipt and contract corpora into a document benchmark. | Shared file schema is not shared company identity or transaction linkage. No multi-gigabyte download. |

Finch task 25 contains Enron-labelled service-invoice/imbalance/settlement sheets and contract-number labels. Task 131 contains a Beaumont worksheet with contract-price and invoice-total labels. Task 169 contains ISO settlement certification schedules. Those labels do **not** verify that these separate tasks describe the same customer/project, independently recorded delivery expenses or signed applicable contract terms. No cross-task joins or assumptions that benchmark-modified inputs are untouched company records were made. These three files were inspected only and never uploaded to ProfitLens or an AI provider. Task instructions inside them were treated as dataset content, not executed.

Inspection evidence is private under `data/private/platform-dataset-search/`: dataset metadata snapshots, the Finch task index, three original workbook responses and the Kaggle file-list snapshot. A console encoding error during one search was corrected and the request rerun; this was not a source-access failure.

**Decision remains: no qualifying all-three real-company source verified, no dashboard mutation.** This search is evidence of checked candidates, not proof that no suitable dataset exists anywhere.
