"""
backend/app/api/pest_forecasting.py
───────────────────────────────────
FastAPI router for Experimental Version 2.0 Pest Outbreak Forecasting.

CRITICAL INVARIANTS:
1. All models and responses are strictly tagged SYNTHETIC_EXPERIMENTAL.
2. Predictions are NOT calibrated real-world outbreak probabilities.
3. Production readiness remains BLOCKED.
4. Both ENVIRONMENTAL_ONLY and SCOUTING_ASSISTED configurations are supported.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status

from backend.app.schemas.pest_forecasting import (
    PestForecastingRequest,
    PestForecastingResponse,
    PestModelInfoResponse,
)

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/pest-forecasting", tags=["experimental pest forecasting"])


@router.get(
    "/model-info",
    response_model=PestModelInfoResponse,
    summary="Get active experimental pest forecasting model metadata and thresholds",
)
def get_pest_model_info(request: Request) -> PestModelInfoResponse:
    """Retrieve metadata, decision thresholds, and readiness status for active experimental models."""
    service = getattr(request.app.state, "pest_forecasting_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pest forecasting service is not initialized on the application state.",
        )
    return service.get_model_info()


@router.get(
    "/example",
    summary="Get sample pest forecasting input payloads",
)
def get_pest_forecasting_example(
    request: Request,
    configuration: str = Query(
        default="ENVIRONMENTAL_ONLY",
        description="Configuration mode: 'ENVIRONMENTAL_ONLY' or 'SCOUTING_ASSISTED'",
    ),
) -> dict[str, Any]:
    """Return verified sample inputs for testing inference."""
    service = getattr(request.app.state, "pest_forecasting_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pest forecasting service is not initialized on the application state.",
        )
    return service.get_example(configuration)


@router.post(
    "/predict",
    response_model=PestForecastingResponse,
    summary="Generate 7-day experimental pest outbreak risk forecast",
    responses={
        200: {"description": "Experimental outbreak forecast generated successfully."},
        400: {"description": "Invalid feature values or configuration mismatch."},
        503: {"description": "Model pipeline artifacts unavailable."},
    },
)
def predict_pest_outbreak(
    payload: PestForecastingRequest,
    request: Request,
) -> PestForecastingResponse:
    """
    Execute 7-day multi-crop pest outbreak forecast using experimental V2 pipelines.

    - Supports ENVIRONMENTAL_ONLY (macro-climatic & topsoil only)
    - Supports SCOUTING_ASSISTED (adds in-field incidence, severity, trap catch)
    - Returns predicted outbreak probability, calibrated warning flag, and scientific disclaimers.
    """
    service = getattr(request.app.state, "pest_forecasting_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pest forecasting service is not initialized on the application state.",
        )
    return service.predict(payload)
