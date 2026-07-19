from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPORT_PATH = Path("CERTIFICATION_SYSTEM_REPORT.md")
CERTIFIED_FILE = Path("app") / "data" / "certified_converters.json"
ALLOWED_LIFECYCLE_STATUSES = {"active", "deprecated", "beta", "certified", "disabled"}
SECTION_DEFAULT_STATUS = {
    "certified": "certified",
    "beta": "beta",
    "disabled": "disabled",
}


def write_report(lines: list[str]) -> None:
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def load_certified_registry(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    raw_data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw_data, list):
        return [dict(item) for item in raw_data], []

    if isinstance(raw_data, dict):
        entries: list[dict[str, Any]] = []
        sections: list[str] = []
        for section_name, section_items in raw_data.items():
            sections.append(section_name)
            if not isinstance(section_items, list):
                raise ValueError(f"Expected section '{section_name}' to contain a list")
            for item in section_items:
                if not isinstance(item, dict):
                    raise ValueError(f"Expected items under '{section_name}' to be objects")
                item_copy = dict(item)
                if not item_copy.get("lifecycle_status"):
                    item_copy["lifecycle_status"] = SECTION_DEFAULT_STATUS.get(section_name, "")
                item_copy["_section"] = section_name
                entries.append(item_copy)
        return entries, sections

    raise ValueError(f"Expected list or object in `{path}`, got {type(raw_data)}")


def main() -> int:
    lines: list[str] = []
    lines.append("# Certification System Report")
    lines.append("")

    if not CERTIFIED_FILE.exists():
        lines.append("CERTIFICATION STATUS: FAIL")
        lines.append("")
        lines.append(f"Reason: missing file `{CERTIFIED_FILE}`")
        write_report(lines)
        print("CERTIFICATION STATUS: FAIL - missing certified_converters.json")
        return 1

    try:
        entries, sections = load_certified_registry(CERTIFIED_FILE)
    except Exception as exc:
        lines.append("CERTIFICATION STATUS: FAIL")
        lines.append("")
        lines.append(f"Reason: failed to parse `{CERTIFIED_FILE}`: {exc}")
        write_report(lines)
        print("CERTIFICATION STATUS: FAIL - invalid registry format")
        return 1

    slugs: list[str] = []
    unique_slugs: set[str] = set()
    issues: list[str] = []
    missing_test_files: list[str] = []
    invalid_lifecycle: list[str] = []
    incorrect_section_status: list[str] = []
    section_counts: dict[str, int] = {}

    for item in entries:
        slug = str(item.get("slug", "")).strip()
        lifecycle = str(item.get("lifecycle_status", "")).strip().lower()
        section = str(item.get("_section", "")).strip().lower()

        if not slug:
            issues.append("Entry missing slug")
            slug = "<missing-slug>"

        normalized = slug.lower()
        slugs.append(normalized)
        unique_slugs.add(normalized)

        if lifecycle not in ALLOWED_LIFECYCLE_STATUSES:
            invalid_lifecycle.append(slug)

        if section:
            if section == "certified" and lifecycle != "certified":
                incorrect_section_status.append(f"{slug} (expected certified)")
            if section == "beta" and lifecycle != "beta":
                incorrect_section_status.append(f"{slug} (expected beta)")
            if section == "disabled" and lifecycle not in {"disabled", "deprecated"}:
                incorrect_section_status.append(f"{slug} (expected disabled or deprecated)")
            section_counts[section] = section_counts.get(section, 0) + 1

        if "test_files" in item:
            files = item.get("test_files") or []
            for file_path in files:
                p = Path(file_path)
                if not p.exists():
                    missing_test_files.append(file_path)

    if len(slugs) != len(unique_slugs):
        issues.append("Duplicate slugs found")

    pass_status = not issues and not missing_test_files and not invalid_lifecycle and not incorrect_section_status
    lines.append("CERTIFICATION STATUS: PASS" if pass_status else "CERTIFICATION STATUS: FAIL")
    lines.append("")
    lines.append("Summary:")
    lines.append("")
    lines.append(f"Total entries: {len(entries)}")
    lines.append(f"Unique slugs: {len(unique_slugs)}")
    if sections:
        for section_name in sections:
            lines.append(f"{section_name.capitalize()} entries: {section_counts.get(section_name, 0)}")
    lines.append("")

    if issues:
        lines.append("Issues:")
        for issue in issues:
            lines.append(f"- {issue}")
        lines.append("")

    if incorrect_section_status:
        lines.append("Section status mismatches:")
        for mismatch in incorrect_section_status:
            lines.append(f"- {mismatch}")
        lines.append("")

    if invalid_lifecycle:
        lines.append("Entries with invalid lifecycle_status:")
        for slug in invalid_lifecycle:
            lines.append(f"- {slug}")
        lines.append("")

    if missing_test_files:
        lines.append("Missing test files referenced in certified list:")
        for file_path in missing_test_files:
            lines.append(f"- {file_path}")
        lines.append("")

    write_report(lines)
    print("Certification check complete; report written to CERTIFICATION_SYSTEM_REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
