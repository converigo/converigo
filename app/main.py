"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Convertin FastAPI Application
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.logging_config import configure_logging
from app.core.settings import settings
from app.services.cleanup_service import CleanupService
from app.core.register_default import (
    register_default_converters,
)

configure_logging()


from app.routers.convert import (
    router as convert_router,
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


# ==========================================
# APPLICATION DIRECTORIES
# ==========================================

settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STATIC_DIR = Path(__file__).resolve().parent / "static"
OUTPUT_DIR = settings.OUTPUT_DIR


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

    title="Convertin",

    version="3.0.0",

    description=(
        "Smart file converter platform "
        "powered by plugin architecture."
    ),

    lifespan=lifespan,

)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "convertin"})


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
    seo_router
)


app.include_router(
    plugins_router
)


app.include_router(
    recommend_router
)