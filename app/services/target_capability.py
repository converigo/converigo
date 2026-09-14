"""
Project : Converigo
Version : 3.0.0

D5 — single authoritative source for user-facing conversion capability.

Every UI surface that offers a "convert to X" choice must render from this
module. Before D5 the homepage (``converigo_main.html``) and the tool-page
result widget (``tool_result_widget_v2.js``) each carried a hand-maintained
``STATIC_TARGET_MAP`` literal, and both drifted from what the converter registry
can actually dispatch (e.g. ``pdf -> WORD`` was advertised for months while the
pair resolving it was a placeholder that always fails).

Authority model
---------------
The authority is ``PluginRegistry.plugins`` — the ``(source, target)`` pair index
``get_plugin()`` actually consults for pair-based dispatch — filtered by what the
user can really do:

1. ``file_validator.ALLOWED_EXTENSIONS`` gates the SOURCE. A source that cannot
   be uploaded can never start a conversion, so it must not own a row. It
   deliberately does NOT gate the target: a target is an output, and
   ``gz -> gzip`` is a live dispatchable output that is not uploadable.
2. ``advertisable`` gates the capability. A plugin that cannot honour a pair (the
   office placeholders) stays registered so the honest ``UNSUPPORTED_CONVERSION``
   message still fires, but it is excluded here so it can never be offered.
3. Self-conversion (``source == target``) is NOT advertised in the plain
   conversion view. The pair index contains format-preserving operations
   (``jpg->jpg`` watermark, ``png->png``/``mp4->mp4`` compress, ``pdf->pdf``
   split) as well as the archive extracts, and the homepage posts no
   ``operation`` field — so offering a self entry there would silently run an
   operation the user never asked for. Operation pages opt in by passing
   ``operation=<slug>``, which authorizes the pairs from
   ``PluginRegistry.slug_winner_pairs`` — the exact set ``get_plugin(slug=...)``
   accepts, so what is offered can never disagree with what is dispatchable.

Alias handling
--------------
Backend acceptance of alias tokens (``word``, ``doc``, ``powerpoint``, ...) is
unchanged: ``/convert`` and the plugins still take them. This module only decides
what the *user* may see, and the rule is that the option value must be the
canonical extension actually delivered:

- ``doc/xls/ppt`` fold to ``docx/xlsx/pptx`` because ``DocumentEngine`` and the
  office plugins normalize the output filename to the OOXML form.
- ``word/powerpoint/spreadsheet`` are product names, not extensions, so they fold
  too — and if a source ever had no dispatchable canonical pair to fold onto, the
  token is dropped and recorded in ``rejections`` rather than shown as an option
  (a red parity test beats a dead dropdown entry).

Folding only ever merges into a pair that is itself dispatchable, so it can never
invent a capability.
"""

from __future__ import annotations

import json
import re
from typing import NamedTuple

from app.plugins.registry import registry as default_registry
from app.utils.file_validator import ALLOWED_EXTENSIONS

__all__ = [
    "CapabilityView",
    "TARGET_CANONICAL",
    "PRODUCT_ALIAS_TOKENS",
    "AUTO_DEFAULT_FIRST",
    "TARGET_ORDER_PREFERENCE",
    "build_capability",
    "conversion_capability",
    "capability_json",
]

# Legacy Office extension tokens -> the extension actually delivered.
TARGET_CANONICAL = {
    "doc": "docx",
    "xls": "xlsx",
    "ppt": "pptx",
    "word": "docx",
    "powerpoint": "pptx",
    "spreadsheet": "xlsx",
}

# Tokens that are product names rather than file extensions. These must never
# become user-visible option values: the option value is an extension, and the
# payload must match what the winning plugin delivers.
PRODUCT_ALIAS_TOKENS = frozenset({"word", "powerpoint", "spreadsheet"})

# ``addFiles()`` in both consumers auto-selects the first entry as the default,
# so array order IS the default-target policy. WS1 pinned wav -> MP3 after a
# production regression (a .wav upload silently ran wav-to-flac because the
# literal had been reordered to ['FLAC','MP3']); mp3 -> WAV keeps the pre-D5
# homepage default. Listed targets come first in the given order, anything else
# the registry adds follows alphabetically.
AUTO_DEFAULT_FIRST = {"wav": "mp3", "mp3": "wav"}
TARGET_ORDER_PREFERENCE = {
    "wav": ["mp3", "flac", "aac"],
    "mp3": ["wav", "aac"],
}

# Anything user-facing must look like a file extension: short and alphanumeric.
# This also guarantees the injected JSON is inert inside a <script> context.
_TOKEN_RE = re.compile(r"^[a-z0-9]{1,8}$")


