"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F0)
Version : 1.0.0

Factory contract generator (F0 deliverable 2).

Deterministic generator for the two converter artifacts required by the
existing governance stack:

- ``<slug>.json``         : converter landing-page payload (the schema used
  by app/data/converters/<slug>.json - hero, features, FAQ, how-to,
  about-formats, CTA, SEO).
- ``<slug>.contract.json``: the machine contract validated by
  app/services/converter_registry_service.py (ConverterRegistryService).

Validation is REUSED, not reimplemented: generated artifacts are loaded
through ConverterRegistryService, so the generator can never produce a
contract that the production validator rejects (required fields, types,
lifecycle values, duplicate ids/slugs).

CLI:
  python scripts/factory_contract_gen.py --selftest
      Build artifacts for a sample spec in a temp dir, validate them with
      the real ConverterRegistryService, print PASS, clean up.
  python scripts/factory_contract_gen.py --spec-file specs.json --out-dir app/data/converters
      Build artifacts for every spec in the JSON file (list of spec dicts)
      and write them into out-dir.
  python scripts/factory_contract_gen.py --check --out-dir app/data/converters
      Validate the contract files already present in out-dir with the real
      ConverterRegistryService and print a summary (governance reuse).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.converter_registry_service import (  # noqa: E402
    ConverterRegistryError,
    ConverterRegistryService,
)

SITE_BASE_URL = "https://converigo.com"


def _require(spec: dict[str, Any], field: str) -> Any:
    value = spec.get(field)
    if not value:
        raise ValueError(f"Spec field '{field}' is required")
    return value


# ---------------------------------------------------------------------------
# Spec -> contract JSON
# ---------------------------------------------------------------------------


def build_contract_json(spec: dict[str, Any]) -> dict[str, Any]:
    """Build the .contract.json payload from a spec dict.

    Required spec fields: slug, name, category, description,
    source_formats, target_formats, accepted_mime_types, conversion_engine.
    Optional: max_upload_mb (default 500), platforms (default ["web"]),
    regression_sample (default tests/sample.<first-source>).
    """
    slug = str(_require(spec, "slug")).strip().lower()
    source_formats = [str(f).strip().lower() for f in spec["source_formats"]]
    target_formats = [str(f).strip().lower() for f in spec["target_formats"]]
    mimes = [str(m) for m in _require(spec, "accepted_mime_types")]

    return {
        "id": slug,
        "slug": slug,
        "name": str(_require(spec, "name")),
        "category": str(spec.get("category", "converter")).strip().lower(),
        "description": str(_require(spec, "description")),
        "input_formats": source_formats,
        "output_formats": target_formats,
        "accepted_mime_types": mimes,
        "max_upload_size": int(spec.get("max_upload_mb", 500)) * 1024 * 1024,
        "conversion_engine": str(_require(spec, "conversion_engine")),
        "landing_path": f"/{slug}",
        "canonical_url": f"{SITE_BASE_URL}/{slug}",
        "seo_status": spec.get("seo_status", "ready"),
        "schema_status": spec.get("schema_status", "ready"),
        "faq_status": spec.get("faq_status", "ready"),
        "regression_sample": str(
            spec.get("regression_sample", f"tests/sample.{source_formats[0]}")
        ),
        "supported_platforms": [str(p) for p in spec.get("platforms", ["web"])],
        "lifecycle_status": spec.get("lifecycle_status", "active"),
    }


# ---------------------------------------------------------------------------
# Spec -> page JSON (app/data/converters/<slug>.json schema)
# ---------------------------------------------------------------------------


def _default_faq(src: str, tgt: str) -> list[dict[str, str]]:
    return [
        {
            "question": f"How do I convert a {src} file to {tgt}?",
            "answer": (
                f"Upload your {src} file to Converigo and the {tgt} output "
                "will be ready for download immediately."
            ),
        },
        {
            "question": "Is the conversion secure?",
            "answer": (
                "Yes, files are processed securely on our servers and "
                "automatically deleted after conversion."
            ),
        },
        {
            "question": "What file sizes are supported?",
            "answer": (
                f"{src} files up to 500MB can be converted instantly on Converigo."
            ),
        },
        {
            "question": "Can I convert files on mobile?",
            "answer": "Yes, Converigo works on all modern browsers and devices.",
        },
    ]


