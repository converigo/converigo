
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.services import public_seo_service
from app.services.authority_service import AuthorityService
from app.services.converter_registry_service import ConverterRegistryService
from app.services.format_knowledge_service import FormatKnowledgeService
from app.services.internal_link_service import InternalLinkService
from app.services.language_service import LanguageService

router = APIRouter(tags=["formats"])

CONTRACTS_DIR = (Path(__file__).resolve().parents[1] / "data" / "converters").resolve()
FORMAT_KNOWLEDGE_DIR = (Path(__file__).resolve().parents[1] / "data" / "format_knowledge").resolve()
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
    payload = _authority_service().generate_all()
    formats = sorted(payload.keys())
    breadcrumb = [{"name": "Home", "url": "/"}, {"name": "Formats", "url": "/formats"}]
    meta = public_seo_service.build_public_meta(
        "/formats",
        "Format Encyclopedia | Converigo",
        "Browse supported file formats, compatibility notes, and reference pages for conversion workflows.",
    )
    structured_data = public_seo_service.build_public_structured_data(
        "/formats",
        "Format Encyclopedia | Converigo",
        "Browse supported file formats, compatibility notes, and reference pages for conversion workflows.",
        schema_type="CollectionPage",
        breadcrumbs=breadcrumb,
    )
    return templates.TemplateResponse(
        request=request,
        name="pages/format_index.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "formats": formats,
            "meta": meta,
            "structured_data": structured_data,
        },
    )


@router.get("/formats/{format_name}", response_class=HTMLResponse)
async def format_page(request: Request, format_name: str) -> HTMLResponse:
    locale_data, t, supported_locales = _get_locale_context(request)
    normalized = format_name.strip().lower()
    payload = _authority_service().generate_all().get(normalized)
    if not payload:
        raise HTTPException(status_code=404, detail="Format page not found")

    related_converters = _build_related_converters(normalized)
    related_formats = _internal_link_service().get_links_for_format(normalized).get("related_formats", [])
    format_knowledge = _format_knowledge_service().get_format_knowledge(normalized)
    breadcrumb = [
        {"name": "Home", "url": "/"},
        {"name": "Formats", "url": "/formats"},
        {"name": payload["title"], "url": f"/formats/{normalized}"},
    ]
    meta = public_seo_service.build_public_meta(
        f"/formats/{normalized}",
        payload["title"],
        payload["description"],
    )
    structured_data = public_seo_service.build_public_structured_data(
        f"/formats/{normalized}",
        payload["title"],
        payload["description"],
        schema_type="WebPage",
        breadcrumbs=breadcrumb,
    )

    return templates.TemplateResponse(
        request=request,
        name="pages/format_page.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "payload": {
                **payload,
                "format_knowledge": format_knowledge,
                "related_converters": related_converters,
            },
            "related_formats": related_formats,
            "breadcrumb": breadcrumb,
            "meta": meta,
            "structured_data": structured_data,
        },
    )
