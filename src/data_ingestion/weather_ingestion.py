"""
weather_ingestion.py
────────────────────
Automated ingestion of authentic historical agrometeorological time-series
from the Open-Meteo Archive API (with fallback support for NASA POWER).
Focuses on major agricultural districts in Maharashtra, India.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)

# Representative centroid coordinates for major Maharashtra agricultural districts
MAHARASHTRA_DISTRICT_COORDINATES: dict[str, dict[str, float]] = {
    "Nagpur": {"latitude": 21.1458, "longitude": 79.0882},
    "Amravati": {"latitude": 20.9374, "longitude": 77.7796},
    "Yavatmal": {"latitude": 20.3888, "longitude": 78.1204},
    "Jalgaon": {"latitude": 21.0077, "longitude": 75.5626},
    "Nashik": {"latitude": 19.9975, "longitude": 73.7898},
    "Pune": {"latitude": 18.5204, "longitude": 73.8567},
    "Chhatrapati Sambhajinagar": {"latitude": 19.8762, "longitude": 75.3433},
    "Kolhapur": {"latitude": 16.7050, "longitude": 74.2433},
    "Solapur": {"latitude": 17.6599, "longitude": 75.9064},
    "Akola": {"latitude": 20.7002, "longitude": 77.0082},
}

DEFAULT_RAW_DIR = Path("data/raw/weather")


@dataclass
class IngestionConfig:
    district: str
    latitude: float
    longitude: float
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    raw_dir: Path = DEFAULT_RAW_DIR
    timeout_seconds: int = 15
    max_retries: int = 3
    base_backoff_seconds: float = 2.0


def fetch_open_meteo_weather(
    config: IngestionConfig,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Fetch daily historical meteorological observations from Open-Meteo Archive API.
    Utilizes local file caching to prevent redundant network requests.
    """
    config.raw_dir.mkdir(parents=True, exist_ok=True)
    cache_file = config.raw_dir / f"weather_{config.district.lower().replace(' ', '_')}_{config.start_date}_{config.end_date}.json"

    if cache_file.exists() and not force_refresh:
        LOGGER.info("Loading cached weather observations from %s", cache_file)
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    params = {
        "latitude": config.latitude,
        "longitude": config.longitude,
        "start_date": config.start_date,
        "end_date": config.end_date,
        "daily": [
            "temperature_2m_mean",
            "temperature_2m_max",
            "temperature_2m_min",
            "relative_humidity_2m_mean",
            "precipitation_sum",
            "wind_speed_10m_max",
            "soil_moisture_0_to_7cm_mean",
        ],
        "timezone": "Asia/Kolkata",
    }

    query_str = urllib.parse.urlencode(params, doseq=True)
    url = f"https://archive-api.open-meteo.com/v1/archive?{query_str}"
    req = urllib.request.Request(url, headers={"User-Agent": "AgriAdapt-Ingestion/1.0"})

    last_error: Exception | None = None
    for attempt in range(1, config.max_retries + 1):
        try:
            LOGGER.info("Fetching Open-Meteo weather for %s (attempt %d/%d)...", config.district, attempt, config.max_retries)
            with urllib.request.urlopen(req, timeout=config.timeout_seconds) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    # Persist raw response
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    LOGGER.info("Successfully fetched and cached %d daily records to %s", len(data.get("daily", {}).get("time", [])), cache_file)
                    return data
                raise RuntimeError(f"Unexpected HTTP status {response.status}")
        except Exception as exc:
            last_error = exc
            LOGGER.warning("Weather fetch failed on attempt %d: %s", attempt, exc)
            if attempt < config.max_retries:
                sleep_time = config.base_backoff_seconds * (2 ** (attempt - 1))
                time.sleep(sleep_time)

    raise RuntimeError(f"Failed to fetch weather for {config.district} after {config.max_retries} attempts: {last_error}") from last_error


def process_weather_data(
    raw_data: dict[str, Any],
    district: str,
    base_temp_gdd: float = 10.0,
) -> pd.DataFrame:
    """
    Parse raw Open-Meteo JSON into a structured, causal DataFrame with rolling features:
    - Growing Degree-Days (GDD)
    - 7-day rolling mean, min, max temperature
    - 7-day rolling mean relative humidity and count of high RH days (RH >= 80%)
    - 7-day and 14-day cumulative rainfall
    """
    daily = raw_data.get("daily", {})
    if not daily or "time" not in daily:
        raise ValueError("Invalid weather payload: missing 'daily' time-series data.")

    df = pd.DataFrame({
        "observation_date": pd.to_datetime(daily["time"]),
        "district": district,
        "latitude": raw_data.get("latitude", 0.0),
        "longitude": raw_data.get("longitude", 0.0),
        "elevation_m": raw_data.get("elevation", 0.0),
        "temperature_mean": daily["temperature_2m_mean"],
        "temperature_max": daily["temperature_2m_max"],
        "temperature_min": daily["temperature_2m_min"],
        "humidity_mean": daily["relative_humidity_2m_mean"],
        "rainfall_mm": daily["precipitation_sum"],
        "soil_moisture_era5_m3m3": daily.get("soil_moisture_0_to_7cm_mean", [np.nan] * len(daily["time"])),
    })

    # Ensure monotonic date order
    df = df.sort_values("observation_date").reset_index(drop=True)

    # Derived daily agroclimatic indicators
    df["diurnal_temp_range"] = (df["temperature_max"] - df["temperature_min"]).round(2)
    df["gdd_daily"] = np.maximum(0.0, df["temperature_mean"] - base_temp_gdd).round(2)

    # Rolling window aggregations (closed='left' or closed='both' strictly up to t0)
    # Using window=7 closed='right' includes t0 and the 6 preceding days (exactly 7 days prior up to t0)
    df["rainfall_7d"] = df["rainfall_mm"].rolling(window=7, min_periods=1).sum().round(2)
    df["rainfall_14d"] = df["rainfall_mm"].rolling(window=14, min_periods=1).sum().round(2)

    df["t7_mean_temp_c"] = df["temperature_mean"].rolling(window=7, min_periods=1).mean().round(2)
    df["t7_min_temp_c"] = df["temperature_min"].rolling(window=7, min_periods=1).min().round(2)
    df["t7_max_temp_c"] = df["temperature_max"].rolling(window=7, min_periods=1).max().round(2)
    df["t7_mean_rh_pct"] = df["humidity_mean"].rolling(window=7, min_periods=1).mean().round(2)

    is_high_rh = (df["humidity_mean"] >= 80.0).astype(int)
    df["t7_high_rh_days"] = is_high_rh.rolling(window=7, min_periods=1).sum().astype(int)

    df["data_source"] = "Open-Meteo-ERA5-Reanalysis"
    return df

