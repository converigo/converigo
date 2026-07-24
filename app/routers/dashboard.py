from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.core.settings import settings
from app.core.templates import templates
from app.services.article_service import ArticleService
from app.services.analytics_service import AnalyticsService
from app.services.converter_registry_service import ConverterRegistryService
from app.services.growth_dashboard_service import GrowthDashboardService
from app.services.language_service import LanguageService
from app.services.seo_service import PRODUCTION_BASE_URL, SeoService
from app.services.seo_audit_engine import SeoAuditEngine
from app.services.search_console_readiness_service import SearchConsoleReadinessService

router = APIRouter(tags=["dashboard"])

ARTICLE_DIR = (Path(__file__).resolve().parents[1] / "data" / "articles").resolve()
LANGUAGE_DIR = (Path(__file__).resolve().parents[1] / "locales").resolve()

article_service = ArticleService(ARTICLE_DIR)
converter_registry_service = ConverterRegistryService(Path("app/data/converters"))
seo_service = SeoService(Path("app/data/converters"))
language_service = LanguageService(LANGUAGE_DIR)
analytics_service = AnalyticsService()


def _get_locale_context(request: Request) -> tuple[dict[str, Any], Any, list[str]]:
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    return locale_data, t, language_service.get_supported_locales()


@router.get("/dashboard/seo-operations", response_class=HTMLResponse)
async def seo_operations_dashboard(request: Request) -> HTMLResponse:
    locale_data, t, supported_locales = _get_locale_context(request)

    dashboard_service = GrowthDashboardService(
        registry_instance=None,
        sitemap_service=None,
        output_dir=settings.OUTPUT_DIR,
        contracts_dir=Path("app/data/converters"),
    )

    dashboard = dashboard_service.build_dashboard()
    analytics_metrics = analytics_service.build_dashboard_metrics()
    articles = article_service.list_articles()
    total_learning_articles = len(articles)
    articles_missing_faq = sum(1 for article in articles if not article.get("faq"))
    articles_missing_cta = sum(1 for article in articles if not article.get("call_to_action"))
    articles_missing_related = sum(
        1
        for article in articles
        if not article.get("related_articles") and not article.get("related_formats") and not article.get("related_converters")
    )

    # Run SEO audit engine for dashboard display
    try:
        audit_engine = SeoAuditEngine(contracts_dir=Path("app/data/converters"))
        seo_audit_result = audit_engine.run_full_audit()
        seo_audit_data = {
            "average_score": seo_audit_result["summary"]["average_score"],
            "pages_audited": seo_audit_result["pages_audited"],
            "overall_status": seo_audit_result["overall_status"],
            "overall_score": seo_audit_result["overall_score"],
            "critical_count": seo_audit_result["summary"]["critical_count"],
            "warnings_count": seo_audit_result["summary"]["warnings_count"],
            "pass_count": seo_audit_result["summary"]["pass_count"],
            "score_distribution": seo_audit_result["score_distribution"],
            "top_issues": seo_audit_result["top_issues"][:5] if seo_audit_result.get("top_issues") else [],
        }
    except Exception:
        seo_audit_data = {
            "average_score": 0,
            "pages_audited": 0,
            "overall_status": "error",
            "overall_score": 0,
            "critical_count": 0,
            "warnings_count": 0,
            "pass_count": 0,
            "score_distribution": {},
            "top_issues": [],
        }

    # Run Search Console Readiness audit for dashboard display
    try:
        readiness_service = SearchConsoleReadinessService(
            contracts_dir=Path("app/data/converters"),
            output_dir=settings.OUTPUT_DIR,
        )
        readiness_audit = readiness_service.run_full_audit()
        search_console_data = {
            "readiness_score": readiness_audit["summary"]["readiness_score"],
            "overall_status": readiness_audit["summary"]["overall_status"],
            "pages_audited": readiness_audit["summary"]["pages_audited"],
            "pages_ready": readiness_audit["summary"]["pages_ready"],
            "critical_count": readiness_audit["summary"]["critical_count"],
            "warning_count": readiness_audit["summary"]["warning_count"],
            "pass_count": readiness_audit["summary"]["pass_count"],
            "total_checks": readiness_audit["metadata"]["total_checks"],
            "categories": {
                cat: {
                    "score": data["score"],
                    "weight": data["weight"],
                    "critical_count": data["critical_count"],
                    "warning_count": data["warning_count"],
                    "pass_count": data["pass_count"],
                }
                for cat, data in readiness_audit.get("category_breakdowns", {}).items()
            },
            "top_recommendations": [r for r in readiness_audit.get("recommendations", [])[:5]],
        }
    except Exception:
        search_console_data = {
            "readiness_score": 0,
            "overall_status": "error",
            "pages_audited": 0,
            "pages_ready": 0,
            "critical_count": 0,
            "warning_count": 0,
            "pass_count": 0,
            "total_checks": 0,
            "categories": {},
            "top_recommendations": [],
        }

    metadata = {
        "title": "SEO Operations Dashboard | Converigo",
        "description": "Internal SEO operations dashboard for content, product, quality, and SEO audit metrics.",
        "canonical": f"{PRODUCTION_BASE_URL}/dashboard/seo-operations",
        "og_url": f"{PRODUCTION_BASE_URL}/dashboard/seo-operations",
        "keywords": "SEO operations, dashboard, content metrics, internal dashboard, SEO audit",
        "author": "Converigo",
        "robots": "noindex,nofollow",
    }

    return templates.TemplateResponse(
        request=request,
        name="pages/seo_operations_dashboard.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "meta": metadata,
            "dashboard": dashboard,
            "analytics_metrics": analytics_metrics,
            "total_learning_articles": total_learning_articles,
            "topic_clusters_total": dashboard.get("topic_clusters", {}).get("topic_clusters_total", 0),
            "published_this_month": "Placeholder: external analytics pending",
            "sitemap_urls": "Placeholder: external sitemap analytics pending",
            "internal_link_count": dashboard.get("internal_linking", {}).get("internal_links_total", 0),
            "indexed_urls": "Placeholder: external index coverage pending",
            "total_converters": dashboard.get("total_converters", 0),
            "certified_converters": sum(
                1
                for converter in converter_registry_service.list_all()
                if str(converter.get("lifecycle_status", "")).strip().lower() == "certified"
            ),
            "articles_missing_faq": articles_missing_faq,
            "articles_missing_cta": articles_missing_cta,
            "articles_missing_related_articles": articles_missing_related,
            "seo_audit": seo_audit_data,
            "search_console": search_console_data,
            "year": 2026,
            "structured_data": seo_service.build_structured_data(
                request,
                page_type="trust_page",
                page_data={
                    "title": metadata["title"],
                    "description": metadata["description"],
                    "url": "/dashboard/seo-operations",
                    "name": metadata["title"],
                },
            ),
        },
    )


