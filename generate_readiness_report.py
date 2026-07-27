#!/usr/bin/env python3
"""Generate Search Console Readiness report."""

from pathlib import Path
from app.services.search_console_readiness_service import SearchConsoleReadinessService


def main() -> None:
    output_dir = Path("outputs") / "execution_020"
    output_dir.mkdir(parents=True, exist_ok=True)

    service = SearchConsoleReadinessService(
        contracts_dir=Path("app/data/converters"),
        output_dir=output_dir,
    )

    # Generate report
    report_path = output_dir / "SEARCH_CONSOLE_READINESS_REPORT.md"
    report = service.generate_report(report_path)
    print(f"Report generated: {report_path}")

    # Print summary
    audit = service.run_full_audit()
    summary = audit["summary"]
    print(f"\n=== Search Console Readiness Summary ===")
    print(f"Readiness Score: {summary['readiness_score']}/100")
    print(f"Overall Status: {summary['overall_status'].upper()}")
    print(f"Pages Audited: {summary['pages_audited']}")
    print(f"Pages Ready: {summary['pages_ready']}")
    print(f"Critical Issues: {summary['critical_count']}")
    print(f"Warnings: {summary['warning_count']}")
    print(f"Passed Checks: {summary['pass_count']}")

    # Category breakdowns
    print(f"\n=== Category Breakdown ===")
    for cat_name, cat_data in sorted(audit.get("category_breakdowns", {}).items()):
        display_name = cat_name.replace("_", " ").title()
        print(f"{display_name}: {cat_data['score']}/100 (W: {cat_data['weight']})")

    # Recommendations
    recs = audit.get("recommendations", [])
    if recs:
        print(f"\n=== Top Recommendations ===")
        for rec in recs[:5]:
            print(f"  [{rec['priority'].upper()}] {rec['recommendation']}")


if __name__ == "__main__":
    main()

