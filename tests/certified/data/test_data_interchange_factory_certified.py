"""
PROJECT: CONVERIGO
TEST SUITE: Certified Data Interchange Cluster - Factory Batch F6 (Jalur 2)

Factory Batch F6 (cluster G-D): the four net-new XML/YAML data-interchange
converters (SPR-20 xml-to-json, SPR-21 json-to-xml, SPR-22 yaml-to-json,
SPR-23 json-to-yaml) built on the F0 factory base (app/factory/plugin_base.py)
via the stdlib xml/json + PyYAML engine.  ONE parametric test file for the
whole F6 batch, using the shared factory harness uniform contract:

    plugin discovered -> POST /convert 201 -> GET /download 200 ->
    output content verified -> honest 422 UNSUPPORTED_CONVERSION

Governance note: no regression sample for xml/yaml/json is tracked in git
(no tests/sample.{xml,yaml,yml,json} exists), so per the F4-validated
tracked-sample policy all four F6 slugs ship page-only (D9 landing pages,
no contract artifacts) - the F5 json-to-xlsx precedent, asserted below.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

from tests.certified._factory_harness import (
    assert_honest_unsupported,
    assert_slug_discovered,
    cleanup_output,
    post_convert,
    run_happy_path,
)

# ---------------------------------------------------------------------------
# Deterministic fixtures + expected payloads
# ---------------------------------------------------------------------------

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

LIBRARY_JSON = json.dumps(
    {
        "library": {
            "book": [
                {"id": 1, "title": "alpha"},
                {"id": 2, "title": "beta"},
            ]
        }
    },
    indent=2,
) + "\n"

LIBRARY_DICT = json.loads(LIBRARY_JSON)


def _write_xml(path: Path) -> Path:
    path.write_text(CATALOG_XML, encoding="utf-8")
    return path


def _write_yaml(path: Path) -> Path:
    path.write_text(CATALOG_YAML, encoding="utf-8")
    return path


def _write_json(path: Path) -> Path:
    path.write_text(LIBRARY_JSON, encoding="utf-8")
    return path


def _verify_json(path: Path, expected: dict) -> None:
    assert json.loads(path.read_text(encoding="utf-8")) == expected


def _verify_xml(path: Path) -> None:
    root = ET.parse(path).getroot()
    assert root.tag == "root", root.tag
    books = root.findall("library/book")
    assert [book.findtext("id") for book in books] == ["1", "2"], list(books)
    assert [book.findtext("title") for book in books] == ["alpha", "beta"], list(books)


def _verify_yaml(path: Path) -> None:
    assert yaml.safe_load(path.read_text(encoding="utf-8")) == LIBRARY_DICT


# ---------------------------------------------------------------------------
# Case table: (slug, target_format, fixture_builder, verifier_name)
# ---------------------------------------------------------------------------

NET_NEW_CASES = [
    ("xml-to-json", "json", _write_xml, "catalog"),
    ("json-to-xml", "xml", _write_json, None),
    ("yaml-to-json", "json", _write_yaml, "catalog"),
    ("json-to-yaml", "yaml", _write_json, None),
]

PAGE_ONLY_SLUGS = [slug for slug, *_ in NET_NEW_CASES]

MIMES = {
    "xml": "application/xml",
    "json": "application/json",
    "yaml": "application/yaml",
    "yml": "application/yaml",
    "txt": "text/plain",
}

# (slug, target, corrupt content, upload mime, filename)
CORRUPT_CASES = [
    ("xml-to-json", "json", "<catalog><book></catalog>", "application/xml", "broken.xml"),
    ("json-to-xml", "xml", "{not valid json", "application/json", "broken.json"),
    ("json-to-yaml", "yaml", "{not valid json", "application/json", "broken.json"),
    ("yaml-to-json", "json", "key: [unclosed", "application/yaml", "broken.yaml"),
]


def _verify_case_output(slug: str, output: Path) -> None:
    if slug == "xml-to-json":
        _verify_json(output, CATALOG_DICT)
    elif slug == "yaml-to-json":
        _verify_json(output, CATALOG_DICT)
    elif slug == "json-to-xml":
        _verify_xml(output)
    elif slug == "json-to-yaml":
        _verify_yaml(output)
    else:  # pragma: no cover - case table guard
        raise AssertionError(f"unknown case {slug}")


# ---------------------------------------------------------------------------
# Uniform factory contract
# ---------------------------------------------------------------------------


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format,expected_source",
    [(slug, target, slug.split("-to-")[0]) for slug, target, _, _ in NET_NEW_CASES],
)
def test_factory_plugin_discovered(slug: str, target_format: str, expected_source: str) -> None:
    """Each F6 net-new slug is registered with its (source, target) pair."""
    assert_slug_discovered(slug, expected_source, target_format)


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format,builder",
    [pytest.param(slug, target, builder, id=slug) for slug, target, builder, _ in NET_NEW_CASES],
)
def test_factory_happy_path_uniform_contract(
    slug: str,
    target_format: str,
    builder,
    tmp_path: Path,
) -> None:
    """Uniform pipeline: 201 -> download 200 -> content verified per case."""
    fixture = builder(tmp_path / f"factory_fixture.{slug.split('-to-')[0]}")
    assert fixture.is_file(), f"fixture builder produced no file: {fixture}"
    output = run_happy_path(
        fixture,
        target_format,
        slug,
        mime=MIMES[slug.split("-to-")[0]],
    )
    try:
        _verify_case_output(slug, output)
    finally:
        cleanup_output(output)


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format",
    [(slug, target) for slug, target, _, _ in NET_NEW_CASES],
)
def test_factory_honest_error_for_unsupported_input(
    slug: str,
    target_format: str,
) -> None:
    """Wrong-extension input gets the honest 422 error class - never fake output."""
    response = post_convert(
        Path("tests/sample.txt"),
        target_format,
        slug,
        mime=MIMES["txt"],
        filename="sample.txt",
    )
    assert_honest_unsupported(response)


@pytest.mark.certified
@pytest.mark.parametrize(
    "slug,target_format,content,mime,filename",
    [pytest.param(*case, id=case[0]) for case in CORRUPT_CASES],
)
def test_factory_honest_error_for_corrupt_input(
    slug: str,
    target_format: str,
    content: str,
    mime: str,
    filename: str,
    tmp_path: Path,
) -> None:
    """Malformed text that passes the (signature-free) upload gate must still
    fail honestly (422 UNSUPPORTED_CONVERSION), never 500/fake output."""
    corrupt = tmp_path / filename
    corrupt.write_text(content, encoding="utf-8")
    response = post_convert(corrupt, target_format, slug, mime=mime, filename=filename)
    assert_honest_unsupported(response)


@pytest.mark.certified
def test_yml_alias_registered_and_converted(tmp_path: Path) -> None:
    """yaml-to-json registers BOTH the canonical .yaml pair and the .yml
    alias, and a real .yml upload converts end-to-end through the route."""
    assert_slug_discovered("yaml-to-json", "yaml", "json")
    assert_slug_discovered("yaml-to-json", "yml", "json")
    fixture = tmp_path / "alias_fixture.yml"
    fixture.write_text(CATALOG_YAML, encoding="utf-8")
    output = run_happy_path(fixture, "json", "yaml-to-json", mime=MIMES["yml"])
    try:
        _verify_json(output, CATALOG_DICT)
    finally:
        cleanup_output(output)


# ---------------------------------------------------------------------------
# Governance artifacts
# ---------------------------------------------------------------------------


@pytest.mark.certified
def test_static_target_map_f6_rows() -> None:
    """The deployed STATIC_TARGET_MAP rows reflect the F6 delta: json gains
    XML + YAML; xml/yaml/yml are net-new sources targeting JSON."""
    html_text = Path("app/templates/main/converigo_main.html").read_text(encoding="utf-8")
    block = html_text.split("const STATIC_TARGET_MAP = {", 1)[1].split("};", 1)[0]
    mapping: dict[str, list[str]] = {}
    for key, values in re.findall(r"(['\"a-zA-Z0-9_]+):\[(.*?)\]", block):
        mapping[key.strip("'\"")] = [
            v.strip().strip("'\"") for v in values.split(",") if v.strip()
        ]

    assert mapping.get("json") == ["CSV", "XLSX", "XML", "YAML"], mapping.get("json")
    assert mapping.get("xml") == ["JSON"], mapping.get("xml")
    assert mapping.get("yaml") == ["JSON"], mapping.get("yaml")
    assert mapping.get("yml") == ["JSON"], mapping.get("yml")


@pytest.mark.certified
def test_d9_page_artifacts_shipped() -> None:
    """All four F6 slugs ship landing pages; each is valid certified JSON."""
    converters_dir = Path("app/data/converters")
    for slug in PAGE_ONLY_SLUGS:
        page_path = converters_dir / f"{slug}.json"
        assert page_path.is_file(), f"missing page artifact: {page_path.name}"
        payload = json.loads(page_path.read_text(encoding="utf-8"))
        assert payload.get("slug") == slug, payload.get("slug")
        assert payload.get("lifecycle_status") == "certified", payload.get("lifecycle_status")


@pytest.mark.certified
def test_page_only_contract_policy() -> None:
    """No tracked xml/yaml/json regression sample exists anywhere in the repo,
    so per the F4-validated tracked-sample policy the F6 slugs ship NO
    contract artifacts (F5 json-to-xlsx precedent)."""
    assert not any(
        (Path("tests") / f"sample.{ext}").exists()
        for ext in ("xml", "yaml", "yml", "json")
    )
    converters_dir = Path("app/data/converters")
    for slug in PAGE_ONLY_SLUGS:
        contract_path = converters_dir / f"{slug}.contract.json"
        assert not contract_path.exists(), f"unexpected contract artifact: {contract_path.name}"

