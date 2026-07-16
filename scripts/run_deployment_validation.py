from pathlib import Path
import json
import sys

from app.services.deployment_validation_service import DeploymentValidationService


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    report_path = root / "DEPLOYMENT_VALIDATION_REPORT.md"

    service = DeploymentValidationService(
        contracts_dir=root / "app" / "data" / "converters",
        output_dir=root / "outputs",
    )
    report = service.run_all_checks()
    markdown = service.generate_markdown_report(report)

    report_path.write_text(markdown, encoding="utf-8")
    print(markdown)

    if report["all_passed"]:
        print("\nDeployment validation passed.")
        return 0

    print("\nDeployment validation failed. See DEPLOYMENT_VALIDATION_REPORT.md for details.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
