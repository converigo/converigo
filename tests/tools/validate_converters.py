import json
from pathlib import Path
from typing import Dict, List

REQUIRED_KEYS = [
    "hero",
    "features",
    "supported_formats",
    "how_to_use",
    "about_formats",
    "cta",
]


def find_converter_files(root: Path) -> List[Path]:
    return sorted([
        p for p in (root / "app" / "data" / "converters").glob("*.json")
        if not p.name.endswith((".contract.json", ".metadata.json"))
    ])


def validate_file(path: Path) -> Dict[str, List[str]]:
    missing = []
    type_issues = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"error": [str(exc)]}

    for key in REQUIRED_KEYS:
        if key not in data:
            missing.append(key)
        else:
            # basic type expectations
            if key == "features" and not isinstance(data[key], list):
                type_issues.append(f"{key} must be list")
            if key == "hero" and not isinstance(data[key], dict):
                type_issues.append(f"{key} must be object")
            if key == "supported_formats" and not isinstance(data[key], dict):
                type_issues.append(f"{key} must be object")
            if key in ("how_to_use", "about_formats") and not isinstance(data[key], list):
                type_issues.append(f"{key} must be list")
            if key == "cta" and not isinstance(data[key], dict):
                type_issues.append(f"{key} must be object")

    result = {}
    if missing:
        result["missing"] = missing
    if type_issues:
        result["type_issues"] = type_issues
    return result


def generate_report(out_path: Path) -> Dict[str, Dict]:
    root = out_path.parent
    files = find_converter_files(root)
    report = {
        "checked": len(files),
        "files": {},
    }

    for p in files:
        report["files"][p.name] = validate_file(p)

    # Write a human-readable report
    lines = ["CONVERTER JSON VALIDATION REPORT", ""]
    lines.append(f"Checked files: {report['checked']}")
    lines.append("")

    missing_count = 0
    for name, info in report["files"].items():
        if info:
            lines.append(f"{name}:")
            for k, v in info.items():
                lines.append(f"  {k}: {', '.join(v)}")
            lines.append("")
            missing_count += 1

    lines.append(f"Files with issues: {missing_count}")
    out_text = "\n".join(lines)
    out_path.write_text(out_text, encoding="utf-8")
    return report


if __name__ == "__main__":
    out_file = Path("RC1_2_CONVERTER_JSON_REPORT.md")
    generate_report(out_file)