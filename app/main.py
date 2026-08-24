"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Converigo FastAPI Application
"""

import logging
import mimetypes
import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import MutableHeaders
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.services.language_manager import LanguageManager

from app.core.logging_config import configure_logging
from app.core.observability import (
    attach_correlation_headers,
    bind_request_context,
    build_error_response,
    current_request_id,
    elapsed_ms,
    generate_request_id,
    get_client_ip,
    hash_ip,
    metrics_registry,
    normalize_error_code,
    reset_request_context,
    response_status_label,
    start_timer,
)
from app.core.templates import templates
from app.services.converter_data_service import ConverterDataService
from app.core.settings import settings
from app.services.cleanup_service import CleanupService
from app.services.analytics_service import AnalyticsService
from app.services.conversion_service import UnsupportedConversionError
from app.core.register_default import (
    register_default_converters,
)


logger = logging.getLogger("app.observability.request")
analytics_service = AnalyticsService()


class HealthCheckTrustedHostMiddleware(TrustedHostMiddleware):
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path") in {
            "/health",
            "/health/",
            "/ready",
            "/ready/",
            "/metrics",
            "/metrics/",
        }:
            await self.app(scope, receive, send)
            return

        await super().__call__(scope, receive, send)


class ObservabilityMiddleware:
    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        state = scope.setdefault("state", {})
        request = Request(scope, receive=receive)
        request_id = generate_request_id()
        user_agent = request.headers.get("user-agent")
        ip_hash = hash_ip(get_client_ip(request))
        conversion_id = request.headers.get("x-conversion-id")

        state["request_id"] = request_id
        state["conversion_id"] = conversion_id
        state["request_started_ns"] = start_timer()
        state["user_agent"] = user_agent
        state["ip_hash"] = ip_hash
        state["error_code"] = None

        tokens = bind_request_context(request_id, user_agent, ip_hash, conversion_id=conversion_id)

        status_code = 500
        response_started = False
        completed = False
        response_meta = {"content_type": ""}

        async def send_wrapper(message):
            nonlocal status_code, response_started, completed

            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]
                headers = MutableHeaders(raw=message["headers"])
                headers["X-Request-ID"] = request_id
                active_conversion_id = state.get("conversion_id")
                if active_conversion_id:
                    headers["X-Conversion-ID"] = active_conversion_id
                response_meta["content_type"] = headers.get("content-type", "")

            if message["type"] == "http.response.body" and not message.get("more_body", False):
                completed = True
                duration_ms = elapsed_ms(state["request_started_ns"])
                route = scope.get("route")
                path_template = getattr(route, "path", scope.get("path", ""))
                method = scope.get("method", "GET")
                status = response_status_label(status_code)
                error_code = state.get("error_code")
    
# Touch file to trigger reload during development (no-op change)

                metrics_registry.increment(
                    "converigo_requests_total",
                    method=method,
                    path=path_template,
                    status=str(status_code),
                )
                metrics_registry.increment(f"converigo_{status}_total", path=path_template)
                metrics_registry.observe(
                    "converigo_request_duration_seconds",
                    duration_ms / 1000,
                    method=method,
                    path=path_template,
                    status=str(status_code),
                )

                if path_template.startswith("/download"):
                    metrics_registry.observe(
                        "converigo_download_duration_seconds",
                        duration_ms / 1000,
                        status=status,
                    )

                logger.info(
                    "Request completed",
                    extra={
                        "method": method,
                        "path": path_template,
                        "duration_ms": duration_ms,
                        "status": status,
                        "status_code": status_code,
                        "error_code": error_code,
                    },
                )

                threshold_ms = getattr(settings, "SLOW_REQUEST_THRESHOLD_MS", 1000)
                if duration_ms >= threshold_ms:
                    logger.warning(
                        "Slow request detected",
                        extra={
                            "method": method,
                            "path": path_template,
                            "duration_ms": duration_ms,
                            "status": status,
                            "status_code": status_code,
                            "error_code": error_code,
                        },
                    )

                if status_code >= 400:
                    analytics_service.track_error(
                        request,
                        error_type=error_code or "HTTP_ERROR",
                        event_status="failure",
                        page_path=path_template,
                    )
                elif method in {"GET", "HEAD"} and response_meta["content_type"].startswith("text/html"):
                    analytics_service.track_page_view(
                        request,
                        page_path=path_template,
                        event_status="success",
                        entry_type=_resolve_entry_type(request),
                        referrer=request.headers.get("referer", ""),
                    )

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            state["error_code"] = normalize_error_code(type(exc).__name__, fallback="INTERNAL_SERVER_ERROR")

            logger.exception(
                "Unhandled request error",
                extra={
                    "method": scope.get("method", "GET"),
                    "path": scope.get("path", ""),
                    "status": "failure",
                    "error_code": state["error_code"],
                },
            )

            if response_started:
                raise

            analytics_service.track_error(
                request,
                error_type=state.get("error_code") or "INTERNAL_SERVER_ERROR",
                event_status="failure",
                page_path=request.url.path,
            )

            response = build_error_response(
                request,
                status_code=500,
                content={
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Internal server error.",
                },
            )
            await response(scope, receive, send_wrapper)
        finally:
            if not completed:
                duration_ms = elapsed_ms(state["request_started_ns"])
                logger.info(
                    "Request aborted before completion",
                    extra={
                        "method": scope.get("method", "GET"),
                        "path": scope.get("path", ""),
                        "duration_ms": duration_ms,
                        "status": "failure",
                        "status_code": status_code,
                        "error_code": state.get("error_code") or "REQUEST_ABORTED",
                    },
                )
            reset_request_context(tokens)


def _resolve_entry_type(request: Request) -> str:
    referrer = (request.headers.get("referer") or "").lower()
    if any(marker in referrer for marker in ("google.", "bing.", "duckduckgo.", "yahoo.", "ecosia.", "brave.")):
        return "organic"
    if referrer:
        return "referral"
    return "direct"


configure_logging()


from app.routers.convert import (  # noqa: E402
    router as convert_router,
    unsupported_conversion_exception_handler,
)

from app.routers.home import (  # noqa: E402
    router as home_router,
)
from app.routers.comparison import (  # noqa: E402
    router as comparison_router,
)
from app.routers.dashboard import (  # noqa: E402
    router as dashboard_router,
)
from app.routers.formats import (  # noqa: E402
    router as formats_router,
)
from app.routers.upload import (  # noqa: E402
    router as upload_router,
)

from app.routers.recommend import (  # noqa: E402
    router as recommend_router,
)
from app.routers.tools import (  # noqa: E402
    router as tools_router,
)
from app.routers.learning import (  # noqa: E402
    router as learning_router,
)
from app.routers.seo import (  # noqa: E402
    router as seo_router,
)
from app.plugins.registry import registry  # noqa: E402


language_manager = LanguageManager(Path("app/locales"))


settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

STATIC_DIR = Path(__file__).resolve().parent / "static"
OUTPUT_DIR = settings.OUTPUT_DIR
MANIFEST_PATH = STATIC_DIR / "site.webmanifest"


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_default_converters()
    CleanupService().clean_old_files()
    yield


app = FastAPI(
    title="Converigo",
    version="3.0.0",
    description=(
        "Smart file converter platform "
        "powered by plugin architecture."
    ),
    lifespan=lifespan,
)

logger.info(
    "FastAPI application initialized",
    extra={"app_id": id(app), "route_count": len(app.routes)},
)

app.add_exception_handler(
    UnsupportedConversionError,
    unsupported_conversion_exception_handler,
)


@app.exception_handler(HTTPException)
async def correlated_http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request.state.error_code = normalize_error_code(exc.detail, fallback=f"HTTP_{exc.status_code}")
    # If the client expects HTML, render the branded 404 HTML page for browser-facing requests.
    accept = (request.headers.get("accept") or "").lower()
    # Render branded HTML for 404 on public, browser-facing routes (non-API paths).
    wants_json = "application/json" in accept
    path = request.url.path or ""
    is_api_path = path.startswith("/api") or path.startswith("/internal")
    logger.info("HTTPException handler invoked", extra={"accept": accept, "wants_json": wants_json, "path": path, "is_api_path": is_api_path})
    if exc.status_code == 404 and not is_api_path:
            try:
                converters = ConverterDataService(Path("app/data/converters")).list_popular_converters()
            except Exception:
                converters = []
            meta = {"title": "Page Not Found", "description": "The requested page could not be found.", "robots": "noindex,follow"}
            try:
                # Provide translation helper and locale context to the template.
                locale_data = language_manager.load_locale(
                    accept_language=request.headers.get("accept-language"),
                    lang_query=request.query_params.get("lang"),
                )

                def t(key: str, default: str = "") -> str:
                    return language_manager.translate(locale_data, key, default)

                tpl = templates.env.get_template("pages/404.html")
                content = tpl.render(request=request, meta=meta, popular_converters=converters, t=t)
                return HTMLResponse(content, status_code=404)
            except Exception as render_exc:
                logger.exception("Failed to render 404 template", extra={"error": str(render_exc)})
                # Fallback to JSON error if template rendering fails
                return build_error_response(
                    request,
                    status_code=404,
                    content=exc.detail,
                    headers=dict(exc.headers or {}),
                )

    return build_error_response(
        request,
        status_code=exc.status_code,
        content=exc.detail,
        headers=dict(exc.headers or {}),
    )


@app.exception_handler(StarletteHTTPException)
async def correlated_starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Delegate to the same behavior as FastAPI HTTPException handler for consistency.
    return await correlated_http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def correlated_unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request.state.error_code = normalize_error_code(type(exc).__name__, fallback="INTERNAL_SERVER_ERROR")
    logger.exception(
        "Unhandled application exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status": "failure",
            "error_code": request.state.error_code,
        },
    )
    return build_error_response(
        request,
        status_code=500,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Internal server error.",
        },
    )


@app.middleware("http")
async def locale_middleware(request: Request, call_next):
    locale_data = language_manager.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_manager.translate(locale_data, key, default)

    request.state.locale = locale_data
    request.state.t = t
    request.state.supported_locales = language_manager.get_supported_locales()
    request.state.verification_token = os.getenv("GOOGLE_SITE_VERIFICATION", settings.GOOGLE_SITE_VERIFICATION or "")
    request.state.bing_verification_token = os.getenv("BING_SITE_VERIFICATION", settings.BING_SITE_VERIFICATION or "")

    response = await call_next(request)
    return response


app.add_middleware(
    HealthCheckTrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)
app.add_middleware(ObservabilityMiddleware)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "converigo"})


@app.get("/ready")
async def ready(request: Request) -> JSONResponse:
    checks = {
        "uploads_dir": settings.UPLOAD_DIR.exists(),
        "outputs_dir": settings.OUTPUT_DIR.exists(),
        "static_dir": STATIC_DIR.exists(),
        "plugin_registry": bool(registry.plugins),
    }
    is_ready = all(checks.values())
    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={
            "status": "ready" if is_ready else "not_ready",
            "service": "converigo",
            "checks": checks,
            "request_id": getattr(request.state, "request_id", None) or current_request_id(),
        },
    )


@app.get("/metrics")
async def metrics_endpoint() -> PlainTextResponse:
    return PlainTextResponse(metrics_registry.render(), media_type="text/plain; version=0.0.4")


@app.get("/static/site.webmanifest")
async def manifest() -> FileResponse:
    if not MANIFEST_PATH.exists():
        raise HTTPException(status_code=404, detail="Manifest not found")

    return FileResponse(
        MANIFEST_PATH,
        media_type="application/manifest+json",
    )


@app.get("/apple-touch-icon.png")
async def apple_touch_icon() -> FileResponse:
    icon_path = STATIC_DIR / "images" / "apple-touch-icon.png"
    if not icon_path.exists():
        raise HTTPException(status_code=404, detail="Icon not found")
    return FileResponse(icon_path, media_type="image/png")


@app.get("/download/{path:path}")
async def download_file(request: Request, path: str) -> FileResponse:
    requested_path = Path(path)
    if requested_path.is_absolute():
        raise HTTPException(status_code=404, detail="File not found")

    candidate = (OUTPUT_DIR / requested_path).resolve(strict=False)
    try:
        candidate.relative_to(OUTPUT_DIR.resolve(strict=False))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="File not found") from exc

    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    media_type, _ = mimetypes.guess_type(candidate.name)
    if not media_type:
        media_type = "application/octet-stream"

    response = FileResponse(
        candidate,
        media_type=media_type,
        filename=candidate.name,
    )
    attach_correlation_headers(response.headers, request)
    analytics_service.track_download(
        request,
        page_path=request.url.path,
        page_title=candidate.name,
        output_format=candidate.suffix.lstrip(".").lower(),
        event_status="success",
    )
    return response


app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)

app.mount(
    "/outputs",
    StaticFiles(directory=str(OUTPUT_DIR)),
    name="outputs",
)


app.include_router(home_router)
app.include_router(comparison_router)
app.include_router(formats_router)
app.include_router(dashboard_router)
app.include_router(tools_router)
app.include_router(learning_router)
app.include_router(seo_router)
app.include_router(upload_router)
app.include_router(convert_router)
app.include_router(recommend_router)

