from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

from app.core.registry import ConverterInfo, ConverterRegistry, registry


class SitemapService:
    """Generate and validate category sitemaps from the converter registry."""

    CATEGORY_FILES = {
        "video": "sitemap-video.xml",
        "image": "sitemap-image.xml",
        "pdf": "sitemap-pdf.xml",
        "audio": "sitemap-audio.xml",
    }

    def __init__(
        self,
        output_dir: Path | str,
        registry_instance: ConverterRegistry | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.registry = registry_instance or registry

    def discover_active_converters(self) -> list[Any]:
        converters = []
        for converter in self.registry.get_all():
            enabled = getattr(converter, "enabled", True)
            if enabled is False:
                continue
            converters.append(converter)
        return converters

    def generate_all(self, base_url: str = "https://converigo.com") -> list[str]:
        base_url = self._normalize_base_url(base_url)
        converters = self.discover_active_converters()
        if not converters:
            raise ValueError("No active converters available for sitemap generation")

        expected_urls: set[str] = set()
        generated_entries: list[tuple[str, str]] = []

        for converter in converters:
            landing_path = self._infer_landing_path(converter)
            canonical_url = str(getattr(converter, "canonical_url", "") or "").strip()

            if not landing_path:
                raise ValueError(f"Missing landing path for converter '{converter.id}'")

            expected_url = self._build_canonical_url(base_url, landing_path)
            if canonical_url and canonical_url != expected_url:
                raise ValueError(
                    f"Canonical URL mismatch for converter '{converter.id}': {canonical_url} != {expected_url}"
                )

            if expected_url in expected_urls:
                raise ValueError(f"Duplicate URL detected: {expected_url}")

            expected_urls.add(expected_url)
            generated_entries.append((self._category_key(converter), expected_url))

        category_groups: dict[str, list[str]] = {key: [] for key in self.CATEGORY_FILES}
        for category, url in generated_entries:
            if category in category_groups:
                category_groups[category].append(url)

        written_files: list[str] = []
        for category in self.CATEGORY_FILES:
            file_path = self.output_dir / self.CATEGORY_FILES[category]
            urls = category_groups[category]
            self._write_urlset(file_path, urls)
            written_files.append(self.CATEGORY_FILES[category])

        index_path = self.output_dir / "sitemap.xml"
        self._write_sitemap_index(index_path, base_url, written_files)
        written_files.insert(0, "sitemap.xml")
        return written_files

    def validate(self) -> list[str]:
        issues: list[str] = []
        converters = self.discover_active_converters()
        if not converters:
            return ["No active converters available for sitemap validation"]

        expected_urls: set[str] = set()
        for converter in converters:
            landing_path = self._infer_landing_path(converter)
            if not landing_path:
                issues.append(f"Missing landing path for converter '{converter.id}'")
                continue

            canonical_url = str(getattr(converter, "canonical_url", "") or "").strip()
            expected_url = self._build_canonical_url(self._default_base_url(), landing_path)
            if canonical_url and canonical_url != expected_url:
                issues.append(f"Canonical URL mismatch for converter '{converter.id}'")

            if expected_url in expected_urls:
                issues.append(f"Duplicate URL detected: {expected_url}")
            expected_urls.add(expected_url)

        generated_urls: set[str] = set()
        for category_file in self.CATEGORY_FILES.values():
            file_path = self.output_dir / category_file
            if not file_path.exists():
                issues.append(f"Missing sitemap file: {category_file}")
                continue

            urls = self._read_urls(file_path)
            generated_urls.update(urls)

        index_path = self.output_dir / "sitemap.xml"
        if not index_path.exists():
            issues.append("Missing sitemap index: sitemap.xml")
            return issues

        for converter in converters:
            landing_path = self._infer_landing_path(converter)
            expected_url = self._build_canonical_url(self._default_base_url(), landing_path)
            occurrences = sum(1 for url in generated_urls if url == expected_url)
            if occurrences != 1:
                issues.append(f"Converter '{converter.id}' appears {occurrences} times")

        return issues

    def _category_key(self, converter: Any) -> str:
        category = str(getattr(converter, "category", "") or "").lower()
        if category in self.CATEGORY_FILES:
            return category
        return "video"

    def _infer_landing_path(self, converter: Any) -> str:
        landing_path = str(getattr(converter, "landing_path", "") or "").strip()
        if landing_path:
            return landing_path

        raw_slug = getattr(converter, "slug", None) or getattr(converter, "id", None)
        if raw_slug:
            slug = str(raw_slug).strip().lower().replace("_", "-")
            if slug:
                return f"/{slug}"

        if isinstance(converter, ConverterInfo):
            slug = str(converter.id).strip().lower().replace("_", "-")
            return f"/{slug}"

        return ""

    def _build_canonical_url(self, base_url: str, landing_path: str) -> str:
        normalized_path = landing_path if landing_path.startswith("/") else f"/{landing_path}"
        return f"{base_url.rstrip('/')}{normalized_path}"

    def _normalize_base_url(self, base_url: str) -> str:
        return base_url.rstrip("/")

    def _default_base_url(self) -> str:
        return "https://converigo.com"

    def _write_urlset(self, path: Path, urls: Iterable[str]) -> None:
        root = ET.Element("urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})
        for url in urls:
            url_element = ET.SubElement(root, "url")
            loc_element = ET.SubElement(url_element, "loc")
            loc_element.text = url
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)

    def _write_sitemap_index(self, path: Path, base_url: str, category_files: Iterable[str]) -> None:
        root = ET.Element("sitemapindex", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})
        for category_file in category_files:
            sitemap_element = ET.SubElement(root, "sitemap")
            loc_element = ET.SubElement(sitemap_element, "loc")
            loc_element.text = f"{base_url.rstrip('/')}/{category_file}"
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)

    def _read_urls(self, path: Path) -> list[str]:
        tree = ET.parse(path)
        root = tree.getroot()
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        return [element.text for element in root.findall(".//sm:url/sm:loc", namespace) if element.text]
