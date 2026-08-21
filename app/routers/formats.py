
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.services.authority_service import AuthorityService
from app.services.converter_registry_service import ConverterRegistryService
from app.services.format_knowledge_service import FormatKnowledgeService
from app.services.internal_link_service import InternalLinkService
from app.services.language_service import LanguageService
from app.services.seo_service import PRODUCTION_BASE_URL, SeoService

router = APIRouter(tags=["formats"])

CONTRACTS_DIR = (Path(__file__).resolve().parents[1] / "data" / "converters").resolve()
FORMAT_KNOWLEDGE_DIR = (Path(__file__).resolve().parents[1] / "data" / "format_knowledge").resolve()
seo_service = SeoService(CONTRACTS_DIR)
language_service = LanguageService((Path(__file__).resolve().parents[1] / "locales").resolve())


def _format_knowledge_service() -> FormatKnowledgeService:
    return FormatKnowledgeService(FORMAT_KNOWLEDGE_DIR)

def _authority_service() -> AuthorityService:
    return AuthorityService(CONTRACTS_DIR)



def _converter_registry() -> ConverterRegistryService:
    return ConverterRegistryService(CONTRACTS_DIR)


def _internal_link_service() -> InternalLinkService:
    return InternalLinkService(CONTRACTS_DIR)


def _known_formats() -> list[str]:
    service = _authority_service()
    return sorted(service.generate_all().keys())


def _get_locale_context(request: Request) -> tuple[dict[str, Any], Any, list[str]]:
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    return locale_data, t, language_service.get_supported_locales()


def _build_related_converters(format_name: str, limit: int = 6) -> list[dict[str, Any]]:
    registry = _converter_registry()
    converters: list[dict[str, Any]] = []
    for contract in registry.get_active():
        input_formats = [str(item).strip().lower() for item in contract.get("input_formats", []) if str(item).strip()]
        output_formats = [str(item).strip().lower() for item in contract.get("output_formats", []) if str(item).strip()]
        if format_name in input_formats or format_name in output_formats:
            slug = str(contract.get("slug", "")).strip()
            if not slug:
                continue
            converters.append(
                {
                    "slug": slug,
                    "title": str(contract.get("name", slug)).strip(),
                    "description": str(contract.get("description", "")).strip(),
                    "href": str(contract.get("landing_path", f"/tools/{slug}")).strip() or f"/tools/{slug}",
                }
            )
    return converters[:limit]


@router.get("/formats", response_class=HTMLResponse)
async def format_index(request: Request) -> HTMLResponse:
    locale_data, t, supported_locales = _get_locale_context(request)
    formats = _known_formats()
    return templates.TemplateResponse(
        request=request,
        name="pages/format_index.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "meta": {
                "title": "Format Encyclopedia | Converigo",
                "description": "Explore the Converigo Format Encyclopedia for detailed information on every supported file format.",
                "canonical": f"{PRODUCTION_BASE_URL}/formats",
                "og_url": f"{PRODUCTION_BASE_URL}/formats",
            },
            "formats": formats,
            "structured_data": seo_service.build_structured_data(
                request,
                page_type="trust_page",
                page_data={
                    "name": "Format Encyclopedia",
                    "description": "Explore the Converigo Format Encyclopedia for detailed information on every supported file format.",
                    "url": "/formats",
                },
            ),
        },
    )


@router.get("/formats/{format_name}", response_class=HTMLResponse)
async def format_page(request: Request, format_name: str) -> HTMLResponse:
    normalized = str(format_name or "").strip().lower()
    formats = _known_formats()
    if normalized not in formats:
        raise HTTPException(status_code=404, detail="Format encyclopedia page not found")

    service = _authority_service()
    try:
        payload = service.generate_payload(normalized)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Format encyclopedia page not found") from exc

    # Merge knowledge enrichment if available (graceful fallback)
    knowledge_service = _format_knowledge_service()
    try:
        enrichment = knowledge_service.build_enrichment(normalized)
        if enrichment is not None:
            payload["format_knowledge"] = enrichment["format_knowledge"]
    except (ValueError, OSError):
        # Graceful degradation: continue without knowledge enrichment
        pass

    seo_meta = dict(payload.get("seo", {}))
    canonical = f"{PRODUCTION_BASE_URL}/formats/{normalized}"
    seo_meta["canonical"] = canonical
    seo_meta["og_url"] = canonical
    seo_meta["keywords"] = seo_meta.get("keywords", f"{normalized}, file format, {normalized} file")

    knowledge_faq = payload.get("format_knowledge", {}).get("faq", []) if payload.get("format_knowledge") else []
    format_page_data = {
        "name": payload.get("title", "Format Encyclopedia"),
        "description": payload.get("description", ""),
        "url": f"/formats/{normalized}",
        "faq_items": knowledge_faq,
    }

    link_service = _internal_link_service()
    format_links = link_service.get_links_for_format(normalized)

    locale_data, t, supported_locales = _get_locale_context(request)
    breadcrumb = [
        {"name": "Home", "url": "/"},
        {"name": "Formats", "url": "/formats"},
        {"name": payload.get("title", normalized.title()), "url": f"/formats/{normalized}"},
    ]
    return templates.TemplateResponse(
        request=request,
        name="pages/format_page.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "meta": seo_meta,
            "payload": payload,
            "canonical": canonical,
            "related_converters": format_links.get("related_converters", []),
            "related_formats": format_links.get("related_formats", []),
            "related_knowledge": format_links.get("related_knowledge", []),
            "related_hubs": format_links.get("related_hubs", []),
            "structured_data": seo_service.build_structured_data(
                request,
                page_type="trust_page",
                page_data=format_page_data,
            ),
        },
    )
