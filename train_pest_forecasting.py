"""
AgriAdapt AI — Synthetic Pest Outbreak Forecaster Training Runner.
Executes reproducible, leakage-free training across 4 candidate models with
chronological train-val-test splitting and 7-day target purging.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models.pest_forecasting.train import PipelineConfig, run_training_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AgriAdapt AI: Train Synthetic Pest Outbreak Forecaster"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/synthetic_multicrop_pest_forecasting.csv",
        help="Path to synthetic pest forecasting dataset CSV",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=str,
        default="models/pest_outbreak_forecasting",
        help="Directory to persist model artifacts and evaluation reports",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Execute quick run with smaller estimators (useful for smoke tests)",
    )
    parser.add_argument(
        "--no-mlflow",
        action="store_true",
        help="Disable MLflow experiment logging",
    )
    parser.add_argument(
        "--purge-days",
        type=int,
        default=7,
        help="Number of days to purge/embargo between chronological splits (default: 7)",
    )

    args = parser.parse_args()

    config = PipelineConfig(
        data_path=args.data_path,
        artifacts_dir=args.artifacts_dir,
        random_seed=args.seed,
        purge_days=args.purge_days,
        quick=args.quick,
        mlflow_enabled=not args.no_mlflow,
    )

    result = run_training_pipeline(config)

    print("\n" + "=" * 70)
    print("AGRIADAPT AI — PEST OUTBREAK TRAINING PIPELINE COMPLETED")
    print("=" * 70)
    print(f"Selected Winner Model: {result['winner_model']}")
    print(f"Optimal Threshold (Validation): {result['optimal_threshold']:.2f}")
    print(f"Model Artifact: {result['model_artifact_path']}")
    print(f"Model Artifact (Root Copy): {result['root_model_path']}")
    print(f"Comparison Report: {result['comparison_report_path']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
