from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.article_schema import ArticleSchemaValidator


class ArticleService:
    """Discover, load, and validate learning center articles from JSON files."""

    def __init__(self, articles_dir: Path | str | None = None) -> None:
        self.articles_dir = Path(articles_dir or "app/data/articles")
        self.validator = ArticleSchemaValidator()

    def discover_article_files(self) -> list[Path]:
        """Discover article JSON files by scanning the articles directory tree."""
        if not self.articles_dir.exists():
            return []

        files = [
            path
            for path in self.articles_dir.rglob("*.json")
            if path.is_file() and not path.name.startswith("_") and path.parent != self.articles_dir
        ]
        return sorted(files, key=lambda path: path.name.lower())

    def load_article(self, slug: str) -> dict[str, Any] | None:
        """Load the article with the provided slug from disk."""
        if not slug:
            return None

        for path in self.discover_article_files():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            if str(data.get("slug", "")).strip() != slug:
                continue

            return data

        return None

    def list_articles(self) -> list[dict[str, Any]]:
        """Return all discovered articles as dictionaries."""
        articles: list[dict[str, Any]] = []
        for path in self.discover_article_files():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

            if not isinstance(data, dict):
                continue

            articles.append(data)

        return sorted(
            articles,
            key=lambda item: (
                str(item.get("category", "")).lower(),
                int(item.get("order", 999999)),
                str(item.get("title", "")).lower(),
            ),
        )

    def list_articles_by_category(self, category: str) -> list[dict[str, Any]]:
        """Return all articles that belong to the requested category."""
        if not category:
            return []

        target_category = str(category).strip().lower()
        return [
            article
            for article in self.list_articles()
            if str(article.get("category", "")).strip().lower() == target_category
        ]

    def validate_article(self, article: dict[str, Any]) -> list[str]:
        """Validate the article structure and return validation errors."""
        return self.validator.validate_article(article)
