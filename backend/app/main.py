from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os

from .router import router as manim_router
from .config import settings
from .scheduler import start_cleanup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    start_cleanup_scheduler()
    logger.info("Application startup complete")

    yield  # Control passes to the app
    logger.info("Shutting down application")
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for generating visualizations using Manim",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(manim_router, prefix="/api/manim", tags=["manim"])

if os.path.exists(settings.RENDER_DIR):
    app.mount("/renders", StaticFiles(directory=settings.RENDER_DIR), name="renders")
    logger.info(f"Mounted render directory: {settings.RENDER_DIR}")


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
