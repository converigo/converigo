from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LanguageService:
    def __init__(self, locales_dir: Path, default_locale: str = "en") -> None:
        self.locales_dir = locales_dir
        self.default_locale = default_locale
        self._cache: dict[str, dict[str, Any]] = {}

    def get_supported_locales(self) -> list[str]:
        if not self.locales_dir.exists():
            return [self.default_locale]
        return sorted(
            path.stem
            for path in self.locales_dir.iterdir()
            if path.is_file() and path.suffix.lower() == ".json"
        )

    def locale_exists(self, locale_code: str) -> bool:
        locale_file = self.locales_dir / f"{locale_code}.json"
        return locale_file.exists()

    def determine_locale(self, accept_language: str | None = None, lang_query: str | None = None) -> str:
        if lang_query:
            candidate = lang_query.strip().lower().split("-")[0]
            if self.locale_exists(candidate):
                return candidate

        if accept_language:
            for language_entry in accept_language.split(","):
                language_code = language_entry.split(";")[0].strip().lower()
                if not language_code:
                    continue
                if self.locale_exists(language_code):
                    return language_code
                if "-" in language_code:
                    base_code = language_code.split("-", 1)[0]
                    if self.locale_exists(base_code):
                        return base_code

        return self.default_locale

    def load_locale(
        self,
        accept_language: str | None = None,
        lang_query: str | None = None,
    ) -> dict[str, Any]:
        locale_code = self.determine_locale(accept_language=accept_language, lang_query=lang_query)
        if locale_code in self._cache:
            return self._cache[locale_code]

        locale_file = self.locales_dir / f"{locale_code}.json"
        try:
            with locale_file.open("r", encoding="utf-8") as handle:
                locale_data = json.load(handle)
        except FileNotFoundError:
            locale_file = self.locales_dir / f"{self.default_locale}.json"
            with locale_file.open("r", encoding="utf-8") as handle:
                locale_data = json.load(handle)
            locale_code = self.default_locale

        locale_data["lang_code"] = locale_code
        self._cache[locale_code] = locale_data
        return locale_data

    def translate(self, locale_data: dict[str, Any], key: str, default: str = "") -> str:
        current: Any = locale_data
        for part in key.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return str(current) if not isinstance(current, dict) else default
