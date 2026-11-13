"""
src/pest_risk
─────────────
Explainable Environmental Pest Risk Assessment Engine (Tier 1 Macro Early Warning).

Provides biophysical environmental favorability evaluation based on
authoritative ICAR, FAO, and agricultural university agronomic thresholds.

NOTE: This engine does NOT provide supervised machine learning predictions
or calibrated outbreak probabilities.
"""
from src.pest_risk.environmental_scoring import (
    DailyFavorabilityScores,
    categorize_favorability_risk,
    compute_daily_favorability,
    compute_humidity_favorability,
    compute_phenological_susceptibility,
    compute_precipitation_favorability,
    compute_soil_moisture_favorability,
    compute_temperature_favorability,
)
from src.pest_risk.explanations import (
    DISCLAIMER_TEXT,
    build_explanation_payload,
    generate_ipm_recommendations,
)
from src.pest_risk.pest_profiles import (
    EdaphicProfile,
    HygrometricProfile,
    PestBiologicalProfile,
    PhenologyProfile,
    PrecipitationProfile,
    ScientificSource,
    ThermalProfile,
    get_pest_profile,
    get_supported_pest_profiles,
    list_supported_crops,
    list_supported_pests_for_crop,
)
from src.pest_risk.risk_assessment import (
    DailyWeatherRecord,
    DayRiskAssessment,
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    assess_pest_risk,
    fetch_open_meteo_forecast,
)

__all__ = [
    # Profiles
    "ThermalProfile",
    "HygrometricProfile",
    "PrecipitationProfile",
    "EdaphicProfile",
    "PhenologyProfile",
    "ScientificSource",
    "PestBiologicalProfile",
    "get_pest_profile",
    "get_supported_pest_profiles",
    "list_supported_crops",
    "list_supported_pests_for_crop",
    # Scoring
    "DailyFavorabilityScores",
    "compute_temperature_favorability",
    "compute_humidity_favorability",
    "compute_precipitation_favorability",
    "compute_soil_moisture_favorability",
    "compute_phenological_susceptibility",
    "compute_daily_favorability",
    "categorize_favorability_risk",
    # Explanations
    "build_explanation_payload",
    "generate_ipm_recommendations",
    "DISCLAIMER_TEXT",
    # Orchestration & Models
    "DailyWeatherRecord",
    "DayRiskAssessment",
    "RiskAssessmentRequest",
    "RiskAssessmentResponse",
    "assess_pest_risk",
    "fetch_open_meteo_forecast",
]
