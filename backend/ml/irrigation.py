"""Agronomic Smart Irrigation Rules Engine for AgriAdapt.

Provides crop-specific soil moisture benchmarks, moisture deficit calculations,
irrigation volume estimates, and automated watering schedules for farm zones.
"""
from __future__ import annotations

from typing import Any

# Crop-specific moisture profiles (% volumetric water content / soil moisture index)
CROP_MOISTURE_PROFILES: dict[str, dict[str, Any]] = {
    "rice": {
        "optimal_min": 70.0,
        "optimal_max": 85.0,
        "critical_min": 55.0,
        "recommended_method": "Shallow flooding / AWD (Alternate Wetting & Drying)",
        "water_sensitivity": "Very High",
        "root_depth_cm": 25,
    },
    "wheat": {
        "optimal_min": 50.0,
        "optimal_max": 65.0,
        "critical_min": 35.0,
        "recommended_method": "Sprinkler or border strip",
        "water_sensitivity": "Moderate",
        "root_depth_cm": 40,
    },
    "maize": {
        "optimal_min": 50.0,
        "optimal_max": 65.0,
        "critical_min": 38.0,
        "recommended_method": "Drip or furrow irrigation",
        "water_sensitivity": "High at tasseling/silking",
        "root_depth_cm": 50,
    },
    "cotton": {
        "optimal_min": 45.0,
        "optimal_max": 60.0,
        "critical_min": 32.0,
        "recommended_method": "Drip irrigation with fertigation",
        "water_sensitivity": "Moderate",
        "root_depth_cm": 60,
    },
    "sugarcane": {
        "optimal_min": 60.0,
        "optimal_max": 75.0,
        "critical_min": 45.0,
        "recommended_method": "Sub-surface drip or paired row furrow",
        "water_sensitivity": "High",
        "root_depth_cm": 75,
    },
    "chickpea": {
        "optimal_min": 35.0,
        "optimal_max": 50.0,
        "critical_min": 25.0,
        "recommended_method": "Light sprinkler (avoids waterlogging / collar rot)",
        "water_sensitivity": "Low (drought tolerant, sensitive to excess)",
        "root_depth_cm": 45,
    },
    "kidneybeans": {
        "optimal_min": 45.0,
        "optimal_max": 60.0,
        "critical_min": 30.0,
        "recommended_method": "Drip or light furrow",
        "water_sensitivity": "Moderate-High at pod set",
        "root_depth_cm": 35,
    },
    "pigeonpeas": {
        "optimal_min": 38.0,
        "optimal_max": 52.0,
        "critical_min": 26.0,
        "recommended_method": "Supplemental drip during dry spells",
        "water_sensitivity": "Low (deep taproot system)",
        "root_depth_cm": 80,
    },
    "mothbeans": {
        "optimal_min": 30.0,
        "optimal_max": 45.0,
        "critical_min": 20.0,
        "recommended_method": "Rainfed / micro-sprinkler if drought persists",
        "water_sensitivity": "Very Low (arid adapted)",
        "root_depth_cm": 35,
    },
    "mungbean": {
        "optimal_min": 40.0,
        "optimal_max": 55.0,
        "critical_min": 28.0,
        "recommended_method": "Check basin or sprinkler",
        "water_sensitivity": "Moderate",
        "root_depth_cm": 35,
    },
    "blackgram": {
        "optimal_min": 40.0,
        "optimal_max": 55.0,
        "critical_min": 28.0,
        "recommended_method": "Check basin or sprinkler",
        "water_sensitivity": "Moderate",
        "root_depth_cm": 35,
    },
    "lentil": {
        "optimal_min": 35.0,
        "optimal_max": 50.0,
        "critical_min": 25.0,
        "recommended_method": "Light sprinkler",
        "water_sensitivity": "Low",
        "root_depth_cm": 30,
    },
    "pomegranate": {
        "optimal_min": 45.0,
        "optimal_max": 60.0,
        "critical_min": 32.0,
        "recommended_method": "Drip irrigation (2 emitters per plant)",
        "water_sensitivity": "Moderate (needs dry period for bahar flowering)",
        "root_depth_cm": 60,
    },
    "banana": {
        "optimal_min": 65.0,
        "optimal_max": 80.0,
        "critical_min": 50.0,
        "recommended_method": "Drip (20-25 L/plant/day) or micro-sprinkler",
        "water_sensitivity": "Very High",
        "root_depth_cm": 45,
    },
    "mango": {
        "optimal_min": 40.0,
        "optimal_max": 55.0,
        "critical_min": 28.0,
        "recommended_method": "Ring basin or drip along dripline",
        "water_sensitivity": "Moderate (withhold before flowering)",
        "root_depth_cm": 90,
    },
    "grapes": {
        "optimal_min": 45.0,
        "optimal_max": 60.0,
        "critical_min": 32.0,
        "recommended_method": "Precision drip with regulated deficit irrigation",
        "water_sensitivity": "High at berry expansion",
        "root_depth_cm": 70,
    },
    "watermelon": {
        "optimal_min": 55.0,
        "optimal_max": 70.0,
        "critical_min": 38.0,
        "recommended_method": "Drip under plastic mulch",
        "water_sensitivity": "High",
        "root_depth_cm": 40,
    },
    "muskmelon": {
        "optimal_min": 50.0,
        "optimal_max": 65.0,
        "critical_min": 35.0,
        "recommended_method": "Drip irrigation (reduce at netting/ripening)",
        "water_sensitivity": "Moderate-High",
        "root_depth_cm": 35,
    },
    "apple": {
        "optimal_min": 55.0,
        "optimal_max": 70.0,
        "critical_min": 40.0,
        "recommended_method": "Micro-sprinkler or drip",
        "water_sensitivity": "High",
        "root_depth_cm": 60,
    },
    "orange": {
        "optimal_min": 50.0,
        "optimal_max": 65.0,
        "critical_min": 35.0,
        "recommended_method": "Drip along canopy dripline",
        "water_sensitivity": "Moderate-High",
        "root_depth_cm": 60,
    },
    "papaya": {
        "optimal_min": 55.0,
        "optimal_max": 70.0,
        "critical_min": 40.0,
        "recommended_method": "Drip or ring basin (avoid stem water contact)",
        "water_sensitivity": "High (sensitive to waterlogging & collar rot)",
        "root_depth_cm": 40,
    },
    "coconut": {
        "optimal_min": 55.0,
        "optimal_max": 70.0,
        "critical_min": 38.0,
        "recommended_method": "Drip (40-50 L/palm/day) or circular basin",
        "water_sensitivity": "Moderate-High",
        "root_depth_cm": 80,
    },
    "jute": {
        "optimal_min": 65.0,
        "optimal_max": 80.0,
        "critical_min": 48.0,
        "recommended_method": "Surface flooding / furrow",
        "water_sensitivity": "High",
        "root_depth_cm": 35,
    },
    "coffee": {
        "optimal_min": 60.0,
        "optimal_max": 75.0,
        "critical_min": 45.0,
        "recommended_method": "Overhead sprinkler / drip",
        "water_sensitivity": "High",
        "root_depth_cm": 50,
    },
}

