"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F6)
Version : 1.0.0

XML/YAML Data Interchange Converters (SPR-20 xml-to-json, SPR-21 json-to-xml,
SPR-22 yaml-to-json, SPR-23 json-to-yaml)
Factory Batch F6 - cluster G-D (data interchange), net-new quartet.

Built on the F0 certified factory scaffolding: the conversion pipeline
(discovery -> supports() check -> working root -> single servable file ->
non-empty output -> honest error) is owned by FactoryConversionPlugin.
Each converter below is pure configuration plus a small hook, consistent
with the certified data cluster engine (stdlib xml.etree.ElementTree + json;
PyYAML safe_load/safe_dump - already in requirements.txt, zero new deps).

Semantics (fixed, D1-consistent, deterministic):
- xml-to-json: xml.etree.ElementTree parse with a fixed, documented mapping:
  attributes -> "@name" keys, child elements grouped by tag (repeated tags
  become lists), text content becomes the element value (or "#text" when the
  element also carries attributes/children).  DTD/entity documents are
  rejected (honest 422) - MVP security posture, no entity expansion.
- json-to-xml: json.loads; object keys become child element tags, arrays
  become repeated elements, scalars become text content; the root element is
  named "root" and output is indented with an XML declaration.  Keys must be
  valid XML tag names (honest 422 otherwise - no silent key mangling).
- yaml-to-json: yaml.safe_load -> json.dumps(indent=2).  YAML scalars that
  are not JSON-native (e.g. dates) serialize to their string form via
  default=str; empty documents raise UnsupportedConversionError -> honest
  422, never a fabricated output.
- json-to-yaml: json.loads -> yaml.safe_dump(default_flow_style=False,
  sort_keys=False) so JSON key order is preserved.
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

from app.factory import make_plugin_class


def _unsupported(source: str, target: str, message: str) -> Exception:
    """Lazily build the honest-422 error (rar-extract/F4 lazy-import precedent)."""
    from app.services.conversion_service import UnsupportedConversionError

    return UnsupportedConversionError(source, target, message)


_TAG_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9._-]*$")


def _element_to_value(element: ET.Element):
    """Deterministic element -> JSON value mapping (see module docstring)."""
    value: dict = {}
    for name, attr in element.attrib.items():
        value[f"@{name}"] = attr

    children: dict[str, list] = {}
    for child in element:
        children.setdefault(child.tag, []).append(_element_to_value(child))
    for tag, values in children.items():
        value[tag] = values if len(values) > 1 else values[0]

    text = (element.text or "").strip()
    if value:  # element carries attributes and/or children
        if text:
            value["#text"] = text
        return value
    return text


def _convert_xml_to_json(
    self, source_path: Path, target_format: str, working_root: Path
) -> Path:
    """Map the XML tree to pretty-printed JSON with the fixed convention."""
    raw = source_path.read_bytes()
    if b"<!DOCTYPE" in raw[:4096] or b"<!ENTITY" in raw[:4096]:
        raise _unsupported(
            "xml",
            "json",
            "XML to JSON conversion failed: DTD/entity documents are not supported.",
        )
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:  # noqa: BLE001 - honest 422 for any parse failure
        raise _unsupported(
            "xml",
            "json",
            f"XML to JSON conversion failed: could not parse the document ({exc}).",
        ) from exc
    output_path = working_root / f"{source_path.stem}.{target_format}"
    payload = {root.tag: _element_to_value(root)}
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return output_path


def _fill_children(element: ET.Element, value) -> None:
    """Render one JSON value into an XML element (honest 422 on bad keys)."""
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not _TAG_NAME.fullmatch(key):
                raise _unsupported(
                    "json",
                    "xml",
                    "JSON to XML conversion failed: key "
                    f"{key!r} is not a valid XML tag name.",
                )
            if isinstance(item, list):
                for entry in item:  # arrays become repeated elements
                    _fill_children(ET.SubElement(element, key), entry)
            else:
                _fill_children(ET.SubElement(element, key), item)
    elif value is None:
        return
    else:
        element.text = str(value)


