# Growth Dashboard

## Architecture

- The dashboard service aggregates data from the existing converter registry, sitemap service, hub service, programmatic SEO service, and production audit service.
- It produces a structured payload with metrics for converter volume, category distribution, landing and hub coverage, registry health, contract coverage, sitemap coverage, regression health, and production readiness.

## Metrics

- total_converters
- converters_by_category
- total_landing_pages
- total_hub_pages
- registry_health
- contract_coverage
- sitemap_coverage
- regression_summary
- production_audit

## Production Metrics

The production_audit block exposes:

- platform_health
- production_ready
- landing_coverage
- knowledge_coverage
- contract_coverage
- hub_coverage
- sitemap_coverage
- regression_coverage
- average_quality_score
- counts_by_status