# Generic fallback profile for unlisted crops
DEFAULT_PROFILE: dict[str, Any] = {
    "optimal_min": 50.0,
    "optimal_max": 65.0,
    "critical_min": 35.0,
    "recommended_method": "Drip or furrow irrigation",
    "water_sensitivity": "Moderate",
    "root_depth_cm": 45,
}


def assess_irrigation_need(
    crop_name: str,
    current_soil_moisture: float,
    current_temp_c: float = 28.0,
    recent_rainfall_mm: float = 0.0,
    zone_area_acres: float = 1.0,
) -> dict[str, Any]:
    """Calculate the precise irrigation advisory for a farm zone.

    Args:
        crop_name: Target crop (e.g. 'rice', 'wheat', 'cotton', etc.)
        current_soil_moisture: Sensor reading in percentage (0 to 100%)
        current_temp_c: Current ambient/soil temperature in °C
        recent_rainfall_mm: Precipitation received recently in mm
        zone_area_acres: Area of the farm zone in acres (default 1.0)

    Returns:
        Structured irrigation advisory dictionary.
    """
    key = crop_name.lower().strip()
    profile = CROP_MOISTURE_PROFILES.get(key, DEFAULT_PROFILE)

    opt_min = profile["optimal_min"]
    opt_max = profile["optimal_max"]
    crit_min = profile["critical_min"]

    # Deduct effective rainfall contribution (e.g., 60% infiltration efficiency)
    effective_rain_moisture_boost = min(20.0, recent_rainfall_mm * 0.4)
    effective_moisture = current_soil_moisture + effective_rain_moisture_boost

    deficit_pct = max(0.0, round(opt_min - effective_moisture, 1))

    # Determine status & urgency
    if effective_moisture < crit_min:
        status = "CRITICAL_DEFICIT"
        urgency = "Immediate (within 12 hours)"
        action = "Start pump immediately. Soil moisture is below wilting stress point."
        color = "#ef4444"  # Red
    elif effective_moisture < opt_min:
        status = "MODERATE_DEFICIT"
        urgency = "Scheduled (within 24-48 hours)"
        action = "Irrigate during evening or early morning to prevent evapotranspiration loss."
        color = "#f59e0b"  # Amber
    elif effective_moisture <= opt_max:
        status = "OPTIMAL"
        urgency = "None"
        action = "Soil moisture is in the optimal growth range. Maintain current schedule."
        color = "#22c55e"  # Green
    elif effective_moisture <= opt_max + 12:
        status = "ADEQUATE_HIGH"
        urgency = "None"
        action = "Moisture is plentiful. Pause irrigation until levels drop below optimal threshold."
        color = "#3b82f6"  # Blue
    else:
        status = "WATERLOGGED"
        urgency = "Drainage Required"
        action = "Excess water detected. Clear drainage furrows to avoid root hypoxia / fungal disease."
        color = "#8b5cf6"  # Purple

    # Estimate required water depth and volume
    # 1 acre = 4046.86 m²
    # Deficit depth mm: approx 1.5mm per 1% moisture deficit for 30-50cm root depth
    root_factor = profile["root_depth_cm"] / 40.0
    water_depth_mm = round(deficit_pct * 1.5 * root_factor, 1) if deficit_pct > 0 else 0.0

    # Evaporation multiplier if temperature > 32°C
    if current_temp_c > 32.0 and water_depth_mm > 0:
        water_depth_mm = round(water_depth_mm * 1.15, 1)

    # 1 mm of water on 1 acre ≈ 4,047 liters
    water_volume_liters = round(water_depth_mm * 4047 * zone_area_acres)

    # Standard farm pump: 5 HP delivers ~20,000 L/hour; 7.5 HP delivers ~30,000 L/hour
    pump_runtime_hours = round(water_volume_liters / 20000.0, 1) if water_volume_liters > 0 else 0.0

    return {
        "crop": crop_name,
        "current_moisture_pct": round(current_soil_moisture, 1),
        "effective_moisture_pct": round(effective_moisture, 1),
        "optimal_range_pct": [opt_min, opt_max],
        "critical_min_pct": crit_min,
        "moisture_deficit_pct": deficit_pct,
        "status": status,
        "urgency": urgency,
        "action": action,
        "status_color": color,
        "recommended_method": profile["recommended_method"],
        "water_sensitivity": profile["water_sensitivity"],
        "water_depth_mm": water_depth_mm,
        "water_volume_liters": water_volume_liters,
        "estimated_pump_runtime_hours": pump_runtime_hours,
        "rainfall_offset_mm": recent_rainfall_mm,
    }
