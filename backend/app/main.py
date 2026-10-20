from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import crop_router, fertilizer_router, advisory_router, monitoring_router
from .core.config import Settings
from .core.config import settings as default_settings
from .core.logging import configure_logging
from .db import DatabaseManager
from .schemas.crop import HealthResponse
from .services import CropModelService, FertilizerModelService

LOGGER = logging.getLogger(__name__)


def create_app(config: Settings | None = None) -> FastAPI:
    app_settings = config or default_settings
    configure_logging(app_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Load models during startup lifespan
        app.state.model_service.load()
        app.state.fertilizer_service.load()
        yield

    app = FastAPI(
        title=app_settings.app_name,
        version="1.2.0",
        description="AgriAdapt Agricultural Intelligence API: Integrated Crop Recommendation, Fertilizer Optimization, and Pest Outbreak Advisory Lifecycle.",
        lifespan=lifespan,
    )

    # Initialize services on state immediately
    app.state.model_service = CropModelService(app_settings)
    app.state.fertilizer_service = FertilizerModelService(app_settings)
    app.state.database = DatabaseManager(app_settings)

    # Also load models eagerly so synchronous clients (e.g. without context manager) work reliably
    app.state.model_service.load()
    app.state.fertilizer_service.load()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(app_settings.cors_origins),
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(crop_router, prefix=app_settings.api_prefix)
    app.include_router(fertilizer_router, prefix=app_settings.api_prefix)
    app.include_router(advisory_router, prefix=app_settings.api_prefix)
    app.include_router(monitoring_router, prefix=app_settings.api_prefix)

    @app.exception_handler(Exception)
    async def internal_error_handler(request: Request, exc: Exception):
        LOGGER.exception("Unhandled API error on %s", request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Unexpected server error. Please retry later."})

    @app.get("/health", response_model=HealthResponse, tags=["service"])
    def health(request: Request):
        crop_svc = getattr(request.app.state, "model_service", None)
        fert_svc = getattr(request.app.state, "fertilizer_service", None)
        database = getattr(request.app.state, "database", None)

        crop_avail = crop_svc.available if crop_svc else False
        fert_avail = fert_svc.available if fert_svc else False
        both_healthy = crop_avail and fert_avail

        return {
            "status": "ok" if both_healthy else "degraded",
            "model_available": crop_avail,
            "model_version": crop_svc.model_version if crop_svc else None,
            "crop_model_available": crop_avail,
            "crop_model_version": crop_svc.model_version if crop_svc else None,
            "fertilizer_model_available": fert_avail,
            "fertilizer_model_version": fert_svc.model_version if fert_svc else None,
            "persistence_enabled": database.enabled if database else False,
            "persistence_available": database.available if database else False,
        }

    return app


app = create_app()
