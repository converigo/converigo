"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F6)
Version : 1.0.0

In-image probe for Factory Batch F6 (cluster G-D: XML/YAML data interchange).

Executed INSIDE the production image by docker-runtime-verify step [4/5]
(dispatch with probe_script=scripts/ci_in_data_interchange_probe.py):

    python scripts/ci_in_data_interchange_probe.py

All fixtures are generated in-image (json/xml/yaml modules), so the probe
is self-sufficient exactly like the F1-F5 probes.  The four F6 net-new
plugins are resolved through the real registry and executed through their
public async convert(); the yml alias pair is conversion-smoked and the
page-only artifact policy (D9 pages, NO contracts) is asserted.
Exit code 0 = PASS.
"""
from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.plugins.registry import registry  # noqa: E402

CATALOG_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    "<catalog>\n"
    '  <book id="1"><title>alpha</title></book>\n'
    '  <book id="2"><title>beta</title></book>\n'
    "</catalog>\n"
)

CATALOG_DICT = {
    "catalog": {
        "book": [
            {"@id": "1", "title": "alpha"},
            {"@id": "2", "title": "beta"},
        ]
    }
}

CATALOG_YAML = yaml.safe_dump(CATALOG_DICT, sort_keys=False)

LIBRARY_DICT = {
    "library": {
        "book": [
            {"id": 1, "title": "alpha"},
            {"id": 2, "title": "beta"},
        ]
    }
}

NET_NEW = ["xml-to-json", "json-to-xml", "yaml-to-json", "json-to-yaml"]
PAGE_ONLY = NET_NEW  # page-only batch: no tracked regression samples -> no contracts


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _verify_json(payload: Path, expected: dict) -> None:
    assert json.loads(payload.read_text(encoding="utf-8")) == expected


def _verify_xml(payload: Path) -> None:
    root = ET.parse(payload).getroot()
    assert root.tag == "root", root.tag
    books = root.findall("library/book")
    assert [book.findtext("id") for book in books] == ["1", "2"], list(books)


def _verify_yaml(payload: Path) -> None:
    assert yaml.safe_load(payload.read_text(encoding="utf-8")) == LIBRARY_DICT


async def _convert(slug: str, source: Path, target: str, working: Path) -> Path:
    plugin = registry.by_slug[slug]
    return await plugin.convert(source, target, output_dir=working)


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="f6_probe_") as tmp:
        root = Path(tmp)
        xml_fixture = _write(root / "probe_fixture.xml", CATALOG_XML)
        yaml_fixture = _write(root / "probe_fixture.yaml", CATALOG_YAML)
        yml_fixture = _write(root / "probe_fixture.yml", CATALOG_YAML)
        json_fixture = _write(root / "probe_fixture.json", json.dumps(LIBRARY_DICT, indent=2))

        plan = [
            ("xml-to-json", xml_fixture, "json", lambda p: _verify_json(p, CATALOG_DICT)),
            ("json-to-xml", json_fixture, "xml", _verify_xml),
            ("yaml-to-json", yaml_fixture, "json", lambda p: _verify_json(p, CATALOG_DICT)),
            ("json-to-yaml", json_fixture, "yaml", _verify_yaml),
        ]
        for slug, fixture, target, verifier in plan:
            try:
                assert registry.has_slug(slug), f"{slug} not registered"
                output_path = asyncio.run(_convert(
                    slug, fixture, target, root / f"out_{slug.replace('-', '_')}"
                ))
                assert output_path.is_file() and output_path.stat().st_size > 0
                verifier(output_path)
                print(f"F6 PROBE OK: {slug} ({fixture.suffix} -> {target})")
            except Exception as exc:  # noqa: BLE001 - probe reports all
                failures.append(f"{slug}: {type(exc).__name__}: {exc}")

        # yml alias pair: same plugin, .yml extension, exercised end-to-end.
        try:
            assert registry.has_slug("yaml-to-json")
            assert ("yml", "json") in registry.registered_keys["yaml-to-json"], (
                "yml alias pair not registered"
            )
            output_path = asyncio.run(_convert(
                "yaml-to-json", yml_fixture, "json", root / "out_yml_alias"
            ))
            assert output_path.is_file() and output_path.stat().st_size > 0
            _verify_json(output_path, CATALOG_DICT)
            print("F6 PROBE OK: yml alias (.yml -> json)")
        except Exception as exc:  # noqa: BLE001 - probe reports all
            failures.append(f"yml-alias: {type(exc).__name__}: {exc}")

        converters_dir = (
            Path(__file__).resolve().parent.parent / "app" / "data" / "converters"
        )
        for slug in NET_NEW:
            page = converters_dir / f"{slug}.json"
            if page.exists():
                print(f"F6 PROBE OK: D9 page artifact {page.name}")
            else:
                failures.append(f"D9 page artifact missing: {page.name}")
        for slug in PAGE_ONLY:
            contract = converters_dir / f"{slug}.contract.json"
            if contract.exists():
                failures.append(
                    f"unexpected contract artifact (page-only policy): {contract.name}"
                )
            else:
                print(f"F6 PROBE OK: page-only policy holds for {slug}")

    if failures:
        print("F6 PROBE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("F6 PROBE: PASS (4/4 data-interchange converters + yml alias verified in-image)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
