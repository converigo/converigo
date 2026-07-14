from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.services.comparison_service import ComparisonService
from app.services.language_service import LanguageService
from app.services.seo_service import PRODUCTION_BASE_URL

router = APIRouter()
comparison_service = ComparisonService(Path("app/data/converters"))
language_service = LanguageService(Path("app/locales"))


@router.get("/pdf-vs-docx", response_class=HTMLResponse)
async def pdf_vs_docx(request: Request) -> HTMLResponse:
    return await _render_comparison_page(request, "pdf-vs-docx")


@router.get("/png-vs-jpg", response_class=HTMLResponse)
async def png_vs_jpg(request: Request) -> HTMLResponse:
    return await _render_comparison_page(request, "png-vs-jpg")


@router.get("/webp-vs-png", response_class=HTMLResponse)
async def webp_vs_png(request: Request) -> HTMLResponse:
    return await _render_comparison_page(request, "webp-vs-png")


@router.get("/mp4-vs-mov", response_class=HTMLResponse)
async def mp4_vs_mov(request: Request) -> HTMLResponse:
    return await _render_comparison_page(request, "mp4-vs-mov")


@router.get("/mp3-vs-wav", response_class=HTMLResponse)
async def mp3_vs_wav(request: Request) -> HTMLResponse:
    return await _render_comparison_page(request, "mp3-vs-wav")


async def _render_comparison_page(request: Request, slug: str) -> HTMLResponse:
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    try:
        context = comparison_service.render_context(request, slug)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    comparison = context["comparison"]
    comparison["meta"]["canonical"] = f"{PRODUCTION_BASE_URL}/{slug}"
    comparison["meta"]["og_url"] = f"{PRODUCTION_BASE_URL}/{slug}"

    return templates.TemplateResponse(
        request=request,
        name="pages/comparison_page.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "title": comparison["seo_title"],
            "meta": comparison["meta"],
            "comparison": comparison,
            "structured_data": comparison["json_ld"],
            "faq": comparison["faq"],
            "related_tools": comparison["related_converters"],
            "year": 2026,
        },
    )
