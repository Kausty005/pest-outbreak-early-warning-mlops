"""
explanations.py
───────────────
Explainability and advisory generation module for the Environmental
Pest Risk Assessment Engine.

Translates physiological sub-scores and atmospheric metrics into
transparent, farmer-comprehensible drivers, limiting factors, actionable
IPM recommendations, and scientific citations.
"""
from __future__ import annotations

from typing import Any, Optional

from src.pest_risk.environmental_scoring import DailyFavorabilityScores
from src.pest_risk.pest_profiles import PestBiologicalProfile

DISCLAIMER_TEXT = (
    "BIOPHYSICAL ADVISORY NOTICE: This assessment represents environmental and microclimatic "
    "favorability for pest proliferation based on peer-reviewed ICAR and FAO agronomic thresholds. "
    "It is NOT a calibrated statistical outbreak probability or guaranteed pest prediction. "
    "Actual pest incidence depends on local pest pressure, previous crop history, beneficial insect "
    "populations, and farm management practices. Physical field scouting and consultation with "
    "local Krishi Vigyan Kendra (KVK) or agricultural extension officers are mandatory before applying any pesticide."
)


def extract_environmental_drivers(
    scores: DailyFavorabilityScores,
    temp_c: float,
    rh_pct: float,
    rainfall_mm: float,
    soil_moisture_m3m3: Optional[float],
    days_since_sowing: Optional[int],
    profile: PestBiologicalProfile,
) -> tuple[list[str], list[str]]:
    """
    Extract key positive drivers elevating risk and limiting factors suppressing risk.

    Returns:
        (favorable_drivers, limiting_factors)
    """
    favorable_drivers: list[str] = []
    limiting_factors: list[str] = []

    # 1. Temperature Analysis
    if scores.temperature_score >= 0.85:
        favorable_drivers.append(
            f"Ambient temperature ({temp_c:.1f}°C) lies within the optimal developmental window "
            f"({profile.thermal.t_opt_min:.1f}°C–{profile.thermal.t_opt_max:.1f}°C), promoting rapid pest metabolism and egg incubation."
        )
    elif scores.temperature_score == 0.0:
        if temp_c <= profile.thermal.t_base:
            limiting_factors.append(
                f"Mean temperature ({temp_c:.1f}°C) is below developmental baseline ({profile.thermal.t_base:.1f}°C), arresting pest growth."
            )
        else:
            limiting_factors.append(
                f"Mean temperature ({temp_c:.1f}°C) exceeds lethal threshold ({profile.thermal.t_upper:.1f}°C), inducing thermal stress and mortality."
            )
    elif scores.temperature_score < 0.50:
        limiting_factors.append(
            f"Sub-optimal thermal conditions ({temp_c:.1f}°C) significantly decelerate developmental rates."
        )

    # 2. Humidity Analysis
    if scores.humidity_score >= 0.85:
        favorable_drivers.append(
            f"Atmospheric humidity ({rh_pct:.1f}%) matches peak suitability ({profile.hygrometric.rh_opt_min:.0f}%–{profile.hygrometric.rh_opt_max:.0f}%), "
            "preventing egg desiccation and enhancing larval survival."
        )
    elif rh_pct < profile.hygrometric.rh_critical_min:
        limiting_factors.append(
            f"Low atmospheric humidity ({rh_pct:.1f}%) induces critical desiccation stress below threshold ({profile.hygrometric.rh_critical_min:.0f}%)."
        )
    elif rh_pct >= profile.hygrometric.rh_pathogen_risk_min:
        limiting_factors.append(
            f"Excessively saturated humidity ({rh_pct:.1f}%) promotes natural entomopathogenic fungal epizootics (e.g. Beauveria bassiana), suppressing populations."
        )

    # 3. Rainfall Analysis
    if rainfall_mm >= profile.precipitation.wash_off_threshold_mm:
        limiting_factors.append(
            f"Torrential rainfall ({rainfall_mm:.1f} mm) exceeds mechanical wash-off threshold ({profile.precipitation.wash_off_threshold_mm:.1f} mm), "
            "dislodging young instars and disrupting adult mating."
        )
    elif profile.precipitation.favorable_daily_rain_min <= rainfall_mm <= profile.precipitation.favorable_daily_rain_max:
        favorable_drivers.append(
            f"Light-to-moderate showers ({rainfall_mm:.1f} mm) sustain canopy microclimate and succulent foliage without causing mechanical dislodgement."
        )
    elif rainfall_mm == 0.0 and profile.precipitation.dry_spell_accelerator:
        favorable_drivers.append(
            "Dry weather interval following previous precipitation accelerates larval feeding activity."
        )

    # 4. Soil Moisture Analysis
    if soil_moisture_m3m3 is not None:
        if scores.soil_moisture_score is not None and scores.soil_moisture_score >= 0.85:
            favorable_drivers.append(
                f"Topsoil volumetric moisture ({soil_moisture_m3m3 * 100:.1f}%) provides optimal friability for pupation and adult emergence."
            )
        elif soil_moisture_m3m3 < profile.edaphic.soil_moisture_min_m3m3:
            limiting_factors.append(
                f"Dry, crusted topsoil ({soil_moisture_m3m3 * 100:.1f}%) restricts larval burrowing and inhibits adult moth eclosion."
            )
        elif soil_moisture_m3m3 > profile.edaphic.soil_moisture_max_m3m3:
            limiting_factors.append(
                f"Waterlogged topsoil ({soil_moisture_m3m3 * 100:.1f}%) causes hypoxia, suppressing pupal emergence."
            )

    # 5. Phenological Susceptibility Analysis
    if days_since_sowing is not None:
        if scores.phenology_score >= 0.85:
            favorable_drivers.append(
                f"Crop age ({days_since_sowing} days since sowing) is in its peak vulnerable phenological stage "
                f"({profile.phenology.peak_susceptibility_start_day}–{profile.phenology.peak_susceptibility_end_day} DSS), "
                f"supplying abundant host tissue ({', '.join(profile.phenology.susceptible_stages)})."
            )
        elif scores.phenology_score <= 0.20:
            limiting_factors.append(
                f"Crop age ({days_since_sowing} DSS) precedes or follows the susceptible window ({profile.phenology.susceptibility_start_day}–{profile.phenology.susceptibility_end_day} DSS); "
                "essential host reproductive structures are absent or senescent."
            )

    return favorable_drivers, limiting_factors


