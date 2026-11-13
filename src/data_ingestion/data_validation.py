"""
data_validation.py
──────────────────
Rigorous data quality, physical plausibility, and integrity validation
for raw and aligned environmental and agricultural surveillance records.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)

# Geographic boundaries for Maharashtra State, India
MAHARASHTRA_BOUNDS = {
    "lat_min": 15.6,
    "lat_max": 22.1,
    "lon_min": 72.6,
    "lon_max": 80.9,
}

# Physical agronomic and atmospheric bounds
PHYSICAL_BOUNDS = {
    "temp_min_c": -5.0,
    "temp_max_c": 55.0,
    "humidity_min_pct": 0.0,
    "humidity_max_pct": 100.0,
    "rainfall_daily_max_mm": 1000.0,
    "soil_moisture_max_m3m3": 0.75,
    "soil_ph_min": 3.0,
    "soil_ph_max": 10.5,
    "pest_pct_max": 100.0,
}


@dataclass
class ValidationReport:
    total_records: int
    is_valid: bool
    passed_checks: list[str] = field(default_factory=list)
    failed_checks: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    null_counts: dict[str, int] = field(default_factory=dict)
    duplicate_count: int = 0
    temporal_gap_days: int = 0
    details: dict[str, Any] = field(default_factory=dict)


def validate_environmental_dataframe(
    df: pd.DataFrame,
    strict_maharashtra_bounds: bool = True,
) -> ValidationReport:
    """
    Execute battery of physical, temporal, and spatial validation tests on environmental data.
    """
    passed: list[str] = []
    failed: list[str] = []
    warnings: list[str] = []

    if df.empty:
        return ValidationReport(total_records=0, is_valid=False, failed_checks=["EMPTY_DATAFRAME"])

    total = len(df)
    null_counts = {col: int(df[col].isnull().sum()) for col in df.columns}

    # 1. Coordinate Validation
    if "latitude" in df.columns and "longitude" in df.columns:
        valid_coords = df["latitude"].notnull() & df["longitude"].notnull()
        if strict_maharashtra_bounds:
            in_bounds = (
                (df["latitude"] >= MAHARASHTRA_BOUNDS["lat_min"]) &
                (df["latitude"] <= MAHARASHTRA_BOUNDS["lat_max"]) &
                (df["longitude"] >= MAHARASHTRA_BOUNDS["lon_min"]) &
                (df["longitude"] <= MAHARASHTRA_BOUNDS["lon_max"])
            )
            out_count = int((~in_bounds & valid_coords).sum())
            if out_count > 0:
                warnings.append(f"COORDINATES_OUTSIDE_MAHARASHTRA: {out_count} records lie outside typical state bounds.")
            else:
                passed.append("GEOGRAPHIC_COORDINATES_WITHIN_BOUNDS")
        else:
            passed.append("COORDINATES_CHECKED")
    else:
        failed.append("MISSING_COORDINATE_COLUMNS")

    # 2. Duplicate Check
    dup_cols = [c for c in ["district", "observation_date"] if c in df.columns]
    dups = int(df.duplicated(subset=dup_cols).sum()) if len(dup_cols) == 2 else 0
    if dups > 0:
        failed.append(f"DUPLICATE_OBSERVATIONS: {dups} duplicate district-date pairs detected.")
    else:
        passed.append("NO_DUPLICATE_DISTRICT_DATES")

    # 3. Timestamp Sanity & Gap Detection
    temporal_gaps = 0
    if "observation_date" in df.columns:
        dates = pd.to_datetime(df["observation_date"])
        now = pd.Timestamp.now(tz=None)
        future_dates = int((dates > now).sum())
        if future_dates > 0:
            failed.append(f"FUTURE_TIMESTAMPS: {future_dates} observations contain future timestamps.")
        else:
            passed.append("TIMESTAMPS_HISTORICAL_ONLY")

        # Gap detection within each district
        if "district" in df.columns:
            for dist, group in df.groupby("district"):
                sorted_dates = group["observation_date"].sort_values()
                deltas = (sorted_dates.diff().dt.total_seconds() / 86400.0).dropna()
                gaps = int((deltas > 1.5).sum())
                temporal_gaps += gaps
            if temporal_gaps > 0:
                warnings.append(f"TEMPORAL_GAPS_DETECTED: {temporal_gaps} missing calendar days identified across series.")
            else:
                passed.append("CONTINUOUS_DAILY_TIME_SERIES")

    # 4. Physical Atmosphere Bounds
    if "temperature_mean" in df.columns:
        t_mean = df["temperature_mean"].dropna()
        viol = int(((t_mean < PHYSICAL_BOUNDS["temp_min_c"]) | (t_mean > PHYSICAL_BOUNDS["temp_max_c"])).sum())
        if viol > 0:
            failed.append(f"TEMPERATURE_PHYSICAL_VIOLATIONS: {viol} records outside [-5°C, 55°C].")
        else:
            passed.append("TEMPERATURE_RANGE_VALID")

    # Thermodynamic Consistency: T_min <= T_mean <= T_max
    if {"temperature_min", "temperature_mean", "temperature_max"}.issubset(df.columns):
        t_sub = df[["temperature_min", "temperature_mean", "temperature_max"]].dropna()
        incons = int(((t_sub["temperature_min"] > t_sub["temperature_mean"] + 1e-4) |
                      (t_sub["temperature_mean"] > t_sub["temperature_max"] + 1e-4)).sum())
        if incons > 0:
            failed.append(f"THERMODYNAMIC_INCONSISTENCY: {incons} rows violate T_min <= T_mean <= T_max.")
        else:
            passed.append("THERMODYNAMIC_CONSISTENCY_PASS")

    # Relative Humidity Bounds
    if "humidity_mean" in df.columns:
        rh = df["humidity_mean"].dropna()
        viol = int(((rh < PHYSICAL_BOUNDS["humidity_min_pct"]) | (rh > PHYSICAL_BOUNDS["humidity_max_pct"])).sum())
        if viol > 0:
            failed.append(f"HUMIDITY_BOUNDS_VIOLATION: {viol} rows outside [0%, 100%].")
        else:
            passed.append("HUMIDITY_RANGE_VALID")

    # Rainfall Non-Negativity & Extremes
    if "rainfall_mm" in df.columns:
        rain = df["rainfall_mm"].dropna()
        viol = int(((rain < 0.0) | (rain > PHYSICAL_BOUNDS["rainfall_daily_max_mm"])).sum())
        if viol > 0:
            failed.append(f"RAINFALL_BOUNDS_VIOLATION: {viol} rows outside [0, 1000 mm].")
        else:
            passed.append("RAINFALL_RANGE_VALID")

    # Soil Moisture Volumetric Bounds
    if "soil_moisture_era5_m3m3" in df.columns:
        sm = df["soil_moisture_era5_m3m3"].dropna()
        viol = int(((sm < 0.0) | (sm > PHYSICAL_BOUNDS["soil_moisture_max_m3m3"])).sum())
        if viol > 0:
            failed.append(f"SOIL_MOISTURE_BOUNDS_VIOLATION: {viol} rows outside [0.0, 0.75 m3/m3].")
        else:
            passed.append("SOIL_MOISTURE_RANGE_VALID")

    is_valid = len(failed) == 0
    return ValidationReport(
        total_records=total,
        is_valid=is_valid,
        passed_checks=passed,
        failed_checks=failed,
        warnings=warnings,
        null_counts=null_counts,
        duplicate_count=dups,
        temporal_gap_days=temporal_gaps,
        details={"validated_at": datetime.now(timezone.utc).isoformat()},
    )

