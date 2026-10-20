"""
src/data/generate_synthetic_pest_data.py
────────────────────────────────────────
AgriAdapt AI: High-fidelity synthetic dataset generator for 7-day multi-crop pest outbreak forecasting.
Simulates longitudinal field trajectories across 3 growing seasons (2022-2024),
enforcing strict temporal causality, biological pest dynamics, and exact 100,000 row output.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

RANDOM_SEED = 42
TARGET_ROW_COUNT = 100_000


@dataclass(frozen=True)
class PestBiologyProfile:
    crop: str
    pest: str
    districts: tuple[str, ...]
    season_type: str  # "kharif", "rabi", "summer"
    base_start_month: int
    base_start_day: int
    cycle_days: int
    temp_opt_min: float
    temp_opt_max: float
    temp_base_mean: float
    temp_diurnal_range: float
    rh_mean_target: float
    rh_std_target: float
    monsoon_rain_prob: float
    etl_severity_pct: float
    etl_incidence_pct: float
    growth_stages: tuple[str, ...]
    stage_durations_pct: tuple[float, ...]
    stage_vulnerability_weights: tuple[float, ...]


PEST_PROFILES: list[PestBiologyProfile] = [
    # 1. Maize — Fall armyworm
    PestBiologyProfile(
        crop="Maize",
        pest="Fall armyworm",
        districts=("Davanagere", "Chhindwara", "Belagavi", "Karimnagar"),
        season_type="kharif",
        base_start_month=6,
        base_start_day=15,
        cycle_days=105,
        temp_opt_min=24.0,
        temp_opt_max=32.0,
        temp_base_mean=27.5,
        temp_diurnal_range=8.5,
        rh_mean_target=74.0,
        rh_std_target=8.0,
        monsoon_rain_prob=0.35,
        etl_severity_pct=10.0,
        etl_incidence_pct=12.0,
        growth_stages=(
            "VE_emergence",
            "V1_V4_early_whorl",
            "V5_V8_mid_whorl",
            "V9_VT_late_whorl",
            "R1_silking",
            "R2_R4_grain_fill",
            "R5_R6_maturity",
        ),
        stage_durations_pct=(0.08, 0.15, 0.22, 0.20, 0.12, 0.15, 0.08),
        stage_vulnerability_weights=(0.30, 0.70, 0.95, 0.85, 0.60, 0.35, 0.10),
    ),
    # 2. Rice — Brown planthopper
    PestBiologyProfile(
        crop="Rice",
        pest="Brown planthopper",
        districts=("East Godavari", "Thanjavur", "Cuttack", "Burdwan"),
        season_type="kharif",
        base_start_month=7,
        base_start_day=1,
        cycle_days=115,
        temp_opt_min=25.0,
        temp_opt_max=31.0,
        temp_base_mean=28.5,
        temp_diurnal_range=6.5,
        rh_mean_target=82.0,
        rh_std_target=7.0,
        monsoon_rain_prob=0.45,
        etl_severity_pct=12.0,
        etl_incidence_pct=15.0,
        growth_stages=(
            "Seedling_transplanting",
            "Active_tillering",
            "Panicle_initiation",
            "Booting_heading",
            "Milky_dough",
            "Ripening_maturity",
        ),
        stage_durations_pct=(0.12, 0.25, 0.22, 0.18, 0.15, 0.08),
        stage_vulnerability_weights=(0.20, 0.85, 1.00, 0.90, 0.50, 0.15),
    ),
    # 3. Cotton — Pink bollworm
    PestBiologyProfile(
        crop="Cotton",
        pest="Pink bollworm",
        districts=("Nagpur", "Amravati", "Yavatmal", "Adilabad"),
        season_type="kharif",
        base_start_month=6,
        base_start_day=20,
        cycle_days=130,
        temp_opt_min=25.0,
        temp_opt_max=33.0,
        temp_base_mean=29.0,
        temp_diurnal_range=9.0,
        rh_mean_target=68.0,
        rh_std_target=9.0,
        monsoon_rain_prob=0.30,
        etl_severity_pct=10.0,
        etl_incidence_pct=10.0,
        growth_stages=(
            "Vegetative",
            "Squaring_bud",
            "Flowering",
            "Boll_formation",
            "Boll_maturation",
            "Bursting_picking",
        ),
        stage_durations_pct=(0.15, 0.20, 0.22, 0.23, 0.12, 0.08),
        stage_vulnerability_weights=(0.15, 0.65, 0.90, 1.00, 0.70, 0.20),
    ),
    # 4. Wheat — Aphids
    PestBiologyProfile(
        crop="Wheat",
        pest="Aphids",
        districts=("Ludhiana", "Karnal", "Indore", "Meerut"),
        season_type="rabi",
        base_start_month=11,
        base_start_day=10,
        cycle_days=110,
        temp_opt_min=13.0,
        temp_opt_max=22.0,
        temp_base_mean=17.0,
        temp_diurnal_range=11.0,
        rh_mean_target=72.0,
        rh_std_target=8.0,
        monsoon_rain_prob=0.08,
        etl_severity_pct=10.0,
        etl_incidence_pct=15.0,
        growth_stages=(
            "Crown_root_initiation",
            "Tillering",
            "Jointing_stem_extension",
            "Booting_heading",
            "Milky_grain",
            "Dough_maturity",
        ),
        stage_durations_pct=(0.12, 0.20, 0.22, 0.20, 0.16, 0.10),
        stage_vulnerability_weights=(0.20, 0.50, 0.85, 0.95, 0.75, 0.15),
    ),
    # 5. Tomato — Fruit borer
    PestBiologyProfile(
        crop="Tomato",
        pest="Fruit borer",
        districts=("Kolar", "Nashik", "Chittoor", "Pune"),
        season_type="rabi",
        base_start_month=10,
        base_start_day=15,
        cycle_days=100,
        temp_opt_min=21.0,
        temp_opt_max=29.0,
        temp_base_mean=24.5,
        temp_diurnal_range=10.0,
        rh_mean_target=65.0,
        rh_std_target=8.5,
        monsoon_rain_prob=0.15,
        etl_severity_pct=8.0,
        etl_incidence_pct=10.0,
        growth_stages=(
            "Transplanting_establishment",
            "Vegetative_branching",
            "Flowering",
            "Fruit_setting",
            "Fruit_development",
            "Harvest_ripening",
        ),
        stage_durations_pct=(0.10, 0.18, 0.22, 0.24, 0.16, 0.10),
        stage_vulnerability_weights=(0.15, 0.35, 0.75, 1.00, 0.85, 0.30),
    ),
    # 6. Chickpea — Pod borer
    PestBiologyProfile(
        crop="Chickpea",
        pest="Pod borer",
        districts=("Kalaburagi", "Akola", "Vidisha", "Dharwad"),
        season_type="rabi",
        base_start_month=10,
        base_start_day=25,
        cycle_days=100,
        temp_opt_min=18.0,
        temp_opt_max=28.0,
        temp_base_mean=23.0,
        temp_diurnal_range=12.0,
        rh_mean_target=58.0,
        rh_std_target=8.0,
        monsoon_rain_prob=0.06,
        etl_severity_pct=8.0,
        etl_incidence_pct=10.0,
        growth_stages=(
            "Seedling",
            "Vegetative_branching",
            "Flowering",
            "Early_pod_formation",
            "Pod_filling",
            "Maturity_senescence",
        ),
        stage_durations_pct=(0.12, 0.20, 0.22, 0.22, 0.16, 0.08),
        stage_vulnerability_weights=(0.10, 0.30, 0.70, 1.00, 0.80, 0.15),
    ),
]


def assign_growth_stage(day_idx: int, total_days: int, profile: PestBiologyProfile) -> str:
    """Determine crop growth stage on day_idx based on cumulative duration percentages."""
    fraction = day_idx / max(total_days, 1)
    cum = 0.0
    for stage, dur in zip(profile.growth_stages, profile.stage_durations_pct):
        cum += dur
        if fraction <= cum:
            return stage
    return profile.growth_stages[-1]


def get_stage_vulnerability(stage: str, profile: PestBiologyProfile) -> float:
    """Get the biological susceptibility weight for the given growth stage."""
    for s, w in zip(profile.growth_stages, profile.stage_vulnerability_weights):
        if s == stage:
            return w
    return 0.5


def simulate_field_season(
    field_id: str,
    district: str,
    profile: PestBiologyProfile,
    season_year: int,
    start_date: date,
    cycle_days: int,
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """
    Simulate daily longitudinal trajectory for a single field over one full season.
    Includes 14 days of burn-in and 7 days forward buffer.
    Returns:
        - daily_df: Full un-truncated daily timeline with raw weather, incidence, and severity.
        - valid_records: Feature records for days t0 where full past (14d) and future (7d) exist.
    """
    total_days = cycle_days + 14 + 7  # 14d burn-in + cycle_days + 7d future buffer

    # Baseline field-level management/microclimate offset
    field_pest_affinity = float(rng.normal(0.0, 0.25))
    field_temp_offset = float(rng.normal(0.0, 0.8))
    field_rh_offset = float(rng.normal(0.0, 2.5))

    # Pre-generate daily weather series
    temps_mean = np.zeros(total_days)
    temps_min = np.zeros(total_days)
    temps_max = np.zeros(total_days)
    rhs_mean = np.zeros(total_days)
    rainfalls = np.zeros(total_days)
    dates = []

    # Seasonal sinusoidal temperature trend
    curr_temp = profile.temp_base_mean + field_temp_offset
    curr_rh = profile.rh_mean_target + field_rh_offset

    for day in range(total_days):
        dates.append(start_date + timedelta(days=day))

        # AR(1) temperature with seasonal gentle drift
        drift = 2.0 * np.sin(2.0 * np.pi * day / total_days)
        curr_temp = 0.80 * curr_temp + 0.20 * (profile.temp_base_mean + field_temp_offset + drift) + rng.normal(0.0, 0.9)
        diurnal = profile.temp_diurnal_range + rng.normal(0.0, 1.0)
        diurnal = max(4.0, diurnal)

        t_min = curr_temp - (diurnal / 2.0)
        t_max = curr_temp + (diurnal / 2.0)
        temps_mean[day] = round(float(curr_temp), 1)
        temps_min[day] = round(float(t_min), 1)
        temps_max[day] = round(float(t_max), 1)

        # Rainfall: Markovian precipitation spells
        rain_prob = profile.monsoon_rain_prob if day < (total_days * 0.7) else profile.monsoon_rain_prob * 0.4
        if rng.random() < rain_prob:
            rain = float(rng.gamma(shape=2.0, scale=8.0))
            rainfalls[day] = round(min(150.0, max(0.5, rain)), 1)
        else:
            rainfalls[day] = 0.0

        # Humidity correlated with rain and temperature
        rh_boost = 12.0 if rainfalls[day] > 0 else -1.5
        curr_rh = 0.75 * curr_rh + 0.25 * (profile.rh_mean_target + field_rh_offset + rh_boost) + rng.normal(0.0, 2.0)
        rhs_mean[day] = round(float(np.clip(curr_rh, 25.0, 98.0)), 1)

    # Simulate Daily Pest Population Dynamics
    incidence_series = np.zeros(total_days)
    severity_series = np.zeros(total_days)
    stages = []

    # Field baseline susceptibility: ~42% of fields experience conditions leading to a potential outbreak window
    field_vulnerable = (rng.random() < 0.42)
    outbreak_days_left = 0
    latent_pressure = 0.0

    for day in range(total_days):
        stage = assign_growth_stage(day, total_days, profile)
        stages.append(stage)
        stage_vuln = get_stage_vulnerability(stage, profile)

        # Weather favorability score [0, 1]
        t_mean = temps_mean[day]
        if profile.temp_opt_min <= t_mean <= profile.temp_opt_max:
            temp_fav = 1.0
        elif abs(t_mean - profile.temp_opt_min) < 3.5 or abs(t_mean - profile.temp_opt_max) < 3.5:
            temp_fav = 0.55
        else:
            temp_fav = 0.15

        rh = rhs_mean[day]
        rh_fav = 1.0 if rh >= 65.0 else max(0.2, rh / 65.0)
        weather_fav = temp_fav * rh_fav

        # Heavy rainfall washes off aphids or young larvae
        if profile.pest == "Aphids" and rainfalls[day] > 15.0:
            weather_fav *= 0.35

        frac = day / total_days
        # Outbreak initiation: during vulnerable stages (mid to late season) when weather is conducive
        if field_vulnerable and outbreak_days_left <= 0 and 0.25 <= frac <= 0.72:
            if weather_fav > 0.55 and stage_vuln >= 0.65 and rng.random() < 0.09:
                outbreak_days_left = int(rng.integers(12, 20))
                latent_pressure = max(latent_pressure, float(rng.uniform(3.5, 6.0)))

        if outbreak_days_left > 0:
            outbreak_days_left -= 1
            latent_pressure = max(2.5, latent_pressure * 0.96 + weather_fav * 0.5)
            if outbreak_days_left == 0:
                latent_pressure *= 0.20  # Knockdown / treatment
        else:
            latent_pressure = max(0.0, latent_pressure * 0.75 + rng.normal(0.0, 0.12))

        # Convert latent pressure to field incidence & severity percentages
        inc = float(np.clip(latent_pressure * 2.2 + rng.normal(0.0, 0.25), 0.0, 85.0))
        sev = float(np.clip(latent_pressure * 1.3 + rng.normal(0.0, 0.15), 0.0, 60.0))

        incidence_series[day] = round(inc, 2)
        severity_series[day] = round(sev, 2)

    # Extract valid records (only for days with complete 14-day history and 7-day future)
    valid_records: list[dict[str, Any]] = []

    # Valid t0 range: index 13 (so days 0..13 exist) to total_days - 8 (so days t0+1..t0+7 exist)
    for t0_idx in range(13, total_days - 7):
        t0_date = dates[t0_idx]

        # 7-day past weather: indices [t0_idx - 6, t0_idx]
        w7_temps_mean = temps_mean[t0_idx - 6 : t0_idx + 1]
        w7_temps_min = temps_min[t0_idx - 6 : t0_idx + 1]
        w7_temps_max = temps_max[t0_idx - 6 : t0_idx + 1]
        w7_rhs = rhs_mean[t0_idx - 6 : t0_idx + 1]
        w7_rain = rainfalls[t0_idx - 6 : t0_idx + 1]

        # 14-day past rainfall: indices [t0_idx - 13, t0_idx]
        w14_rain = rainfalls[t0_idx - 13 : t0_idx + 1]

        t7_mean_temp = float(np.mean(w7_temps_mean))
        t7_min_temp = float(np.min(w7_temps_min))
        t7_max_temp = float(np.max(w7_temps_max))
        t7_mean_rh = float(np.mean(w7_rhs))
        t7_high_rh_days = int(np.sum(w7_rhs >= 80.0))
        t7_rainfall = float(np.sum(w7_rain))
        t14_rainfall = float(np.sum(w14_rain))

        # Current observations strictly at t0
        inc_t0 = float(incidence_series[t0_idx])
        sev_t0 = float(severity_series[t0_idx])
        pest_present = 1 if inc_t0 > 0.5 else 0
        current_stage = stages[t0_idx]

        # GROUND TRUTH TARGET: Look strictly into future window [t0_idx + 1, t0_idx + 7]
        future_inc = incidence_series[t0_idx + 1 : t0_idx + 8]
        future_sev = severity_series[t0_idx + 1 : t0_idx + 8]

        max_future_inc = float(np.max(future_inc))
        max_future_sev = float(np.max(future_sev))
        inc_surge = max_future_inc - inc_t0

        # Outbreak criterion:
        # Crosses economic severity threshold OR economic incidence threshold OR explosive surge of >= 8%
        if (
            max_future_sev >= profile.etl_severity_pct
            or max_future_inc >= profile.etl_incidence_pct
            or inc_surge >= 8.0
        ):
            outbreak_7d = 1
        else:
            outbreak_7d = 0

        valid_records.append({
            "field_id": field_id,
            "district": district,
            "crop": profile.crop,
            "pest": profile.pest,
            "date": str(t0_date),
            "growth_stage": current_stage,
            "t7_mean_temp_c": round(t7_mean_temp, 2),
            "t7_min_temp_c": round(t7_min_temp, 2),
            "t7_max_temp_c": round(t7_max_temp, 2),
            "t7_mean_rh_pct": round(t7_mean_rh, 2),
            "t7_high_rh_days": t7_high_rh_days,
            "t7_rainfall_mm": round(t7_rainfall, 2),
            "t14_rainfall_mm": round(t14_rainfall, 2),
            "current_incidence_pct_t0": round(inc_t0, 2),
            "current_severity_pct_t0": round(sev_t0, 2),
            "pest_present_t0": pest_present,
            "outbreak_within_7d": outbreak_7d,
        })

    return None, valid_records


def generate_multicrop_dataset(
    target_total: int = TARGET_ROW_COUNT,
    seed: int = RANDOM_SEED,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Generate exactly target_total records partitioned across all 6 crop-pest pairs.
    """
    rng = np.random.default_rng(seed)

    num_crops = len(PEST_PROFILES)
    base_per_crop = target_total // num_crops
    remainder = target_total % num_crops

    # Crop target quotas (e.g. 16667 for 4 crops, 16666 for 2 crops)
    crop_quotas = [base_per_crop + (1 if i < remainder else 0) for i in range(num_crops)]

    all_records: list[dict[str, Any]] = []
    crop_stats: dict[str, Any] = {}

    seasons = [2022, 2023, 2024]

    for profile, quota in zip(PEST_PROFILES, crop_quotas):
        crop_records: list[dict[str, Any]] = []
        field_counter = 1

        # Cycle through seasons and districts until quota is fulfilled
        while len(crop_records) < quota:
            for s_year in seasons:
                if len(crop_records) >= quota:
                    break
                district = profile.districts[(field_counter - 1) % len(profile.districts)]
                field_id = f"FLD-{profile.crop[:3].upper()}-{district[:3].upper()}-{field_counter:04d}"

                # Slight planting jitter (+/- 8 days)
                jitter_days = int(rng.integers(-8, 9))
                start_date = date(s_year, profile.base_start_month, profile.base_start_day) + timedelta(days=jitter_days)

                _, records = simulate_field_season(
                    field_id=field_id,
                    district=district,
                    profile=profile,
                    season_year=s_year,
                    start_date=start_date,
                    cycle_days=profile.cycle_days,
                    rng=rng,
                )

                remaining = quota - len(crop_records)
                if len(records) > remaining:
                    crop_records.extend(records[:remaining])
                else:
                    crop_records.extend(records)

                field_counter += 1

        all_records.extend(crop_records)
        c_df = pd.DataFrame(crop_records)
        crop_stats[f"{profile.crop} ({profile.pest})"] = {
            "record_count": len(crop_records),
            "outbreak_count": int(c_df["outbreak_within_7d"].sum()),
            "outbreak_rate_pct": round(float(c_df["outbreak_within_7d"].mean() * 100), 2),
            "districts": list(profile.districts),
            "date_range": [str(c_df["date"].min()), str(c_df["date"].max())],
        }

    # Combine into DataFrame
    df = pd.DataFrame(all_records)

    # Sort strictly chronologically
    df["date_dt"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["date_dt", "crop", "field_id"]).reset_index(drop=True)
    df = df.drop(columns=["date_dt"])

    # Strict assertion
    if len(df) != target_total:
        raise ValueError(f"Expected exactly {target_total} rows, but got {len(df)}")

    metadata = {
        "random_seed": seed,
        "total_records": len(df),
        "crops_count": num_crops,
        "seasons_simulated": seasons,
        "overall_outbreak_count": int(df["outbreak_within_7d"].sum()),
        "overall_outbreak_rate_pct": round(float(df["outbreak_within_7d"].mean() * 100), 2),
        "columns": list(df.columns),
        "per_crop_breakdown": crop_stats,
    }

    return df, metadata
