"""
integration_example.py
──────────────────────
AgriAdapt AI: Standalone Fertilizer Recommendation Model Integration Example

This script demonstrates:
  1. Loading the trained model from the local package directory.
  2. Formatting input data using real test holdout samples (Andhra Pradesh Rice, Bihar Wheat).
  3. Calling the prediction function (supports dict, list of dicts, and pandas DataFrame).
  4. Displaying predicted fertilizer requirements with nutrient names, chemical forms,
     and units (kg/ha), along with approximate commercial fertilizer conversions.
  5. Demonstrating strict input validation and error rejection.

Usage:
    python integration_example.py
"""

from __future__ import annotations

import sys
from pathlib import Path
import json

# Ensure the package root is in sys.path when running as a standalone script
PACKAGE_ROOT = Path(__file__).resolve().parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

import pandas as pd
from src.models.predict import FertilizerPredictor, predict_fertilizer


def run_single_prediction_example(predictor: FertilizerPredictor):
    print("=" * 70)
    print("EXAMPLE 1: Single Plot Prediction (Python Dictionary)")
    print("=" * 70)

    # Genuine sample from test holdout: Visakhapatnam district, Andhra Pradesh
    test_sample_rice = {
        "crop": "Rice",
        "state_name": "Andhra Pradesh",
        "crop_season": "Kharif",
        "nitrogen__nutrient_index": 1.45,
        "nitrogen__pct_low": 55.12,
        "nitrogen__pct_medium": 44.71,
        "nitrogen__pct_high": 0.17,
        "phosphorus__nutrient_index": 2.36,
        "phosphorus__pct_low": 20.66,
        "phosphorus__pct_medium": 22.64,
        "phosphorus__pct_high": 56.69,
        "potassium__nutrient_index": 1.67,
        "potassium__pct_low": 45.66,
        "potassium__pct_medium": 41.40,
        "potassium__pct_high": 12.93,
        "soil_ph__nutrient_index": 2.03,
        "organic_carbon__nutrient_index": 1.80,
    }

    print("\n[Input Plot Profile]:")
    print(f"  Crop:        {test_sample_rice['crop']} ({test_sample_rice['crop_season']} season)")
    print(f"  Location:    {test_sample_rice['state_name']}")
    print(f"  Soil N Index: {test_sample_rice['nitrogen__nutrient_index']} (Low fertility)")
    print(f"  Soil P Index: {test_sample_rice['phosphorus__nutrient_index']} (Medium-High fertility)")
    print(f"  Soil K Index: {test_sample_rice['potassium__nutrient_index']} (Low-Medium fertility)")

    # Execute prediction
    result = predictor.predict(test_sample_rice)

    print("\n[Recommended Fertilizer Requirements]:")
    recs = result["recommendations"]
    for nutrient, data in recs.items():
        print(f"  • {nutrient.upper():<10} ({data['chemical_form']:<17}): "
              f"{data['value']:>6.2f} {data['unit']}")

    print("\n[Commercial Fertilizer Bag Equivalents (approx)]: ")
    comm = result["fertilizer_commercial_equivalent_approx"]
    print(f"  • Urea (46% N)       : {comm['urea_46_pct_n_kg_ha']} kg/ha")
    print(f"  • DAP (46% P2O5)     : {comm['dap_46_pct_p2o5_kg_ha']} kg/ha")
    print(f"  • MOP (60% K2O)      : {comm['mop_60_pct_k2o_kg_ha']} kg/ha")

    print(f"\n[Advisory Note]: {result['disclaimer']}")


def run_batch_prediction_example(predictor: FertilizerPredictor):
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Batch Prediction (pandas DataFrame)")
    print("=" * 70)

    # Two genuine samples: AP Rice and Bihar Wheat
    batch_records = [
        {
            "crop": "Rice",
            "state_name": "Andhra Pradesh",
            "nitrogen__nutrient_index": 1.45,
            "phosphorus__nutrient_index": 2.36,
            "potassium__nutrient_index": 1.67,
            "soil_ph__nutrient_index": 2.03,
            "organic_carbon__nutrient_index": 1.80,
        },
        {
            "crop": "Wheat",
            "state_name": "Bihar",
            "nitrogen__nutrient_index": 1.76,
            "phosphorus__nutrient_index": 1.89,
            "potassium__nutrient_index": 2.12,
            "soil_ph__nutrient_index": 2.05,
            "organic_carbon__nutrient_index": 1.62,
        },
    ]

    df_input = pd.DataFrame(batch_records)
    df_output = predictor.predict(df_input)

    print("\n[Batch Output DataFrame]:")
    print(df_output[["crop", "state_name", "recommended_n_kg_ha", "recommended_p2o5_kg_ha", "recommended_k2o_kg_ha", "unit"]].to_string(index=False))


def run_validation_guard_example(predictor: FertilizerPredictor):
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Input Validation & Error Handling")
    print("=" * 70)

    # 1. Missing required feature
    invalid_input = {
        "crop": "Rice",
        # 'state_name' is missing
        "nitrogen__nutrient_index": 1.5,
        "phosphorus__nutrient_index": 2.0,
        "potassium__nutrient_index": 2.0,
        "soil_ph__nutrient_index": 2.0,
        "organic_carbon__nutrient_index": 1.8,
    }

    try:
        predictor.predict(invalid_input)
    except ValueError as e:
        print(f"\n[Guard 1: Missing Feature Caught Successfully]:\n  --> {e}")

    # 2. Out-of-bounds physical value
    bad_bounds_input = {
        "crop": "Rice",
        "state_name": "Punjab",
        "nitrogen__nutrient_index": 15.0,  # Invalid! Nutrient Index must be in [1.0, 3.0]
        "phosphorus__nutrient_index": 2.0,
        "potassium__nutrient_index": 2.0,
        "soil_ph__nutrient_index": 2.0,
        "organic_carbon__nutrient_index": 1.8,
    }

    try:
        predictor.predict(bad_bounds_input)
    except ValueError as e:
        print(f"\n[Guard 2: Out-of-Bounds Rejection Caught Successfully]:\n  --> {e}")


if __name__ == "__main__":
    print("\nInitializing AgriAdapt AI Fertilizer Recommendation Predictor...")
    predictor = FertilizerPredictor()
    print("Model loaded successfully from local package.")

    run_single_prediction_example(predictor)
    run_batch_prediction_example(predictor)
    run_validation_guard_example(predictor)
    print("\n" + "=" * 70)
    print("All integration examples completed successfully.")
    print("=" * 70 + "\n")
