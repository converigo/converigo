from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.services.article_service import ArticleService
from app.services.language_service import LanguageService
from app.services.seo_service import PRODUCTION_BASE_URL, SeoService
from app.services.internal_link_service import InternalLinkService
from pathlib import Path

router = APIRouter(tags=["learning"])

ARTICLE_DIR = (Path(__file__).resolve().parents[1] / "data" / "articles").resolve()
article_service = ArticleService(ARTICLE_DIR)
seo_service = SeoService(Path("app/data/converters"))
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
    articles = article_service.list_articles()
    locale_data, t, supported_locales = _get_locale_context(request)

    metadata = {
        "title": "Learning Center | Converigo",
        "description": "Explore practical learning resources and guides for file conversion workflows.",
        "canonical": f"{PRODUCTION_BASE_URL}/learning",
        "og_url": f"{PRODUCTION_BASE_URL}/learning",
        "keywords": "learning center, file conversion guides, how to convert files",
        "author": "Converigo",
        "robots": "index,follow",
    }

    return templates.TemplateResponse(
        request=request,
        name="pages/learning_index.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "meta": metadata,
            "articles": articles,
            "structured_data": seo_service.build_structured_data(
                request,
                page_type="blog_index",
                page_data={
                    "name": "Learning Center",
                    "description": metadata["description"],
                    "url": "/learning",
                    "articles": articles,
                },
            ),
            "year": 2026,
        },
    )


@router.get("/learning/{slug}", response_class=HTMLResponse)
async def learning_article(request: Request, slug: str) -> HTMLResponse:
    article = article_service.load_article(slug)
    if article is None:
        raise HTTPException(status_code=404, detail="Learning article not found")

    locale_data, t, supported_locales = _get_locale_context(request)
    breadcrumb = [
        {"name": "Home", "url": "/"},
        {"name": "Learning", "url": "/learning"},
        {"name": str(article.get("title", slug)), "url": f"/learning/{slug}"},
    ]
    metadata = {
        "title": str(article.get("title", slug)),
        "description": str(article.get("description", "")),
        "canonical": f"{PRODUCTION_BASE_URL}/learning/{slug}",
        "og_url": f"{PRODUCTION_BASE_URL}/learning/{slug}",
        "keywords": ", ".join(str(item) for item in article.get("keywords", [])),
        "author": str(article.get("author", "Converigo")),
        "robots": "index,follow",
    }

    # Infer and attach related converters when missing using topic/format signals
    try:
        if not article.get("related_converters"):
            candidates: list[str] = []
            formats = [str(f).lower() for f in (article.get("related_formats") or article.get("topics") or []) if f]
            for fmt in formats:
                try:
                    links = internal_link_service.get_links_for_format(fmt)
                except Exception:
                    links = {}
                for itm in links.get("related_converters", []) or []:
                    href = str(itm.get("href", "")).strip()
                    slug_candidate = ""
                    if href.startswith("/tools/"):
                        slug_candidate = href.split("/tools/", 1)[1].split("/")[0]
                    elif href.startswith("/"):
                        slug_candidate = href.lstrip("/").split("/")[0]
                    else:
                        slug_candidate = href
                    if slug_candidate and slug_candidate not in candidates:
                        candidates.append(slug_candidate)
                    if len(candidates) >= 6:
                        break
                if len(candidates) >= 6:
                    break
            if candidates:
                article["related_converters"] = candidates

        # Infer and attach related articles when missing by topic overlap
        if not article.get("related_articles"):
            candidates: list[str] = []
            this_topics = set(str(x).lower() for x in (article.get("topics") or []) + (article.get("related_formats") or []))
            for other in article_service.list_articles():
                other_slug = other.get("slug")
                if not other_slug or other_slug == article.get("slug"):
                    continue
                other_topics = set(str(x).lower() for x in (other.get("topics") or []) + (other.get("related_formats") or []))
                if this_topics & other_topics:
                    candidates.append(other_slug)
                if len(candidates) >= 6:
                    break
            if candidates:
                article["related_articles"] = candidates
    except Exception:
        # Non-fatal: leave article as-is if inference fails
        pass

    return templates.TemplateResponse(
        request=request,
        name="pages/learning_article.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "meta": metadata,
            "article": {
                **article,
                "breadcrumb": breadcrumb,
                "canonical": metadata["canonical"],
                "og_url": metadata["og_url"],
            },
            "structured_data": seo_service.build_structured_data(
                request,
                page_type="blog_article",
                page_data={
                    "headline": str(article.get("title", slug)),
                    "description": str(article.get("description", "")),
                    "url": f"/learning/{slug}",
                    "breadcrumb": breadcrumb,
                },
            ),
            "year": 2026,
        },
    )
