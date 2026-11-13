"""
src/pest_forecasting/synthetic_generator_v2.py
─────────────────────────────────────────────
Biophysical and epidemiological synthetic data generator (Version 2.0)
for multicrop pest outbreak early warning experimentation.

Key Improvements over v1:
1. Latent Population State (L_t): Continuous population dynamics driven by
   species-specific thermal, moisture, and host-phenological differential growth.
2. Intermittent & Noisy Observation Process: Scouting occurs at realistic 7-14 day
   intervals. Between visits, only the last known observation is available, tracked
   by `days_since_scouting`.
3. Target Generation Integrity: Target `outbreak_within_7d` is determined by the
   future latent population trajectory L_{t0+1..t0+7} exceeding biological ETLs,
   breaking trivial synchronous correlation with current scouting metrics.
4. Soil Moisture Hydrology: Integrated daily water balance with evaporation and drainage.
5. Strict Temporal Ordering and Field Tracking: Preserves temporal causality,
   autocorrelation, and seasonal agronomic calendars.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

LOGGER = logging.getLogger(__name__)

# Core Maharashtra / Central India Districts
DISTRICTS = [
    "Nagpur",
    "Amravati",
    "Yavatmal",
    "Jalgaon",
    "Akola",
    "Wardha",
    "Buldhana",
    "Washim",
]

# Pest & Crop Biological Profiles
# References: Fand et al. (2021) Crop Protection; ICAR-CICR Crop Protocols; CABI Compendium
BIOLOGICAL_PROFILES = {
    "Cotton": {
        "pest": "Pink bollworm",
        "scientific_name": "Pectinophora gossypiella",
        "t_base": 12.0,
        "t_opt": 28.0,
        "t_max": 38.0,
        "rh_opt_min": 60.0,
        "rh_opt_max": 85.0,
        "stages": ["Vegetative", "Squaring", "Flowering", "Boll Development", "Maturity"],
        "stage_susceptibility": [0.15, 0.45, 0.85, 1.00, 0.30],
        "sowing_month_start": 6,
        "growth_days": 160,
        "latent_etl": 4.5,
        "trap_efficiency": 2.2,
    },
    "Soybean": {
        "pest": "Tobacco caterpillar",
        "scientific_name": "Spodoptera litura",
        "t_base": 10.5,
        "t_opt": 28.5,
        "t_max": 35.5,
        "rh_opt_min": 70.0,
        "rh_opt_max": 95.0,
        "stages": ["Germination", "Vegetative", "Flowering", "Pod Formation", "Maturity"],
        "stage_susceptibility": [0.10, 0.60, 0.90, 1.00, 0.20],
        "sowing_month_start": 6,
        "growth_days": 105,
        "latent_etl": 4.2,
        "trap_efficiency": 2.5,
    },
    "Maize": {
        "pest": "Fall armyworm",
        "scientific_name": "Spodoptera frugiperda",
        "t_base": 10.0,
        "t_opt": 27.5,
        "t_max": 36.0,
        "rh_opt_min": 55.0,
        "rh_opt_max": 85.0,
        "stages": ["Seedling", "Early Whorl", "Late Whorl", "Tasseling", "Silking", "Maturity"],
        "stage_susceptibility": [0.70, 1.00, 0.85, 0.50, 0.40, 0.15],
        "sowing_month_start": 6,
        "growth_days": 115,
        "latent_etl": 4.0,
        "trap_efficiency": 2.8,
    },
    "Rice": {
        "pest": "Brown planthopper",
        "scientific_name": "Nilaparvata lugens",
        "t_base": 11.5,
        "t_opt": 26.5,
        "t_max": 32.5,
        "rh_opt_min": 75.0,
        "rh_opt_max": 98.0,
        "stages": ["Seedling", "Tillering", "Stem Elongation", "Booting", "Ripening"],
        "stage_susceptibility": [0.20, 0.80, 1.00, 0.90, 0.25],
        "sowing_month_start": 6,
        "growth_days": 130,
        "latent_etl": 4.6,
        "trap_efficiency": 1.8,
    },
    "Chickpea": {
        "pest": "Pod borer",
        "scientific_name": "Helicoverpa armigera",
        "t_base": 10.0,
        "t_opt": 23.5,
        "t_max": 32.0,
        "rh_opt_min": 45.0,
        "rh_opt_max": 75.0,
        "stages": ["Vegetative", "Branching", "Flowering", "Pod Development", "Maturity"],
        "stage_susceptibility": [0.20, 0.40, 0.85, 1.00, 0.25],
        "sowing_month_start": 10,
        "growth_days": 120,
        "latent_etl": 4.1,
        "trap_efficiency": 2.4,
    },
    "Tomato": {
        "pest": "Fruit borer",
        "scientific_name": "Helicoverpa armigera",
        "t_base": 10.0,
        "t_opt": 25.0,
        "t_max": 34.0,
        "rh_opt_min": 50.0,
        "rh_opt_max": 80.0,
        "stages": ["Vegetative", "Flowering", "Fruit Formation", "Ripening"],
        "stage_susceptibility": [0.25, 0.75, 1.00, 0.60],
        "sowing_month_start": 7,
        "growth_days": 135,
        "latent_etl": 3.8,
        "trap_efficiency": 2.3,
    },
}


def simulate_district_weather_series(
    district: str,
    dates: pd.DatetimeIndex,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    Simulate physically plausible continuous daily weather for a district
    with realistic seasonal cycles, AR(1) autocorrelation, and soil moisture hydrology.
    """
    n_days = len(dates)
    doy = dates.dayofyear.values

    # Base seasonal temperature (Vidarbha climate: peak heat in May, cool in Dec-Jan)
    t_season = 28.0 + 7.5 * np.sin(2 * np.pi * (doy - 105) / 365.25)
    
    # AR(1) thermal fluctuation
    t_noise = np.zeros(n_days)
    for i in range(1, n_days):
        t_noise[i] = 0.78 * t_noise[i - 1] + rng.normal(0, 1.4)
    t_mean = np.clip(t_season + t_noise, 12.0, 44.0)
    
    # Diurnal range
    diurnal_range = 8.0 + 4.0 * np.cos(2 * np.pi * (doy - 105) / 365.25) + rng.normal(0, 1.0, n_days)
    diurnal_range = np.clip(diurnal_range, 5.0, 16.0)
    t_min = t_mean - diurnal_range * 0.45
    t_max = t_mean + diurnal_range * 0.55

    # Monsoon rainfall simulation (Markov chain: dry -> rain, rain -> rain)
    is_monsoon = (doy >= 160) & (doy <= 275)
    
    rain = np.zeros(n_days)
    in_rain_state = False
    for i in range(n_days):
        if is_monsoon[i]:
            p_start = 0.32
            p_cont = 0.58
        else:
            p_start = 0.04
            p_cont = 0.20
            
        if in_rain_state:
            in_rain_state = rng.random() < p_cont
        else:
            in_rain_state = rng.random() < p_start
            
        if in_rain_state:
            rain[i] = rng.exponential(scale=18.0 if is_monsoon[i] else 6.0)
            if rain[i] < 0.5:
                rain[i] = 0.0
                in_rain_state = False
        else:
            rain[i] = 0.0

    # Relative humidity
    base_rh = 60.0 - 15.0 * np.sin(2 * np.pi * (doy - 105) / 365.25)
    base_rh[is_monsoon] += 22.0
    rh_noise = np.zeros(n_days)
    for i in range(1, n_days):
        rh_noise[i] = 0.70 * rh_noise[i - 1] + rng.normal(0, 3.5)
    rh_mean = base_rh + rh_noise + np.clip(rain * 1.2, 0, 25)
    rh_mean = np.clip(rh_mean, 28.0, 98.0)

    # Soil moisture dynamics (m3/m3, bounded [0.10, 0.45])
    soil_moisture = np.zeros(n_days)
    soil_moisture[0] = 0.22
    for i in range(1, n_days):
        inflow = min(0.15, rain[i] * 0.004)
        evap = 0.008 * (t_mean[i] / 30.0) * (1.0 - rh_mean[i] / 120.0)
        soil_moisture[i] = np.clip(soil_moisture[i - 1] + inflow - evap, 0.11, 0.44)

    return pd.DataFrame({
        "date": dates,
        "district": district,
        "t_mean": np.round(t_mean, 2),
        "t_min": np.round(t_min, 2),
        "t_max": np.round(t_max, 2),
        "rh_mean": np.round(rh_mean, 2),
        "rainfall_mm": np.round(rain, 1),
        "soil_moisture": np.round(soil_moisture, 3),
    })


