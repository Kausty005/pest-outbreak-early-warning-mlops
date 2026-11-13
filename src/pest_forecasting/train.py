"""
src/pest_forecasting/train.py
─────────────────────────────
Training engine for experimental multi-crop pest outbreak forecasting.
Trains and compares Logistic Regression, Random Forest, XGBoost, and LightGBM
across both FULL and ENVIRONMENTAL-ONLY feature sets.
Saves versioned artifacts to models/experimental_synthetic_pest/.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from .dataset import (
    ENVIRONMENTAL_FEATURE_COLUMNS,
    FULL_FEATURE_COLUMNS,
    TARGET_COLUMN,
    chronological_split_with_purging,
    load_and_validate_dataset,
)
from .evaluate import (
    evaluate_predictions,
    evaluate_slices_by_column,
    find_optimal_threshold,
)
from .preprocessor import build_model_pipeline

LOGGER = logging.getLogger(__name__)

MODELS_DIR = Path("models/experimental_synthetic_pest")
RANDOM_SEED = 42


def get_model_instances(imbalance_ratio: float) -> dict[str, Any]:
    """
    Instantiate the 4 candidate models with appropriate class-imbalance strategies.
    All random seeds pinned to 42 for complete reproducibility.
    """
    return {
        "LogisticRegression": LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=RANDOM_SEED,
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=100,
            max_depth=12,
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        ),
        "XGBoost": XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            scale_pos_weight=imbalance_ratio,
            eval_metric="logloss",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        ),
        "LightGBM": LGBMClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
            verbose=-1,
        ),
    }


def train_and_evaluate_configuration(
    df: pd.DataFrame,
    feature_config: str = "full",
) -> tuple[dict[str, Any], Any, str]:
    """
    Train and evaluate all 4 model families for a given feature configuration.
    Returns comparison summary dictionary, best pipeline, and best model name.
    """
    splits, meta = chronological_split_with_purging(df, feature_set=feature_config, purge_days=7)

    # Calculate class imbalance ratio strictly on training split
    neg_count = int((splits.y_train == 0).sum())
    pos_count = int((splits.y_train == 1).sum())
    imbalance_ratio = neg_count / max(pos_count, 1)

    selected_features = list(FULL_FEATURE_COLUMNS if feature_config == "full" else ENVIRONMENTAL_FEATURE_COLUMNS)
    candidate_models = get_model_instances(imbalance_ratio)

    results: dict[str, Any] = {}
    best_model_name = ""
    best_val_pr_auc = -1.0
    best_pipeline = None

    for name, clf in candidate_models.items():
        print(f"  Training {name} on {feature_config.upper()} feature set ({len(splits.X_train)} samples)...")
        pipeline = build_model_pipeline(classifier=clf, feature_columns=selected_features)
        pipeline.fit(splits.X_train, splits.y_train)

        # Validation probability predictions
        val_probs = pipeline.predict_proba(splits.X_val)[:, 1]
        tuned_thresh, best_f1 = find_optimal_threshold(splits.y_val.values, val_probs, metric="f1")

        # Validation evaluation at tuned threshold
        val_metrics = evaluate_predictions(
            y_true=splits.y_val.values,
            y_prob=val_probs,
            model_name=name,
            feature_set=feature_config.upper(),
            split_name="validation",
            threshold=tuned_thresh,
        )

        # Test probability predictions (out-of-time test partition)
        test_probs = pipeline.predict_proba(splits.X_test)[:, 1]
        test_metrics_default = evaluate_predictions(
            y_true=splits.y_test.values,
            y_prob=test_probs,
            model_name=name,
            feature_set=feature_config.upper(),
            split_name="test_default_0.50",
            threshold=0.50,
        )
        test_metrics_tuned = evaluate_predictions(
            y_true=splits.y_test.values,
            y_prob=test_probs,
            model_name=name,
            feature_set=feature_config.upper(),
            split_name="test_tuned",
            threshold=tuned_thresh,
        )

        # Sliced evaluation across Crops and Pests
        crop_slices = evaluate_slices_by_column(
            splits.X_test, splits.y_test.values, test_probs, column="crop", threshold=tuned_thresh
        )
        pest_slices = evaluate_slices_by_column(
            splits.X_test, splits.y_test.values, test_probs, column="pest", threshold=tuned_thresh
        )

        model_result = {
            "model_name": name,
            "feature_set": feature_config.upper(),
            "optimal_threshold": tuned_thresh,
            "validation_metrics": val_metrics.to_dict(),
            "test_metrics_default_threshold": test_metrics_default.to_dict(),
            "test_metrics_tuned_threshold": test_metrics_tuned.to_dict(),
            "per_crop_slices": crop_slices,
            "per_pest_slices": pest_slices,
        }
        results[name] = model_result

        # Track best model by validation PR-AUC
        if val_metrics.pr_auc > best_val_pr_auc:
            best_val_pr_auc = val_metrics.pr_auc
            best_model_name = name
            best_pipeline = pipeline

    summary = {
        "feature_configuration": feature_config.upper(),
        "feature_count": len(selected_features),
        "features": selected_features,
        "split_metadata": {
            "train_samples": meta.train_count,
            "val_samples": meta.val_count,
            "test_samples": meta.test_count,
            "purged_samples": meta.total_purged_count,
            "train_dates": [meta.train_start_date, meta.train_end_date],
            "val_dates": [meta.val_start_date, meta.val_end_date],
            "test_dates": [meta.test_start_date, meta.test_end_date],
        },
        "best_model_name": best_model_name,
        "best_validation_pr_auc": best_val_pr_auc,
        "models": results,
    }
    return summary, best_pipeline, best_model_name


def run_full_experimental_training(
    dataset_path: str | Path = "data/synthetic_multicrop_pest_forecasting.csv",
    save_artifacts: bool = True,
) -> dict[str, Any]:
    """
    Execute complete experimental benchmark across both FULL and ENVIRONMENTAL-ONLY configurations.
    Saves trained pipelines and reproducible metadata.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df = load_and_validate_dataset(dataset_path)

    print("\n=======================================================")
    print("1. RUNNING FULL SYNTHETIC EXPERIMENT (14 FEATURES)")
    print("=======================================================")
    full_summary, full_best_pipe, full_best_name = train_and_evaluate_configuration(df, feature_config="full")

    print("\n=======================================================")
    print("2. RUNNING ENVIRONMENTAL-ONLY EXPERIMENT (11 FEATURES)")
    print("=======================================================")
    env_summary, env_best_pipe, env_best_name = train_and_evaluate_configuration(df, feature_config="environmental")

    overall_results = {
        "experiment_timestamp": datetime.utcnow().isoformat(),
        "random_seed": RANDOM_SEED,
        "dataset_path": str(dataset_path),
        "total_records": len(df),
        "target_column": TARGET_COLUMN,
        "classification": "SYNTHETIC_EXPERIMENTAL_BENCHMARK",
        "scientific_disclaimer": (
            "All metrics are benchmark results obtained on simulated synthetic data. "
            "They do NOT establish real-world predictive validity and must NOT be used for operational pest management."
        ),
        "experiments": {
            "FULL_SYNTHETIC": full_summary,
            "ENVIRONMENTAL_ONLY": env_summary,
        },
    }

    if save_artifacts:
        # 1. Save full model pipeline
        full_path = MODELS_DIR / "full_model_pipeline.joblib"
        joblib.dump(full_best_pipe, full_path)

        # 2. Save environmental model pipeline
        env_path = MODELS_DIR / "environmental_model_pipeline.joblib"
        joblib.dump(env_best_pipe, env_path)

        # 3. Save feature schema
        schema_path = MODELS_DIR / "feature_schemas.json"
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "FULL_SYNTHETIC_FEATURES": list(FULL_FEATURE_COLUMNS),
                    "ENVIRONMENTAL_ONLY_FEATURES": list(ENVIRONMENTAL_FEATURE_COLUMNS),
                    "EXCLUDED_FROM_ENVIRONMENTAL": ["current_incidence_pct_t0", "current_severity_pct_t0", "pest_present_t0"],
                    "FORBIDDEN_LEAKAGE_COLUMNS": ["date", "field_id", TARGET_COLUMN],
                },
                f,
                indent=2,
            )

        # 4. Save experiment comparison summary
        summary_path = MODELS_DIR / "experiment_comparison_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(overall_results, f, indent=2)

        # 5. Save synthetic data provenance metadata
        prov_path = MODELS_DIR / "synthetic_provenance_metadata.json"
        with open(prov_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "source_dataset": str(dataset_path),
                    "synthetic_generation_module": "src/data/generate_synthetic_pest_data.py",
                    "simulation_type": "biophysical_population_dynamics",
                    "authentic_field_observations_used": 0,
                    "production_deployment_eligible": False,
                    "pipeline_version": "1.0.0-experimental",
                },
                f,
                indent=2,
            )

        print(f"\nArtifacts successfully written to {MODELS_DIR}/")

    return overall_results


if __name__ == "__main__":
    run_full_experimental_training()

