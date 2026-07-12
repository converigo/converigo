from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.services.converter_data_service import ConverterDataService
from app.services.language_service import LanguageService
from app.services.seo_service import PRODUCTION_BASE_URL, SeoService

router = APIRouter(prefix="/tools", tags=["tools"])
converter_data_service = ConverterDataService(Path("app/data/converters"))
seo_service = SeoService(Path("app/data/converters"))
language_service = LanguageService(Path("app/locales"))


async def render_universal_tool_page(
    request: Request,
    slug: str,
    canonical_path: str | None = None,
    meta_overrides: dict[str, str] | None = None,
    faq_items: list[dict[str, str]] | None = None,
) -> HTMLResponse:
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    try:
        tool_data = converter_data_service.load_converter_by_slug(slug)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Tool page not found")

    seo_data = seo_service.build_tool_meta(request, tool_data)
    related_tools = converter_data_service.resolve_related_tools(tool_data, limit=4)

    fallback_faq = []
    label = tool_data.get("title", "").replace(" Converter", "").strip()
    slug = tool_data.get("slug", "")
    if label:
        fallback_faq = [
            {
                "question": f"What is {label} conversion?",
                "answer": f"Use this tool to convert {label} files quickly and securely.",
            },
            {
                "question": f"How do I convert {label}?",
                "answer": "Upload your file, choose the output format, and download the converted result.",
            },
            {
                "question": f"Is {label} converter free?",
                "answer": "Yes, this converter is free to use for standard conversion tasks.",
            },
            {
                "question": f"Why convert {label}?",
                "answer": f"Converting {label} helps improve compatibility, sharing, and workflow automation.",
            },
        ]
        if slug.endswith("-png") or slug.endswith("-to-png"):
            fallback_faq.append(
                {
                    "question": "Does PNG preserve image quality?",
                    "answer": "PNG uses lossless compression, so image quality stays intact during conversion.",
                }
            )

    faq_items = list(faq_items or tool_data.get("faq", []))
    existing_questions = {item.get("question", "").lower() for item in faq_items}
    for fallback_item in fallback_faq:
        if fallback_item["question"].lower() not in existing_questions:
            faq_items.append(fallback_item)

    if meta_overrides:
        seo_data.update(meta_overrides)

    if canonical_path is not None:
        seo_data["canonical"] = f"{PRODUCTION_BASE_URL}{canonical_path}"
        seo_data["og_url"] = seo_data["canonical"]

    return templates.TemplateResponse(
        request=request,
        name="tool_page.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "title": seo_data["title"],
            "meta": seo_data,
            "seo": seo_data,
            "tool": tool_data,
            "faq": faq_items,
            "upload_form": tool_data.get("upload_form", {}),
            "related_tools": related_tools,
            "structured_data": seo_service.build_structured_data(request, tool_data),
        },
    )


@router.get("/{slug}", response_class=HTMLResponse)
async def tool_page(request: Request, slug: str):
    return await render_universal_tool_page(request, slug, canonical_path=f"/tools/{slug}")