def build_page_json(spec: dict[str, Any]) -> dict[str, Any]:
    """Build the landing-page payload from a spec dict.

    Optional spec fields: title, popular, featured, related_tools
    (list of {slug,title}), faq (list of {question,answer}),
    keywords (comma string), about_source, about_target.
    """
    slug = str(_require(spec, "slug")).strip().lower()
    name = str(_require(spec, "name"))
    description = str(_require(spec, "description"))
    source_formats = [str(f).strip().upper() for f in spec["source_formats"]]
    target_formats = [str(f).strip().upper() for f in spec["target_formats"]]
    src0, tgt0 = source_formats[0], target_formats[0]

    faq = [
        {"question": str(qa["question"]), "answer": str(qa["answer"])}
        for qa in spec.get("faq", _default_faq(src0, tgt0))
    ]

    page = {
        "slug": slug,
        "title": str(spec.get("title", f"{src0} to {tgt0} Converter")),
        "description": description,
        "upload_form": {
            "action": "/upload",
            "method": "post",
            "accept": " ".join(f".{f.lower()}" for f in source_formats),
            "button_text": f"Upload {src0}",
        },
        "faq": faq,
        "related_tools": [
            {"slug": str(rt["slug"]), "title": str(rt["title"])}
            for rt in spec.get("related_tools", [])
        ],
        "seo": {
            "title": f"{src0} to {tgt0} Converter Online Free | Converigo",
            "description": (
                f"Convert {src0} files to {tgt0} online for free using "
                "Converigo. Fast, secure browser-based conversion with no "
                "software installation required."
            ),
            "keywords": str(
                spec.get("keywords", f"{slug}, {src0} to {tgt0}, converigo")
            ),
            "image": "/static/images/og-default.png",
            "og_image_alt": (
                f"Convert {src0} to {tgt0} - Converigo free online converter"
            ),
            "twitter_title": f"{src0} to {tgt0} Converter Online Free | Converigo",
            "twitter_description": (
                f"Convert {src0} files to {tgt0} online for free using "
                "Converigo. Fast, secure browser-based conversion with no "
                "software installation required."
            ),
            "twitter_image": "/static/images/og-default.png",
            "canonical": f"{SITE_BASE_URL}/tools/{slug}",
        },
        "source": source_formats[0].lower(),
        "target": target_formats[0].lower(),
        "category": str(spec.get("category", "converter")).strip().lower(),
        "active": True,
        "popular": bool(spec.get("popular", False)),
        "featured": bool(spec.get("featured", False)),
    }

    page["hero"] = {
        "eyebrow": "Converter",
        "title": f"Convert {src0} to {tgt0} Online Free",
        "description": (
            f"Convert {src0} files to {tgt0} online for free. Fast, "
            "secure browser-based conversion with no software "
            f"installation. Get high-quality {target_formats[0].lower()} "
            "output in seconds using Converigo."
        ),
        "panel_label": "Ready to convert",
        "panel_title": (
            f"Upload a {src0} file and receive your "
            f"{target_formats[0].lower()} output instantly."
        ),
    }
    page["features"] = [
        {
            "title": "Instant conversion",
            "text": (
                f"Convert {src0} to {tgt0} in seconds without installing "
                "any software."
            ),
        },
        {
            "title": "Secure processing",
            "text": (
                "Your files are processed securely and automatically "
                "deleted after conversion."
            ),
        },
        {
            "title": "Large file support",
            "text": f"Convert {src0} files up to 500MB in size instantly.",
        },
        {
            "title": "Cross-platform",
            "text": "Works on Windows, Mac, Linux, and all modern mobile devices.",
        },
    ]
    page["supported_formats"] = {
        "input": source_formats,
        "output": target_formats,
        "description": f"{src0} input, {target_formats[0].lower()} output",
    }
    page["how_to_use"] = [
        {
            "title": f"Upload your {src0} file",
            "description": (
                f"Select a {src0} file from your device to begin the conversion."
            ),
        },
        {
            "title": "Wait for processing",
            "description": (
                "Converigo processes the conversion instantly with secure handling."
            ),
        },
        {
            "title": f"Download your {tgt0} file",
            "description": (
                f"Get the {target_formats[0].lower()} output ready to "
                "download immediately."
            ),
        },
    ]
    page["about_formats"] = [
        {
            "title": f"What is a {src0} file?",
            "text": spec.get(
                "about_source",
                f"A {src0} file is processed fully server-side by "
                "Converigo - no plugin or download needed.",
            ),
        },
        {
            "title": f"Why convert {src0} to {tgt0}?",
            "text": spec.get(
                "about_target",
                f"The {target_formats[0].lower()} output keeps your data "
                "portable and ready for the tools you use next.",
            ),
        },
    ]
    page["cta"] = {
        "eyebrow": "Ready to convert",
        "title": f"Convert {src0} files in seconds",
        "text": (
            f"Upload your {src0} file and get the "
            f"{target_formats[0].lower()} output instantly."
        ),
        "primary_text": "Convert now",
        "secondary_text": "Read FAQs",
        "primary_href": "#converter",
        "secondary_href": "#faq",
    }
    page["lifecycle_status"] = spec.get("lifecycle_status", "active")
    return page


