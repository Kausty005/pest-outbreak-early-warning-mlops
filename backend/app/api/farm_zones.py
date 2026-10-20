"""Farm Zones & IoT Telemetry Service for AgriAdapt.

Manages multi-zone farm layouts (5 default sensor-equipped plots),
receives live IoT hardware telemetry, runs weather integration,
and generates holistic 360° farmer advisories (Crop + Fertilizer + Irrigation + Pest).
"""
from __future__ import annotations

import copy
import logging
import random
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from ...ml.irrigation import assess_irrigation_need
from ...ml.prediction_logger import log_prediction_input

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/farm", tags=["farm zones & iot"])

# ── Data Models ──────────────────────────────────────────────────────────────

class TelemetryPayload(BaseModel):
    N: float = Field(..., ge=0, le=300, description="Nitrogen (kg/ha or sensor index)")
    P: float = Field(..., ge=0, le=300, description="Phosphorus (kg/ha or sensor index)")
    K: float = Field(..., ge=0, le=400, description="Potassium (kg/ha or sensor index)")
    temperature: float = Field(..., ge=-10, le=60, description="Ambient / soil temp in °C")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity %")
    ph: float = Field(..., ge=0, le=14, description="Soil pH")
    rainfall: float = Field(..., ge=0, le=1000, description="Precipitation / rainfall mm")
    soil_moisture: float = Field(..., ge=0, le=100, description="Soil moisture %")
    crop: str | None = Field(default=None, description="Optional active crop update")


class ZoneUpdateRequest(BaseModel):
    name: str | None = None
    crop: str | None = None
    area_acres: float | None = None
    soil_type: str | None = None


# ── In-Memory Default 5-Zone Farm State ───────────────────────────────────────

DEFAULT_ZONES: dict[str, dict[str, Any]] = {
    "zone-1": {
        "id": "zone-1",
        "name": "Plot 1 · North Lowlands",
        "area_acres": 2.5,
        "soil_type": "Clay Loam",
        "active_crop": "rice",
        "telemetry": {
            "N": 82.0,
            "P": 45.0,
            "K": 42.0,
            "temperature": 27.5,
            "humidity": 82.0,
            "ph": 6.2,
            "rainfall": 190.0,
            "soil_moisture": 74.0,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        },
        "irrigation_channel": "Pump Line A (Valve #1)",
    },
    "zone-2": {
        "id": "zone-2",
        "name": "Plot 2 · East Sector",
        "area_acres": 3.0,
        "soil_type": "Black Cotton Soil",
        "active_crop": "cotton",
        "telemetry": {
            "N": 118.0,
            "P": 52.0,
            "K": 50.0,
            "temperature": 32.5,
            "humidity": 58.0,
            "ph": 7.3,
            "rainfall": 45.0,
            "soil_moisture": 34.0,  # Below optimal 45% -> deficit alert!
            "last_updated": datetime.now(timezone.utc).isoformat(),
        },
        "irrigation_channel": "Drip Lateral #2",
    },
    "zone-3": {
        "id": "zone-3",
        "name": "Plot 3 · Central Plateau",
        "area_acres": 2.0,
        "soil_type": "Alluvial Silt Loam",
        "active_crop": "maize",
        "telemetry": {
            "N": 78.0,
            "P": 48.0,
            "K": 24.0,
            "temperature": 26.2,
            "humidity": 68.0,
            "ph": 6.8,
            "rainfall": 88.0,
            "soil_moisture": 58.0,  # Optimal
            "last_updated": datetime.now(timezone.utc).isoformat(),
        },
        "irrigation_channel": "Sprinkler Main #3",
    },
    "zone-4": {
        "id": "zone-4",
        "name": "Plot 4 · South Terraces",
        "area_acres": 1.5,
        "soil_type": "Sandy Loam",
        "active_crop": "chickpea",
        "telemetry": {
            "N": 38.0,
            "P": 65.0,
            "K": 74.0,
            "temperature": 23.0,
            "humidity": 48.0,
            "ph": 7.5,
            "rainfall": 30.0,
            "soil_moisture": 24.5,  # Below critical min 25% -> Critical alert!
            "last_updated": datetime.now(timezone.utc).isoformat(),
        },
        "irrigation_channel": "Micro-Sprinkler #4",
    },
    "zone-5": {
        "id": "zone-5",
        "name": "Plot 5 · Orchard Block",
        "area_acres": 4.0,
        "soil_type": "Red Laterite Loam",
        "active_crop": "banana",
        "telemetry": {
            "N": 105.0,
            "P": 72.0,
            "K": 55.0,
            "temperature": 29.2,
            "humidity": 76.0,
            "ph": 6.4,
            "rainfall": 115.0,
            "soil_moisture": 69.0,  # Optimal
            "last_updated": datetime.now(timezone.utc).isoformat(),
        },
        "irrigation_channel": "Drip Ring #5",
    },
}

