# Search for a complete genuine ProfitLens dataset

Checked: 15 October 2026. Requirement: genuine business records, explicit reuse rights, stable links between customer invoices, attributable expenses and contract evidence. The project owner explicitly rejected substituting an expanded synthetic dataset.

**Outcome:** Genuine public datasets were found, but no candidate verified in this search satisfies all of those conditions. No replacement dataset was imported and no synthetic records were added to the real-data workspace. This is a source-availability limitation, not a successful full-data import.

## Closest candidates and reasons they were not imported

| Candidate and primary source | Genuine-data evidence | Rights information | Missing requirement / decision |
|---|---|---|---|
| [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail), DOI 10.24432/C5BW33 | UCI describes actual transactions from a UK non-store retailer, December 2010–December 2011; 541,909 line records. | Explicit CC BY 4.0. | Has invoice/customer/product IDs, quantity, dates, sterling unit prices and country. No linked cost ledger, explicit VAT amounts or contracts. Would improve sales coverage, but cannot establish customer profit or pricing discrepancies. Do not assume missing tax is zero. Original 22.6 MB workbook not downloaded in this follow-up. |
| [Microsoft/obviEnce Customer Profitability](https://learn.microsoft.com/en-us/power-bi/create-reports/sample-customer-profitability) | Microsoft explicitly says obviEnce used real anonymized data; revenue, costs, customers and gross margin are present in the described model. | [Publisher terms](https://learn.microsoft.com/en-us/power-bi/create-reports/sample-datasets#legal-guidelines-for-using-samples) describe internal-reference use and sharing solely to demonstrate Power BI. Permission for a separate ProfitLens demonstration is not established. | Strongest candidate for profitability analysis, but neither source invoice/contract coverage nor appropriate ProfitLens reuse permission was verified. Do not convert reported aggregates into purported original invoices. Not downloaded/imported. |
| [Atomic Common-Day Invoice Clearing, Mendeley](https://data.mendeley.com/datasets/28rbmvwsm9/1), DOI 10.17632/28rbmvwsm9.1 | Publisher attributes the records to IMI/Ministry of Economics, Romania; pseudonymous invoice, debtor and creditor identifiers, integer euro cents and dates. | CC BY 4.0 listed. Publisher also notes that exact amounts/dates/network relations remain pseudonymized and mentions governing data-use agreements. | Described schema is suitable for payable/receivable network research, not verified customer-specific expense allocation or contract pricing. VAT breakdown and contracts are not established. No transaction download or import performed. |
| [Open Contracting Data Standard](https://www.open-contracting.org/data/) | Real procurement publishers can expose process IDs across tender, award, contract and implementation. | Licence must be verified for each publisher; the standard itself does not grant rights to every dataset. | Buyer-side contract/payment records do not establish a supplier's internal costs or profit. Cannot turn procurement payments into both revenue and costs for the same fictitious business. |
| [Existing FHDC council sources](REAL_DATA_DEMO.md) | Official transaction-level council expenditure; original files already inspected and reconciled. | Publisher explicitly identifies OGL v3. | Real expenses verified; no sales ledger, cost allocation or reliable contract linkage. Remains a separate real-data ingestion demo. |

## Attractive candidates rejected as synthetic

- [BookSQL's original paper](https://aclanthology.org/2024.naacl-long.28/): explains that names, businesses **and numbers** were replaced with fictional values while preserving accounting constraints. It must not be relabelled as unchanged real financial records.
- [Mercor APEX-Accounting dataset card](https://huggingface.co/datasets/mercor/apex-accounting/blob/0048883e4c7ce7451c0b32bb597d4ac7c1309184/README.md): explicitly describes self-contained synthetic company worlds.
- [Microsoft AdventureWorks](https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure): sample database, not verified original ProfitLens business transactions.

No large replacement dataset was downloaded simply to populate a dashboard with unrelated or unsupported values. No sample-data site, repository code licence or third-party tutorial was treated as proof that underlying transactions were real and reusable.

## Practical consequence

The current empty revenue and profit fields in the real FHDC workspace are correct: those inputs are absent. Filling every module with genuine evidence needs either:

1. A reusable source providing linked sales invoices, explicit taxes/refunds, attributable costs, billing dates/currency and matching customer contracts; or
2. Permission to use an anonymized export from an actual business with those fields.

Customer IDs can be pseudonyms. What matters is preserving the genuine amounts, dates and verified relationships. Company-wide costs cannot be silently allocated to customers; an unsigned template or unrelated contract register cannot stand in for an actual agreement. Contract rates must be reviewed from the source before financial mismatch rules use them.

Until those records or permissions are available, the report must distinguish real-source partial workflows from the existing separate synthetic financial benchmark. The requested all-feature genuine-data replacement remains **unfulfilled**, rather than being disguised as complete.