class CapabilityView(NamedTuple):
    """Derived capability plus an audit trail of everything dropped."""

    map: dict[str, list[str]]
    rejections: list[str]


def _is_advertisable(plugin: object) -> bool:
    # Opt-out flag: only plugins that explicitly declare themselves
    # non-advertisable (placeholders) are hidden. Objects without the attribute
    # stay visible so test stubs and third-party plugins keep working.
    return getattr(plugin, "advertisable", True) is not False


def _order(source: str, targets: set[str]) -> list[str]:
    ordered = sorted(targets)
    preferred = [t for t in TARGET_ORDER_PREFERENCE.get(source, ()) if t in targets]
    if preferred:
        return preferred + [t for t in ordered if t not in preferred]
    pinned = AUTO_DEFAULT_FIRST.get(source)
    if pinned and pinned in ordered:
        ordered.remove(pinned)
        ordered.insert(0, pinned)
    return ordered


def build_capability(
    operation: str | None = None,
    *,
    registry=None,
    allowed_extensions=None,
) -> CapabilityView:
    """Derive the user-facing ``source -> [TARGET, ...]`` capability map.

    ``operation`` additionally authorizes the pairs ``get_plugin()`` would accept
    for that slug (including the legitimate self-conversions used by the archive
    extract pages), so a mounted widget advertises exactly what its own request
    contract can resolve — and nothing else.
    """

    reg = registry or default_registry
    allowed = ALLOWED_EXTENSIONS if allowed_extensions is None else allowed_extensions
    pair_index = reg.plugins
    rejections: list[str] = []
    collected: dict[str, set[str]] = {}

    def admit(source: str, target: str, *, allow_self: bool) -> None:
        canonical = TARGET_CANONICAL.get(target, target)
        if canonical != target:
            folded_pair = (source, canonical)
            if folded_pair in pair_index and _is_advertisable(pair_index[folded_pair]):
                # Fold onto a pair that really dispatches: dedupe, never invent.
                target = canonical
            elif target in PRODUCT_ALIAS_TOKENS:
                rejections.append(
                    f"{source}->{target}: product-alias option value with no "
                    f"dispatchable ({source},{canonical}) pair"
                )
                return
        if not _TOKEN_RE.match(target):
            rejections.append(f"{source}->{target}: not a file-extension token")
            return
        if target == source and not allow_self:
            return
        collected.setdefault(source, set()).add(target)

    # 1. Plain conversion view: the index pair-based dispatch resolves against.
    for (source, target), plugin in pair_index.items():
        if not _is_advertisable(plugin):
            rejections.append(f"{source}->{target}: winning plugin is not advertisable")
            continue
        if source not in allowed:
            continue
        if source == target:
            # Format-preserving operation: operation-context only.
            continue
        admit(source, target, allow_self=False)

    # 2. Operation overlay: the winner's own claim set, which is precisely the
    #    authority PluginRegistry.get_plugin(slug=...) guards with.
    if operation:
        slug = str(operation).lower().strip()
        plugin = getattr(reg, "by_slug", {}).get(slug)
        claimed = getattr(reg, "slug_winner_pairs", {}).get(slug, set())
        if plugin is None:
            rejections.append(f"{slug}: operation is not registered")
        elif not _is_advertisable(plugin):
            rejections.append(f"{slug}: operation winner is not advertisable")
        else:
            for source, target in sorted(claimed):
                if source not in allowed:
                    continue
                admit(source, target, allow_self=True)

    view = {
        source: _order(source, targets)
        for source, targets in sorted(collected.items())
    }
    return CapabilityView(map=view, rejections=sorted(set(rejections)))


def conversion_capability(registry=None) -> dict[str, list[str]]:
    """The plain conversion view, upper-cased for direct use as UI options."""

    return _upper(build_capability(registry=registry).map)


def capability_json(operation: str | None = None, *, registry=None) -> str:
    """Serialize the capability map for injection into a rendered page.

    Compact separators are deliberate: ``tests/test_wav_ui_default_target.py``
    parses the served homepage with ``const STATIC_TARGET_MAP = {...};`` and
    ``key:[...]`` regexes, so the injected object literal must keep that exact
    textual shape. Every token has already been shape-checked by
    :func:`build_capability`, so the payload is inert in a script context.
    """

    return json.dumps(
        _upper(build_capability(operation, registry=registry).map),
        sort_keys=True,
        separators=(",", ":"),
    )


def _upper(view_map: dict[str, list[str]]) -> dict[str, list[str]]:
    return {
        source: [target.upper() for target in targets]
        for source, targets in view_map.items()
    }
