# PHASE 19.2 — Data Acquisition Report

Date: 2026-08-20

Summary:
- This report documents availability and basic validation outcomes for the three inbound SEO CSV sources: GSC Performance, Indexing/Coverage, and GA4 Traffic. All checks performed are read-only and limited to `seo_data/*` and `docs/*`.

Sources:

1) GSC Performance — `seo_data/gsc/performance.csv`
- Status: NOT AVAILABLE (header-only; no data rows present)
- Header: Query,Page,Clicks,Impressions,CTR,Position,Country,Device,Date
- Row count: 0 data rows
- Date range: NOT AVAILABLE
- Notes: CSV readable; encoding appears UTF-8. See `seo_data/gsc/performance.meta.json` for recorded metadata and checksum placeholder.

2) Indexing/Coverage — `seo_data/indexing/coverage.csv`
- Status: NOT AVAILABLE (header-only; no data rows present)
- Header: URL,Status,Reason,LastCrawl
- Row count: 0 data rows
- Date range: NOT AVAILABLE
- Notes: CSV readable; encoding appears UTF-8. See `seo_data/indexing/coverage.meta.json`.

3) GA4 Traffic — `seo_data/ga4/traffic.csv`
- Status: NOT AVAILABLE (header-only; no data rows present)
- Header: Date,PagePath,Sessions,Users,EngagementRate,Conversions
- Row count: 0 data rows
- Date range: NOT AVAILABLE
- Notes: CSV readable; encoding appears UTF-8. See `seo_data/ga4/traffic.meta.json`.

Checksum verification:
- All three files were hashed (SHA256) and matched the `checksum_placeholder` values currently recorded in their `.meta.json` files.
  - `seo_data/gsc/performance.csv` SHA256: C06EE21C5B226DACA9F625EB955D68113F418B84F146BD6CC88C8FC9C768F978
  - `seo_data/indexing/coverage.csv` SHA256: 88C4D2C87D4B7D35D6653B04225366DC351C1D8A31B39583FE67CBABC68727C5
  - `seo_data/ga4/traffic.csv` SHA256: 2945ADB703FF32A91BA563ECB500DAC138CDADFF8567241033120B5A32A209E4

Validation summary:
- Header conformity: Headers match expected schema from `docs/SEO_DATA_IMPORT_SCHEMA.md`.
- Data completeness: FAIL for all three sources (no data rows). Marked NOT AVAILABLE.
- Date overlap checks: N/A (no date values present).
- Duplicate/malformed rows: N/A (no data rows present).

Next steps / Recommendations:
- Request raw exports (GSC performance, GSC indexing/coverage, GA4 page-level) from site owner and place under `seo_data/` with companion `.meta.json` populated.
- Re-run the validation checklist in `docs/SEO_DATA_VALIDATION_RULES.md` once real export rows are present.