def generate_ipm_recommendations(
    category: str,
    profile: PestBiologicalProfile,
    days_since_sowing: Optional[int] = None,
) -> list[str]:
    """Generate agronomic recommendations aligned with ICAR/NCIPM IPM guidelines."""
    recommendations: list[str] = []

    if category == "LOW":
        recommendations.append(
            "Microclimate currently suppresses rapid pest propagation. Maintain routine crop monitoring at 10–14 day intervals."
        )
        recommendations.append(
            "Conserve naturally occurring beneficial predators and parasitoids (e.g. Chrysoperla carnea, Trichogramma chilonis). Avoid unnecessary chemical sprays."
        )
    elif category == "MODERATE":
        recommendations.append(
            f"Environmental conditions are conducive for {profile.common_name} buildup. Deploy surveillance pheromone traps (5 traps/ha) or light traps to monitor adult moth flights."
        )
        recommendations.append(
            "Initiate weekly scouting: inspect 20 representative plants randomly selected across 5 field quadrants. Record flower/bud damage and presence of early instars."
        )
        recommendations.append(
            "Prepare biological or botanical deterrents (e.g. 5% Neem Seed Kernel Extract / NSKE 1500 ppm or Bacillus thuringiensis) for timely intervention if trap catches exceed threshold."
        )
    else:  # HIGH
        recommendations.append(
            f"CRITICAL FAVORABILITY ALERT: Microclimatic conditions are highly favorable for rapid {profile.common_name} population expansion."
        )
        recommendations.append(
            "Perform immediate intensive field scouting within 24–48 hours across 20–25 random plants across all field boundaries and interiors."
        )
        recommendations.append(
            f"Check local Economic Threshold Level (ETL): e.g. for Pink Bollworm, 8–10 moths/trap/night for 3 consecutive days or 10% rosette flowers / green boll damage."
        )
        recommendations.append(
            "If field scouting confirms pest numbers at or above ETL, execute recommended ICAR-approved targeted intervention without delay. Consult local KVK extension specialist."
        )

    return recommendations


