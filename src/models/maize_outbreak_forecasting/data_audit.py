"""
src/models/maize_outbreak_forecasting/data_audit.py
───────────────────────────────────────────────────
Automated Data Sufficiency Auditor for Maize Disease Outbreak Forecasting.
Conducts a comprehensive inspection of all project assets, CSVs, models, and schemas.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import pandas as pd


@dataclass
class DatasetAuditEntry:
    path: str
    record_count: int
    columns: list[str]
    has_date_index: bool
    date_range: tuple[str, str] | None
    crop_coverage: list[str]
    location_coverage: list[str]
    disease_labels: list[str]
    suitability_for_7d_forecasting: str
    remarks: str


@dataclass
class DataAuditResult:
    can_train_forecasting_model: bool
    decision_reason: str
    datasets_audited: list[DatasetAuditEntry]
    weather_sensor_data_available: bool
    historical_disease_surveillance_available: bool
    existing_cnn_artifacts: dict[str, Any]
    existing_apis_summary: list[str]
    missing_data_requirements: list[str]
    required_collection_process: list[str]
    proposed_feature_schema: list[str]
    label_creation_strategy: str


def audit_project_data_sufficiency(project_root: str | Path = ".") -> DataAuditResult:
    root = Path(project_root).resolve()
    datasets: list[DatasetAuditEntry] = []

    # 1. Audit Crop_recommendation.csv
    crop_rec_paths = [
        root / "data" / "raw" / "Crop_recommendation.csv",
        root / "Crop_recommendation.csv",
    ]
    for p in crop_rec_paths:
        if p.exists():
            try:
                df = pd.read_csv(p)
                datasets.append(DatasetAuditEntry(
                    path=str(p.relative_to(root)),
                    record_count=len(df),
                    columns=list(df.columns),
                    has_date_index=False,
                    date_range=None,
                    crop_coverage=sorted(df["label"].unique().tolist()) if "label" in df.columns else [],
                    location_coverage=["None - No geographic identifiers in dataset"],
                    disease_labels=["None - Target 'label' is crop name to plant"],
                    suitability_for_7d_forecasting="UNSUITABLE",
                    remarks=(
                        "Static tabular dataset for planting crop recommendation based on N, P, K, pH, "
                        "and single-point climatic means. Contains no temporal sequence, no field locations, "
                        "and no disease observations."
                    )
                ))
            except Exception as e:
                pass
            break  # Audit only once

    # 2. Audit Maize Leaf Disease Image Dataset
    maize_clean_dir = root / "data" / "maize_leaf_disease"
    maize_raw_dir = root / "data" / "corn_maize_leaf_disease-main" / "corn_leaves"
    target_img_dir = maize_clean_dir if maize_clean_dir.exists() else maize_raw_dir

    if target_img_dir.exists():
        classes = [d.name for d in target_img_dir.iterdir() if d.is_dir() and d.name != "splits"]
        total_imgs = sum(len(list(d.glob("*.*"))) for d in target_img_dir.iterdir() if d.is_dir() and d.name != "splits")
        datasets.append(DatasetAuditEntry(
            path=str(target_img_dir.relative_to(root)),
            record_count=total_imgs,
            columns=["image_file", "class_folder", "bounding_box_csv"],
            has_date_index=False,
            date_range=None,
            crop_coverage=["Maize (Zea mays)"],
            location_coverage=["None - Image metadata lacks GPS/field coordinates"],
            disease_labels=sorted(classes),
            suitability_for_7d_forecasting="UNSUITABLE_AS_OUTBREAK_LABELS",
            remarks=(
                "Image classification dataset containing excised leaf photographs across 4 static categories "
                "(blight, common_rust, gray_leaf_spot, healthy). These represent instantaneous visual symptoms, "
                "not temporal field epidemic outbreaks. Cannot be used to generate future temporal labels."
            )
        ))

    # 3. Check for Weather & Sensor Data
    weather_found = False
    for ext in ("*.csv", "*.parquet", "*.json"):
        for f in (root / "data").rglob(ext):
            name_lower = f.name.lower()
            if any(k in name_lower for k in ("weather", "sensor", "station", "meteo", "climate_series", "rainfall_daily")):
                weather_found = True
                break

    # 4. Check for Historical Pest/Disease Surveillance Records
    surveillance_found = False
    for ext in ("*.csv", "*.parquet", "*.json"):
        for f in (root / "data").rglob(ext):
            name_lower = f.name.lower()
            if any(k in name_lower for k in ("scouting", "trap", "surveillance", "incidence", "outbreak_log", "rust_survey")):
                surveillance_found = True
                break

    # 5. Existing CNN Artifacts
    cnn_artifacts = {}
    cnn_dir = root / "models" / "maize_disease"
    if cnn_dir.exists():
        for f in cnn_dir.iterdir():
            if f.is_file():
                cnn_artifacts[f.name] = f"{round(f.stat().st_size / (1024 * 1024), 2)} MB" if f.stat().st_size > 1024*1024 else f"{f.stat().st_size} bytes"

    # 6. Existing APIs Summary
    apis_summary = [
        "POST /api/v1/crop/recommend (Soil nutrient & climate crop selector)",
        "POST /api/v1/fertilizer/recommend (ICAR-IISS nutrient optimizer)",
        "POST /api/v1/advisory/unified (Combined advisory with preliminary rule-based pest risk)",
        "GET  /api/v1/pest/eligible-crops (Canonical crop eligibility spec)",
        "GET  /api/v1/pest/spec/{crop_identifier} (Target pest biological thresholds)",
        "POST /api/v1/pest/preview (Rule-based agroclimatic pest risk preview)",
    ]

    # Decision logic
    can_train = weather_found and surveillance_found
    reason = (
        "SUFFICIENT DATA AVAILABLE: Longitudinal field scouting and weather time-series detected."
        if can_train
        else (
            "CRITICAL DATA DEFICIT — MODEL TRAINING HALTED:\n"
            "1. Zero time-indexed longitudinal field disease surveillance records exist in workspace.\n"
            "2. Zero daily weather time-series records exist for historical field plots.\n"
            "3. The existing corn leaf dataset contains static leaf photos with no dates or locations; "
            "fabricating temporal outbreak labels from them is scientifically invalid and prohibited."
        )
    )

    missing_requirements = [
        "Daily meteorological time-series (T_min, T_max, RH_morning, RH_evening, Rainfall mm, Leaf wetness hours) for specific fields.",
        "Longitudinal scouting logs with unique field/plot ID, GPS coordinates, date of observation, and maize growth stage.",
        "Quantitative disease measurements (% infected plants incidence, % leaf area affected severity on Cobb scale).",
        "Multi-season surveillance (minimum 2–3 growing seasons) to capture non-outbreak vs epidemic outbreak transitions.",
    ]

    collection_process = [
        "Phase A: Ingest historical surveillance records from ICAR-IIMR (Ludhiana/Hyderabad), UAS Dharwad, or CIMMYT India maize rust surveys.",
        "Phase B: Connect NASA POWER Agroclimatology API / IMD gridded daily weather for target field coordinates over past seasons.",
        "Phase C: Align weekly field scouting with 7-day preceding weather summaries [t-7 to t0] and 7-day forward outbreak transition [t+1 to t+7].",
        "Phase D: Execute the implemented time-based stratified splitting pipeline on true ground truth.",
    ]

    proposed_schema = [
        "field_id (string)", "observation_date (date, t0)", "growth_stage (BBCH/CIMMYT scale)",
        "t7_mean_temp_c (float)", "t7_min_temp_c (float)", "t7_max_temp_c (float)",
        "t7_temp_favorable_rust_hours_est (float, 16-25°C hours)",
        "t7_mean_rh_pct (float)", "t7_high_rh_days (int, RH > 80%)",
        "t7_cumulative_rainfall_mm (float)", "t7_rainy_days_count (int)",
        "t7_estimated_leaf_wetness_hours_sum (float)",
        "t14_cumulative_rainfall_mm (float)",
        "growth_stage_vulnerability_index (float [0.1, 1.0])",
        "current_incidence_at_t0 (float %)", "current_severity_at_t0 (float %)",
        "disease_already_present_t0 (binary 0/1)",
        "regional_outbreak_pressure_last_14d (float [0, 1])",
        "cnn_observed_leaf_rust_probability_t0 (optional visual symptom score at t0)",
    ]

    label_strategy = (
        "Target Y_{t+7} in {0, 1}:\n"
        "Y = 1 if field transitions from sub-threshold (severity < 5%) at t0 to crossing economic threshold "
        "(severity >= 5% or incidence surge delta >= 10%) within forward window [t0+1d, t0+7d].\n"
        "Y = 0 if field remains below action threshold or already had an uncontained outbreak at t0."
    )

    return DataAuditResult(
        can_train_forecasting_model=can_train,
        decision_reason=reason,
        datasets_audited=datasets,
        weather_sensor_data_available=weather_found,
        historical_disease_surveillance_available=surveillance_found,
        existing_cnn_artifacts=cnn_artifacts,
        existing_apis_summary=apis_summary,
        missing_data_requirements=missing_requirements,
        required_collection_process=collection_process,
        proposed_feature_schema=proposed_schema,
        label_creation_strategy=label_strategy,
    )
