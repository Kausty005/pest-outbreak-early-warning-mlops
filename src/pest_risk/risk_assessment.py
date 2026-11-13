"""
risk_assessment.py
──────────────────
Core orchestrator for the Environmental Pest Risk Assessment Engine.

Coordinates:
- Biological profile retrieval
- Antecedent observation scoring
- Live/provided 7-day weather forecast ingestion
- Trend analysis (RISING / STABLE / DECLINING)
- Explainability and IPM advisory synthesis

STRICT ARCHITECTURAL NOTE:
This engine generates biophysical favorability indices grounded in verified
agronomic thresholds. It does NOT generate machine learning outbreak predictions
or calibrated probability estimates.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from src.pest_risk.environmental_scoring import (
    DailyFavorabilityScores,
    categorize_favorability_risk,
    compute_daily_favorability,
)
from src.pest_risk.explanations import (
    DISCLAIMER_TEXT,
    build_explanation_payload,
    generate_ipm_recommendations,
)
from src.pest_risk.pest_profiles import (
    PestBiologicalProfile,
    get_pest_profile,
    list_supported_crops,
)

LOGGER = logging.getLogger(__name__)


class DailyWeatherRecord(BaseModel):
    """Atmospheric and edaphic weather observation or forecast for a single date."""
    date: str = Field(description="ISO 8601 date string (YYYY-MM-DD)")
    temp_mean: float = Field(description="Daily mean 2m temperature (°C)")
    temp_min: Optional[float] = Field(default=None, description="Daily minimum 2m temperature (°C)")
    temp_max: Optional[float] = Field(default=None, description="Daily maximum 2m temperature (°C)")
    humidity_mean: float = Field(description="Daily mean relative humidity (%)")
    rainfall_mm: float = Field(description="Daily accumulated rainfall (mm)")
    soil_moisture_m3m3: Optional[float] = Field(
        default=None,
        description="Topsoil (0-7 cm) volumetric soil moisture (m³/m³)",
    )

    @field_validator("humidity_mean")
    @classmethod
    def validate_humidity(cls, v: float) -> float:
        if v < 0.0 or v > 100.0:
            raise ValueError(f"Relative humidity must be in [0, 100]%, got {v}")
        return v

    @field_validator("rainfall_mm")
    @classmethod
    def validate_rainfall(cls, v: float) -> float:
        if v < 0.0:
            raise ValueError(f"Rainfall cannot be negative, got {v}")
        return v


class RiskAssessmentRequest(BaseModel):
    """Input payload requesting a biophysical pest risk assessment."""
    crop: str = Field(description="Target crop (e.g. cotton, soybean, rice, maize)")
    pest: Optional[str] = Field(default=None, description="Optional target pest name")
    location_name: str = Field(description="District or farm name (e.g. Nagpur)")
    latitude: float = Field(description="WGS84 latitude")
    longitude: float = Field(description="WGS84 longitude")
    planting_date: Optional[str] = Field(default=None, description="Sowing date (YYYY-MM-DD)")
    current_date: Optional[str] = Field(default=None, description="Reference date (YYYY-MM-DD)")
    antecedent_weather: list[DailyWeatherRecord] = Field(
        description="Observed weather leading up to current date (e.g. past 7 days)"
    )
    forecast_weather: Optional[list[DailyWeatherRecord]] = Field(
        default=None,
        description="Optional 7-day projected forecast weather"
    )
    fetch_live_forecast: bool = Field(
        default=False,
        description="If True and forecast_weather is None, queries Open-Meteo forecast API"
    )


class DayRiskAssessment(BaseModel):
    """Calculated favorability scores for a specific day."""
    date: str
    temperature_c: float
    humidity_pct: float
    rainfall_mm: float
    soil_moisture_m3m3: Optional[float]
    temperature_score: float
    humidity_score: float
    rainfall_score: float
    soil_moisture_score: Optional[float]
    phenology_score: float
    composite_favorability_index: float
    risk_category: str
    edaphic_included: bool


class RiskAssessmentResponse(BaseModel):
    """Complete explainable biophysical pest favorability assessment."""
    crop: str
    pest_common_name: str
    pest_scientific_name: str
    location_name: str
    latitude: float
    longitude: float
    assessment_date: str
    days_since_sowing: Optional[int]
    current_favorability: DayRiskAssessment
    antecedent_mean_favorability: float
    forecast_mean_favorability: Optional[float]
    forecast_days: list[DayRiskAssessment]
    risk_trend: str  # "RISING", "STABLE", "DECLINING", "UNKNOWN"
    primary_advisory_category: str
    favorable_drivers: list[str]
    limiting_factors: list[str]
    data_notices: list[str]
    recommendations: list[str]
    biological_thresholds: dict[str, Any]
    scientific_citations: list[dict[str, Any]]
    disclaimer: str


def fetch_open_meteo_forecast(
    latitude: float,
    longitude: float,
    days: int = 7,
    timeout_sec: float = 5.0,
) -> tuple[list[DailyWeatherRecord], Optional[str]]:
    """
    Fetch 7-day atmospheric and topsoil moisture forecast from Open-Meteo API.

    Returns:
        (records, error_message)
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude:.4f}&longitude={longitude:.4f}&"
        f"daily=temperature_2m_mean,temperature_2m_max,temperature_2m_min,"
        f"relative_humidity_2m_mean,precipitation_sum,soil_moisture_0_to_7cm_mean&"
        f"timezone=auto&forecast_days={days}"
    )

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AgriAdapt-PestRiskEngine/1.0 (Agricultural Research)"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            if response.status != 200:
                return [], f"Open-Meteo API responded with HTTP {response.status}"
            payload = json.loads(response.read().decode("utf-8"))

        daily = payload.get("daily", {})
        times = daily.get("time", [])
        temp_means = daily.get("temperature_2m_mean", [])
        temp_mins = daily.get("temperature_2m_min", [])
        temp_maxs = daily.get("temperature_2m_max", [])
        humidity = daily.get("relative_humidity_2m_mean", [])
        precip = daily.get("precipitation_sum", [])
        soil_m = daily.get("soil_moisture_0_to_7cm_mean", [])

        records: list[DailyWeatherRecord] = []
        for i, dt in enumerate(times):
            t_mean = float(temp_means[i]) if i < len(temp_means) and temp_means[i] is not None else 25.0
            t_min = float(temp_mins[i]) if i < len(temp_mins) and temp_mins[i] is not None else None
            t_max = float(temp_maxs[i]) if i < len(temp_maxs) and temp_maxs[i] is not None else None
            rh = float(humidity[i]) if i < len(humidity) and humidity[i] is not None else 60.0
            pr = float(precip[i]) if i < len(precip) and precip[i] is not None else 0.0
            sm = float(soil_m[i]) if i < len(soil_m) and soil_m[i] is not None else None

            records.append(
                DailyWeatherRecord(
                    date=dt,
                    temp_mean=t_mean,
                    temp_min=t_min,
                    temp_max=t_max,
                    humidity_mean=rh,
                    rainfall_mm=pr,
                    soil_moisture_m3m3=sm,
                )
            )

        return records, None

    except Exception as exc:
        LOGGER.warning("Failed to fetch live Open-Meteo forecast for (%s, %s): %s", latitude, longitude, exc)
        return [], f"Live forecast acquisition failed: {str(exc)}"


