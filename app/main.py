"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 1.0.0
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers.convert import router as convert_router
from app.routers.home import router as home_router
from app.routers.tools import router as tools_router
from app.routers.upload import router as upload_router

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Convertin",
    version="1.0.0",
    description="Video, Audio and Document Converter",
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