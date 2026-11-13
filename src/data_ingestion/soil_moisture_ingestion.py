"""
soil_moisture_ingestion.py
──────────────────────────
Acquisition and normalization of root-zone and topsoil moisture data
derived from Copernicus ERA5-Land (0.1° grid) via Open-Meteo or in-situ IoT telemetry.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .weather_ingestion import IngestionConfig, fetch_open_meteo_weather

LOGGER = logging.getLogger(__name__)
DEFAULT_SOIL_RAW_DIR = Path("data/raw/soil")


def extract_soil_moisture_series(
    config: IngestionConfig,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Extract standardized soil moisture series for the specified district and date range.
    Normalizes volumetric soil water content (m3/m3) into volumetric percentage (0-100%).
    """
    DEFAULT_SOIL_RAW_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = DEFAULT_SOIL_RAW_DIR / f"soil_{config.district.lower().replace(' ', '_')}_{config.start_date}_{config.end_date}.json"

    # Reuse cached weather payload if present or fetch freshly
    weather_raw = fetch_open_meteo_weather(config, force_refresh=force_refresh)
    daily = weather_raw.get("daily", {})

    times = daily.get("time", [])
    sm_raw = daily.get("soil_moisture_0_to_7cm_mean", [np.nan] * len(times))

    # Save dedicated soil snapshot
    soil_payload = {
        "district": config.district,
        "latitude": config.latitude,
        "longitude": config.longitude,
        "start_date": config.start_date,
        "end_date": config.end_date,
        "soil_layer": "0-7cm (Topsoil)",
        "source": "Copernicus-ERA5-Land",
        "data": [{"date": t, "soil_moisture_m3m3": sm} for t, sm in zip(times, sm_raw)],
    }
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(soil_payload, f, indent=2)

    df_soil = pd.DataFrame({
        "observation_date": pd.to_datetime(times),
        "district": config.district,
        "soil_moisture_volumetric_m3m3": [float(v) if v is not None else np.nan for v in sm_raw],
    })

    # Convert m3/m3 to soil moisture percentage (0 - 100%)
    df_soil["soil_moisture_pct"] = (df_soil["soil_moisture_volumetric_m3m3"] * 100.0).round(2)

    # Flag saturation or dry conditions
    # Permanent wilting point typically ~0.10 m3/m3, field capacity ~0.35-0.45 m3/m3
    conditions = [
        df_soil["soil_moisture_volumetric_m3m3"] < 0.15,
        (df_soil["soil_moisture_volumetric_m3m3"] >= 0.15) & (df_soil["soil_moisture_volumetric_m3m3"] <= 0.40),
        df_soil["soil_moisture_volumetric_m3m3"] > 0.40,
    ]
    choices = ["DEFICIT", "OPTIMAL", "SURPLUS_SATURATED"]
    df_soil["moisture_status"] = np.select(conditions, choices, default="UNKNOWN")

    LOGGER.info("Extracted %d daily soil moisture records for %s", len(df_soil), config.district)
    return df_soil

