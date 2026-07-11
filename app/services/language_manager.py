from pathlib import Path

from app.services.language_service import LanguageService


class LanguageManager:
    def __init__(self, locales_dir: Path, default_locale: str = "en") -> None:
        self.service = LanguageService(locales_dir, default_locale)

    def get_supported_locales(self) -> list[str]:
        return self.service.get_supported_locales()

    def locale_exists(self, locale_code: str) -> bool:
        return self.service.locale_exists(locale_code)

    def determine_locale(self, accept_language: str | None = None, lang_query: str | None = None) -> str:
        return self.service.determine_locale(accept_language=accept_language, lang_query=lang_query)

    def load_locale(
        self,
        accept_language: str | None = None,
        lang_query: str | None = None,
    ) -> dict[str, str]:
        return self.service.load_locale(accept_language=accept_language, lang_query=lang_query)

    def translate(self, locale_data: dict[str, str], key: str, default: str = "") -> str:
        return self.service.translate(locale_data, key, default)