# ---------------------------------------------------------------------------
# Validation (REUSED from the production validator - not reimplemented)
# ---------------------------------------------------------------------------


def validate_contracts_dir(contracts_dir: Path) -> list[dict[str, Any]]:
    """Load+validate every *.contract.json in dir via ConverterRegistryService.

    Raises ConverterRegistryError on any invalid or duplicate contract.
    """
    service = ConverterRegistryService(contracts_dir)
    contracts = service.list_all()
    if not contracts:
        raise ConverterRegistryError(
            f"No contract files found under {contracts_dir}"
        )
    return contracts


def write_artifacts(
    spec: dict[str, Any],
    out_dir: Path,
) -> tuple[Path, Path]:
    """Build both artifacts for one spec and write them into out_dir."""
    slug = str(_require(spec, "slug")).strip().lower()
    contract = build_contract_json(spec)
    page = build_page_json(spec)

    contract_path = out_dir / f"{slug}.contract.json"
    page_path = out_dir / f"{slug}.json"

    contract_path.write_text(
        json.dumps(contract, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    page_path.write_text(
        json.dumps(page, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return page_path, contract_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _selftest() -> int:
    sample_spec = {
        "slug": "csv-to-json",
        "name": "CSV to JSON",
        "description": "Convert CSV data files to JSON format.",
        "category": "spreadsheet",
        "conversion_engine": "spreadsheet",
        "source_formats": ["csv"],
        "target_formats": ["json"],
        "accepted_mime_types": ["text/csv"],
        "regression_sample": "tests/sample.csv",
    }
    with tempfile.TemporaryDirectory(prefix="factory_contract_selftest_") as tmp:
        out_dir = Path(tmp)
        page_path, contract_path = write_artifacts(sample_spec, out_dir)
        contracts = validate_contracts_dir(out_dir)
        contract = contracts[0]
        assert contract["slug"] == "csv-to-json", contract
        page = json.loads(page_path.read_text(encoding="utf-8"))
        for key in (
            "slug", "title", "description", "upload_form", "faq", "seo",
            "source", "target", "category", "hero", "features",
            "supported_formats", "how_to_use", "about_formats", "cta",
            "lifecycle_status",
        ):
            assert key in page, f"page JSON missing '{key}'"
        print(f"contract file : {contract_path.name}  VALID")
        print(f"page file     : {page_path.name}  {len(page)} top-level keys")
    print("SELFTEST PASS: generator output accepted by ConverterRegistryService.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if "--selftest" in args:
        return _selftest()

    out_dir = Path("app/data/converters")
    if "--out-dir" in args:
        out_dir = Path(args[args.index("--out-dir") + 1])

    if "--check" in args:
        contracts = validate_contracts_dir(out_dir)
        print(
            f"CHECK PASS: {len(contracts)} contract(s) in {out_dir} are valid "
            "per ConverterRegistryService."
        )
        for contract in contracts:
            print(f"  - {contract['slug']}: {contract['lifecycle_status']}")
        return 0

    if "--spec-file" in args:
        spec_path = Path(args[args.index("--spec-file") + 1])
        specs = json.loads(spec_path.read_text(encoding="utf-8"))
        if isinstance(specs, dict):
            specs = [specs]
        written: list[str] = []
        for spec in specs:
            page_path, contract_path = write_artifacts(spec, out_dir)
            written.extend([page_path.name, contract_path.name])
            print(f"WROTE {out_dir / page_path.name}")
            print(f"WROTE {out_dir / contract_path.name}")
        print(f"{len(written)} artifact file(s) written. Run --check to validate.")
        return 0

    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

