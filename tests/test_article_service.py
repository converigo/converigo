from __future__ import annotations

import json
from pathlib import Path

from app.services.article_service import ArticleService


def _write_article(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_article_service_discovers_and_loads_articles(tmp_path: Path) -> None:
    articles_dir = tmp_path / "articles"
    fundamentals_dir = articles_dir / "fundamentals"
    guides_dir = articles_dir / "guides"

    _write_article(
        fundamentals_dir / "getting-started.json",
        {
            "slug": "getting-started",
            "title": "Getting Started",
            "description": "Learn the basics of file conversion.",
            "category": "Fundamentals",
            "topics": ["basics"],
            "author": "Converigo",
            "date_published": "2026-07-01",
            "read_time_minutes": 5,
            "keywords": ["conversion", "basics"],
            "sections": [{"id": "intro", "title": "Intro", "content": "Intro content."}],
            "faq": [{"question": "Why convert?", "answer": "To use files in another format."}],
        },
    )
    _write_article(
        guides_dir / "batch-conversion.json",
        {
            "slug": "batch-conversion",
            "title": "Batch Conversion",
            "description": "Convert multiple files with one workflow.",
            "category": "Guides",
            "topics": ["workflow"],
            "author": "Converigo",
            "date_published": "2026-07-05",
            "read_time_minutes": 6,
            "keywords": ["batch", "workflow"],
            "sections": [{"id": "workflow", "title": "Workflow", "content": "Workflow content."}],
            "faq": [{"question": "Is batch conversion supported?", "answer": "Yes."}],
        },
    )

    service = ArticleService(articles_dir)

    files = service.discover_article_files()
    assert len(files) == 2
    assert files[0].name == "batch-conversion.json"

    article = service.load_article("getting-started")
    assert article is not None
    assert article["slug"] == "getting-started"
    assert article["category"] == "Fundamentals"

    all_articles = service.list_articles()
    assert len(all_articles) == 2

    fundamentals_articles = service.list_articles_by_category("Fundamentals")
    assert len(fundamentals_articles) == 1
    assert fundamentals_articles[0]["slug"] == "getting-started"

    errors = service.validate_article(
        {
            "slug": "sample",
            "title": "Sample",
            "description": "Sample description",
            "category": "Fundamentals",
            "topics": ["sample"],
            "author": "Converigo",
            "date_published": "2026-07-01",
            "read_time_minutes": 3,
            "keywords": ["sample"],
            "sections": [{"id": "intro", "title": "Intro", "content": "Yes"}],
            "faq": [{"question": "Why?", "answer": "Because."}],
        }
    )
    assert errors == []

    invalid_errors = service.validate_article({"slug": "bad"})
    assert invalid_errors
