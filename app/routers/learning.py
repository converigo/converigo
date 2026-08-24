from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.services.article_service import ArticleService
from app.services.language_service import LanguageService
from app.services.internal_link_service import InternalLinkService
from app.services.public_seo_service import PRODUCTION_BASE_URL, build_public_page_seo
from pathlib import Path

router = APIRouter(tags=["learning"])

ARTICLE_DIR = (Path(__file__).resolve().parents[1] / "data" / "articles").resolve()
article_service = ArticleService(ARTICLE_DIR)
internal_link_service = InternalLinkService(Path("app/data/converters"))
language_service = LanguageService((Path(__file__).resolve().parents[1] / "locales").resolve())


def _get_locale_context(request: Request) -> tuple[dict[str, Any], Any, list[str]]:
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    return locale_data, t, language_service.get_supported_locales()


@router.get("/learning", response_class=HTMLResponse)
async def learning_index(request: Request) -> HTMLResponse:
    locale_data, t, supported_locales = _get_locale_context(request)
    articles = article_service.list_articles()[:12]
    seo = build_public_page_seo(
        "/learning",
        "Learning Center | Converigo",
        "Browse practical file conversion guides, explanations, and workflow tips from Converigo.",
        schema_type="WebPage",
        breadcrumbs=[{"name": "Home", "url": "/"}, {"name": "Learning", "url": "/learning"}],
    )
    return templates.TemplateResponse(
        request=request,
        name="pages/learning_index.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "meta": seo["meta"],
            "articles": articles,
            "structured_data": seo["structured_data"],
            "year": datetime.utcnow().year,
        },
    )


@router.get("/learning/{slug}", response_class=HTMLResponse)
async def learning_article(request: Request, slug: str) -> HTMLResponse:
    article = article_service.load_article(slug)
    if article is None:
        raise HTTPException(status_code=404, detail="Learning article not found")

    locale_data, t, supported_locales = _get_locale_context(request)
    seo = build_public_page_seo(
        f"/learning/{slug}",
        str(article.get("title") or "Learning article"),
        str(article.get("description") or "Learn more with Converigo."),
        schema_type="Article",
        breadcrumbs=[
            {"name": "Home", "url": "/"},
            {"name": "Learning", "url": "/learning"},
            {"name": str(article.get("title") or slug), "url": f"/learning/{slug}"},
        ],
        faq_items=article.get("faq") or [],
    )
    return templates.TemplateResponse(
        request=request,
        name="pages/learning_article.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "meta": seo["meta"],
            "article": article,
            "structured_data": seo["structured_data"],
            "year": datetime.utcnow().year,
        },
    )
