"""
Project : Converigo
Service : Result Widget Feature Flags (F0)

Runtime feature-flag resolver for the dual result-widget migration.

Reads ``app/data/feature_flags.json`` on every request and resolves whether the
V2 "Hasil Konversi" result widget is enabled for a given ``/tools/<slug>`` page.

Scope grammar (inside ``scope``):

* ``slug:<slug>``          -> matches one tool page
* ``category:<category>``  -> matches every tool page in that category
* ``all``                  -> matches everything

The file is re-read only when its mtime changes, so toggling a flag takes
effect without a redeploy and without a restart.  When the file is missing or
malformed the flag is treated as OFF (fail-safe default).
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

from app.core.settings import settings

logger = logging.getLogger(__name__)

FLAG_KEY = "result_widget_v2"
DEFAULT_FLAG_STATE: dict[str, Any] = {"enabled": False, "scope": []}


class ResultWidgetFlagService:
    """Reads and evaluates the ``result_widget_v2`` feature flag."""

    def __init__(self, flags_path: Path | str | None = None) -> None:
        self._path = Path(flags_path) if flags_path is not None else Path(settings.FEATURE_FLAGS_PATH)
        self._lock = threading.Lock()
        self._cached_mtime: float | None = None
        self._cached_payload: dict[str, Any] = {}

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> dict[str, Any]:
        try:
            mtime = self._path.stat().st_mtime
        except OSError:
            return {}

        with self._lock:
            if self._cached_mtime == mtime:
                return self._cached_payload

            payload: dict[str, Any] = {}
            try:
                parsed = json.loads(self._path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                logger.warning("Feature flag file could not be read/parsed: %s", self._path)
                parsed = {}

            if isinstance(parsed, dict):
                payload = parsed

            self._cached_mtime = mtime
            self._cached_payload = payload
            return payload

    def get_flag(self, key: str = FLAG_KEY) -> dict[str, Any]:
        raw_flag = self._load().get(key)
        if not isinstance(raw_flag, dict):
            return {"enabled": False, "scope": []}

        scope = raw_flag.get("scope") or []
        if isinstance(scope, str):
            scope = [scope]
        elif not isinstance(scope, (list, tuple, set)):
            scope = []

        clean_scope: list[str] = []
        for entry in scope:
            text = str(entry).strip()
            if text:
                clean_scope.append(text)

        return {"enabled": bool(raw_flag.get("enabled", False)), "scope": clean_scope}

    @staticmethod
    def _matches(scope_entry: str, slug: str | None, category: str | None) -> bool:
        entry = scope_entry.strip().lower()
        if not entry:
            return False
        if entry == "all":
            return True
        if entry.startswith("slug:"):
            target = entry[len("slug:"):].strip()
            return bool(target) and bool(slug) and target == str(slug).strip().lower()
        if entry.startswith("category:"):
            target = entry[len("category:"):].strip()
            return bool(target) and bool(category) and target == str(category).strip().lower()
        return False

    def is_enabled(
        self,
        *,
        slug: str | None = None,
        category: str | None = None,
        key: str = FLAG_KEY,
    ) -> bool:
        flag = self.get_flag(key)
        if not flag["enabled"]:
            return False
        return any(self._matches(entry, slug, category) for entry in flag["scope"])


result_widget_service = ResultWidgetFlagService()


def is_result_widget_v2_enabled(*, slug: str | None = None, category: str | None = None) -> bool:
    """Convenience wrapper used by the routers."""
    return result_widget_service.is_enabled(slug=slug, category=category)