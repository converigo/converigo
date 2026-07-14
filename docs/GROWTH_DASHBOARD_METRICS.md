# Growth Dashboard Metrics - Archive Cluster (GROWTH-001)

**Date:** July 14, 2026

## Overview
This document captures initial growth dashboard metrics for the Archive Cluster after deployment.

## Key Metrics (initial)

- New converters: 5
- Landing pages created: 5
- Tests added: 17
- Regression status: 17/17 passing
- Production audit average score: 88
- Hub inclusion: pending (0/5)

## Dashboard KPIs

- **Impressions:** Measure search impressions for archive pages (target: +20% month-on-month)
- **Clicks (CTR):** Monitor CTR for `zip-extract` and `rar-extract` (target > 3%)
- **Conversion Rate:** Users who extract files / users who visited landing (target 8-12%)
- **Retention/Return Rate:** Track repeat visitors to archive pages
- **Internal Link Flow:** Monitor internal navigation from archive pages to other converters

## Aggregation Sources
- ConverterRegistryService (contract counts)
- ConverterDataService (landing readiness)
- ProductionAuditService (quality scores)
- SitemapService (index coverage)
- HubPageService (hub inclusion metrics)

## Initial Dashboard Widgets

1. **Converter Coverage**
   - Active converters by category (post-change: archive +5)
2. **Audit Score Distribution**
   - Histogram of quality scores across converters (highlight archives)
3. **Landing Readiness**
   - % of converters with valid landing contracts (expected 100% for archives)
4. **Tests Status**
   - Latest test run summary (145/145 passing)
5. **Traffic Opportunity**
   - Top keywords and estimated relative volume for archive pages

## Next Steps for Growth Phase
- Instrument UTM parameters on CTAs for archive pages
- Add Sentry/analytics events for extraction success/failure
- Add SEO A/B tests on `zip-extract` title/description
- Promote `zip-extract` via short guides and social snippets
- Re-run audits after hub inclusion and verify `READY` status

***