def _convert_json_to_xml(
    self, source_path: Path, target_format: str, working_root: Path
) -> Path:
    """Render JSON as an indented XML document (root element: <root>)."""
    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _unsupported(
            "json",
            "xml",
            f"JSON to XML conversion failed: file is not valid JSON ({exc}).",
        ) from exc
    if data is None:
        raise _unsupported(
            "json", "xml", "JSON to XML conversion failed: the file contains no data."
        )
    root = ET.Element("root")
    if isinstance(data, list):
        for item in data:
            _fill_children(ET.SubElement(root, "item"), item)
    else:
        _fill_children(root, data)
    ET.indent(root, space="  ")
    output_path = working_root / f"{source_path.stem}.{target_format}"
    ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)
    return output_path


def _convert_yaml_to_json(
    self, source_path: Path, target_format: str, working_root: Path
) -> Path:
    """yaml.safe_load -> pretty-printed JSON (non-JSON-native scalars stringify)."""
    try:
        data = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise _unsupported(
            "yaml",
            "json",
            f"YAML to JSON conversion failed: could not parse the document ({exc}).",
        ) from exc
    if data is None:
        raise _unsupported(
            "yaml",
            "json",
            "YAML to JSON conversion failed: the document is empty.",
        )
    output_path = working_root / f"{source_path.stem}.{target_format}"
    output_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return output_path


def _convert_json_to_yaml(
    self, source_path: Path, target_format: str, working_root: Path
) -> Path:
    """json.loads -> yaml.safe_dump (flow style off, JSON key order kept)."""
    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _unsupported(
            "json",
            "yaml",
            f"JSON to YAML conversion failed: file is not valid JSON ({exc}).",
        ) from exc
    if data is None:
        raise _unsupported(
            "json",
            "yaml",
            "JSON to YAML conversion failed: the file contains no data.",
        )
    output_path = working_root / f"{source_path.stem}.{target_format}"
    output_path.write_text(
        yaml.safe_dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return output_path


XmlToJsonPlugin = make_plugin_class(
    slug="xml-to-json",
    source_formats=["xml"],
    target_formats=["json"],
    engine_hook=_convert_xml_to_json,
    name="XML to JSON",
    description="Convert XML documents to JSON data files.",
    category="data",
    engine="data",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    seo_title="XML to JSON Converter | Converigo",
    seo_description="Convert XML documents to JSON data files quickly and easily.",
)

JsonToXmlPlugin = make_plugin_class(
    slug="json-to-xml",
    source_formats=["json"],
    target_formats=["xml"],
    engine_hook=_convert_json_to_xml,
    name="JSON to XML",
    description="Convert JSON data files to clean, indented XML documents.",
    category="data",
    engine="data",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    seo_title="JSON to XML Converter | Converigo",
    seo_description="Convert JSON data files to well-formed XML documents quickly and easily.",
)

YamlToJsonPlugin = make_plugin_class(
    slug="yaml-to-json",
    source_formats=["yaml", "yml"],
    target_formats=["json"],
    engine_hook=_convert_yaml_to_json,
    name="YAML to JSON",
    description="Convert YAML data files to JSON data files.",
    category="data",
    engine="data",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    seo_title="YAML to JSON Converter | Converigo",
    seo_description="Convert YAML (and YML) data files to JSON format quickly and easily.",
)

JsonToYamlPlugin = make_plugin_class(
    slug="json-to-yaml",
    source_formats=["json"],
    target_formats=["yaml"],
    engine_hook=_convert_json_to_yaml,
    name="JSON to YAML",
    description="Convert JSON data files to YAML data files.",
    category="data",
    engine="data",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    seo_title="JSON to YAML Converter | Converigo",
    seo_description="Convert JSON data files to human-friendly YAML format quickly and easily.",
)