def compute_suitability_arrays(
    t_means: np.ndarray,
    rh_means: np.ndarray,
    t_base: float,
    t_opt: float,
    t_max: float,
    rh_min: float,
    rh_max: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized calculation of thermal and humidity suitability factors."""
    # Thermal response
    t_suit = np.zeros_like(t_means)
    mask_low = (t_means > t_base) & (t_means <= t_opt)
    mask_high = (t_means > t_opt) & (t_means < t_max)
    t_suit[mask_low] = ((t_means[mask_low] - t_base) / (t_opt - t_base)) ** 1.5
    t_suit[mask_high] = np.maximum(0.0, 1.0 - ((t_means[mask_high] - t_opt) / (t_max - t_opt)) ** 1.8)

    # Humidity response
    rh_suit = np.full_like(rh_means, 0.1)
    mask_opt = (rh_means >= rh_min) & (rh_means <= rh_max)
    mask_mid = (rh_means >= (rh_min - 15.0)) & (rh_means < rh_min)
    mask_high_rh = rh_means > rh_max
    rh_suit[mask_opt] = 1.0
    rh_suit[mask_mid] = 0.1 + 0.9 * ((rh_means[mask_mid] - (rh_min - 15.0)) / 15.0)
    rh_suit[mask_high_rh] = np.maximum(0.7, 1.0 - 0.3 * ((rh_means[mask_high_rh] - rh_max) / (100.0 - rh_max + 1e-3)))

    return t_suit, rh_suit


def generate_synthetic_dataset_v2(
    start_date: str = "2023-01-01",
    end_date: str = "2025-12-31",
    num_fields_per_pair: int = 12,
    random_seed: int = 42,
    output_path: str | Path = "data/experimental/synthetic_pest_forecasting_v2.csv",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Generate version 2.0 of the synthetic multi-crop pest forecasting dataset.
    Vectorized and computationally efficient.
    """
    rng = np.random.default_rng(random_seed)
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    n_days = len(dates)

    LOGGER.info("Generating realistic weather time series across %d districts...", len(DISTRICTS))
    district_weather: dict[str, pd.DataFrame] = {}
    for d in DISTRICTS:
        district_weather[d] = simulate_district_weather_series(d, dates, rng)

    field_dfs: list[pd.DataFrame] = []
    field_counter = 1

    target_horizon = 7

    for crop_name, profile in BIOLOGICAL_PROFILES.items():
        pest_name = profile["pest"]
        t_base = profile["t_base"]
        t_opt = profile["t_opt"]
        t_max = profile["t_max"]
        rh_min = profile["rh_opt_min"]
        rh_max = profile["rh_opt_max"]
        stages = profile["stages"]
        stage_susceptibility = profile["stage_susceptibility"]
        growth_days = profile["growth_days"]
        latent_etl = profile["latent_etl"]
        trap_eff = profile["trap_efficiency"]

        for dist in DISTRICTS:
            w_df = district_weather[dist]
            t_means = w_df["t_mean"].values
            t_mins = w_df["t_min"].values
            t_maxs = w_df["t_max"].values
            rh_means = w_df["rh_mean"].values
            rains = w_df["rainfall_mm"].values
            soils = w_df["soil_moisture"].values

            # Precalculate rolling weather features
            t7_mean_temp = pd.Series(t_means).rolling(7, min_periods=1).mean().values
            t7_min_temp = pd.Series(t_mins).rolling(7, min_periods=1).min().values
            t7_max_temp = pd.Series(t_maxs).rolling(7, min_periods=1).max().values
            t7_mean_rh = pd.Series(rh_means).rolling(7, min_periods=1).mean().values
            t7_high_rh_days = (pd.Series(rh_means) >= 80.0).rolling(7, min_periods=1).sum().astype(int).values
            t7_rainfall = pd.Series(rains).rolling(7, min_periods=1).sum().values
            t14_rainfall = pd.Series(rains).rolling(14, min_periods=1).sum().values
            t7_soil = pd.Series(soils).rolling(7, min_periods=1).mean().values
            
            is_dry = (rains < 1.0).astype(int)
            consec_dry = pd.Series(is_dry).rolling(7, min_periods=1).sum().astype(int).values

            # Vectorized suitability factors
            t_suit_arr, rh_suit_arr = compute_suitability_arrays(
                t_means, rh_means, t_base, t_opt, t_max, rh_min, rh_max
            )

            for f_idx in range(num_fields_per_pair):
                field_id = f"FLD-V2-{dist[:3].upper()}-{crop_name[:3].upper()}-{field_counter:04d}"
                field_counter += 1

                # Active crop calendar
                is_active_crop = np.zeros(n_days, dtype=bool)
                growth_stage_day = np.full(n_days, "Fallow", dtype=object)
                susceptibility_arr = np.zeros(n_days)

                for year in range(dates[0].year, dates[-1].year + 1):
                    sow_month = profile["sowing_month_start"]
                    sow_day = 15 + rng.integers(-8, 9)
                    sow_date = pd.Timestamp(year, sow_month, sow_day)
                    harvest_date = sow_date + pd.Timedelta(days=growth_days)

                    mask_cycle = (dates >= sow_date) & (dates <= harvest_date)
                    if mask_cycle.any():
                        cycle_indices = np.where(mask_cycle)[0]
                        is_active_crop[cycle_indices] = True
                        cycle_len = len(cycle_indices)
                        stage_count = len(stages)
                        for c_i, idx in enumerate(cycle_indices):
                            s_idx = min(stage_count - 1, int((c_i / cycle_len) * stage_count))
                            growth_stage_day[idx] = stages[s_idx]
                            susceptibility_arr[idx] = stage_susceptibility[s_idx]

                # Latent population trajectory
                latent_pop = np.zeros(n_days)
                latent_pop[0] = rng.uniform(0.1, 0.4)
                washoff_arr = np.where(rains > 45.0, 0.25, 0.0)

                for t in range(1, n_days):
                    if not is_active_crop[t]:
                        latent_pop[t] = max(0.05, latent_pop[t - 1] * 0.88 + rng.normal(0, 0.01))
                    else:
                        r_growth = 0.35 * t_suit_arr[t] * rh_suit_arr[t] * susceptibility_arr[t] - 0.12 - washoff_arr[t]
                        stoch = rng.normal(0, 0.06)
                        l_next = latent_pop[t - 1] * np.exp(r_growth + stoch)
                        latent_pop[t] = float(np.clip(l_next, 0.02, 12.0))

                # Intermittent scouting simulation
                scout_incidence = np.zeros(n_days)
                scout_severity = np.zeros(n_days)
                trap_catches = np.zeros(n_days)
                days_since_scouting = np.zeros(n_days, dtype=int)

                last_inc = 0.0
                last_sev = 0.0
                last_trap = 0.0
                days_elapsed = rng.integers(0, 7)

                for t in range(n_days):
                    visit_today = (days_elapsed >= 7 and rng.random() < 0.40) or (days_elapsed >= 12)
                    if visit_today and is_active_crop[t]:
                        l_t = latent_pop[t]
                        if l_t < 1.2:
                            last_trap = 0.0 if rng.random() < 0.85 else float(rng.poisson(lam=0.5))
                            last_inc = 0.0 if rng.random() < 0.90 else float(rng.integers(1, 3))
                            last_sev = 0.0 if last_inc == 0.0 else float(rng.uniform(0.1, 0.5))
                        else:
                            # Imperfect detection in field scouting
                            detect_prob = min(0.95, 0.45 + 0.12 * l_t)
                            if rng.random() < detect_prob:
                                true_p = float(np.clip((l_t - 1.0) / 9.0, 0.02, 0.75))
                                last_inc = float(rng.binomial(n=100, p=true_p))
                                last_sev = float(np.clip(last_inc * rng.uniform(0.3, 0.6) + rng.normal(0, 0.4), 0.0, 35.0))
                            else:
                                last_inc = 0.0
                                last_sev = 0.0
                            last_trap = float(rng.poisson(lam=max(0.0, trap_eff * (l_t - 0.8))))
                        days_elapsed = 0
                    else:
                        days_elapsed += 1

                    scout_incidence[t] = last_inc
                    scout_severity[t] = last_sev
                    trap_catches[t] = last_trap
                    days_since_scouting[t] = days_elapsed

                # Vectorized forward 7-day maximum of latent population
                # Rolling 7 backward on reversed series gives forward rolling max
                future_latent_max = (
                    pd.Series(latent_pop)
                    .iloc[::-1]
                    .rolling(target_horizon, min_periods=1)
                    .max()
                    .iloc[::-1]
                    .shift(-1)
                    .values
                )

                # Filter valid rows: active crop and valid forward target
                valid_mask = is_active_crop & (~np.isnan(future_latent_max))
                if not valid_mask.any():
                    continue

                outbreak_labels = (future_latent_max[valid_mask] >= latent_etl).astype(int)
                p_present = ((trap_catches[valid_mask] > 0) | (scout_incidence[valid_mask] > 0)).astype(int)

                f_df = pd.DataFrame({
                    "field_id": field_id,
                    "district": dist,
                    "crop": crop_name,
                    "pest": pest_name,
                    "date": [str(d.date()) for d in dates[valid_mask]],
                    "growth_stage": growth_stage_day[valid_mask],
                    "t7_mean_temp_c": np.round(t7_mean_temp[valid_mask], 2),
                    "t7_min_temp_c": np.round(t7_min_temp[valid_mask], 2),
                    "t7_max_temp_c": np.round(t7_max_temp[valid_mask], 2),
                    "t7_mean_rh_pct": np.round(t7_mean_rh[valid_mask], 2),
                    "t7_high_rh_days": t7_high_rh_days[valid_mask],
                    "t7_rainfall_mm": np.round(t7_rainfall[valid_mask], 1),
                    "t14_rainfall_mm": np.round(t14_rainfall[valid_mask], 1),
                    "t7_mean_soil_moisture": np.round(t7_soil[valid_mask], 3),
                    "t7_consecutive_dry_days": consec_dry[valid_mask],
                    "days_since_scouting": days_since_scouting[valid_mask],
                    "scout_incidence_pct": np.round(scout_incidence[valid_mask], 1),
                    "scout_severity_pct": np.round(scout_severity[valid_mask], 1),
                    "trap_catch_count": np.round(trap_catches[valid_mask], 1),
                    "pest_present": p_present,
                    "outbreak_within_7d": outbreak_labels,
                })
                field_dfs.append(f_df)

    LOGGER.info("Concatenating %d field observation sets...", len(field_dfs))
    df = pd.concat(field_dfs, ignore_index=True)

    # Sort strictly chronologically by date, then field_id
    df["date_dt"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["date_dt", "field_id"]).reset_index(drop=True)
    df = df.drop(columns=["date_dt"])

    # Target exact size: 100,000 records
    target_rows = 100000
    if len(df) > target_rows:
        indices = np.linspace(0, len(df) - 1, target_rows, dtype=int)
        df = df.iloc[indices].reset_index(drop=True)
    elif len(df) < target_rows:
        LOGGER.warning("Generated %d rows, which is less than %d", len(df), target_rows)

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_file, index=False)

    with open(out_file, "rb") as fp:
        sha256_hash = hashlib.sha256(fp.read()).hexdigest()

    metadata = {
        "generator_version": "2.0.0",
        "random_seed": random_seed,
        "record_count": len(df),
        "columns_count": len(df.columns),
        "columns": list(df.columns),
        "target_column": "outbreak_within_7d",
        "sha256_checksum": sha256_hash,
        "date_range": [str(df["date"].min()), str(df["date"].max())],
        "outbreak_prevalence": float(df["outbreak_within_7d"].mean()),
        "outbreak_count": int(df["outbreak_within_7d"].sum()),
        "crops": list(df["crop"].unique()),
        "districts": list(df["district"].unique()),
        "fields_count": int(df["field_id"].nunique()),
    }

    LOGGER.info("Successfully generated %d records at %s (SHA-256: %s)", len(df), out_file, sha256_hash)
    return df, metadata


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df, meta = generate_synthetic_dataset_v2()
    print(json.dumps(meta, indent=2))
