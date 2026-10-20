"""
backend/app/api/pest.py
───────────────────────
Pest Outbreak Early-Warning System (Phase 2 Interface & Advisory API).
Provides canonical-aware pest risk screening, outbreak model specifications,
and crop eligibility inspection without altering existing model functionality.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, status

from ..core.crop_catalog import get_crop_catalog
from ..schemas.pest import (
    PestOutbreakSpecification,
    PestRiskPreviewRequest,
    PestRiskPreviewResponse,
    TargetPestInfo,
)
from .advisory import evaluate_pest_risk_preview

router = APIRouter(prefix="/pest", tags=["pest early-warning system"])


@router.get("/eligible-crops", response_model=list[PestOutbreakSpecification])
def list_eligible_crops() -> list[dict[str, Any]]:
    """
    Returns crops evaluated and categorized for pest outbreak prediction.
    Distinguishes Tier-1 primary targets (cotton, rice, maize) from data-limited crops.
    """
    catalog = get_crop_catalog()
    eligible = catalog.list_pest_eligible_crops()
    result = []
    for crop in eligible:
        spec = crop.get("pest_outbreak_prediction", {})
        result.append({
            "canonical_id": crop["canonical_id"],
            "display_name": crop["display_name"],
            "category": crop["category"],
            "priority_tier": spec.get("priority_tier", "TIER_3_DATA_LIMITED"),
            "target_pests": spec.get("target_pests", []),
            "historical_data_requirements": spec.get("historical_data_requirements", []),
            "weather_feature_requirements": spec.get("weather_feature_requirements", []),
            "training_data_availability": spec.get("training_data_availability", "sparse"),
            "data_sources": spec.get("data_sources", []),
        })
    return result


@router.get("/spec/{crop_identifier}", response_model=PestOutbreakSpecification)
def get_crop_pest_spec(crop_identifier: str) -> dict[str, Any]:
    """
    Retrieve pest species, economic thresholds, weather parameters,
    and historical surveillance requirements for a specific crop.
    """
    catalog = get_crop_catalog()
    crop = catalog.get_crop(crop_identifier)
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop '{crop_identifier}' not found in central catalog."
        )

    spec = crop.get("pest_outbreak_prediction", {})
    if not spec.get("eligible"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Crop '{crop['display_name']}' is currently not eligible for pest outbreak prediction due to insufficient regional surveillance data."
        )

    return {
        "canonical_id": crop["canonical_id"],
        "display_name": crop["display_name"],
        "category": crop["category"],
        "priority_tier": spec.get("priority_tier", "TIER_3_DATA_LIMITED"),
        "target_pests": spec.get("target_pests", []),
        "historical_data_requirements": spec.get("historical_data_requirements", []),
        "weather_feature_requirements": spec.get("weather_feature_requirements", []),
        "training_data_availability": spec.get("training_data_availability", "sparse"),
        "data_sources": spec.get("data_sources", []),
    }


@router.post("/preview", response_model=PestRiskPreviewResponse, status_code=status.HTTP_200_OK)
def preview_pest_risk(payload: PestRiskPreviewRequest) -> dict[str, Any]:
    """
    Run canonical-aware preliminary agroclimatic pest risk preview.
    Uses canonical identifier resolution to ensure 'corn' maps to 'maize', 'paddy' maps to 'rice', etc.
    """
    catalog = get_crop_catalog()
    crop = catalog.get_crop(payload.crop)
    canonical_id = crop["canonical_id"] if crop else payload.crop.lower().strip()
    display_name = crop["display_name"] if crop else payload.crop

    # Call the established agroclimatic rule engine
    preview = evaluate_pest_risk_preview(
        canonical_id,
        payload.temperature,
        payload.humidity,
        payload.rainfall,
    )

    target_pests_raw = crop.get("pest_outbreak_prediction", {}).get("target_pests", []) if crop else []
    target_pests = [
        TargetPestInfo(
            common_name=p["common_name"],
            scientific_name=p["scientific_name"],
            economic_threshold=p.get("economic_threshold", "N/A"),
        )
        for p in target_pests_raw
    ]

    return {
        "crop_canonical_id": canonical_id,
        "crop_display_name": display_name,
        "primary_threat": preview["primary_threat"],
        "preliminary_risk_level": preview["preliminary_risk_level"],
        "environmental_factors": preview["environmental_factors"],
        "target_pests": target_pests,
        "next_phase_note": preview["next_phase_note"],
    }
