"""
audit_maize_forecasting.py
──────────────────────────
CLI tool to audit project data sufficiency for 7-Day Maize Disease Outbreak Forecasting,
print the technical findings, and verify the forecasting pipeline skeleton.

Usage:
    python audit_maize_forecasting.py
    python audit_maize_forecasting.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.maize_outbreak_forecasting import (
    audit_project_data_sufficiency,
    MaizeDiseaseOutbreakPipeline,
    MaizeDiseaseForecastRequest,
    MaizeGrowthStage,
    TargetDisease,
)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def print_audit_report(audit) -> None:
    print("")
    print("=" * 75)
    print("   AgriAdapt AI -- 7-Day Maize Disease Outbreak Pipeline Data Audit")
    print("=" * 75)
    print(f"  Decision Status:     {'CAN TRAIN' if audit.can_train_forecasting_model else 'MODEL TRAINING HALTED (DATA INSUFFICIENT)'}")
    print("-" * 75)
    print("  EXECUTIVE SUMMARY:")
    for line in audit.decision_reason.split("\n"):
        print(f"    {line}")
    print("-" * 75)

    print("  AUDITED DATASETS IN WORKSPACE:")
    for d in audit.datasets_audited:
        print(f"\n  * Dataset Path:      {d.path}")
        print(f"    Record Count:      {d.record_count:,}")
        print(f"    Columns:           {', '.join(d.columns[:8])}{'...' if len(d.columns) > 8 else ''}")
        print(f"    Temporal Index:    {'YES' if d.has_date_index else 'NO (Zero temporal fields)'}")
        print(f"    Crop Coverage:     {', '.join(d.crop_coverage[:5])}{'...' if len(d.crop_coverage) > 5 else ''}")
        print(f"    Location Coverage: {', '.join(d.location_coverage)}")
        print(f"    Suitability:       {d.suitability_for_7d_forecasting}")
        print(f"    Audit Remarks:     {d.remarks}")

    print("\n" + "-" * 75)
    print("  EXISTING MAIZE CNN ARTIFACTS:")
    if audit.existing_cnn_artifacts:
        for fname, size in audit.existing_cnn_artifacts.items():
            print(f"    * {fname:<30} ({size})")
    else:
        print("    * None detected in models/maize_disease")

    print("\n" + "-" * 75)
    print("  CRITICAL MISSING DATA:")
    for req in audit.missing_data_requirements:
        print(f"    [!] {req}")

    print("\n" + "-" * 75)
    print("  REQUIRED HISTORICAL COLLECTION PROCESS:")
    for step in audit.required_collection_process:
        print(f"    --> {step}")

    print("\n" + "-" * 75)
    print("  7-DAY OUTBREAK GROUND TRUTH LABEL DEFINITION:")
    for line in audit.label_creation_strategy.split("\n"):
        print(f"    {line}")

    print("\n" + "=" * 75)
    print("  RUNNING PIPELINE SKELETON DEMO (Bio-Climatic Screening):")
    pipeline = MaizeDiseaseOutbreakPipeline()
    req = MaizeDiseaseForecastRequest(
        field_id="FIELD-KAR-BLG-042",
        district="Belagavi",
        state="Karnataka",
        reference_date=date(2026, 10, 20),
        growth_stage=MaizeGrowthStage.SILKING_R1,
        target_disease=TargetDisease.COMMON_RUST,
        current_incidence_pct=2.0,
        current_severity_pct=0.8,
        t7_mean_temperature_c=21.5,
        t7_mean_humidity_pct=84.0,
        t7_cumulative_rainfall_mm=38.5,
        t7_consecutive_high_humidity_days=4,
    )
    resp = pipeline.forecast_7day_risk(req)
    print(f"    Target Disease:        {resp.target_disease.upper()}")
    print(f"    Field Identifier:      {resp.field_id} ({req.district}, {req.state})")
    print(f"    Prediction Window:     {resp.forecast_valid_from} to {resp.forecast_valid_to} (7 days)")
    print(f"    Outbreak Probability:  {resp.outbreak_probability:.1%}")
    print(f"    Assigned Risk Tier:    {resp.risk_tier}")
    print(f"    Current Field Status:  {resp.current_field_status}")
    print(f"    Model Provenance:      {resp.model_provenance['status']}")
    print(f"    Advisory:              {resp.recommended_preventive_action}")
    print("=" * 75)
    print("")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit data sufficiency for 7-day maize disease outbreak forecasting.")
    parser.add_argument("--json", action="store_true", help="Output audit results in JSON format")
    args = parser.parse_args()

    audit = audit_project_data_sufficiency(PROJECT_ROOT)

    # Save to models/maize_outbreak/
    out_dir = PROJECT_ROOT / "models" / "maize_outbreak"
    out_dir.mkdir(parents=True, exist_ok=True)
    audit_dict = {
        "can_train_forecasting_model": audit.can_train_forecasting_model,
        "decision_reason": audit.decision_reason,
        "weather_sensor_data_available": audit.weather_sensor_data_available,
        "historical_disease_surveillance_available": audit.historical_disease_surveillance_available,
        "existing_cnn_artifacts": audit.existing_cnn_artifacts,
        "missing_data_requirements": audit.missing_data_requirements,
        "required_collection_process": audit.required_collection_process,
        "proposed_feature_schema": audit.proposed_feature_schema,
        "label_creation_strategy": audit.label_creation_strategy,
    }
    with open(out_dir / "data_sufficiency_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit_dict, f, indent=2)

    if args.json:
        print(json.dumps(audit_dict, indent=2))
    else:
        print_audit_report(audit)

    return 0


if __name__ == "__main__":
    sys.exit(main())
