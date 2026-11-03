# Project-change PDF and evidence snapshot - 3 November 2026

The six-page project briefing is a local-only study document. Generated PDFs are excluded from GitHub.

The final two pages contain executed test evidence and real-data validation. This is a dated snapshot of application commit `7402602`, not a claim that the new release is deployed.

## Evidence collected for this document

- Fresh local command: `python -m pytest tests/test_planning.py tests/test_showcase.py tests/test_real_refresh.py -q` using isolated test PostgreSQL through the private local runner.
- Actual result: `6 passed in 3.38s`.
- [GitHub CI run 41646449021](https://github.com/karankirtisharma/Profitlens/actions/runs/41646449021): `199 passed, 3 skipped in 18.13s`; browser suite `27 passed (3.2m)`. Logs were retrieved during document preparation. Three private-data tests are skipped when their files are absent in CI.
- Earlier full local suite: 202 passed in 19.50 seconds, recorded in the release guide; not repeated in full for this document.
- Private earlier hosted operations result: 47 checks passed, relating to the previous operations release only.
- Private migration check: revision `20261103_planning`; backup 402484 bytes; selected existing business values unchanged. Restoration not rehearsed.
- Fresh real-data test verifies 600 DWP expenditure rows, total GBP 539682013.66, monthly totals, retry safety, source references, byte-equal file download and tenant rejection. Data remains expenditure, not sales or profit.

## Publication boundary

PR #2 was open at report creation. API preview ready; frontend preview failed. Vercel team authorization was requested to inspect the failure. The new hosted demo publication has not run. Earlier demo archive labels are a prepared workflow, not a completed production action.

## Reproduce the document

`python scripts/reports/build_changes_report.py` requires ReportLab. Output is a six-page A4 PDF. All six rendered pages were visually inspected with Poppler; no clipped tables or text were observed. Links point to the actual CI run, PR and official dataset/licence pages. Source code contains this dated snapshot, not live status queries.

