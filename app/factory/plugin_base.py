"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F0)
Version : 1.0.0

Factory Plugin Base - configurable thin plugin template.

Jalur 2 (Factory Batch Plan, F0): formalizes the proven certified-plugin
pattern (Gate-1/Gate-2 clusters: discovery -> supports() check -> engine
call -> single servable file -> honest RuntimeError for unsupported input)
into one declarative base class, so a batch of converters is expressed as
configuration instead of boilerplate.

Design rules (governance unchanged):
- One concrete subclass per slug: the registry keeps independent entries.
- The subclass (or the spec passed to make_plugin_class) owns slug, name,
  description, source/target formats, engine wiring and metadata; the base
  owns the conversion pipeline skeleton and the output guarantees.
- Output MUST be a single servable FILE (the /download route serves files,
  not directories).
- Unsupported input raises RuntimeError -> the API maps it to 422
  UNSUPPORTED_CONVERSION (honest error, never a fake output).

Note: this module intentionally lives OUTSIDE app/plugins/ because plugin
discovery rglobs every app/plugins/**/*.py file; an intermediate base class
placed there would be discovered as if it were a plugin.  Concrete factory
plugins still live under app/plugins/<cluster>/ and are discovered as usual.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from app.plugins.base import ConverterPlugin

#: Signature of a fully declarative conversion hook:
#: (plugin, source_path, target_format, working_root) -> output_path
EngineHook = Callable[[ConverterPlugin, Path, str, Path], Path]


class FactoryConversionPlugin(ConverterPlugin):
    """Configurable thin base class for factory-built converters.

    Subclasses (or specs built via :func:`make_plugin_class`) declare the
    usual ConverterPlugin identity attributes plus:

    - ``working_subdir``: subfolder of the output root used when the caller
      supplies neither ``temp_dir`` nor ``output_dir``.
    - ``min_output_bytes``: minimum accepted output size (default 1 byte,
      i.e. empty files are rejected).

    Subclasses must either implement :meth:`_convert` or be built with an
    ``engine_hook``; the public :meth:`convert` pipeline (supports-check,
    working root setup, single-file guarantee, empty-output rejection) is
    inherited unchanged so every factory converter behaves identically at
    the API boundary.
    """

    # --------------------------------------------------
    # Declarative configuration
    # --------------------------------------------------

    working_subdir: str = "factory"

    min_output_bytes: int = 1

    # --------------------------------------------------
    # Conversion pipeline (template method)
    # --------------------------------------------------

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        slug_label = self.slug or type(self).__name__

        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError(self.unsupported_message())

        from app.core.settings import settings

        working_root = (
            temp_dir
            or output_dir
            or (settings.OUTPUT_DIR / self.working_subdir)
        )
        working_root.mkdir(parents=True, exist_ok=True)

        output_path = Path(self._convert(source_path, target_format, working_root))

        if not output_path.is_file():
            raise RuntimeError(
                f"{slug_label} did not produce a single servable output file."
            )
        if output_path.stat().st_size < self.min_output_bytes:
            raise RuntimeError(f"{slug_label} produced an empty output file.")
        return output_path

    def _convert(
        self,
        source_path: Path,
        target_format: str,
        working_root: Path,
    ) -> Path:
        """Perform the actual conversion; return the single output file path.

        ``working_root`` is an existing directory the implementation may use
        for intermediates; the returned path must be a servable file.
        """
        raise NotImplementedError(
            "Factory plugin must implement _convert() or be built via "
            "make_plugin_class(engine_hook=...)."
        )

    # --------------------------------------------------
    # Metadata helpers
    # --------------------------------------------------

    def unsupported_message(self) -> str:
        """Honest, non-fabricated error text for unsupported input."""
        source_list = ", ".join(self.source_formats) or "?"
        target_list = ", ".join(self.target_formats) or "?"
        return (
            f"{self.slug or type(self).__name__} only supports "
            f"{source_list} -> {target_list} conversion."
        )

    def default_display_name(self) -> str:
        source = " / ".join(f.upper() for f in self.source_formats)
        target = " / ".join(f.upper() for f in self.target_formats)
        return f"{source} to {target} Converter"


