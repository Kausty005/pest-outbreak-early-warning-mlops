"""
backend/app/api/pest_risk.py
────────────────────────────
FastAPI router for the Experimental Environmental Pest Risk Assessment API.

CRITICAL DISTINCTION:
This endpoint estimates biophysical environmental favorability based on
verified ICAR/FAO agroclimatic thresholds. It does NOT generate calibrated
outbreak probabilities or machine learning predictions.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.pest_risk import (
    DataQualitySummary,
    EnvironmentalAssessmentRequest,
    EnvironmentalAssessmentResponse,
    EnvironmentalObservationSummary,
    ForecastDayItem,
    ForecastSummary,
    SupportedProfilesResponse,
)
from src.pest_risk import (
    DISCLAIMER_TEXT,
    DailyWeatherRecord,
    PestBiologicalProfile,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    assess_pest_risk,
    get_pest_profile,
    get_supported_pest_profiles,
    list_supported_crops,
    list_supported_pests_for_crop,
)

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/pest-risk", tags=["experimental pest risk assessment"])

# Path to the real-world aligned environmental surveillance dataset
DATASET_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "aligned_environmental_surveillance_2023-06-01_2023-10-31.csv"
)

# In-memory dataframe cache
_CACHED_DF: Optional[pd.DataFrame] = None


def get_surveillance_dataframe() -> pd.DataFrame:
    """Load and cache the processed environmental surveillance records."""
    global _CACHED_DF
    if _CACHED_DF is None:
        if not DATASET_PATH.exists():
            raise FileNotFoundError(f"Surveillance dataset not found at: {DATASET_PATH}")
        df = pd.read_csv(DATASET_PATH)
        df["observation_date"] = pd.to_datetime(df["observation_date"]).dt.strftime("%Y-%m-%d")
        df["district_normalized"] = df["district"].astype(str).str.strip().str.lower()
        _CACHED_DF = df
    return _CACHED_DF


@router.get(
    "/supported-profiles",
    response_model=SupportedProfilesResponse,
    summary="List supported crops, pests, and available surveillance districts",
)
def get_supported_profiles():
    """Returns all scientifically registered crop-pest profiles and available geographical districts."""
    crops = list_supported_crops()
    all_profiles = get_supported_pest_profiles()

    crop_pests_mapping: dict[str, list[dict[str, str]]] = {}
    for crop in crops:
        crop_pests_mapping[crop] = []
        pests = list_supported_pests_for_crop(crop)
        for p in pests:
            prof = all_profiles.get((crop, p))
            if prof:
                crop_pests_mapping[crop].append({
                    "pest_id": prof.pest_id,
                    "common_name": prof.common_name,
                    "scientific_name": prof.scientific_name,
                })

    try:
        df = get_surveillance_dataframe()
        districts = sorted(df["district"].unique().tolist())
        date_min = str(df["observation_date"].min())
        date_max = str(df["observation_date"].max())
    except Exception:
        districts = ["Nagpur", "Amravati", "Yavatmal", "Jalgaon"]
        date_min = "2023-06-01"
        date_max = "2023-10-31"

    return SupportedProfilesResponse(
        supported_crops=crops,
        crop_pests_mapping=crop_pests_mapping,
        available_surveillance_districts=districts,
        available_date_range={"start": date_min, "end": date_max},
    )


@router.post(
    "/environmental-assessment",
    response_model=EnvironmentalAssessmentResponse,
    summary="Evaluate experimental biophysical pest favorability",
    responses={
        200: {"description": "Assessment generated successfully."},
        400: {"description": "Unsupported crop/pest combination or invalid district/date."},
    },
)
def assess_environmental_pest_risk(payload: EnvironmentalAssessmentRequest):
    """
    Evaluate 7-day environmental and microclimatic favorability for target crop and pest.

    - Grounded in authoritative ICAR/FAO biophysical response thresholds.
    - Uses real-world gridded weather and ERA5-Land topsoil moisture data.
    - Explicitly partitioned from future forecast projections.
    - Outputs strictly an Environmental Favorability Index [0.0, 1.0].
    """
    # 1. Validate Crop and Pest
    try:
        pest_profile = get_pest_profile(crop=payload.crop, pest=payload.pest)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # 2. Retrieve Surveillance Data for District
    try:
        df = get_surveillance_dataframe()
    except Exception as exc:
        LOGGER.error("Failed to load processed environmental dataset: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Environmental surveillance data repository is currently unavailable.",
        )

    norm_district = payload.district.strip().lower()
    district_df = df[df["district_normalized"] == norm_district].sort_values("observation_date")

    if district_df.empty:
        available = sorted(df["district"].unique().tolist())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Surveillance data for district '{payload.district}' is not yet available in the ingested records. "
                f"Currently available districts: {available}."
            ),
        )

    # District spatial metadata
    lat = float(district_df["latitude"].iloc[0])
    lon = float(district_df["longitude"].iloc[0])
    district_display = str(district_df["district"].iloc[0])

    # 3. Determine Assessment Date & Filter Antecedent Window
    if payload.assessment_date:
        ref_date = payload.assessment_date[:10]
        matching_antecedent = district_df[district_df["observation_date"] <= ref_date]
        if matching_antecedent.empty:
            date_min = district_df["observation_date"].min()
            date_max = district_df["observation_date"].max()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Assessment date '{ref_date}' precedes earliest available record ({date_min}). "
                    f"Surveillance data range for {district_display} is {date_min} to {date_max}."
                ),
            )
    else:
        # Default to latest date in dataset
        ref_date = district_df["observation_date"].max()
        matching_antecedent = district_df

    # Take antecedent window up to 7 days leading up to ref_date
    antecedent_window_df = matching_antecedent.tail(7)
    current_row = antecedent_window_df.iloc[-1]
    actual_ref_date = str(current_row["observation_date"])

    # 4. Convert to Engine Records
    missing_fields: list[str] = []
    antecedent_records: list[DailyWeatherRecord] = []

    for _, row in antecedent_window_df.iterrows():
        sm_val = row.get("soil_moisture_era5_m3m3")
        if pd.isna(sm_val):
            soil_moisture = None
            if "soil_moisture_era5_m3m3" not in missing_fields:
                missing_fields.append("soil_moisture_era5_m3m3")
        else:
            soil_moisture = float(sm_val)

        t_min = float(row["temperature_min"]) if pd.notna(row.get("temperature_min")) else None
        t_max = float(row["temperature_max"]) if pd.notna(row.get("temperature_max")) else None

        antecedent_records.append(
            DailyWeatherRecord(
                date=str(row["observation_date"]),
                temp_mean=float(row["temperature_mean"]),
                temp_min=t_min,
                temp_max=t_max,
                humidity_mean=float(row["humidity_mean"]),
                rainfall_mm=float(row["rainfall_mm"]),
                soil_moisture_m3m3=soil_moisture,
            )
        )

    # 5. Invoke Phase 4 Biophysical Risk Engine
    engine_request = RiskAssessmentRequest(
        crop=payload.crop,
        pest=payload.pest,
        location_name=district_display,
        latitude=lat,
        longitude=lon,
        planting_date=payload.planting_date,
        current_date=actual_ref_date,
        antecedent_weather=antecedent_records,
        fetch_live_forecast=payload.fetch_live_forecast,
    )

    try:
        engine_resp: RiskAssessmentResponse = assess_pest_risk(engine_request)
    except Exception as exc:
        LOGGER.exception("Error executing assess_pest_risk: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating biophysical favorability: {str(exc)}",
        )

    # 6. Build Summary Structures
    current_fav = engine_resp.current_favorability

    # Aggregate antecedent metrics
    ant_temps = [r.temp_mean for r in antecedent_records]
    ant_rhs = [r.humidity_mean for r in antecedent_records]
    ant_rains = [r.rainfall_mm for r in antecedent_records]

    env_observations = EnvironmentalObservationSummary(
        date=actual_ref_date,
        temperature_mean_c=current_fav.temperature_c,
        temperature_min_c=current_row.get("temperature_min") if pd.notna(current_row.get("temperature_min")) else None,
        temperature_max_c=current_row.get("temperature_max") if pd.notna(current_row.get("temperature_max")) else None,
        relative_humidity_pct=current_fav.humidity_pct,
        rainfall_mm=current_fav.rainfall_mm,
        soil_moisture_m3m3=current_fav.soil_moisture_m3m3,
        antecedent_window_days=len(antecedent_records),
        antecedent_mean_temperature_c=round(float(np.mean(ant_temps)), 2),
        antecedent_mean_humidity_pct=round(float(np.mean(ant_rhs)), 2),
        antecedent_accumulated_rainfall_mm=round(float(np.sum(ant_rains)), 2),
    )

    data_quality = DataQualitySummary(
        records_used=len(antecedent_records),
        data_source="Open-Meteo Historical Archive & Copernicus ERA5-Land Reanalysis",
        edaphic_data_available=bool(current_fav.soil_moisture_m3m3 is not None),
        phenology_data_available=bool(payload.planting_date is not None),
        missing_fields=missing_fields,
        data_notices=engine_resp.data_notices,
    )

    forecast_summary: Optional[ForecastSummary] = None
    if engine_resp.forecast_days:
        daily_projections = [
            ForecastDayItem(
                date=f_day.date,
                temperature_c=f_day.temperature_c,
                humidity_pct=f_day.humidity_pct,
                rainfall_mm=f_day.rainfall_mm,
                soil_moisture_m3m3=f_day.soil_moisture_m3m3,
                favorability_score=f_day.composite_favorability_index,
                risk_category=f_day.risk_category,
            )
            for f_day in engine_resp.forecast_days
        ]
        forecast_summary = ForecastSummary(
            forecast_available=True,
            forecast_source="Open-Meteo High-Resolution Numerical Weather Prediction",
            forecast_days_count=len(daily_projections),
            forecast_mean_favorability=engine_resp.forecast_mean_favorability,
            daily_projections=daily_projections,
        )

    biological_limitations = [
        "High environmental favorability indicates microclimatic suitability for pest propagation, "
        "but does NOT guarantee an outbreak if initial pest inoculum or local trap counts are zero.",
        "Biological factors such as natural enemy presence (predators, parasitoids), prior pesticide sprays, "
        "and crop variety resistance are not measured by microclimate sensors alone.",
        "Physical in-field scouting and pheromone trap monitoring are mandatory before initiating chemical or biological interventions.",
        "This experimental module evaluates environmental favorability, NOT statistical outbreak probability.",
    ]

    references_list = [
        {
            "title": src.title,
            "authors": src.authors,
            "year": src.year,
            "institution_or_journal": src.institution_or_journal,
            "url": src.url,
            "key_finding": src.relevance_notes,
        }
        for src in pest_profile.sources
    ]

    return EnvironmentalAssessmentResponse(
        assessment_type="EXPERIMENTAL_ENVIRONMENTAL_FAVORABILITY_ASSESSMENT",
        crop=pest_profile.target_crop,
        pest=pest_profile.common_name,
        scientific_name=pest_profile.scientific_name,
        location=district_display,
        assessment_date=actual_ref_date,
        assessment_horizon_days=7,
        environmental_favorability_score=current_fav.composite_favorability_index,
        risk_category=current_fav.risk_category,
        risk_trend=engine_resp.risk_trend,
        contributing_factors={
            "favorable_drivers": engine_resp.favorable_drivers,
            "limiting_factors": engine_resp.limiting_factors,
        },
        environmental_observations=env_observations,
        data_quality=data_quality,
        forecast_available=bool(forecast_summary is not None),
        forecast_summary=forecast_summary,
        recommendations=engine_resp.recommendations,
        limitations=biological_limitations,
        references=references_list,
        disclaimer=DISCLAIMER_TEXT,
    )