@router.get("/dashboard/api/seo-audit")
async def seo_audit_api(request: Request) -> JSONResponse:
    """JSON endpoint returning the full SEO Audit Engine report.

    Returns aggregated SEO health data for all converter pages.
    No architecture or routing changes — read-only analysis.
    """
    audit_engine = SeoAuditEngine(contracts_dir=Path("app/data/converters"))
    audit_result = audit_engine.run_full_audit()

    # Return a trimmed payload (exclude full per-page details for API efficiency)
    api_payload = {
        "version": audit_result["version"],
        "generated_at": audit_result["generated_at"],
        "pages_audited": audit_result["pages_audited"],
        "total_converters": audit_result["total_converters"],
        "overall_score": audit_result["overall_score"],
        "overall_status": audit_result["overall_status"],
        "summary": audit_result["summary"],
        "score_distribution": audit_result["score_distribution"],
        "critical_issues_count": len(audit_result["critical_issues"]),
        "warnings_count": len(audit_result["warnings"]),
        "passed_checks_count": len(audit_result["passed_checks"]),
        "top_issues": audit_result["top_issues"],
        "recommendations": audit_result["recommendations"],
        "checks_definition": audit_result["checks_definition"],
        "critical_issues": audit_result["critical_issues"],
        "warnings": audit_result["warnings"],
        "page_results": [
            {
                "slug": p["slug"],
                "name": p["name"],
                "category": p["category"],
                "score": p["score"],
                "status": p["status"],
                "critical_issues_count": p["critical_issues_count"],
                "warnings_count": p["warnings_count"],
                "passed_count": p["passed_count"],
                "total_checks": p["total_checks"],
                "checks": p["checks"],
            }
            for p in audit_result["page_results"]
        ],
    }

    return JSONResponse(content=api_payload)


@router.get("/dashboard/api/search-console-readiness")
async def search_console_readiness_api(request: Request) -> JSONResponse:
    """JSON endpoint returning the Search Console Readiness audit.

    Returns Search Console readiness metrics for all converter pages.
    No architecture or routing changes — read-only analysis.
    """
    readiness_service = SearchConsoleReadinessService(
        contracts_dir=Path("app/data/converters"),
        output_dir=settings.OUTPUT_DIR,
    )
    audit = readiness_service.run_full_audit()

    # Build a clean API payload
    api_payload = {
        "version": "1.0.0",
        "generated_at": audit["metadata"]["generated_at"],
        "total_checks": audit["metadata"]["total_checks"],
        "summary": {
            "readiness_score": audit["summary"]["readiness_score"],
            "overall_status": audit["summary"]["overall_status"],
            "pages_audited": audit["summary"]["pages_audited"],
            "pages_ready": audit["summary"]["pages_ready"],
            "critical_count": audit["summary"]["critical_count"],
            "warning_count": audit["summary"]["warning_count"],
            "pass_count": audit["summary"]["pass_count"],
        },
        "categories": audit["category_breakdowns"],
        "recommendations": audit["recommendations"][:10],
        "per_converter": [
            {
                "converter_slug": p["converter_slug"],
                "title": p["title"],
                "readiness_score": p["readiness_score"],
                "status": p["status"],
                "lifecycle_status": p.get("lifecycle_status", ""),
                "total_checks": p["total_checks"],
                "pass_count": p["pass_count"],
                "warning_count": p["warning_count"],
                "critical_count": p["critical_count"],
            }
            for p in audit.get("per_converter", [])
        ],
    }

    return JSONResponse(content=api_payload)

