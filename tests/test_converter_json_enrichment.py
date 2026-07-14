import json
from pathlib import Path


def test_all_converters_include_universal_tool_page_sections() -> None:
    converter_dir = Path("app/data/converters")
    files = sorted([f for f in converter_dir.glob("*.json") if not f.name.endswith((".contract.json", ".metadata.json"))])

    assert files, "No converter JSON files were found"

    required_keys = [
        "hero",
        "features",
        "supported_formats",
        "how_to_use",
        "about_formats",
        "cta",
    ]

    for path in files:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        for key in required_keys:
            assert key in data, f"{path.name} is missing {key}"

        assert isinstance(data["hero"], dict)
        assert isinstance(data["features"], list)
        assert isinstance(data["supported_formats"], dict)
        assert isinstance(data["how_to_use"], list)
        assert isinstance(data["about_formats"], list)
        assert isinstance(data["cta"], dict)
