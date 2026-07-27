from __future__ import annotations

from app.services.article_schema import ArticleSchemaValidator
from app.services.article_service import ArticleService


def test_validator_reports_required_and_type_errors() -> None:
    validator = ArticleSchemaValidator()
    errors = validator.validate_article({"slug": "Bad Slug"})

    assert "missing required field: title" in errors
    assert "slug must be a lowercase slug" in errors


def test_validator_reports_section_and_faq_errors() -> None:
    validator = ArticleSchemaValidator()
    errors = validator.validate_article(
        {
            "slug": "valid-slug",
            "title": "Valid title",
            "description": "Valid description",
            "category": "Fundamentals",
            "topics": ["basics"],
            "author": "Converigo",
            "date_published": "2026-07-01",
            "read_time_minutes": 4,
            "keywords": ["conversion"],
            "sections": [{"id": "", "title": "", "content": 123}],
            "faq": [{"question": "", "answer": 5}],
        }
    )

    assert any("sections[0].id must be a non-empty string" in error for error in errors)
    assert any("sections[0].content must be a non-empty string" in error for error in errors)
    assert any("faq[0].question must be a non-empty string" in error for error in errors)
    assert any("faq[0].answer must be a non-empty string" in error for error in errors)


def test_article_service_reuses_schema_validator() -> None:
    service = ArticleService("app/data/articles")
    valid_article = {
        "slug": "schema-example",
        "title": "Schema Example",
        "description": "A valid article for schema validation.",
        "category": "Fundamentals",
        "topics": ["schema"],
        "author": "Converigo",
        "date_published": "2026-07-01",
        "read_time_minutes": 3,
        "keywords": ["schema"],
        "sections": [{"id": "intro", "title": "Intro", "content": "Content"}],
        "faq": [{"question": "Why?", "answer": "Because."}],
    }

    assert service.validate_article(valid_article) == []
