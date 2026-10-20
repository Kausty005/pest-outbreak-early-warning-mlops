"""
src/models/maize_outbreak_forecasting/feature_engineering.py
────────────────────────────────────────────────────────────
Causal, leakage-safe feature engineering for 7-day maize disease outbreak forecasting.
Extracts agronomic, epidemiological, and meteorological features strictly prior to t0.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Sequence
import numpy as np
import pandas as pd

from .schemas import (
    DailyAgroclimaticRecord,
    FieldSurveillanceObservation,
    ForecastingFeatureRecord,
    MaizeGrowthStage,
    TargetDisease,
)


class AgroclimaticDiseaseIndices:
    """
    Bio-climatic models for maize common rust (Puccinia sorghi) spore germination & pustule eruption.
    Biophysical constraints:
      - Optimal germination temperature: 16°C – 25°C
      - Extreme temperature inhibition: < 8°C or > 32°C (urediniospores inactivated)
      - Moisture requirement: Relative humidity > 80% or continuous free moisture for >= 6 hours
    """

    @staticmethod
    def calculate_rust_thermal_favorability(temp_c: float) -> float:
        """Normalized thermal favorability factor [0, 1] for Puccinia sorghi."""
        if temp_c < 10.0 or temp_c > 32.0:
            return 0.0
        elif 16.0 <= temp_c <= 25.0:
            return 1.0
        elif 10.0 <= temp_c < 16.0:
            return (temp_c - 10.0) / 6.0
        else:
            return (32.0 - temp_c) / 7.0

    @staticmethod
    def calculate_dew_hours_estimate(rh_mean: float, rh_morning: float, rainfall_mm: float) -> float:
        """Estimate leaf wetness / dew duration hours from daily weather summaries."""
        hours = 0.0
        if rainfall_mm > 0.0:
            hours += min(12.0, 4.0 + rainfall_mm * 0.5)
        if rh_morning >= 85.0:
            hours += 4.0 + (rh_morning - 85.0) * 0.4
        elif rh_mean >= 80.0:
            hours += 3.0 + (rh_mean - 80.0) * 0.3
        return min(24.0, max(0.0, hours))


class TemporalFeatureEngineer:
    """
    Transforms time-series weather and scouting history into leakage-free tabular features.
    Strictly verifies that no information from after t0 is included.
    """

    FEATURE_NAMES = [
        "t7_mean_temp_c",
        "t7_min_temp_c",
        "t7_max_temp_c",
        "t7_temp_favorable_rust_hours_est",
        "t7_mean_rh_pct",
        "t7_high_rh_days",
        "t7_cumulative_rainfall_mm",
        "t7_rainy_days_count",
        "t7_estimated_leaf_wetness_hours_sum",
        "t14_cumulative_rainfall_mm",
        "growth_stage_vulnerability_index",
        "current_incidence_at_t0",
        "current_severity_at_t0",
        "disease_already_present_t0",
        "regional_outbreak_pressure_last_14d",
        "has_cnn_image_feature",
        "cnn_observed_leaf_rust_probability_t0",
    ]

    # Vulnerability score per growth stage (0.1 = resistant seedling, 1.0 = peak vulnerable silking/grain filling)
    STAGE_WEIGHTS: dict[MaizeGrowthStage, float] = {
        MaizeGrowthStage.EMERGENCE_VE: 0.15,
        MaizeGrowthStage.EARLY_WHORL_V1_V4: 0.30,
        MaizeGrowthStage.MID_WHORL_V5_V8: 0.65,
        MaizeGrowthStage.LATE_WHORL_V9_VT: 0.85,
        MaizeGrowthStage.SILKING_R1: 1.00,
        MaizeGrowthStage.BLISTER_R2: 0.90,
        MaizeGrowthStage.MILK_R3: 0.75,
        MaizeGrowthStage.DOUGH_R4: 0.50,
        MaizeGrowthStage.DENT_R5: 0.30,
        MaizeGrowthStage.MATURITY_R6: 0.10,
    }

    def extract_features(
        self,
        t0_obs: FieldSurveillanceObservation,
        weather_records: Sequence[DailyAgroclimaticRecord],
        regional_observations: Sequence[FieldSurveillanceObservation] | None = None,
        cnn_leaf_prob_t0: float | None = None,
    ) -> ForecastingFeatureRecord:
        """
        Build a single feature record for field at date t0.
        All inputs are filtered to <= t0.
        """
        ref_date = t0_obs.observation_date
        t7_start = ref_date - timedelta(days=6)
        t14_start = ref_date - timedelta(days=13)

        # Filter field weather strictly in past windows [t0-6d, t0] and [t0-13d, t0]
        w_past = [
            w for w in weather_records
            if w.field_id == t0_obs.field_id and w.date <= ref_date
        ]

        w_7d = [w for w in w_past if w.date >= t7_start]
        w_14d = [w for w in w_past if w.date >= t14_start]

        if not w_7d:
            raise ValueError(
                f"Cannot build features for field '{t0_obs.field_id}' on {ref_date}: "
                f"Missing weather observations in recent 7-day window ({t7_start} to {ref_date})."
            )

        # 7-day weather aggregates
        t7_mean_temp = float(np.mean([w.temp_mean_c for w in w_7d]))
        t7_min_temp = float(np.min([w.temp_min_c for w in w_7d]))
        t7_max_temp = float(np.max([w.temp_max_c for w in w_7d]))
        t7_mean_rh = float(np.mean([w.rh_mean_pct for w in w_7d]))
        t7_high_rh_days = sum(1 for w in w_7d if w.rh_mean_pct >= 80.0 or w.rh_morning_pct >= 85.0)
        t7_cum_rain = float(np.sum([w.rainfall_mm for w in w_7d]))
        t7_rainy_days = sum(1 for w in w_7d if w.rainfall_mm >= 1.0)

        # Daily favorable rust hours estimation
        favorable_hours_list = []
        wetness_hours_list = []
        for w in w_7d:
            tf = AgroclimaticDiseaseIndices.calculate_rust_thermal_favorability(w.temp_mean_c)
            # Estimate daily hours in favorable band
            favorable_hours = tf * 14.0
            favorable_hours_list.append(favorable_hours)

            if w.leaf_wetness_hours is not None:
                wetness_hours_list.append(w.leaf_wetness_hours)
            else:
                wetness_hours_list.append(
                    AgroclimaticDiseaseIndices.calculate_dew_hours_estimate(
                        w.rh_mean_pct, w.rh_morning_pct, w.rainfall_mm
                    )
                )

        t7_favorable_rust_hours_est = float(np.mean(favorable_hours_list))
        t7_leaf_wetness_sum = float(np.sum(wetness_hours_list))

        # 14-day cumulative rainfall
        t14_cum_rain = float(np.sum([w.rainfall_mm for w in w_14d])) if w_14d else t7_cum_rain

        # Regional outbreak pressure (proportion of nearby fields with active outbreaks in past 14 days)
        reg_pressure = 0.0
        if regional_observations:
            reg_past = [
                ro for ro in regional_observations
                if ro.field_id != t0_obs.field_id
                and ro.district == t0_obs.district
                and t14_start <= ro.observation_date <= ref_date
            ]
            if reg_past:
                outbreak_count = sum(1 for ro in reg_past if ro.severity_pct >= 5.0)
                reg_pressure = float(outbreak_count / len(reg_past))

        # Stage vulnerability
        growth_stage_str = t0_obs.growth_stage.value if hasattr(t0_obs.growth_stage, "value") else str(t0_obs.growth_stage)

        return ForecastingFeatureRecord(
            field_id=t0_obs.field_id,
            reference_date=ref_date,
            target_disease=t0_obs.target_disease.value if hasattr(t0_obs.target_disease, "value") else str(t0_obs.target_disease),
            growth_stage=growth_stage_str,
            t7_mean_temp_c=round(t7_mean_temp, 2),
            t7_min_temp_c=round(t7_min_temp, 2),
            t7_max_temp_c=round(t7_max_temp, 2),
            t7_temp_favorable_rust_hours_est=round(t7_favorable_rust_hours_est, 2),
            t7_mean_rh_pct=round(t7_mean_rh, 2),
            t7_high_rh_days=t7_high_rh_days,
            t7_cumulative_rainfall_mm=round(t7_cum_rain, 2),
            t7_rainy_days_count=t7_rainy_days,
            t7_estimated_leaf_wetness_hours_sum=round(t7_leaf_wetness_sum, 2),
            t14_cumulative_rainfall_mm=round(t14_cum_rain, 2),
            current_incidence_at_t0=round(t0_obs.incidence_pct, 2),
            current_severity_at_t0=round(t0_obs.severity_pct, 2),
            disease_already_present_t0=1 if t0_obs.incidence_pct > 0.0 else 0,
            regional_outbreak_pressure_last_14d=round(reg_pressure, 3),
            cnn_observed_leaf_rust_probability_t0=round(cnn_leaf_prob_t0, 4) if cnn_leaf_prob_t0 is not None else None,
        )

    def to_model_matrix(self, records: Sequence[ForecastingFeatureRecord]) -> pd.DataFrame:
        """Convert a list of feature records to a numerical ML feature matrix."""
        rows = []
        for r in records:
            # Map stage to vulnerability index
            try:
                stage_enum = MaizeGrowthStage(r.growth_stage)
                v_idx = self.STAGE_WEIGHTS.get(stage_enum, 0.5)
            except Exception:
                v_idx = 0.5

            rows.append({
                "t7_mean_temp_c": r.t7_mean_temp_c,
                "t7_min_temp_c": r.t7_min_temp_c,
                "t7_max_temp_c": r.t7_max_temp_c,
                "t7_temp_favorable_rust_hours_est": r.t7_temp_favorable_rust_hours_est,
                "t7_mean_rh_pct": r.t7_mean_rh_pct,
                "t7_high_rh_days": r.t7_high_rh_days,
                "t7_cumulative_rainfall_mm": r.t7_cumulative_rainfall_mm,
                "t7_rainy_days_count": r.t7_rainy_days_count,
                "t7_estimated_leaf_wetness_hours_sum": r.t7_estimated_leaf_wetness_hours_sum,
                "t14_cumulative_rainfall_mm": r.t14_cumulative_rainfall_mm,
                "growth_stage_vulnerability_index": v_idx,
                "current_incidence_at_t0": r.current_incidence_at_t0,
                "current_severity_at_t0": r.current_severity_at_t0,
                "disease_already_present_t0": r.disease_already_present_t0,
                "regional_outbreak_pressure_last_14d": r.regional_outbreak_pressure_last_14d,
                "has_cnn_image_feature": 1 if r.cnn_observed_leaf_rust_probability_t0 is not None else 0,
                "cnn_observed_leaf_rust_probability_t0": r.cnn_observed_leaf_rust_probability_t0 or 0.0,
            })
        return pd.DataFrame(rows)