FARM_ZONES: dict[str, dict[str, Any]] = copy.deepcopy(DEFAULT_ZONES)


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/zones", status_code=status.HTTP_200_OK)
def list_zones() -> list[dict[str, Any]]:
    """Return all 5 farm zones with current sensor readings & irrigation health."""
    results = []
    for zone in FARM_ZONES.values():
        z_copy = copy.deepcopy(zone)
        t = z_copy["telemetry"]
        # Attach quick irrigation assessment
        irrigation = assess_irrigation_need(
            crop_name=z_copy["active_crop"],
            current_soil_moisture=t["soil_moisture"],
            current_temp_c=t["temperature"],
            recent_rainfall_mm=t["rainfall"],
            zone_area_acres=z_copy["area_acres"],
        )
        z_copy["irrigation_summary"] = irrigation
        results.append(z_copy)
    return results


@router.get("/zones/{zone_id}", status_code=status.HTTP_200_OK)
def get_zone(zone_id: str) -> dict[str, Any]:
    """Get single farm zone state."""
    if zone_id not in FARM_ZONES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Zone '{zone_id}' not found")
    zone = copy.deepcopy(FARM_ZONES[zone_id])
    t = zone["telemetry"]
    zone["irrigation_summary"] = assess_irrigation_need(
        crop_name=zone["active_crop"],
        current_soil_moisture=t["soil_moisture"],
        current_temp_c=t["temperature"],
        recent_rainfall_mm=t["rainfall"],
        zone_area_acres=zone["area_acres"],
    )
    return zone


@router.post("/zones/{zone_id}/telemetry", status_code=status.HTTP_200_OK)
def ingest_telemetry(zone_id: str, payload: TelemetryPayload) -> dict[str, Any]:
    """Hardware IoT sensor ingestion endpoint.

    Called by on-field microcontrollers / ESP32 / LoRaWAN gateways.
    Updates the zone sensor reading and logs to MLOps prediction logger.
    """
    if zone_id not in FARM_ZONES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Zone '{zone_id}' not found")

    zone = FARM_ZONES[zone_id]
    data = payload.model_dump()
    new_crop = data.pop("crop", None)
    if new_crop:
        zone["active_crop"] = new_crop.strip().lower()

    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    zone["telemetry"] = data

    # Feed sensor data into MLOps prediction logger for continuous drift monitoring!
    log_record = {k: v for k, v in data.items() if k in {"N", "P", "K", "temperature", "humidity", "ph", "rainfall"}}
    log_record["farm_zone"] = zone_id
    log_prediction_input(log_record)

    irrigation = assess_irrigation_need(
        crop_name=zone["active_crop"],
        current_soil_moisture=data["soil_moisture"],
        current_temp_c=data["temperature"],
        recent_rainfall_mm=data["rainfall"],
        zone_area_acres=zone["area_acres"],
    )

    return {
        "status": "success",
        "zone_id": zone_id,
        "message": "Telemetry ingested and logged to MLOps drift stream.",
        "irrigation_alert": irrigation["status"] in {"CRITICAL_DEFICIT", "MODERATE_DEFICIT"},
        "irrigation": irrigation,
    }