#: Metadata keys accepted by make_plugin_class (ConverterPlugin attributes).
METADATA_KEYS = frozenset({
    "name", "description", "category", "engine", "goal", "use_case",
    "priority", "quality", "compatibility", "estimated_saving",
    "badge", "icon", "color", "seo_title", "seo_description",
})


def make_plugin_class(
    base: type[FactoryConversionPlugin] = FactoryConversionPlugin,
    *,
    slug: str,
    source_formats: list[str],
    target_formats: list[str],
    engine_hook: EngineHook | None = None,
    class_name: str | None = None,
    working_subdir: str = "factory",
    min_output_bytes: int = 1,
    **metadata: Any,
) -> type[FactoryConversionPlugin]:
    """Build a concrete plugin class from a declarative spec.

    Typical factory usage inside ``app/plugins/<cluster>/<slug>.py``::

        from app.factory import make_plugin_class

        CSVToJSONPlugin = make_plugin_class(
            slug="csv-to-json",
            source_formats=["csv"],
            target_formats=["json"],
            engine_hook=_convert_csv_to_json,
            name="CSV to JSON",
            description="Convert CSV data files to JSON format.",
            category="spreadsheet",
            engine="spreadsheet",
        )

    ``engine_hook`` is a plain synchronous callable receiving the plugin
    instance, the source path, the requested target format and an existing
    working directory; it must return a single servable output file path.

    ``metadata`` accepts any ConverterPlugin class attribute (see
    METADATA_KEYS).  Missing values are derived deterministically from
    slug/formats so every generated plugin has complete, honest metadata
    without boilerplate.
    """
    if not slug or not str(slug).strip():
        raise ValueError("make_plugin_class requires a non-empty slug.")
    slug = str(slug).strip().lower()
    source_formats = [str(f).strip().lower() for f in source_formats]
    target_formats = [str(f).strip().lower() for f in target_formats]
    if not source_formats or not target_formats:
        raise ValueError(
            f"make_plugin_class({slug}): source/target formats must be non-empty."
        )
    if not working_subdir:
        raise ValueError(f"make_plugin_class({slug}): working_subdir must be non-empty.")

    unknown_metadata = set(metadata) - METADATA_KEYS
    if unknown_metadata:
        raise TypeError(
            f"make_plugin_class({slug}): unsupported metadata keys: "
            f"{sorted(unknown_metadata)}"
        )

    src_label = source_formats[0].upper()
    tgt_label = target_formats[0].upper()

    if class_name is None:
        class_name = (
            "".join(part.capitalize() for part in slug.replace("_", "-").split("-"))
            + "Plugin"
        )

    attrs: dict[str, Any] = {
        "slug": slug,
        "source_formats": source_formats,
        "target_formats": target_formats,
        "working_subdir": working_subdir,
        "min_output_bytes": int(min_output_bytes),
        "name": f"{src_label} to {tgt_label} Converter",
        "description": f"Convert {src_label} files to {tgt_label} format.",
        "category": "converter",
        "engine": base.engine or "",
        "goal": "conversion",
        "use_case": (
            f"Best when users need to convert {src_label} files to "
            f"{tgt_label} quickly."
        ),
        "priority": 60,
        "quality": 90,
        "compatibility": 90,
        "estimated_saving": 0,
        "badge": f"{tgt_label} Output",
        "seo_title": f"{src_label} to {tgt_label} Converter | Converigo",
        "seo_description": (
            f"Convert {src_label} files to {tgt_label} format online. "
            "Fast, free, and secure."
        ),
    }
    attrs.update(metadata)

    if engine_hook is not None:
        def _convert(
            self: FactoryConversionPlugin,
            source_path: Path,
            target_format: str,
            working_root: Path,
            _hook: EngineHook = engine_hook,
        ) -> Path:
            return _hook(self, source_path, target_format, working_root)

        attrs["_convert"] = _convert

    return type(class_name, (base,), attrs)