def _calculate_dss(planting_date_str: Optional[str], target_date_str: str) -> Optional[int]:
    """Calculate days since sowing from planting date and target date."""
    if not planting_date_str:
        return None
    try:
        p_date = datetime.strptime(planting_date_str[:10], "%Y-%m-%d").date()
        t_date = datetime.strptime(target_date_str[:10], "%Y-%m-%d").date()
        return max(0, (t_date - p_date).days)
    except Exception:
        return None


def assess_pest_risk(request: RiskAssessmentRequest) -> RiskAssessmentResponse:
    """
    Execute end-to-end explainable biophysical pest risk assessment.

    1. Retrieves authoritative pest biological profile (validates crop/pest support).
    2. Scores antecedent observed weather records.
    3. Obtains or incorporates 7-day forecast weather (strictly separated).
    4. Computes forecast favorabilities and future trend (RISING/STABLE/DECLINING).
    5. Formulates farmer-comprehensible drivers, limiting factors, and IPM advisories.
    """
    # 1. Biological profile lookup
    profile: PestBiologicalProfile = get_pest_profile(request.crop, request.pest)

    if not request.antecedent_weather:
        raise ValueError(
            "Antecedent weather records cannot be empty. At least one historical observation is required."
        )

    # 2. Determine assessment date and current record
    if request.current_date:
        ref_date = request.current_date
        # Find matching antecedent record or use last
        matching = [r for r in request.antecedent_weather if r.date == ref_date]
        current_record = matching[0] if matching else request.antecedent_weather[-1]
    else:
        current_record = request.antecedent_weather[-1]
        ref_date = current_record.date

    # 3. Calculate Days Since Sowing (DSS)
    dss_current = _calculate_dss(request.planting_date, ref_date)

    # 4. Score Antecedent Records
    antecedent_scores: list[float] = []
    for rec in request.antecedent_weather:
        dss_rec = _calculate_dss(request.planting_date, rec.date)
        day_score = compute_daily_favorability(
            temp_c=rec.temp_mean,
            rh_pct=rec.humidity_mean,
            rainfall_mm=rec.rainfall_mm,
            soil_moisture_m3m3=rec.soil_moisture_m3m3,
            days_since_sowing=dss_rec,
            pest_profile=profile,
        )
        antecedent_scores.append(day_score.composite_index)

    antecedent_mean = round(sum(antecedent_scores) / max(1, len(antecedent_scores)), 4)

    # Current Day Detailed Score
    current_day_score = compute_daily_favorability(
        temp_c=current_record.temp_mean,
        rh_pct=current_record.humidity_mean,
        rainfall_mm=current_record.rainfall_mm,
        soil_moisture_m3m3=current_record.soil_moisture_m3m3,
        days_since_sowing=dss_current,
        pest_profile=profile,
    )

    current_favorability = DayRiskAssessment(
        date=ref_date,
        temperature_c=current_record.temp_mean,
        humidity_pct=current_record.humidity_mean,
        rainfall_mm=current_record.rainfall_mm,
        soil_moisture_m3m3=current_record.soil_moisture_m3m3,
        temperature_score=current_day_score.temperature_score,
        humidity_score=current_day_score.humidity_score,
        rainfall_score=current_day_score.rainfall_score,
        soil_moisture_score=current_day_score.soil_moisture_score,
        phenology_score=current_day_score.phenology_score,
        composite_favorability_index=current_day_score.composite_index,
        risk_category=current_day_score.risk_category,
        edaphic_included=current_day_score.edaphic_included,
    )

    # 5. Handle Forecast Weather (Strictly Partitioned)
    forecast_records: list[DailyWeatherRecord] = []
    data_notices: list[str] = []

    if request.forecast_weather:
        forecast_records = request.forecast_weather
    elif request.fetch_live_forecast:
        live_records, fetch_err = fetch_open_meteo_forecast(
            latitude=request.latitude,
            longitude=request.longitude,
            days=7,
        )
        if live_records:
            forecast_records = live_records
        else:
            data_notices.append(f"Live forecast unavailable: {fetch_err}. Proceeding with antecedent assessment only.")

    forecast_days: list[DayRiskAssessment] = []
    forecast_scores: list[float] = []

    for f_rec in forecast_records:
        dss_f = _calculate_dss(request.planting_date, f_rec.date)
        f_scores = compute_daily_favorability(
            temp_c=f_rec.temp_mean,
            rh_pct=f_rec.humidity_mean,
            rainfall_mm=f_rec.rainfall_mm,
            soil_moisture_m3m3=f_rec.soil_moisture_m3m3,
            days_since_sowing=dss_f,
            pest_profile=profile,
        )
        forecast_scores.append(f_scores.composite_index)
        forecast_days.append(
            DayRiskAssessment(
                date=f_rec.date,
                temperature_c=f_rec.temp_mean,
                humidity_pct=f_rec.humidity_mean,
                rainfall_mm=f_rec.rainfall_mm,
                soil_moisture_m3m3=f_rec.soil_moisture_m3m3,
                temperature_score=f_scores.temperature_score,
                humidity_score=f_scores.humidity_score,
                rainfall_score=f_scores.rainfall_score,
                soil_moisture_score=f_scores.soil_moisture_score,
                phenology_score=f_scores.phenology_score,
                composite_favorability_index=f_scores.composite_index,
                risk_category=f_scores.risk_category,
                edaphic_included=f_scores.edaphic_included,
            )
        )

    # 6. Trend Analysis
    if forecast_scores:
        forecast_mean: Optional[float] = round(sum(forecast_scores) / len(forecast_scores), 4)
        delta = forecast_mean - antecedent_mean
        if delta >= 0.10:
            risk_trend = "RISING"
        elif delta <= -0.10:
            risk_trend = "DECLINING"
        else:
            risk_trend = "STABLE"

        # Advisory category considers both current and projected peak
        peak_forecast = max(forecast_scores)
        effective_index = max(current_day_score.composite_index, peak_forecast)
        primary_advisory_category = categorize_favorability_risk(effective_index)
    else:
        forecast_mean = None
        risk_trend = "UNKNOWN"
        primary_advisory_category = current_day_score.risk_category

    # 7. Synthesize Explanations & IPM Advisories
    expl = build_explanation_payload(
        scores=current_day_score,
        temp_c=current_record.temp_mean,
        rh_pct=current_record.humidity_mean,
        rainfall_mm=current_record.rainfall_mm,
        soil_moisture_m3m3=current_record.soil_moisture_m3m3,
        days_since_sowing=dss_current,
        profile=profile,
    )

    data_notices.extend(expl["data_notices"])

    # If forecast indicates a rising trend, enrich recommendations
    recommendations = list(expl["recommendations"])
    if risk_trend == "RISING":
        recommendations.insert(
            0,
            f"TREND WARNING (RISING RISK): 7-day meteorological forecast indicates shifting microclimatic conditions "
            f"favorable for a surge in {profile.common_name} population (Forecast Index: {forecast_mean:.2f} vs Past: {antecedent_mean:.2f}). "
            "Heighten scouting frequency across the next 7 days."
        )
    elif risk_trend == "DECLINING":
        recommendations.insert(
            0,
            f"TREND NOTICE (DECLINING RISK): Upcoming meteorological conditions are projected to become less favorable "
            f"for {profile.common_name} (Forecast Index: {forecast_mean:.2f} vs Past: {antecedent_mean:.2f})."
        )

    return RiskAssessmentResponse(
        crop=profile.target_crop,
        pest_common_name=profile.common_name,
        pest_scientific_name=profile.scientific_name,
        location_name=request.location_name,
        latitude=request.latitude,
        longitude=request.longitude,
        assessment_date=ref_date,
        days_since_sowing=dss_current,
        current_favorability=current_favorability,
        antecedent_mean_favorability=antecedent_mean,
        forecast_mean_favorability=forecast_mean,
        forecast_days=forecast_days,
        risk_trend=risk_trend,
        primary_advisory_category=primary_advisory_category,
        favorable_drivers=expl["favorable_drivers"],
        limiting_factors=expl["limiting_factors"],
        data_notices=data_notices,
        recommendations=recommendations,
        biological_thresholds=expl["biological_thresholds"],
        scientific_citations=expl["scientific_citations"],
        disclaimer=expl["disclaimer"],
    )
