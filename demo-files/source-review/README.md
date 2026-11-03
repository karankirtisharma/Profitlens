# Source review demo — synthetic only

These small files are invented QA fixtures. They are not real bank statements, real company records or evidence of business impact. Import them into a separate synthetic workspace in its declared currency. Do not mix them into the licensed real-data workspaces.

## Spending review
Upload `synthetic-monthly-spending.csv` under Source data & insights. Select **expenditure**, direct source amount, ISO dates, dot decimals, declared workspace currency. Review the proposed Date/Amount/Supplier/Description mappings, preview, then confirm.

Run Monthly business review for **2026-02 / Spending recorded**. Expected recorded January amount is 350.00; February is 440.00; observed difference 90.00. Demo Hosting explains a comparable +50.00 (160 less a 10 credit, compared with 100). Demo Contractor change is zero. Demo Tools has 40 only in February, so its change is **not comparable**, not an invented +40. The undated 5 is excluded from both months and counted as missing-date information. Driver rows deliberately do not claim to explain the entire total. Click Selected records to inspect exact source names/rows.

## Bank cash observations
Upload `synthetic-bank.tsv`; select **cash inflow**, then **Bank statement: separate money received / paid**. Review Credit as money received and Debit as money paid; Date is ISO. Reference and Memo may stay preserved but unmapped (map Memo to description if desired). Confirm only after reviewing all four rows. Expected money received 1500.00; money paid 325.50. These totals are not revenue, expenses or profit. Blank opposite-side cells are accepted only alongside one positive amount; double-sided, negative and empty/zero-only rows are rejected.

Re-uploading identical bytes returns the original document and does not add duplicates. Existing confirmed mappings are immutable. All originals remain accessible through authorized download.
