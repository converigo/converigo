# SEO Data Requirements

This document lists available and missing SEO/analytics data, required formats, export instructions for Google Search Console, and collection priorities. All work performed in read-only mode.

## 1. Data available (in repository)
- References to Search Console readiness & audit reports:
  - `brain/PROJECT_STATE.md`, `brain/NEXT.md`, `brain/EXECUTION_INDEX.md` reference `SEARCH_CONSOLE_READINESS_REPORT.md` (execution_020) and earlier audit reports (execution_018/019).
- SEO coverage and keyword readiness analysis:
  - `CONVERTER_SEO_COVERAGE_MATRIX.md` contains per-converter SEO coverage, missing `related_tools`, and keyword-readiness notes.
- Analytics instrumentation and local event storage path:
  - `ANALYTICS_IMPLEMENTATION_REPORT.md` documents analytics events and confirms instrumentation; `app/core/settings.py` references `analytics.jsonl` (append-only JSONL) as default log path.
- Code-level readiness/audit services present under `app/services/` (e.g., `search_console_readiness_service.py`, `seo_service.py`) and corresponding tests under `tests/`.

Notes: execution reports are referenced but the `outputs/` folder with generated report files or raw GSC/GA exports is not present in repository root (no GSC CSV/GA4 export files found in repo). Some generated/AI artifacts in `.tmp/` reference these outputs but do not replace official telemetry exports.

## 2. Data not available (missing from repository)
- Google Search Console (GSC) Performance export (Queries/Pages/Positions/Clicks/Impressions/CTR) — NOT found.
- GSC Coverage / Indexing export (index status, errors, blocked resources) — NOT found.
- GSC Rich Results / Structured Data report exports — NOT found.
- Google Analytics (GA4) raw export or BigQuery export for organic sessions by page — NOT found.
- SERP rank-tracking exports (Ahrefs/SEMrush/Rank Tracker) — NOT found.
- Backlink / referring domains raw export — NOT found.
- Crawl logs (server access logs mapped to Googlebot) — NOT found.

## 3. Format of data required (recommended)
1. GSC Performance (per day, last 90 days) — CSV or JSON with columns:
   - date (YYYY-MM-DD)
   - query
   - page (URL)
   - device (optional)
   - country (optional)
   - clicks
   - impressions
   - ctr (calculated or provided)
   - position (average)
2. GSC Page/URL Inspection / Coverage — CSV or JSON with:
   - url
   - index_status (indexed / not indexed)
   - status_detail (e.g., "Excluded by noindex", "Blocked by robots.txt")
   - last_crawl
   - canonical (if available)
3. GSC Rich Results / Structured Data report — CSV/JSON listing URLs and structured data status (error/warning/valid) and types (HowTo, Breadcrumb, WebPage).
4. Sitemap.xml — full sitemap index file and any generated sitemaps (XML). Provide as files or a URL to the sitemap index.
5. GA4 organic traffic by page (last 90 days) — CSV or BigQuery dataset with fields:
   - date
   - page_path or page_location
   - sessions
   - users
   - new_users
   - organic_sessions (or session attribution)
   - conversions (if applicable)
6. Rank-tracking export (3rd party) — CSV with:
   - date
   - keyword
   - page
   - position
   - volume (optional)
   - intent/category (optional)
7. Backlink report — CSV with:
   - source_url
   - target_url
   - anchor_text
   - domain_authority (if provided)
8. Crawl logs (server access logs) — raw log files (gz) with timestamps and user-agent (useful to isolate Googlebot requests).

## 4. How to export from Google Search Console (manual steps)
(Recommended: collect programmatically via API for reproducibility; manual CSV exports are acceptable for ad-hoc audits.)

A. Manual export (GSC web UI) — Performance report
1. Open Google Search Console and select the verified Property for `https://converigo.com`.
2. Click on "Performance" in the left nav.
3. Set the date range (recommended: Last 90 days).
4. Optionally filter by Query or Page (or export all rows by selecting a table view that lists Queries or Pages).
5. Click the "Export" button (top-right) and choose "CSV" or "Google Sheets". Save as CSV.

B. Manual export — Coverage report (Indexing)
1. Click "Coverage" in the left nav.
2. Check the status tabs (Error / Valid with warnings / Valid / Excluded).
3. Use the table and the Export button to download the URL list for each status category (CSV).

C. Manual export — Rich results / Enhancements
1. Under "Enhancements" or "Rich Results", select relevant schema types (HowTo, Breadcrumbs, etc.).
2. Export the list of URLs with errors/warnings via the Export button.

D. Sitemaps
1. In GSC, go to "Sitemaps".
2. Copy the sitemap index URL(s) and download the XML files.

E. API export (recommended for automation)
- Use the Google Search Console API (Search Analytics: `searchanalytics.query`) to pull Performance data programmatically.
- OAuth scope: `https://www.googleapis.com/auth/webmasters.readonly`.
- Example (Python):
  - Use `google-api-python-client` with service account or OAuth credentials bound to a user with access to the property.
  - Call `service.searchanalytics().query(siteUrl='https://converigo.com', body={"startDate":"2026-05-01","endDate":"2026-07-31","dimensions":["query","page"],"rowLimit":25000})`.
- For Coverage and other indexed data, use the Indexing API (if available) or export from the GSC web UI; Coverage export is currently primarily via web UI.

## 5. How to export GA4 data (manual & programmatic)
A. Manual (GA4 web UI)
1. Open Google Analytics 4 property.
2. Use Reports → Engagement → Pages and screens.
3. Set date range (Last 90 days) and apply a filter to include only organic traffic if possible (session default channel grouping).
4. Use the Export button to download CSV.

B. Programmatic (recommended)
- Use the GA4 Data API or BigQuery export (preferred for robust exports).
- BigQuery: enable GA4 BigQuery linking and export events; then run SQL to aggregate organic sessions by `page_location`.
- GA4 Data API: use `runReport` to fetch metrics (`sessions`, `users`) grouped by `pagePath` for the date range.

## 6. Prioritization for collection (recommended)
Priority 1 (collect immediately)
- GSC Performance export (Queries & Pages, last 90 days) — required to identify keyword & CTR opportunities.
- GSC Coverage/Indexing export (Coverage report) — required to identify indexing blockers.
- Sitemap XML (sitemap index) — required to verify sitemap completeness and mapping to canonical URLs.
- GA4 organic traffic by page (Last 90 days) — required to tie GSC impressions/CTR to site traffic.

Priority 2 (important)
- GSC Rich Results / Structured Data report — validate HowTo/Breadcrumb markup coverage.
- GA4 event-level exports (if GA4 BigQuery available) — for advanced funnel and engagement ties.
- SERP rank-tracker export for prioritized keywords (Ahrefs/Semrush) — to validate ranking positions.

Priority 3 (nice-to-have)
- Backlink / referring domains exports.
- Crawl logs for detailed bot behavior.
- Historical exports (6–12 months) for trend analysis.

## 7. Delivery checklist for each data item
- Include property name (e.g., `https://converigo.com`), date range, export timestamp, and the person who exported.
- Provide file name conventions: `gsc_performance_YYYYMMDD_YYYYMMDD.csv`, `gsc_coverage_YYYYMMDD.csv`, `ga4_organic_pages_YYYYMMDD_YYYYMMDD.csv`, `sitemap_index_YYYYMMDD.xml`.
- For API exports, provide the script and the exact API request body or SQL query used (in repository `data/` or `scripts/` outside application code), and store credentials securely (do NOT check credentials into repo).

---
Report created by executor in read-only mode. No code or data files were modified.
