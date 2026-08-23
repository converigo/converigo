# SEO Google Data Mapping

Purpose
- Document how Google data fields (GSC and GA4) map into signals used by the SEO scoring and opportunity engine.

1) Mapping overview
- Primary join key: normalized canonical `URL` (from GSC `Page` and GA4 `PagePath`).
- Date alignment: align to `YYYY-MM-DD` and the same date window for both GSC and GA4; convert GA4 dates using property timezone if necessary.

2) GSC → SEO signals
- `Impressions` → Visibility (raw impressions; use normalized scale for scoring).
- `Clicks` → Observed clicks (used directly and for uplift calculations).
- `CTR` → Performance signal (normalize to 0-1).
- `Position` → Ranking position (used for rank-opportunity modeling).
- `Query` → Keyword-level opportunities; group into intents where possible for content recommendations.
- `Device`, `Country` → Dimension breakdowns for segment-specific scoring.

3) GA4 → SEO signals
- `Sessions` → Engagement volume (used to weight potential impact when converting clicks → sessions).
- `Users` → Unique visitors metric for engagement-normalized scoring.
- `EngagementRate` → Engagement quality (0-1 normalized).
- `Conversions` → Conversion signal to prioritize revenue-impacting pages.

4) Derived metrics & normalization rules
- CTR normalization: accept percent or decimal, convert to decimal (e.g., `12.3%` → `0.123`).
- Weighted position: when aggregating rows, compute impression-weighted average of `Position`.
- CTR potential / benchmark:
  - Use historical CTR-by-position curve to determine benchmark CTR for a given position.
  - `CTR_gap = benchmark_CTR(position) - current_CTR` (floor 0).
- Estimated clicks uplift: `EstimatedClicksUplift = Impressions * CTR_gap`.
- Rank improvement uplift:
  - For a target position delta, estimate CTR_at_target = CTR_curve[target_position]
  - `EstimatedClicksUplift_rank = Impressions * (CTR_at_target - current_CTR)`.
- Composite normalization: scale Impressions, Sessions, and EstimatedUplift to 0-1 using percentile-based normalization or log-scale normalization before weighted scoring.

5) Join rules and fallbacks
- Normalized URL equality is primary join; matching steps:
  1. Exact match on normalized URL.
  2. Trailing-slash/index.html heuristics.
  3. Strip common tracking parameters and retry.
  4. Use sitemap canonical mapping as fallback.
- If multiple GA4 rows map to the same normalized URL (e.g., differing query strings), aggregate by summing Sessions/Users/Conversions and computing weighted EngagementRate.

6) Scoring inputs to Opportunity Engine
- VisibilitySignal: normalized(Impressions)
- PerformanceSignal: inverse(Position) and CTR
- EngagementSignal: normalized(Sessions) * EngagementRate
- IndexingSignal: binary or graded signal from coverage (0=Not indexed, 1=Indexed) with penalties for `Excluded` or `Redirect` statuses
- FeasibilitySignal: derived from content quality heuristics and backlink indicators (optional external data)

7) Handling missing or sampled data
- If GA4 is sampled: mark `ga4_sampling_flag=true`, reduce weight of engagement signals or prefer BigQuery exports.
- If GA4 missing: compute scores using GSC-only signals and mark confidence accordingly.
- If GSC missing: rare for pages with GA4 sessions; reconcile with sitemap and server logs where possible.

8) Provenance
- Record source column, source filename, and checksum for each derived metric in the analysis output.

Examples
- Example output row columns:
  - `URL,Impressions,Clicks,CTR,AvgPosition,GA4_Sessions,GA4_EngagementRate,EstimatedClicksUplift,VisibilityNorm,PerformanceNorm,EngagementNorm,CompositeScore`

Operational notes
- Keep mapping logic versioned and document CTR curve source and computation method.
- Provide an optional config to adjust normalization strategy (percentile vs log) and weights used in composite scoring.
