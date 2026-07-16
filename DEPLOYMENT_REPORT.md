# Deployment Validation Report

This repository includes a production-focused deployment validation suite that checks all critical release readiness stages before deployment.

## 16-stage deployment validation checklist

1. Contract schema validation
2. Converter data presence
3. Duplicate slug detection
4. Plugin registry coverage
5. Route generation validation
6. SEO metadata generation
7. Hub inclusion consistency
8. Recommendation coverage
9. Sitemap generation
10. Sitemap validation
11. Robots and sitemap availability
12. Internal link coverage
13. Topic cluster coverage
14. Programmatic SEO coverage
15. Content quality gating
16. Production audit summary

## Usage

Run the deployment validation script:

```bash
python scripts/run_deployment_validation.py
```

This writes `DEPLOYMENT_VALIDATION_REPORT.md` in the repository root and exits with a non-zero status if any stage fails.

## Goals

- Ensure production contracts and converter data are complete and consistent.
- Verify SEO metadata, sitemap generation, and robots directives.
- Confirm hub and recommendation coverage.
- Validate internal linking and topic cluster completeness.
- Gate publication with programmatic SEO generation and content quality metrics.
- Produce a final production audit summary for deployment readiness.
