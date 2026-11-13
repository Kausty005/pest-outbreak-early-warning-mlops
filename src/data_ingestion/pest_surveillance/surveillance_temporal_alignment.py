"""
surveillance_temporal_alignment.py
──────────────────────────────────
Temporal alignment module linking weekly/periodic pest observations
with daily gridded environmental time-series without lookahead leakage.

Implements:
- Standard Meteorological Week (SMW 1–52) derivation (IMD convention)
- Causal antecedent environmental feature aggregation [T-6, T]
- Temporal gap validation
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np
import pandas as pd

from src.data_ingestion.pest_surveillance.surveillance_schema import SurveillanceRecord

LOGGER = logging.getLogger(__name__)


def calculate_smw(target_date: str | datetime | pd.Timestamp) -> int:
    """
    Compute Standard Meteorological Week (SMW 1 to 52) following IMD convention.

    Week 1 starts on January 1st; each week spans exactly 7 calendar days.
    Days 358–365 (or 366 in leap year) map to SMW 52.
    """
    if isinstance(target_date, str):
        dt = datetime.strptime(target_date[:10], "%Y-%m-%d")
    elif isinstance(target_date, (pd.Timestamp, datetime)):
        dt = target_date
    else:
        raise ValueError(f"Unsupported date format: {type(target_date)}")

    day_of_year = dt.timetuple().tm_yday
    smw = min(52, ((day_of_year - 1) // 7) + 1)
    return int(smw)


@dataclass
class TemporallyAlignedFeatures:
    """Causal antecedent environmental features aligned to a surveillance observation date."""
    observation_id: str
    observation_date: str
    smw: int
    matched_environmental_location: str
    antecedent_window_days: int
    t7_mean_temp_c: float
    t7_min_temp_c: float
    t7_max_temp_c: float
    t7_mean_rh_pct: float
    t7_high_rh_days: int
    rainfall_7d_mm: float
    rainfall_14d_mm: Optional[float]
    soil_moisture_era5_m3m3: Optional[float]
    gdd_accumulated_7d: float
    temporal_coverage_complete: bool
    data_notices: list[str]


def extract_antecedent_environmental_features(
    record: SurveillanceRecord,
    matched_location: str,
    environmental_df: pd.DataFrame,
    base_temp_c: float = 12.0,
) -> TemporallyAlignedFeatures:
    """
    Extract causal antecedent rolling weather and soil moisture features up to observation date T.

    STRICT CAUSALITY GUARANTEE:
    Only observations where observation_date <= T are utilized.
    Zero future information is leaked into the feature vector.
    """
    t_obs = record.observation_date[:10]
    smw = calculate_smw(t_obs)

    # Normalize column names in environmental_df
    df = environmental_df.copy()
    if "observation_date" not in df.columns and "date" in df.columns:
        df["observation_date"] = df["date"]

    df["observation_date"] = pd.to_datetime(df["observation_date"]).dt.strftime("%Y-%m-%d")
    df["district_normalized"] = df["district"].astype(str).str.strip().str.lower()

    norm_loc = matched_location.strip().lower()
    district_env = df[df["district_normalized"] == norm_loc].sort_values("observation_date")

    # Filter to antecedent window [T-6, T]
    antecedent = district_env[district_env["observation_date"] <= t_obs].tail(7)

    notices: list[str] = []
    if len(antecedent) < 7:
        notices.append(
            f"Incomplete antecedent weather coverage: only {len(antecedent)} records available "
            f"leading up to {t_obs} (requires 7)."
        )

    if antecedent.empty:
        raise ValueError(
            f"Zero antecedent environmental records found for {matched_location} on or before {t_obs}."
        )

    # Compute aggregates
    t_mean = float(antecedent["temperature_mean"].mean())
    t_min = float(antecedent["temperature_min"].min()) if "temperature_min" in antecedent.columns else t_mean
    t_max = float(antecedent["temperature_max"].max()) if "temperature_max" in antecedent.columns else t_mean
    rh_mean = float(antecedent["humidity_mean"].mean())
    rain_7d = float(antecedent["rainfall_mm"].sum())

    # High humidity days (RH >= 75%)
    high_rh_days = int((antecedent["humidity_mean"] >= 75.0).sum())

    # 14-day rainfall if available
    antecedent_14 = district_env[district_env["observation_date"] <= t_obs].tail(14)
    rain_14d = float(antecedent_14["rainfall_mm"].sum()) if len(antecedent_14) >= 10 else None

    # Soil moisture from ERA5-Land
    sm_val: Optional[float] = None
    if "soil_moisture_era5_m3m3" in antecedent.columns:
        valid_sm = antecedent["soil_moisture_era5_m3m3"].dropna()
        if not valid_sm.empty:
            sm_val = round(float(valid_sm.mean()), 4)

    # GDD accumulated over 7 days
    gdd_series = (antecedent["temperature_mean"] - base_temp_c).clip(lower=0.0)
    gdd_7d = round(float(gdd_series.sum()), 2)

    return TemporallyAlignedFeatures(
        observation_id=record.observation_id,
        observation_date=t_obs,
        smw=smw,
        matched_environmental_location=matched_location,
        antecedent_window_days=len(antecedent),
        t7_mean_temp_c=round(t_mean, 2),
        t7_min_temp_c=round(t_min, 2),
        t7_max_temp_c=round(t_max, 2),
        t7_mean_rh_pct=round(rh_mean, 2),
        t7_high_rh_days=high_rh_days,
        rainfall_7d_mm=round(rain_7d, 2),
        rainfall_14d_mm=round(rain_14d, 2) if rain_14d is not None else None,
        soil_moisture_era5_m3m3=sm_val,
        gdd_accumulated_7d=gdd_7d,
        temporal_coverage_complete=(len(antecedent) == 7),
        data_notices=notices,
    )