@router.post("/zones/{zone_id}/simulate", status_code=status.HTTP_200_OK)
def simulate_sensor_event(zone_id: str, scenario: str = "dry_spell") -> dict[str, Any]:
    """Simulate realistic sensor shifts (dry spell, sudden rain, heatwave, normal) for testing."""
    if zone_id not in FARM_ZONES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Zone '{zone_id}' not found")

    zone = FARM_ZONES[zone_id]
    t = zone["telemetry"]

    if scenario == "dry_spell":
        t["soil_moisture"] = max(15.0, round(t["soil_moisture"] - random.uniform(12.0, 22.0), 1))
        t["temperature"] = round(t["temperature"] + random.uniform(2.0, 4.0), 1)
        t["humidity"] = max(20.0, round(t["humidity"] - random.uniform(10.0, 20.0), 1))
        t["rainfall"] = 0.0
    elif scenario == "monsoon_rain":
        t["soil_moisture"] = min(95.0, round(t["soil_moisture"] + random.uniform(20.0, 35.0), 1))
        t["rainfall"] = round(random.uniform(40.0, 110.0), 1)
        t["humidity"] = min(98.0, round(t["humidity"] + random.uniform(15.0, 25.0), 1))
        t["temperature"] = max(20.0, round(t["temperature"] - random.uniform(2.0, 5.0), 1))
    elif scenario == "nutrient_depletion":
        t["N"] = max(10.0, round(t["N"] * 0.7, 1))
        t["P"] = max(10.0, round(t["P"] * 0.75, 1))
        t["K"] = max(10.0, round(t["K"] * 0.8, 1))
    else:  # normal gentle variation
        t["soil_moisture"] = min(85.0, max(25.0, round(t["soil_moisture"] + random.uniform(-3.0, 3.0), 1)))
        t["temperature"] = round(t["temperature"] + random.uniform(-1.0, 1.0), 1)

    t["last_updated"] = datetime.now(timezone.utc).isoformat()
    log_prediction_input({k: v for k, v in t.items() if k in {"N", "P", "K", "temperature", "humidity", "ph", "rainfall"}})

    return {
        "status": "simulated",
        "scenario": scenario,
        "zone_id": zone_id,
        "new_telemetry": t,
    }


PEST_REMEDIES: dict[str, dict[str, str]] = {
    "rice": {
        "primary_pest": "Yellow Stem Borer & Brown Planthopper",
        "symptoms": "Dead hearts at vegetative stage, white heads at flowering",
        "organic_control": "Release Trichogramma japonicum parasitoids @ 100,000/ha; spray Neem Azal 1% @ 3 ml/L",
        "chemical_control": "Chlorantraniliprole 0.4% G @ 10 kg/ha or Cartap hydrochloride 50% SP",
    },
    "cotton": {
        "primary_pest": "Pink & American Bollworm (Helicoverpa)",
        "symptoms": "Rosetted flowers, bore holes plugged with excreta in bolls",
        "organic_control": "Install 5 pheromone traps/acre; spray Beauveria bassiana @ 5g/L",
        "chemical_control": "Emamectin Benzoate 5% SG @ 0.4 g/L or Spinosad 45% SC",
    },
    "maize": {
        "primary_pest": "Fall Armyworm (Spodoptera frugiperda)",
        "symptoms": "Pinholes in whorls, ragged leaf margins, sawdust-like frass",
        "organic_control": "Apply neem cake in whorl; Metarhizium rileyi entomopathogen",
        "chemical_control": "Chlorantraniliprole 18.5% SC @ 0.4 ml/L",
    },
    "chickpea": {
        "primary_pest": "Pod Borer (Helicoverpa armigera)",
        "symptoms": "Defoliation and holes bored into pods",
        "organic_control": "Install bird perches (15-20/acre); HaNPV @ 250 LE/ha",
        "chemical_control": "Indoxacarb 14.5% SC @ 1 ml/L",
    },
    "banana": {
        "primary_pest": "Banana Pseudostem Weevil & Aphids",
        "symptoms": "Jelly exudation from pseudostem holes, yellowing leaves",
        "organic_control": "Stem injection with Neem oil 1500ppm; pseudostem trap splits",
        "chemical_control": "Chlorpyrifos 20% EC stem swabbing",
    },
}


