"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F8)
Version : 1.0.0

In-image probe for Factory Batch F8 (5 net-new converters, 3 sub-batches).

Executed INSIDE the production image by docker-runtime-verify
(dispatch with probe_script=scripts/ci_in_f8_probe.py):

    python scripts/ci_in_f8_probe.py

All fixtures are generated in-image (Pillow / mammoth / markdown / stdlib),
so the probe is self-sufficient exactly like the F1-F6 probes.  The five
F8 net-new plugins are resolved through the real registry and executed
through their public async convert(); the artifact policies (contracts for
the tracked-sample slugs, page-only for md-to-html / html-to-csv) are
asserted.  Exit code 0 = PASS.
"""
from __future__ import annotations

import asyncio
import base64
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image  # noqa: E402

from app.plugins.registry import registry  # noqa: E402

NET_NEW = [
    "docx-to-md",
    "image-to-base64",
    "base64-to-image",
    "md-to-html",
    "html-to-csv",
]
PAGE_ONLY = ("md-to-html", "html-to-csv")

MD_TEXT = "# Probe heading\n\nBody with **bold** text.\n"
HTML_TEXT = (
    "<html><body><table><tr><th>k</th></tr><tr><td>v</td></tr></table></body></html>"
)


async def _convert(slug: str, source: Path, target: str, working: Path) -> Path:
    plugin = registry.by_slug[slug]
    return await plugin.convert(source, target, output_dir=working)


def _verify_png(path: Path) -> None:
    with Image.open(path) as image:
        assert image.format == "PNG", image.format


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="f8_probe_") as tmp:
        root = Path(tmp)

        png = root / "probe.png"
        Image.new("RGB", (8, 8), (10, 200, 30)).save(png, format="PNG")

        docx = root / "probe.docx"
        try:
            from docx import Document

            document = Document()
            document.add_heading("Probe", level=1)
            document.add_paragraph("F8 probe body")
            document.save(str(docx))
        except ImportError as exc:  # pragma: no cover - requirements pin it
            failures.append(f"python-docx unavailable: {exc}")
            docx = None

        plan = [
            ("image-to-base64", png, "txt", None),
            ("base64-to-image", None, "png", png),
            ("md-to-html", None, "html", None),
            ("html-to-csv", None, "csv", None),
        ]

        for slug, source, target, roundtrip_source in plan:
            try:
                assert registry.has_slug(slug), f"{slug} not registered"
                if slug == "base64-to-image":
                    fixture = root / "probe_b64.txt"
                    fixture.write_text(
                        "data:image/png;base64,"
                        + base64.b64encode(png.read_bytes()).decode("ascii"),
                        encoding="ascii",
                    )
                    source = fixture
                elif slug == "md-to-html":
                    source = root / "probe.md"
                    source.write_text(MD_TEXT, encoding="utf-8")
                elif slug == "html-to-csv":
                    source = root / "probe.html"
                    source.write_text(HTML_TEXT, encoding="utf-8")
                output_path = asyncio.run(_convert(
                    slug, source, target, root / f"out_{slug.replace('-', '_')}"
                ))
                assert output_path.is_file() and output_path.stat().st_size > 0
                if target == "png":
                    _verify_png(output_path)
                print(f"F8 PROBE OK: {slug} ({source.suffix} -> {target})")
                if roundtrip_source is not None and slug == "base64-to-image":
                    with Image.open(roundtrip_source) as original, Image.open(output_path) as rebuilt:
                        assert rebuilt.size == original.size
                        assert rebuilt.convert("RGB").tobytes() == original.convert("RGB").tobytes()
                    print("F8 PROBE OK: base64 round-trip is pixel-identical")
            except Exception as exc:  # noqa: BLE001 - probe reports all
                failures.append(f"{slug}: {type(exc).__name__}: {exc}")

        if docx is not None:
            try:
                assert registry.has_slug("docx-to-md")
                output_path = asyncio.run(_convert(
                    "docx-to-md", docx, "md", root / "out_docx_to_md"
                ))
                text = output_path.read_text(encoding="utf-8")
                assert "Probe" in text, text[:120]
                print("F8 PROBE OK: docx-to-md (docx -> md)")
            except Exception as exc:  # noqa: BLE001 - probe reports all
                failures.append(f"docx-to-md: {type(exc).__name__}: {exc}")

        converters_dir = (
            Path(__file__).resolve().parent.parent / "app" / "data" / "converters"
        )
        for slug in NET_NEW:
            page = converters_dir / f"{slug}.json"
            if page.exists():
                print(f"F8 PROBE OK: D9 page artifact {page.name}")
            else:
                failures.append(f"D9 page artifact missing: {page.name}")
        for slug in PAGE_ONLY:
            contract = converters_dir / f"{slug}.contract.json"
            if contract.exists():
                failures.append(
                    f"unexpected contract artifact (page-only policy): {contract.name}"
                )
            else:
                print(f"F8 PROBE OK: page-only policy holds for {slug}")

    if failures:
        print("F8 PROBE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("F8 PROBE: PASS (5/5 net-new converters verified in-image)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
