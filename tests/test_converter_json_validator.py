from pathlib import Path
from tests.tools.validate_converters import generate_report


def test_generate_converter_json_report():
    out = Path("RC1_2_CONVERTER_JSON_REPORT.md")
    report = generate_report(out)
    # The test does not fail the suite; it produces a report for inspection.
    assert out.exists()
    assert "checked" in report