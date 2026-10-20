"""
src/models/maize_outbreak_forecasting/labeling.py
─────────────────────────────────────────────────
Scientifically rigorous ground-truth labeling engine for 7-day disease outbreak prediction.
Implements epidemiological thresholding and prevents temporal label leakage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import Sequence

import pandas as pd

from .schemas import (
    FieldSurveillanceObservation,
    MaizeGrowthStage,
    OutbreakPredictionTarget,
    TargetDisease,
    DiseaseOccurrenceStatus,
)


class OutbreakClassificationType(str, Enum):
    """Categorical classification of field disease transition."""
    NO_OUTBREAK_HEALTHY = "NO_OUTBREAK_HEALTHY"               # Remained healthy / trace
    NO_OUTBREAK_CHRONIC = "NO_OUTBREAK_CHRONIC"               # Existing infection stayed stable without outbreak surge
    NEW_EPIDEMIC_OUTBREAK = "NEW_EPIDEMIC_OUTBREAK"           # Crossed economic threshold from previously manageable state
    EXPLOSIVE_SURGE_OUTBREAK = "EXPLOSIVE_SURGE_OUTBREAK"     # Rapid acceleration (> 10% incidence jump in 7 days)


@dataclass(frozen=True)
class OutbreakThresholdConfig:
    """Agronomic and epidemiological action thresholds for common maize diseases."""
    disease: TargetDisease = TargetDisease.COMMON_RUST

    # Trace detection limit (below this is considered disease-free)
    trace_incidence_threshold_pct: float = 0.5

    # Economic Injury / Action Threshold (severity on leaf area, Cobb scale)
    # ICAR-IIMR & CIMMYT standard: 5% leaf area affected on ear leaf or leaves below ear prior to dent stage
    economic_severity_threshold_pct: float = 5.0

    # Rapid progression threshold (surge in % infected plants in 7 days)
    rapid_incidence_surge_delta_pct: float = 10.0

    # Critical vulnerable growth stages where rust outbreak causes significant yield loss
    vulnerable_stages: tuple[MaizeGrowthStage, ...] = (
        MaizeGrowthStage.MID_WHORL_V5_V8,
        MaizeGrowthStage.LATE_WHORL_V9_VT,
        MaizeGrowthStage.SILKING_R1,
        MaizeGrowthStage.BLISTER_R2,
        MaizeGrowthStage.MILK_R3,
    )


class DiseaseOutbreakLabeler:
    """
    Constructs forward-looking 7-day outbreak labels from longitudinal scouting records.
    Ensures zero temporal label contamination and strict causality.
    """

    def __init__(self, config: OutbreakThresholdConfig | None = None) -> None:
        self.config = config or OutbreakThresholdConfig()

    def determine_status_at_t0(
        self,
        obs: FieldSurveillanceObservation,
    ) -> DiseaseOccurrenceStatus:
        """
        Evaluate disease status strictly on date t0.
        Must distinguish:
          1. Disease absent
          2. Trace / newly detected
          3. Endemic / established
          4. Already active outbreak
        """
        if obs.severity_pct >= self.config.economic_severity_threshold_pct:
            return DiseaseOccurrenceStatus.ACTIVE_OUTBREAK
        elif obs.incidence_pct >= 2.0 or obs.severity_pct >= 1.0:
            return DiseaseOccurrenceStatus.ESTABLISHED_ENDEMIC
        elif obs.incidence_pct >= self.config.trace_incidence_threshold_pct:
            return DiseaseOccurrenceStatus.DETECTED_TRACE
        else:
            return DiseaseOccurrenceStatus.ABSENT

    def generate_7day_outbreak_label(
        self,
        t0_obs: FieldSurveillanceObservation,
        future_observations: Sequence[FieldSurveillanceObservation],
    ) -> OutbreakPredictionTarget:
        """
        Generate 7-day outbreak label for t0_obs by inspecting future window [t0 + 1d, t0 + 7d].

        Outbreak Definition:
        "Will a NEW disease outbreak be observed in this field within the next 7 days?"
        - If the field ALREADY had an uncontrolled outbreak at t0, it CANNOT be labeled as a
          'new outbreak' (label = 0, chronic state), preventing trivial self-correlation.
        - If the field was below threshold at t0 and crosses severity >= 5% in next 7 days, label = 1.
        - If the field exhibits a rapid incidence surge delta >= 10% in next 7 days, label = 1.
        - Otherwise, label = 0.
        """
        ref_date = t0_obs.observation_date
        window_end = ref_date + timedelta(days=7)

        # Filter observations strictly in forward window [t0 + 1, t0 + 7]
        forward_obs = [
            obs for obs in future_observations
            if obs.field_id == t0_obs.field_id
            and ref_date < obs.observation_date <= window_end
        ]

        status_t0 = self.determine_status_at_t0(t0_obs)
        base_incidence = t0_obs.incidence_pct
        base_severity = t0_obs.severity_pct

        if not forward_obs:
            # If no ground truth scouting visits occurred in next 7 days, cannot fabricate labels!
            raise ValueError(
                f"Cannot generate 7-day outbreak label for field '{t0_obs.field_id}' on {ref_date}: "
                f"No future scouting visits exist in the [t0+1d, t0+7d] window."
            )

        max_future_incidence = max(obs.incidence_pct for obs in forward_obs)
        max_future_severity = max(obs.severity_pct for obs in forward_obs)
        incidence_delta = max_future_incidence - base_incidence

        # Epidemiological decision logic
        if status_t0 == DiseaseOccurrenceStatus.ACTIVE_OUTBREAK:
            # Disease was ALREADY in active outbreak at t0.
            # Not a new outbreak event.
            outbreak_label = 0
            reason = (
                f"No new outbreak event: Field already had an active outbreak at t0 "
                f"(severity {base_severity:.1f}% >= threshold {self.config.economic_severity_threshold_pct}%)."
            )
        elif max_future_severity >= self.config.economic_severity_threshold_pct:
            outbreak_label = 1
            reason = (
                f"New outbreak detected: Severity crossed economic injury threshold "
                f"from baseline {base_severity:.1f}% to {max_future_severity:.1f}% "
                f"(threshold: {self.config.economic_severity_threshold_pct}%)."
            )
        elif incidence_delta >= self.config.rapid_incidence_surge_delta_pct:
            outbreak_label = 1
            reason = (
                f"New outbreak detected: Rapid epidemic expansion observed with "
                f"incidence surge delta +{incidence_delta:.1f}% in next 7 days "
                f"(threshold: +{self.config.rapid_incidence_surge_delta_pct}%)."
            )
        else:
            outbreak_label = 0
            reason = (
                f"No outbreak: Future severity reached max {max_future_severity:.1f}% "
                f"and incidence delta was +{incidence_delta:.1f}%, remaining below action thresholds."
            )

        return OutbreakPredictionTarget(
            field_id=t0_obs.field_id,
            reference_date=ref_date,
            forecast_horizon_days=7,
            target_disease=t0_obs.target_disease,
            status_at_t0=status_t0,
            baseline_incidence_at_t0=base_incidence,
            future_max_incidence_next_7d=max_future_incidence,
            future_max_severity_next_7d=max_future_severity,
            incidence_delta_next_7d=incidence_delta,
            outbreak_label_7d=outbreak_label,
            outbreak_reason=reason,
        )
