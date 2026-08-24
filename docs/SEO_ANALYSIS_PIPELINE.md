# SEO Analysis Pipeline

Purpose
- Describe the high-level pipeline transforming raw GSC CSV exports into a prioritized Opportunity Matrix and an `SEO Growth Report`.

Pipeline Overview
GSC CSV
 -> Validation
 -> URL Normalization & Enrichment (sitemap, coverage, GA4)
 -> Opportunity Matrix (scoring & prioritization)
 -> SEO Growth Report (executive summary, recommended actions, metrics)

1) Ingest: GSC CSV
- Accepts validated GSC CSVs conforming to `docs/GSC_EXPORT_VALIDATION.md`.
- Record ingest metadata: filename, checksum, date range, exporter.

2) Validation (see `docs/GSC_EXPORT_VALIDATION.md`)
- Header, row, and URL normalization checks.
- Produce cleaned CSV ready for aggregation and a validation report.

3) URL Normalization & Enrichment
- Normalize URLs per URL matching rules.
- Enrich with:
  - Sitemap presence and `lastmod` (from sitemap files).
  - Indexing/Coverage status (from `seo_data/indexing/coverage.csv` if available).
  - GA4 metrics (sessions, users, engagement rate) matched by PagePath from GA4 exports for the same date range.
- If exact matches fail, attempt fuzzy matching heuristics (trailing slash, index file removal, query param stripping) and log the mapping confidence.

4) Aggregation and Baseline Metrics
- Aggregate GSC rows to page-level per date range (sum clicks/impressions, weighted CTR/Position).
- Compute baseline metrics per URL:
  - Impressions, Clicks, CTR, Avg Position, Click-through Opportunity (CTR_potential), Impression Share.
- Compute GA-derived engagement metrics where available.

5) Opportunity Matrix (scoring)
- For each URL compute signals:
  - Visibility: Impressions (normalized scale)
  - Performance: CTR and Position (current)
  - Potential: Estimated uplift if CTR improved to benchmark (e.g., top-3 CTR for the same position)
  - Indexing Risk: sitemap presence, coverage status
  - Engagement: GA4 sessions and engagement rate
- Scoring model (example):
  Score = w1 * normalized(Impressions) + w2 * position_gap + w3 * ctr_gap + w4 * indexing_risk + w5 * engagement
- Produce `opportunity_matrix.csv` with columns: URL, Impressions, Clicks, CTR, Position, GA4_Sessions, Indexing_Status, Score, Rank, Notes

6) Prioritization and Bucketing
- Bucket opportunities by score (e.g., High/Medium/Low) and by effort estimate (small, medium, large) if effort estimates available.
- Create shortlists for quick wins (high score, low estimated effort) and structural fixes (sitemap/indexing issues).

7) SEO Growth Report (deliverable)
- Executive summary: total opportunities, expected traffic uplift estimate, top 10 quick wins.
- Methodology: data sources, validation rules, scoring formula, date range.
- Detailed findings: CSVs and charts (opportunity_matrix.csv, top_10.csv, sitemap_gaps.csv).
- Action plan: recommended fixes, owners, estimated impact.
- Data issues and caveats: missing GA4, sparse GSC data, normalization caveats.

Outputs & Artifacts
- `seo_data/validated/<original_filename>.clean.csv` — cleaned GSC CSV used for analysis.
- `seo_data/validated/<original_filename>.validation.md` — validation report.
- `analysis/opportunity_matrix.csv` — scored and ranked opportunities.
- `analysis/top_10_quick_wins.csv` — export used in the report.
- `reports/SEO_GROWTH_REPORT_<date-range>.md` — human readable report with executive summary and attachments.

File naming and provenance
- All outputs must include source file reference, checksum, pipeline run timestamp, and version of the pipeline used.

Operational notes
- Automation: run pipeline on validated exports only. Any validation failures must be reviewed before analysis.
- Sensitivity: do not include PII in reports; strip query or query-parameter values that reveal personal data.
- Re-runs: pipeline should be idempotent — use checksums to detect reprocessing.

