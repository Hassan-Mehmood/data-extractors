from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.router import router
from src.core.config import get_settings


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    exports_dir = Path(settings.EXPORTS_DIR)
    exports_dir.mkdir(parents=True, exist_ok=True)
    application.mount("/exports", StaticFiles(directory=str(exports_dir)), name="exports")
    yield


app = FastAPI(title="ANX Data Extraction API", lifespan=lifespan)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "ANX Data Extraction API — POST /api/upload to extract"}
