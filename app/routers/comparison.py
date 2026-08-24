from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.services.comparison_service import ComparisonService
from app.services.language_service import LanguageService

router = APIRouter()
comparison_service = ComparisonService(Path("app/data/converters"))
language_service = LanguageService(Path("app/locales"))


def _get_locale_context(request: Request):
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    return locale_data, t, language_service.get_supported_locales()


def _render_comparison_page(request: Request, slug: str) -> HTMLResponse:
    try:
        context = comparison_service.render_context(request, slug)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Comparison page not found") from exc

    locale_data, t, supported_locales = _get_locale_context(request)
    context.update({
        "locale": locale_data,
        "t": t,
        "supported_locales": supported_locales,
    })
    return templates.TemplateResponse(
        request=request,
        name="pages/comparison_page.html",
        context=context,
    )


@router.get("/pdf-vs-docx", response_class=HTMLResponse)
async def pdf_vs_docx(request: Request) -> HTMLResponse:
    return _render_comparison_page(request, "pdf-vs-docx")


@router.get("/png-vs-jpg", response_class=HTMLResponse)
async def png_vs_jpg(request: Request) -> HTMLResponse:
    return _render_comparison_page(request, "png-vs-jpg")


@router.get("/webp-vs-png", response_class=HTMLResponse)
async def webp_vs_png(request: Request) -> HTMLResponse:
    return _render_comparison_page(request, "webp-vs-png")


@router.get("/mp4-vs-mov", response_class=HTMLResponse)
async def mp4_vs_mov(request: Request) -> HTMLResponse:
    return _render_comparison_page(request, "mp4-vs-mov")


@router.get("/mp3-vs-wav", response_class=HTMLResponse)
async def mp3_vs_wav(request: Request) -> HTMLResponse:
    return _render_comparison_page(request, "mp3-vs-wav")
