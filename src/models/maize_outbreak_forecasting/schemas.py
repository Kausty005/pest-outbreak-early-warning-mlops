"""
src/models/maize_outbreak_forecasting/schemas.py
────────────────────────────────────────────────
Data schemas, contracts, and type definitions for 7-day maize disease outbreak forecasting.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class MaizeGrowthStage(str, Enum):
    """Standard BBCH/CIMMYT physiological growth stages of maize."""
    EMERGENCE_VE = "VE_emergence"
    EARLY_WHORL_V1_V4 = "V1_V4_early_whorl"
    MID_WHORL_V5_V8 = "V5_V8_mid_whorl"
    LATE_WHORL_V9_VT = "V9_VT_late_whorl_tasseling"
    SILKING_R1 = "R1_silking"
    BLISTER_R2 = "R2_blister"
    MILK_R3 = "R3_milk"
    DOUGH_R4 = "R4_dough"
    DENT_R5 = "R5_dent"
    MATURITY_R6 = "R6_physiological_maturity"


class TargetDisease(str, Enum):
    """Target foliar diseases in maize with epidemic potential."""
    COMMON_RUST = "common_rust"           # Puccinia sorghi
    SOUTHERN_RUST = "southern_rust"       # Puccinia polysora
    TURCICUM_BLIGHT = "turcicum_blight"   # Exserohilum turcicum
    GRAY_LEAF_SPOT = "gray_leaf_spot"     # Cercospora zeae-maydis


class DiseaseOccurrenceStatus(str, Enum):
    """Epidemiological categorization at observation time t0."""
    ABSENT = "ABSENT"                             # No disease detected in field (< 0.5% incidence)
    DETECTED_TRACE = "DETECTED_TRACE"             # Trace symptoms detected (0.5% - 2.0% incidence)
    ESTABLISHED_ENDEMIC = "ESTABLISHED_ENDEMIC"   # Low-to-moderate presence without rapid surge (2% - 5%)
    ACTIVE_OUTBREAK = "ACTIVE_OUTBREAK"           # Severe infestation exceeding action threshold (>= 5% severity)


class FieldSurveillanceObservation(BaseModel):
    """
    Standardized in-field scouting observation recorded on observation_date.
    Represents ground truth scouting collected by extension workers / digital traps.
    """
    model_config = ConfigDict(extra="ignore")

    field_id: str = Field(description="Unique identifier for farm plot or geo-cluster")
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    state: str = Field(description="State / Province")
    district: str = Field(description="District / County")
    observation_date: date = Field(description="Date of field visit")

    crop: str = Field(default="maize", description="Must be maize/corn")
    hybrid_variety: str | None = Field(default=None, description="Cultivar or hybrid name (e.g. Pioneer 3396, DKC 9108)")
    variety_resistance_rating: str | None = Field(
        default="MODERATELY_SUSCEPTIBLE",
        description="RESISTANT | MODERATELY_RESISTANT | MODERATELY_SUSCEPTIBLE | SUSCEPTIBLE"
    )
    growth_stage: MaizeGrowthStage = Field(description="Physiological growth stage of crop")
    sowing_date: date | None = Field(default=None, description="Crop planting date")

    target_disease: TargetDisease = Field(default=TargetDisease.COMMON_RUST)
    incidence_pct: float = Field(
        ge=0.0, le=100.0,
        description="Percentage of inspected plants showing leaf symptoms (e.g. 15 plants infected out of 100 = 15%)"
    )
    severity_pct: float = Field(
        ge=0.0, le=100.0,
        description="Percentage of leaf surface area covered by pustules/lesions (Cobb modified scale)"
    )
    pustule_density_score: int | None = Field(
        default=None, ge=0, le=5,
        description="Visual rating score (0 = none, 1 = trace, 2 = low, 3 = moderate, 4 = severe, 5 = devastating)"
    )
    spore_trap_count_per_m3: float | None = Field(
        default=None, ge=0.0,
        description="Airborne urediniospore density if spore trap is active"
    )
    prior_fungicide_applied_days_ago: int | None = Field(
        default=None, ge=0,
        description="Days since last systemic/contact fungicide application, if any"
    )


class DailyAgroclimaticRecord(BaseModel):
    """
    Daily meteorological readings from weather station / NASA POWER / IMD grid for a field.
    """
    model_config = ConfigDict(extra="ignore")

    field_id: str
    date: date
    temp_max_c: float = Field(ge=-10.0, le=55.0, description="Daily maximum temperature in °C")
    temp_min_c: float = Field(ge=-15.0, le=45.0, description="Daily minimum temperature in °C")
    temp_mean_c: float = Field(ge=-10.0, le=50.0, description="Daily average temperature in °C")
    rh_morning_pct: float = Field(ge=0.0, le=100.0, description="Relative humidity at 08:30 IST / morning (%)")
    rh_evening_pct: float = Field(ge=0.0, le=100.0, description="Relative humidity at 17:30 IST / evening (%)")
    rh_mean_pct: float = Field(ge=0.0, le=100.0, description="Daily average relative humidity (%)")
    rainfall_mm: float = Field(ge=0.0, le=500.0, description="Daily cumulative precipitation in mm")
    leaf_wetness_hours: float | None = Field(
        default=None, ge=0.0, le=24.0,
        description="Hours of free moisture on leaf surface (critical for urediniospore germination)"
    )
    wind_speed_kmh: float | None = Field(
        default=None, ge=0.0, le=150.0,
        description="Average wind speed (facilitates spore dispersal)"
    )
    solar_radiation_mj_m2: float | None = Field(
        default=None, ge=0.0,
        description="Surface solar radiation"
    )


class OutbreakPredictionTarget(BaseModel):
    """
    The strictly defined prediction target for a field at date t0 over [t+1, t+7].
    """
    field_id: str
    reference_date: date
    forecast_horizon_days: int = Field(default=7, description="7-day forward window")
    target_disease: TargetDisease = Field(default=TargetDisease.COMMON_RUST)

    # State at t0 (baseline status - MUST NOT be used as the future label!)
    status_at_t0: DiseaseOccurrenceStatus = Field(
        description="Baseline disease presence at date t0 (already present vs absent)"
    )
    baseline_incidence_at_t0: float = Field(description="Incidence at t0 (%)")

    # Future ground truth over [t0 + 1, t0 + 7]
    future_max_incidence_next_7d: float = Field(description="Max incidence recorded in next 7 days")
    future_max_severity_next_7d: float = Field(description="Max severity recorded in next 7 days")
    incidence_delta_next_7d: float = Field(description="Incidence change (future_max - baseline)")

    # Binary outcome target:
    # 1 = A NEW outbreak event occurs in the next 7 days (e.g. crossing economic threshold of >= 5% severity
    #     or rapid jump of >= 10% incidence given baseline was non-outbreak).
    # 0 = No new outbreak observed in next 7 days.
    outbreak_label_7d: int = Field(
        ge=0, le=1,
        description="1 if a new outbreak occurs within 7 days, else 0"
    )
    outbreak_reason: str = Field(description="Epidemiological explanation for assigned label")


class ForecastingFeatureRecord(BaseModel):
    """
    Leakage-free feature vector calculated STRICTLY using data known at date t0.
    """
    field_id: str
    reference_date: date
    target_disease: str
    growth_stage: str

    # Historical weather features over t0-7 to t0
    t7_mean_temp_c: float
    t7_min_temp_c: float
    t7_max_temp_c: float
    t7_temp_favorable_rust_hours_est: float = Field(
        description="Estimated daily hours with temperature between 16°C and 25°C (optimal for Puccinia sorghi)"
    )
    t7_mean_rh_pct: float
    t7_high_rh_days: int = Field(description="Number of days in last 7 with RH > 80%")
    t7_cumulative_rainfall_mm: float
    t7_rainy_days_count: int
    t7_estimated_leaf_wetness_hours_sum: float

    # 14-day cumulative moisture index
    t14_cumulative_rainfall_mm: float

    # Disease pressure & surveillance history at t0 and past
    current_incidence_at_t0: float
    current_severity_at_t0: float
    disease_already_present_t0: int = Field(ge=0, le=1, description="Binary flag: 1 if incidence > 0 at t0")
    regional_outbreak_pressure_last_14d: float = Field(
        default=0.0,
        description="Proportion of neighboring fields in district with active outbreaks in past 14 days"
    )

    # Optional CNN diagnostic feature at t0 (if leaf image was photographed during scouting at t0)
    cnn_observed_leaf_rust_probability_t0: float | None = Field(
        default=None, ge=0.0, le=1.0,
        description="Visual symptom score from MobileNetV2 CNN on leaf sampled at t0 (NOT future forecast)"
    )


class MaizeDiseaseForecastRequest(BaseModel):
    """User/API payload requesting 7-day disease outbreak forecast for a field."""
    field_id: str = Field(description="Field or farm identifier")
    district: str = Field(description="District name (e.g., Belagavi, Davanagere, Chhindwara)")
    state: str = Field(default="Karnataka", description="State name")
    reference_date: date = Field(description="Date for which forecast is generated")
    growth_stage: MaizeGrowthStage = Field(description="Current maize growth stage")
    target_disease: TargetDisease = Field(default=TargetDisease.COMMON_RUST)

    # Current observed field conditions (from recent scouting visit)
    current_incidence_pct: float = Field(
        ge=0.0, le=100.0, default=0.0,
        description="Current visual infection rate (% of plants)"
    )
    current_severity_pct: float = Field(
        ge=0.0, le=100.0, default=0.0,
        description="Current visual severity (% leaf area)"
    )

    # Recent weather observations (last 7 days)
    t7_mean_temperature_c: float = Field(ge=-10.0, le=55.0)
    t7_mean_humidity_pct: float = Field(ge=0.0, le=100.0)
    t7_cumulative_rainfall_mm: float = Field(ge=0.0, le=1000.0)
    t7_consecutive_high_humidity_days: int = Field(default=0, ge=0, le=7)

    # Optional CNN diagnostic image input
    leaf_image_path_at_t0: str | None = Field(
        default=None,
        description="Optional local leaf photograph taken at t0 for CNN symptom feature extraction"
    )


class MaizeDiseaseForecastResponse(BaseModel):
    """Forecast response delivering 7-day risk assessment."""
    field_id: str
    target_disease: str
    forecast_horizon_days: int = 7
    forecast_valid_from: date
    forecast_valid_to: date

    outbreak_probability: float = Field(ge=0.0, le=1.0, description="Calibrated risk probability of outbreak within 7 days")
    risk_tier: str = Field(description="LOW | MODERATE | HIGH | CRITICAL")
    current_field_status: str = Field(description="Status of disease in field today (t0)")
    primary_driving_factors: list[str] = Field(description="Top agroclimatic & epidemiological drivers")
    recommended_preventive_action: str = Field(description="Targeted IPM or fungicide advisory")
    model_provenance: dict[str, Any] = Field(description="Model type, training data disclosure, pipeline version")
    scientific_disclaimer: str
