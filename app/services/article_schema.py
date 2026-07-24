from __future__ import annotations

import re
from typing import Any


class ArticleSchemaValidator:
    """Validate Learning Center article JSON payloads."""

    REQUIRED_FIELDS = {
        "slug",
        "title",
        "description",
        "category",
        "topics",
        "author",
        "date_published",
        "read_time_minutes",
        "keywords",
        "sections",
        "faq",
    }

    OPTIONAL_FIELDS = {
        "date_modified",
        "seo_keywords",
        "og_image",
        "og_image_alt",
        "canonical",
        "featured",
        "order",
        "related_formats",
        "related_converters",
        "related_articles",
        "call_to_action",
        "related_tools",
        "breadcrumb_override",
    }

    def validate_article(self, article: dict[str, Any]) -> list[str]:
        """Validate the article structure and return a list of validation errors."""
        if not isinstance(article, dict):
            return ["article must be an object"]

        errors: list[str] = []

        for field in sorted(self.REQUIRED_FIELDS):
            if field not in article:
                errors.append(f"missing required field: {field}")
                continue

            value = article[field]
            if field == "slug":
                if not isinstance(value, str) or not str(value).strip():
                    errors.append("slug must be a non-empty string")
                elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(value)):
                    errors.append("slug must be a lowercase slug")
            elif field in {"title", "description", "category", "author"}:
                if not isinstance(value, str) or not str(value).strip():
                    errors.append(f"{field} must be a non-empty string")
            elif field in {"topics", "keywords"}:
                if not isinstance(value, list) or not all(isinstance(item, str) and str(item).strip() for item in value):
                    errors.append(f"{field} must be a list of non-empty strings")
            elif field == "read_time_minutes":
                if not isinstance(value, int) or value <= 0:
                    errors.append("read_time_minutes must be a positive integer")
            elif field == "date_published":
                if not isinstance(value, str) or not str(value).strip():
                    errors.append("date_published must be a non-empty string")
            elif field == "sections":
                self._validate_sections(value, errors)
            elif field == "faq":
                self._validate_faq(value, errors)

        for field in sorted(self.OPTIONAL_FIELDS):
            if field not in article:
                continue

            value = article[field]
            if field == "featured" and not isinstance(value, bool):
                errors.append("featured must be a boolean")
            elif field == "order" and not isinstance(value, int):
                errors.append("order must be an integer")
            elif field in {"seo_keywords", "related_formats", "related_converters", "related_articles"}:
                if not isinstance(value, list) or not all(isinstance(item, str) and str(item).strip() for item in value):
                    errors.append(f"{field} must be a list of non-empty strings")
            elif field in {"date_modified", "og_image", "og_image_alt", "canonical"}:
                if not isinstance(value, str) or not str(value).strip():
                    errors.append(f"{field} must be a non-empty string")
            elif field == "call_to_action":
                self._validate_call_to_action(value, errors)
            elif field == "related_tools":
                self._validate_related_tools(value, errors)
            elif field == "breadcrumb_override":
                self._validate_breadcrumb_override(value, errors)

        return errors

    def _validate_sections(self, value: Any, errors: list[str]) -> None:
        if not isinstance(value, list):
            errors.append("sections must be a list")
            return

        for index, item in enumerate(value):
            if not isinstance(item, dict):
                errors.append(f"sections[{index}] must be an object")
                continue
            if not isinstance(item.get("id"), str) or not str(item.get("id", "")).strip():
                errors.append(f"sections[{index}].id must be a non-empty string")
            if not isinstance(item.get("title"), str) or not str(item.get("title", "")).strip():
                errors.append(f"sections[{index}].title must be a non-empty string")
            if not isinstance(item.get("content"), str) or not str(item.get("content", "")).strip():
                errors.append(f"sections[{index}].content must be a non-empty string")

    def _validate_faq(self, value: Any, errors: list[str]) -> None:
        if not isinstance(value, list):
            errors.append("faq must be a list")
            return

        for index, item in enumerate(value):
            if not isinstance(item, dict):
                errors.append(f"faq[{index}] must be an object")
                continue
            if not isinstance(item.get("question"), str) or not str(item.get("question", "")).strip():
                errors.append(f"faq[{index}].question must be a non-empty string")
            if not isinstance(item.get("answer"), str) or not str(item.get("answer", "")).strip():
                errors.append(f"faq[{index}].answer must be a non-empty string")

    def _validate_call_to_action(self, value: Any, errors: list[str]) -> None:
        if not isinstance(value, dict):
            errors.append("call_to_action must be an object")
            return
        if not isinstance(value.get("text"), str) or not str(value.get("text", "")).strip():
            errors.append("call_to_action.text must be a non-empty string")
        if not isinstance(value.get("url"), str) or not str(value.get("url", "")).strip():
            errors.append("call_to_action.url must be a non-empty string")
        if not isinstance(value.get("button_text"), str) or not str(value.get("button_text", "")).strip():
            errors.append("call_to_action.button_text must be a non-empty string")

    def _validate_related_tools(self, value: Any, errors: list[str]) -> None:
        if not isinstance(value, list):
            errors.append("related_tools must be a list")
            return
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                errors.append(f"related_tools[{index}] must be an object")
                continue
            if not isinstance(item.get("slug"), str) or not str(item.get("slug", "")).strip():
                errors.append(f"related_tools[{index}].slug must be a non-empty string")
            if not isinstance(item.get("title"), str) or not str(item.get("title", "")).strip():
                errors.append(f"related_tools[{index}].title must be a non-empty string")
            if not isinstance(item.get("description"), str) or not str(item.get("description", "")).strip():
                errors.append(f"related_tools[{index}].description must be a non-empty string")
            if not isinstance(item.get("href"), str) or not str(item.get("href", "")).strip():
                errors.append(f"related_tools[{index}].href must be a non-empty string")

    def _validate_breadcrumb_override(self, value: Any, errors: list[str]) -> None:
        if not isinstance(value, list):
            errors.append("breadcrumb_override must be a list")
            return
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                errors.append(f"breadcrumb_override[{index}] must be an object")
                continue
            if not isinstance(item.get("name"), str) or not str(item.get("name", "")).strip():
                errors.append(f"breadcrumb_override[{index}].name must be a non-empty string")
            if not isinstance(item.get("url"), str) or not str(item.get("url", "")).strip():
                errors.append(f"breadcrumb_override[{index}].url must be a non-empty string")
