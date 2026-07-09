"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 1.2.0
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.register_default import register_default_converters
from app.routers.convert import router as convert_router
from app.routers.home import router as home_router
from app.routers.plugins import router as plugins_router
from app.routers.seo import router as seo_router
from app.routers.tools import router as tools_router
from app.routers.upload import router as upload_router

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup / shutdown.
    """

    register_default_converters()

    yield


app = FastAPI(
    title="Convertin",
    version="1.2.0",
    description="Video, Audio and Document Converter",
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)

app.mount(
    "/outputs",
    StaticFiles(directory=str(OUTPUT_DIR)),
    name="outputs",
)

app.include_router(home_router)
app.include_router(upload_router)
app.include_router(convert_router)
app.include_router(tools_router)
app.include_router(seo_router)
app.include_router(plugins_router)