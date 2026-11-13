"""
environmental_scoring.py
────────────────────────
Biophysical scoring algorithms computing environmental favorability
sub-indices for pest multiplication and damage.

CRITICAL ARCHITECTURAL PRINCIPLE:
Every function here computes physiological suitability on a continuous
[0.0, 1.0] scale using non-linear and trapezoidal biological response curves.
This output represents strictly an ENVIRONMENTAL FAVORABILITY INDEX (EFI),
NOT a calibrated outbreak probability or machine learning prediction.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from src.pest_risk.pest_profiles import (
    EdaphicProfile,
    HygrometricProfile,
    PestBiologicalProfile,
    PhenologyProfile,
    PrecipitationProfile,
    ThermalProfile,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DailyFavorabilityScores:
    """Detailed favorability sub-scores and composite index for a single day."""
    temperature_score: float
    humidity_score: float
    rainfall_score: float
    soil_moisture_score: Optional[float]
    phenology_score: float
    composite_index: float
    risk_category: str  # "LOW", "MODERATE", "HIGH"
    edaphic_included: bool


def compute_temperature_favorability(temp_c: float, profile: ThermalProfile) -> float:
    """
    Compute temperature favorability score S_T in [0.0, 1.0].

    Implements trapezoidal thermal development curve based on:
    - Lower developmental threshold (t_base)
    - Optimum thermal plateau (t_opt_min to t_opt_max)
    - Upper developmental/lethal threshold (t_upper)

    Returns:
        float in [0.0, 1.0]. Returns 0.0 if temp <= t_base or temp >= t_upper.
    """
    if temp_c <= profile.t_base or temp_c >= profile.t_upper:
        return 0.0

    if profile.t_opt_min <= temp_c <= profile.t_opt_max:
        return 1.0

    if profile.t_base < temp_c < profile.t_opt_min:
        return max(0.0, min(1.0, (temp_c - profile.t_base) / (profile.t_opt_min - profile.t_base)))

    # temp_c between t_opt_max and t_upper
    return max(0.0, min(1.0, (profile.t_upper - temp_c) / (profile.t_upper - profile.t_opt_max)))


def compute_humidity_favorability(rh_pct: float, profile: HygrometricProfile) -> float:
    """
    Compute atmospheric relative humidity favorability score S_RH in [0.0, 1.0].

    Grounded in insect desiccation thresholds and entomopathogenic fungal dynamics.
    - Low RH (< rh_critical_min) causes egg desiccation and nymphal mortality.
    - Optimal RH (rh_opt_min to rh_opt_max) supports rapid development.
    - Saturated RH (> rh_pathogen_risk_min) promotes natural fungal epizootics.

    Returns:
        float in [0.0, 1.0].
    """
    clamped_rh = max(0.0, min(100.0, rh_pct))

    if clamped_rh <= profile.rh_critical_min:
        # Severe desiccating stress; residual baseline 0.05
        return max(0.0, 0.05 * (clamped_rh / max(1.0, profile.rh_critical_min)))

    if profile.rh_opt_min <= clamped_rh <= profile.rh_opt_max:
        return 1.0

    if profile.rh_critical_min < clamped_rh < profile.rh_opt_min:
        # Ascending limb
        fraction = (clamped_rh - profile.rh_critical_min) / (profile.rh_opt_min - profile.rh_critical_min)
        return 0.05 + 0.95 * fraction

    # clamped_rh > profile.rh_opt_max
    if clamped_rh >= profile.rh_pathogen_risk_min:
        # High humidity favors entomopathogens (Beauveria bassiana, Metarhizium),
        # offering natural biological suppression (modulates score down to 0.70)
        excess = (clamped_rh - profile.rh_pathogen_risk_min) / (100.0 - profile.rh_pathogen_risk_min)
        return max(0.65, 1.0 - 0.35 * excess)

    # Moderate plateau between rh_opt_max and rh_pathogen_risk_min
    return 1.0


def compute_precipitation_favorability(rainfall_mm: float, profile: PrecipitationProfile) -> float:
    """
    Compute daily precipitation favorability score S_R in [0.0, 1.0].

    Captures:
    - Light-moderate rain (2-20 mm) maintains canopy moisture and host succulent turgor.
    - Zero rain: favorable if dry_spell_accelerator is active, else neutral baseline (0.70).
    - Torrential rainfall (> wash_off_threshold_mm): mechanical wash-off of eggs and early instars.

    Returns:
        float in [0.0, 1.0].
    """
    r = max(0.0, rainfall_mm)

    if r == 0.0:
        return 0.85 if profile.dry_spell_accelerator else 0.70

    if profile.favorable_daily_rain_min <= r <= profile.favorable_daily_rain_max:
        return 1.0

    if 0.0 < r < profile.favorable_daily_rain_min:
        # Ascending towards optimal
        base = 0.85 if profile.dry_spell_accelerator else 0.70
        fraction = r / profile.favorable_daily_rain_min
        return base + (1.0 - base) * fraction

    if profile.favorable_daily_rain_max < r <= profile.wash_off_threshold_mm:
        # Mild disturbance, descending towards 0.40
        fraction = (r - profile.favorable_daily_rain_max) / (profile.wash_off_threshold_mm - profile.favorable_daily_rain_max)
        return max(0.40, 1.0 - 0.60 * fraction)

    # Extreme rainfall above wash-off threshold (> 40-60 mm/day): mechanical wash-off
    excess = min(1.0, (r - profile.wash_off_threshold_mm) / 50.0)
    return max(0.10, 0.40 - 0.30 * excess)


def compute_soil_moisture_favorability(
    soil_moisture_m3m3: Optional[float],
    profile: EdaphicProfile,
) -> Optional[float]:
    """
    Compute topsoil (0-7 cm) moisture favorability score S_SM in [0.0, 1.0].

    Relevant for pests pupating in soil (e.g. Pink Bollworm, Spodoptera litura, Helicoverpa):
    - Dry soil (< min): soil crusting prevents pupal entry or traps adults upon eclosion.
    - Optimal soil moisture (opt_min to opt_max): favorable for pupation, survival, and emergence.
    - Saturated soil (> max): hypoxia and pupal drowning/rot.

    Returns:
        float in [0.0, 1.0] if soil_moisture_m3m3 is provided, else None.
    """
    if soil_moisture_m3m3 is None:
        return None

    sm = max(0.0, min(1.0, soil_moisture_m3m3))

    if not profile.pupates_in_soil:
        # For foliage/stem pests like Brown Planthopper on rice, high soil moisture
        # promotes high canopy micro-humidity
        if sm >= profile.soil_moisture_opt_min:
            return 1.0
        return max(0.40, sm / profile.soil_moisture_opt_min)

    if sm < profile.soil_moisture_min_m3m3:
        fraction = sm / max(0.01, profile.soil_moisture_min_m3m3)
        return max(0.05, 0.15 * fraction)

    if profile.soil_moisture_opt_min <= sm <= profile.soil_moisture_opt_max:
        return 1.0

    if profile.soil_moisture_min_m3m3 <= sm < profile.soil_moisture_opt_min:
        fraction = (sm - profile.soil_moisture_min_m3m3) / (profile.soil_moisture_opt_min - profile.soil_moisture_min_m3m3)
        return 0.15 + 0.85 * fraction

    if profile.soil_moisture_opt_max < sm <= profile.soil_moisture_max_m3m3:
        fraction = (sm - profile.soil_moisture_opt_max) / (profile.soil_moisture_max_m3m3 - profile.soil_moisture_opt_max)
        return max(0.15, 1.0 - 0.85 * fraction)

    # Waterlogged (> max)
    return 0.10


def compute_phenological_susceptibility(
    days_since_sowing: Optional[int],
    profile: PhenologyProfile,
) -> float:
    """
    Compute crop host tissue availability and susceptibility score S_P in [0.0, 1.0].

    Prevents false early warnings when target host structures (e.g., squares/bolls for
    Pink Bollworm, cobs for FAW) are agronomically absent from the field.

    Returns:
        float in [0.05, 1.0]. Returns 0.85 default if days_since_sowing is None.
    """
    if days_since_sowing is None:
        return 0.85  # Neutral-conservative susceptibility when sowing date is unknown

    dss = max(0, days_since_sowing)

    if dss < profile.susceptibility_start_day:
        # Host tissue absent (e.g. seedling cotton has no buds or bolls)
        return 0.10

    if profile.susceptibility_start_day <= dss < profile.peak_susceptibility_start_day:
        # Host entering vulnerable stage
        fraction = (dss - profile.susceptibility_start_day) / max(1, profile.peak_susceptibility_start_day - profile.susceptibility_start_day)
        return 0.10 + 0.90 * fraction

    if profile.peak_susceptibility_start_day <= dss <= profile.peak_susceptibility_end_day:
        # Peak susceptibility window (e.g. green boll formation)
        return 1.0

    if profile.peak_susceptibility_end_day < dss <= profile.susceptibility_end_day:
        # Senescence / maturing
        fraction = (dss - profile.peak_susceptibility_end_day) / max(1, profile.susceptibility_end_day - profile.peak_susceptibility_end_day)
        return max(0.15, 1.0 - 0.85 * fraction)

    # Post-harvest / dry stalks
    return 0.05


def categorize_favorability_risk(composite_index: float) -> str:
    """
    Categorize continuous favorability index into categorical advisory levels.

    - LOW: < 0.40 (Environmental conditions actively suppress or arrest pest development)
    - MODERATE: 0.40 to 0.69 (Conducive microclimate; routine scouting warranted)
    - HIGH: >= 0.70 (Highly favorable conditions; rapid pest population surge supported)
    """
    if composite_index < 0.40:
        return "LOW"
    elif composite_index < 0.70:
        return "MODERATE"
    else:
        return "HIGH"


def compute_daily_favorability(
    temp_c: float,
    rh_pct: float,
    rainfall_mm: float,
    soil_moisture_m3m3: Optional[float],
    days_since_sowing: Optional[int],
    pest_profile: PestBiologicalProfile,
) -> DailyFavorabilityScores:
    """
    Compute physiological sub-scores and composite Environmental Favorability Index.

    MATHEMATICAL FORMULATION:
    1. Temperature is a non-compensatory developmental gate:
       If ambient temperature is lethal or below developmental base (S_T == 0),
       development stops completely regardless of moisture.
    2. Environmental microclimate favorability S_env is the weighted combination
       of Relative Humidity, Precipitation, and (optionally) Soil Moisture.
       - With soil moisture: w_rh = 0.50, w_rain = 0.25, w_sm = 0.25
       - Without soil moisture: w_rh = 0.65, w_rain = 0.35 (normalized)
    3. Phenological susceptibility S_P scales the accessible host biomass.
    4. Composite EFI = S_T * S_env * S_P

    Returns:
        DailyFavorabilityScores instance with sub-scores, composite index, and category.
    """
    s_temp = compute_temperature_favorability(temp_c, pest_profile.thermal)
    s_rh = compute_humidity_favorability(rh_pct, pest_profile.hygrometric)
    s_rain = compute_precipitation_favorability(rainfall_mm, pest_profile.precipitation)
    s_sm = compute_soil_moisture_favorability(soil_moisture_m3m3, pest_profile.edaphic)
    s_pheno = compute_phenological_susceptibility(days_since_sowing, pest_profile.phenology)

    # Compute microclimate environmental sub-index
    if s_sm is not None:
        w_rh = 0.50
        w_rain = 0.25
        w_sm = 0.25
        s_env = (w_rh * s_rh) + (w_rain * s_rain) + (w_sm * s_sm)
        edaphic_included = True
    else:
        w_rh = 0.65
        w_rain = 0.35
        s_env = (w_rh * s_rh) + (w_rain * s_rain)
        edaphic_included = False

    # Composite index calculation
    composite = s_temp * s_env * s_pheno
    composite = max(0.0, min(1.0, round(composite, 4)))

    category = categorize_favorability_risk(composite)

    return DailyFavorabilityScores(
        temperature_score=round(s_temp, 4),
        humidity_score=round(s_rh, 4),
        rainfall_score=round(s_rain, 4),
        soil_moisture_score=round(s_sm, 4) if s_sm is not None else None,
        phenology_score=round(s_pheno, 4),
        composite_index=composite,
        risk_category=category,
        edaphic_included=edaphic_included,
    )