def build_explanation_payload(
    scores: DailyFavorabilityScores,
    temp_c: float,
    rh_pct: float,
    rainfall_mm: float,
    soil_moisture_m3m3: Optional[float],
    days_since_sowing: Optional[int],
    profile: PestBiologicalProfile,
) -> dict[str, Any]:
    """
    Build complete explainability dictionary including drivers, inhibitors,
    agronomic recommendations, missing feature notices, and authoritative citations.
    """
    favorable_drivers, limiting_factors = extract_environmental_drivers(
        scores=scores,
        temp_c=temp_c,
        rh_pct=rh_pct,
        rainfall_mm=rainfall_mm,
        soil_moisture_m3m3=soil_moisture_m3m3,
        days_since_sowing=days_since_sowing,
        profile=profile,
    )

    recommendations = generate_ipm_recommendations(
        category=scores.risk_category,
        profile=profile,
        days_since_sowing=days_since_sowing,
    )

    data_notices: list[str] = []
    if soil_moisture_m3m3 is None:
        data_notices.append(
            "Topsoil volumetric moisture data was unavailable. Edaphic suitability was excluded, and atmospheric weights were re-normalized."
        )
    if days_since_sowing is None:
        data_notices.append(
            "Sowing date was not specified. A baseline host susceptibility factor (0.85) was applied. Provide planting date for refined phenological precision."
        )

    sources_summary = [
        {
            "title": src.title,
            "authors": src.authors,
            "year": src.year,
            "institution_or_journal": src.institution_or_journal,
            "url": src.url,
            "key_finding": src.relevance_notes,
        }
        for src in profile.sources
    ]

    return {
        "pest_common_name": profile.common_name,
        "pest_scientific_name": profile.scientific_name,
        "target_crop": profile.target_crop,
        "composite_favorability_index": scores.composite_index,
        "risk_category": scores.risk_category,
        "favorable_drivers": favorable_drivers,
        "limiting_factors": limiting_factors,
        "data_notices": data_notices,
        "recommendations": recommendations,
        "biological_thresholds": {
            "thermal": {
                "t_base_c": profile.thermal.t_base,
                "t_opt_min_c": profile.thermal.t_opt_min,
                "t_opt_max_c": profile.thermal.t_opt_max,
                "t_upper_c": profile.thermal.t_upper,
                "generation_gdd": profile.thermal.generation_degree_days,
            },
            "hygrometric": {
                "rh_critical_min_pct": profile.hygrometric.rh_critical_min,
                "rh_opt_min_pct": profile.hygrometric.rh_opt_min,
                "rh_opt_max_pct": profile.hygrometric.rh_opt_max,
            },
            "precipitation": {
                "favorable_rain_max_mm": profile.precipitation.favorable_daily_rain_max,
                "wash_off_threshold_mm": profile.precipitation.wash_off_threshold_mm,
            },
            "edaphic": {
                "soil_moisture_opt_min_m3m3": profile.edaphic.soil_moisture_opt_min,
                "soil_moisture_opt_max_m3m3": profile.edaphic.soil_moisture_opt_max,
                "pupates_in_soil": profile.edaphic.pupates_in_soil,
            },
            "phenology": {
                "susceptible_stages": profile.phenology.susceptible_stages,
                "peak_susceptibility_window_dss": [
                    profile.phenology.peak_susceptibility_start_day,
                    profile.phenology.peak_susceptibility_end_day,
                ],
            },
        },
        "scientific_citations": sources_summary,
        "disclaimer": DISCLAIMER_TEXT,
    }
