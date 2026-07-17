"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Converigo FastAPI Application
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.services.language_manager import LanguageManager

from app.core.logging_config import configure_logging
from app.core.settings import settings
from app.services.cleanup_service import CleanupService
from app.services.conversion_service import UnsupportedConversionError
from app.core.register_default import (
    register_default_converters,
)


class HealthCheckTrustedHostMiddleware(TrustedHostMiddleware):
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path") in {"/health", "/health/"}:
            await self.app(scope, receive, send)
            return

        await super().__call__(scope, receive, send)

configure_logging()


from app.routers.convert import (
    router as convert_router,
    unsupported_conversion_exception_handler,
)

from app.routers.home import (
    router as home_router,
)

from app.routers.plugins import (
    router as plugins_router,
)

from app.routers.seo import (
    router as seo_router,
)

from app.routers.tools import (
    router as tools_router,
)

from app.routers.upload import (
    router as upload_router,
)

from app.routers.recommend import (
    router as recommend_router,
)
from app.routers.formats import router as formats_router
from app.routers.comparison import router as comparison_router

# Ensure formats router is imported before app creation


language_manager = LanguageManager(Path("app/locales"))


# ==========================================
# APPLICATION DIRECTORIES
# ==========================================

settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STATIC_DIR = Path(__file__).resolve().parent / "static"
OUTPUT_DIR = settings.OUTPUT_DIR
MANIFEST_PATH = STATIC_DIR / "site.webmanifest"


# ==========================================
# APPLICATION LIFECYCLE
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    """
    Application startup / shutdown.
    """

    register_default_converters()
    CleanupService().clean_old_files()

    yield



# ==========================================
# FASTAPI APP
# ==========================================

app = FastAPI(

    title="Converigo",

    version="3.0.0",

    description=(
        "Smart file converter platform "
        "powered by plugin architecture."
    ),

    lifespan=lifespan,

)

print("DEBUG APP CREATED")
print("APP ID:", id(app))
print("ROUTES AFTER CREATE:", len(app.routes))



app.add_exception_handler(
    UnsupportedConversionError,
    unsupported_conversion_exception_handler,
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

    response = await call_next(request)
    return response

app.add_middleware(
    HealthCheckTrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "converigo"})


@app.get("/static/site.webmanifest")
async def manifest() -> FileResponse:
    if not MANIFEST_PATH.exists():
        raise HTTPException(status_code=404, detail="Manifest not found")

    return FileResponse(
        MANIFEST_PATH,
        media_type="application/manifest+json",
    )


# ==========================================
# STATIC FILES
# ==========================================

app.mount(

    "/static",

    StaticFiles(
        directory=str(STATIC_DIR)
    ),

    name="static",

)



app.mount(

    "/outputs",

    StaticFiles(
        directory=str(OUTPUT_DIR)
    ),

    name="outputs",

)



# ==========================================
# ROUTERS
# ==========================================

app.include_router(
    seo_router
)




app.include_router(
    comparison_router
)

app.include_router(
    formats_router
)

app.include_router(
    home_router
)


app.include_router(
    upload_router
)


app.include_router(
    convert_router
)


app.include_router(
    tools_router
)


app.include_router(
    plugins_router
)

