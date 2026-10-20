"""
AgriAdapt AI — Feature Ablation and Threshold Audit Runner.
Executes Experiment A (Full), Experiment B (Weather & Crop), and Experiment C (Early Warning),
performing permutation feature importance, threshold grid evaluation, and separate MLflow logging.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models.pest_forecasting.ablation import run_ablation_suite


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AgriAdapt AI: Run Pest Forecasting Feature Ablation and Threshold Audit"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/synthetic_multicrop_pest_forecasting.csv",
        help="Path to synthetic pest forecasting dataset CSV",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="experiments/pest_forecasting_ablation",
        help="Directory to persist ablation experiment artifacts",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--no-mlflow",
        action="store_true",
        help="Disable MLflow experiment logging",
    )

    args = parser.parse_args()

    print("=" * 75)
    print("AGRIADAPT AI — PEST OUTBREAK FEATURE ABLATION & THRESHOLD AUDIT")
    print("=" * 75)

    result = run_ablation_suite(
        data_path=args.data_path,
        output_dir=args.output_dir,
        random_seed=args.seed,
        enable_mlflow=not args.no_mlflow,
    )

    print("\n" + "=" * 75)
    print("ABLATION SUITE COMPLETED SUCCESSFULLY")
    print("=" * 75)
    print(f"Report: {result['report_path']}")
    print(f"Summary JSON: {result['summary_json_path']}")
    print("=" * 75)


if __name__ == "__main__":
    main()
