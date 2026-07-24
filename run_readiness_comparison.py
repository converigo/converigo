"""Run Search Console Readiness Engine and generate comparison report."""
import json
from pathlib import Path
from datetime import datetime, timezone

# Force cache refresh by importing directly
import sys
sys.modules.pop("app.services.search_console_readiness_service", None)

from app.services.search_console_readiness_service import SearchConsoleReadinessService

service = SearchConsoleReadinessService(
    contracts_dir=Path("app/data/converters"),
    output_dir=Path("outputs"),
)

# Clear internal cache
service._converter_cache = None

audit = service.run_full_audit()
report = service.generate_report(
    output_path=Path("outputs/execution_021/SEARCH_CONSOLE_READINESS_REPORT.md")
)

summary = audit["summary"]
categories = audit["category_breakdowns"]

print("=" * 60)
print("SEARCH CONSOLE READINESS — AFTER FIX")
print("=" * 60)
print(f"\n  Readiness Score: {summary['readiness_score']}/100 ({summary['overall_status'].upper()})")
print(f"  Pages Audited:  {summary['pages_audited']}")
print(f"  Pages Ready:    {summary['pages_ready']}")
print(f"  Critical:       {summary['critical_count']}")
print(f"  Warnings:       {summary['warning_count']}")
print(f"  Passed:         {summary['pass_count']}")
print(f"  Total Checks:   {summary['critical_count'] + summary['warning_count'] + summary['pass_count']}")
print()

print("  Category Scores:")
for cat, data in sorted(categories.items()):
    print(f"    {cat:20s} {data['score']:6.1f}/100 (weight={data['weight']}, weighted={data['weighted_score']})")

print()
print("BEFORE vs AFTER")
print(f"  Before:  41.2/100 (CRITICAL)")
print(f"  After:   {summary['readiness_score']}/100 ({summary['overall_status'].upper()})")
print(f"  Change:  +{summary['readiness_score'] - 41.2:.1f} points")
print()

# Generate comparison section in report
comparison = f"""
## Before vs After Comparison

| Metric | Before (Sprint 03C) | After (Sprint 03D) | Change |
|--------|-------------------|-------------------|--------|
| **Readiness Score** | 41.2/100 (CRITICAL) | {summary['readiness_score']}/100 ({summary['overall_status'].upper()}) | **+{summary['readiness_score'] - 41.2:.1f}** |
| **Pages Audited** | 61 | {summary['pages_audited']} | — |
| **Critical Issues** | 184 | {summary['critical_count']} | **-{184 - summary['critical_count']}** |
| **Warnings** | 82 | {summary['warning_count']} | **-{82 - summary['warning_count']}** |
| **Passed Checks** | 470 | {summary['pass_count']} | **+{summary['pass_count'] - 470}** |
"""

# Add category comparison
comparison += """
### Category Score Comparison

| Category | Before | After | Change | Weight |
|----------|--------|-------|--------|--------|
"""
before_categories = {
    "canonical": 0.0,
    "core_seo": 91.6,
    "indexability": 50.0,
    "robots": 100.0,
    "sitemap": 50.0,
    "structured_data": 0.0,
}

for cat in sorted(categories.keys()):
    before = before_categories.get(cat, 0)
    after = categories[cat]["score"]
    change = after - before
    weight = categories[cat]["weight"]
    comparison += f"| {cat.replace('_', ' ').title():20s} | {before:6.1f}/100 | {after:6.1f}/100 | {'+' if change >= 0 else ''}{change:+.1f} | {weight} |\n"

# Append comparison to report
report_path = Path("outputs/execution_021/SEARCH_CONSOLE_READINESS_REPORT.md")
existing = report_path.read_text(encoding="utf-8")
report_path.write_text(existing + comparison, encoding="utf-8")

print(f"Full report: {report_path}")
print()
print("Key Success Criteria:")
print(f"  ✓ Score >= 90: {summary['readiness_score'] >= 90}")
print(f"  ✓ Canonical Coverage = 100%: {categories.get('canonical', {}).get('score', 0) >= 99}")
print(f"  ✓ Lifecycle Coverage = 100%: {categories.get('indexability', {}).get('score', 0) >= 99}")