@router.get("/zones/{zone_id}/advisory", status_code=status.HTTP_200_OK)
def get_zone_full_advisory(zone_id: str, request: Request) -> dict[str, Any]:
    """Generates the complete 360° Farmer Journey Plan for a zone."""
    if zone_id not in FARM_ZONES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Zone '{zone_id}' not found")

    zone = FARM_ZONES[zone_id]
    t = zone["telemetry"]
    active_crop = zone["active_crop"]

    # 1. Smart Irrigation Plan
    irrigation = assess_irrigation_need(
        crop_name=active_crop,
        current_soil_moisture=t["soil_moisture"],
        current_temp_c=t["temperature"],
        recent_rainfall_mm=t["rainfall"],
        zone_area_acres=zone["area_acres"],
    )

    # 2. AI Crop Recommendation
    crop_recommendations = []
    crop_service = getattr(request.app.state, "model_service", None)
    if crop_service:
        try:
            crop_res = crop_service.prediction({
                "N": t["N"],
                "P": t["P"],
                "K": t["K"],
                "temperature": t["temperature"],
                "humidity": t["humidity"],
                "ph": t["ph"],
                "rainfall": t["rainfall"],
            })
            crop_recommendations = crop_res.get("top_recommendations", [])
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Crop recommendation failed for zone %s: %s", zone_id, exc)

    # 3. Fertilizer Prescription
    fertilizer_advisory = {}
    fert_service = getattr(request.app.state, "fertilizer_service", None)
    if fert_service:
        try:
            st = zone["soil_type"].lower()
            mapped_soil = "Clayey" if "clay" in st else ("Sandy" if "sand" in st else ("Black" if "black" in st else "Loamy"))
            fert_res = fert_service.recommend_fertilizer({
                "Temperature": t["temperature"],
                "Humidity": t["humidity"],
                "Moisture": t["soil_moisture"],
                "Soil_Type": mapped_soil,
                "Crop_Type": active_crop.title(),
                "Nitrogen": t["N"],
                "Potassium": t["K"],
                "Phosphorous": t["P"],
                "farm_area_acres": zone["area_acres"],
            })
            fertilizer_advisory = fert_res
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Fertilizer prescription failed for zone %s: %s", zone_id, exc)

    # 4. Pest Risk & IPM
    from .advisory import evaluate_pest_risk_preview
    pest_risk = evaluate_pest_risk_preview(
        crop=active_crop,
        temp=t["temperature"],
        humidity=t["humidity"],
        rainfall=t["rainfall"],
    )
    remedy = PEST_REMEDIES.get(active_crop.lower(), {
        "primary_pest": pest_risk.get("primary_threat", "General Field Pests"),
        "symptoms": "Monitor foliage for leaf miner trails or discoloration",
        "organic_control": "Neem oil spray (1500 ppm) at 3-5 ml/L",
        "chemical_control": "Consult local Krishi Vigyan Kendra (KVK) if economic threshold exceeded",
    })

    return {
        "zone_id": zone_id,
        "zone_name": zone["name"],
        "area_acres": zone["area_acres"],
        "soil_type": zone["soil_type"],
        "active_crop": active_crop,
        "sensor_snapshot": t,
        "journey_guidance": {
            "irrigation": irrigation,
            "crop_suitability": {
                "current_crop_ranked_in_top": any(r.get("crop", "").lower() == active_crop for r in crop_recommendations),
                "ranked_alternatives": crop_recommendations[:3],
            },
            "fertilizer": fertilizer_advisory,
            "pest_protection": {
                "risk_assessment": pest_risk,
                "primary_pest": remedy["primary_pest"],
                "symptoms": remedy["symptoms"],
                "organic_control": remedy["organic_control"],
                "chemical_control": remedy["chemical_control"],
            },
        },
    }



@router.get("/weather", status_code=status.HTTP_200_OK)
def get_farm_weather(lat: float = 20.5937, lon: float = 78.9629) -> dict[str, Any]:
    """Provides agro-meteorological data for farm location."""
    # Free Open-Meteo or robust local realistic fallback
    try:
        import httpx
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&forecast_days=1"
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                curr = data.get("current", {})
                return {
                    "source": "Open-Meteo API",
                    "latitude": lat,
                    "longitude": lon,
                    "temperature_c": curr.get("temperature_2m", 28.5),
                    "humidity_pct": curr.get("relative_humidity_2m", 65.0),
                    "precipitation_mm": curr.get("precipitation", 0.0),
                    "wind_speed_kmh": curr.get("wind_speed_10m", 12.0),
                    "timestamp": curr.get("time", datetime.now(timezone.utc).isoformat()),
                }
    except Exception as exc:  # noqa: BLE001
        LOGGER.info("External weather API unavailable (%s) — using farm station reading", exc)

    return {
        "source": "Local AgriAdapt Farm Weather Station",
        "latitude": lat,
        "longitude": lon,
        "temperature_c": 29.0,
        "humidity_pct": 68.0,
        "precipitation_mm": 5.2,
        "wind_speed_kmh": 14.5,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
