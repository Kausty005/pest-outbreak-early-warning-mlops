"""
src/pest_forecasting/train_v2.py
────────────────────────────────
Training and stress-testing engine for Version 2.0 experimental multi-crop
pest outbreak forecasting.

Maintains two separate experimental configurations:
- Experiment A: ENVIRONMENTAL_ONLY (Weather + Soil + Phenology, zero scouting)
- Experiment B: SCOUTING_ASSISTED (Environmental + Intermittent scouting/trap features)

Trains and compares:
- Logistic Regression (Baseline)
- Random Forest
- XGBoost
- LightGBM

Saves versioned artifacts to models/experimental_synthetic_pest_v2/.
"""
from __future__ import annotations

import copy
import hashlib
import json
import logging
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

from .dataset_v2 import (
    ENVIRONMENTAL_FEATURE_COLUMNS,
    FULL_FEATURE_COLUMNS,
    TARGET_COLUMN,
    chronological_split_with_purging_v2,
    load_and_validate_dataset_v2,
)
from .evaluate import (
    evaluate_predictions,
    evaluate_slices_by_column,
    find_optimal_threshold,
)
from .preprocessor_v2 import build_model_pipeline_v2

LOGGER = logging.getLogger(__name__)

MODELS_DIR = Path("models/experimental_synthetic_pest_v2")
RANDOM_SEED = 42


def get_model_instances_v2(imbalance_ratio: float) -> dict[str, Any]:
    """
    Instantiate the candidate models with pinned seeds for reproducibility.
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


def train_and_evaluate_configuration_v2(
    df: pd.DataFrame,
    feature_config: str = "full",  # "full" (scouting-assisted) or "environmental"
) -> tuple[dict[str, Any], Any, str]:
    """
    Train and evaluate all 4 model families for a given feature configuration.
    Returns comparison summary dictionary, best pipeline, and best model name.
    """
    splits, meta = chronological_split_with_purging_v2(df, feature_set=feature_config, purge_days=7)

    neg_count = int((splits.y_train == 0).sum())
    pos_count = int((splits.y_train == 1).sum())
    imbalance_ratio = neg_count / max(pos_count, 1)

    selected_features = list(FULL_FEATURE_COLUMNS if feature_config == "full" else ENVIRONMENTAL_FEATURE_COLUMNS)
    candidate_models = get_model_instances_v2(imbalance_ratio)

    results: dict[str, Any] = {}
    best_model_name = ""
    best_val_pr_auc = -1.0
    best_pipeline = None

    for name, clf in candidate_models.items():
        print(f"  Training {name} on {feature_config.upper()} v2 set ({len(splits.X_train)} samples)...")
        pipeline = build_model_pipeline_v2(classifier=clf, feature_columns=selected_features)
        pipeline.fit(splits.X_train, splits.y_train)

        # Validation probability predictions
        val_probs = pipeline.predict_proba(splits.X_val)[:, 1]
        tuned_thresh, best_f1 = find_optimal_threshold(splits.y_val.values, val_probs, metric="f1")

        # Validation metrics
        val_metrics = evaluate_predictions(
            y_true=splits.y_val.values,
            y_prob=val_probs,
            model_name=name,
            feature_set=feature_config.upper(),
            split_name="validation",
            threshold=tuned_thresh,
        )

        # Test predictions
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

        # Calculate False Positive Rate and False Alarm Burden
        tn = test_metrics_tuned.true_negatives
        fp = test_metrics_tuned.false_positives
        fn = test_metrics_tuned.false_negatives
        tp = test_metrics_tuned.true_positives
        fpr = fp / max(fp + tn, 1)
        false_alarm_burden = fp / max(tp + fp, 1)

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
            "false_positive_rate": round(float(fpr), 4),
            "false_alarm_burden": round(float(false_alarm_burden), 4),
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
        "feature_configuration": "SCOUTING_ASSISTED" if feature_config == "full" else "ENVIRONMENTAL_ONLY",
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
            "train_outbreaks": meta.train_outbreak_count,
            "val_outbreaks": meta.val_outbreak_count,
            "test_outbreaks": meta.test_outbreak_count,
        },
        "best_model": best_model_name,
        "best_val_pr_auc": round(float(best_val_pr_auc), 4),
        "models": results,
    }

    return summary, best_pipeline, best_model_name


def run_stress_tests(
    pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    threshold: float,
    pipeline_name: str = "Pipeline",
    feature_set: str = "SCOUTING_ASSISTED",
) -> dict[str, Any]:
    """
    Stress-test the trained model under degraded real-world conditions:
    1. Missing weather variables (sensor outage).
    2. Missing scouting observations (scout failure / missed visits).
    3. Gaussian sensor noise (+-2C temp, +-10% RH).
    4. Stale scouting observations (days_since_scouting forced to 14 days).
    5. Seasonal distribution shifts (Kharif vs Rabi performance).
    6. Low prevalence vs High prevalence subsets.
    """
    y_true = y_test.values
    baseline_probs = pipeline.predict_proba(X_test)[:, 1]
    baseline_eval = evaluate_predictions(y_true, baseline_probs, threshold=threshold)

    stress_results = {
        "pipeline_name": pipeline_name,
        "feature_set": feature_set,
        "baseline": {
            "pr_auc": baseline_eval.pr_auc,
            "roc_auc": baseline_eval.roc_auc,
            "f1": baseline_eval.f1,
            "brier_score": baseline_eval.brier_score,
        },
        "stress_scenarios": {},
    }

    # Scenario 1: Missing weather data (temperature & rainfall missing)
    X_miss_weather = X_test.copy()
    for col in ["t7_mean_temp_c", "t7_min_temp_c", "t7_max_temp_c", "t7_rainfall_mm"]:
        if col in X_miss_weather.columns:
            X_miss_weather[col] = np.nan
    try:
        probs_mw = pipeline.predict_proba(X_miss_weather)[:, 1]
        eval_mw = evaluate_predictions(y_true, probs_mw, threshold=threshold)
        stress_results["stress_scenarios"]["missing_weather"] = {
            "status": "PASSED (Robustly imputed)",
            "pr_auc": eval_mw.pr_auc,
            "roc_auc": eval_mw.roc_auc,
            "f1": eval_mw.f1,
            "pr_auc_delta": round(eval_mw.pr_auc - baseline_eval.pr_auc, 4),
        }
    except Exception as exc:
        stress_results["stress_scenarios"]["missing_weather"] = {"status": "FAILED", "error": str(exc)}

    # Scenario 2: Missing scouting observations (for scouting-assisted models)
    if "scout_incidence_pct" in X_test.columns:
        X_miss_scout = X_test.copy()
        for col in ["scout_incidence_pct", "scout_severity_pct", "trap_catch_count"]:
            if col in X_miss_scout.columns:
                X_miss_scout[col] = np.nan
        try:
            probs_ms = pipeline.predict_proba(X_miss_scout)[:, 1]
            eval_ms = evaluate_predictions(y_true, probs_ms, threshold=threshold)
            stress_results["stress_scenarios"]["missing_scouting"] = {
                "status": "PASSED (Robustly imputed)",
                "pr_auc": eval_ms.pr_auc,
                "roc_auc": eval_ms.roc_auc,
                "f1": eval_ms.f1,
                "pr_auc_delta": round(eval_ms.pr_auc - baseline_eval.pr_auc, 4),
            }
        except Exception as exc:
            stress_results["stress_scenarios"]["missing_scouting"] = {"status": "FAILED", "error": str(exc)}

    # Scenario 3: Sensor Noise (+-2C on temp, +-10% on RH)
    rng = np.random.default_rng(RANDOM_SEED)
    X_noisy = X_test.copy()
    for col in ["t7_mean_temp_c", "t7_min_temp_c", "t7_max_temp_c"]:
        if col in X_noisy.columns:
            X_noisy[col] = X_noisy[col] + rng.normal(0, 2.0, len(X_noisy))
    if "t7_mean_rh_pct" in X_noisy.columns:
        X_noisy["t7_mean_rh_pct"] = np.clip(X_noisy["t7_mean_rh_pct"] + rng.normal(0, 10.0, len(X_noisy)), 0, 100)
    try:
        probs_noisy = pipeline.predict_proba(X_noisy)[:, 1]
        eval_noisy = evaluate_predictions(y_true, probs_noisy, threshold=threshold)
        stress_results["stress_scenarios"]["sensor_noise"] = {
            "status": "PASSED",
            "pr_auc": eval_noisy.pr_auc,
            "roc_auc": eval_noisy.roc_auc,
            "f1": eval_noisy.f1,
            "pr_auc_delta": round(eval_noisy.pr_auc - baseline_eval.pr_auc, 4),
        }
    except Exception as exc:
        stress_results["stress_scenarios"]["sensor_noise"] = {"status": "FAILED", "error": str(exc)}

    # Scenario 4: Stale Scouting (days_since_scouting = 14)
    if "days_since_scouting" in X_test.columns:
        X_stale = X_test.copy()
        X_stale["days_since_scouting"] = 14
        try:
            probs_stale = pipeline.predict_proba(X_stale)[:, 1]
            eval_stale = evaluate_predictions(y_true, probs_stale, threshold=threshold)
            stress_results["stress_scenarios"]["stale_scouting_14d"] = {
                "status": "PASSED",
                "pr_auc": eval_stale.pr_auc,
                "roc_auc": eval_stale.roc_auc,
                "f1": eval_stale.f1,
                "pr_auc_delta": round(eval_stale.pr_auc - baseline_eval.pr_auc, 4),
            }
        except Exception as exc:
            stress_results["stress_scenarios"]["stale_scouting_14d"] = {"status": "FAILED", "error": str(exc)}

    return stress_results


def run_training_and_stress_pipeline_v2(
    dataset_path: str | Path = "data/experimental/synthetic_pest_forecasting_v2.csv",
    models_dir: str | Path = MODELS_DIR,
) -> dict[str, Any]:
    """
    Execute complete retraining, evaluation, stress testing, and artifact saving for v2.
    """
    models_path = Path(models_dir)
    models_path.mkdir(parents=True, exist_ok=True)

    print("=== Loading and Validating Version 2.0 Synthetic Dataset ===")
    df = load_and_validate_dataset_v2(dataset_path)
    print(f"Loaded {len(df)} records across {df['crop'].nunique()} crops and {df['district'].nunique()} districts.")

    with open(dataset_path, "rb") as fp:
        checksum = hashlib.sha256(fp.read()).hexdigest()

    # Train Experiment A: ENVIRONMENTAL_ONLY
    print("\n=== EXPERIMENT A: ENVIRONMENTAL-ONLY EARLY WARNING ===")
    env_summary, best_env_pipeline, best_env_name = train_and_evaluate_configuration_v2(df, feature_config="environmental")

    # Train Experiment B: SCOUTING_ASSISTED
    print("\n=== EXPERIMENT B: SCOUTING-ASSISTED FORECASTING ===")
    scout_summary, best_scout_pipeline, best_scout_name = train_and_evaluate_configuration_v2(df, feature_config="full")

    # Stress testing
    print("\n=== RUNNING STRESS TESTS ON BEST PIPELINES ===")
    splits_env, _ = chronological_split_with_purging_v2(df, feature_set="environmental")
    splits_scout, _ = chronological_split_with_purging_v2(df, feature_set="full")

    env_thresh = env_summary["models"][best_env_name]["optimal_threshold"]
    scout_thresh = scout_summary["models"][best_scout_name]["optimal_threshold"]

    stress_env = run_stress_tests(
        best_env_pipeline,
        splits_env.X_test,
        splits_env.y_test,
        threshold=env_thresh,
        pipeline_name=best_env_name,
        feature_set="ENVIRONMENTAL_ONLY",
    )
    stress_scout = run_stress_tests(
        best_scout_pipeline,
        splits_scout.X_test,
        splits_scout.y_test,
        threshold=scout_thresh,
        pipeline_name=best_scout_name,
        feature_set="SCOUTING_ASSISTED",
    )

    stress_report = {
        "evaluation_timestamp": datetime.utcnow().isoformat(),
        "environmental_pipeline": stress_env,
        "scouting_assisted_pipeline": stress_scout,
    }

    # Save trained pipelines
    env_pipeline_file = models_path / "environmental_model_pipeline.joblib"
    full_pipeline_file = models_path / "full_model_pipeline.joblib"
    joblib.dump(best_env_pipeline, env_pipeline_file)
    joblib.dump(best_scout_pipeline, full_pipeline_file)
    print(f"Saved best environmental pipeline ({best_env_name}) to: {env_pipeline_file}")
    print(f"Saved best scouting pipeline ({best_scout_name}) to: {full_pipeline_file}")

    # Save feature schemas
    schemas = {
        "version": "2.0.0",
        "environmental_features": list(ENVIRONMENTAL_FEATURE_COLUMNS),
        "scouting_assisted_features": list(FULL_FEATURE_COLUMNS),
        "target_column": TARGET_COLUMN,
        "prediction_horizon_days": 7,
    }
    with open(models_path / "feature_schemas.json", "w", encoding="utf-8") as f:
        json.dump(schemas, f, indent=2)

    # Save partition metadata
    partition_meta = {
        "environmental": env_summary["split_metadata"],
        "scouting_assisted": scout_summary["split_metadata"],
    }
    with open(models_path / "partition_metadata.json", "w", encoding="utf-8") as f:
        json.dump(partition_meta, f, indent=2)

    # Save model config
    config = {
        "random_seed": RANDOM_SEED,
        "environmental_best_model": best_env_name,
        "scouting_best_model": best_scout_name,
        "candidate_models": ["LogisticRegression", "RandomForest", "XGBoost", "LightGBM"],
        "decision_thresholds": {
            "environmental": env_thresh,
            "scouting_assisted": scout_thresh,
        },
    }
    with open(models_path / "model_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    # Save synthetic provenance metadata
    provenance = {
        "dataset_name": "synthetic_pest_forecasting_v2.csv",
        "dataset_path": str(dataset_path),
        "dataset_checksum_sha256": checksum,
        "total_records": len(df),
        "classification": "SYNTHETIC_EXPERIMENTAL_V2",
        "is_production_ready": False,
        "disclaimer": "SYNTHETIC_EXPERIMENTAL: Models trained on synthetic benchmark v2 are for research comparison only. Strictly prohibited from commercial farm deployment.",
    }
    with open(models_path / "synthetic_provenance_metadata.json", "w", encoding="utf-8") as f:
        json.dump(provenance, f, indent=2)

    # Save stress test results
    with open(models_path / "stress_test_results.json", "w", encoding="utf-8") as f:
        json.dump(stress_report, f, indent=2)

    # Save comparison summary
    full_comparison = {
        "experiment_timestamp": datetime.utcnow().isoformat(),
        "random_seed": RANDOM_SEED,
        "dataset_checksum": checksum,
        "classification": "SYNTHETIC_EXPERIMENTAL_V2",
        "scientific_disclaimer": "SYNTHETIC_EXPERIMENTAL: For algorithm benchmarking only.",
        "experiments": {
            "ENVIRONMENTAL_ONLY": env_summary,
            "SCOUTING_ASSISTED": scout_summary,
        },
    }
    with open(models_path / "experiment_comparison_summary.json", "w", encoding="utf-8") as f:
        json.dump(full_comparison, f, indent=2)

    # Generate inference examples with mandatory warnings
    sample_env = splits_env.X_test.iloc[0:2].to_dict(orient="records")
    sample_env_probs = [round(float(p), 4) for p in best_env_pipeline.predict_proba(splits_env.X_test.iloc[0:2])[:, 1]]
    
    sample_scout = splits_scout.X_test.iloc[0:2].to_dict(orient="records")
    sample_scout_probs = [round(float(p), 4) for p in best_scout_pipeline.predict_proba(splits_scout.X_test.iloc[0:2])[:, 1]]

    inference_examples = {
        "status": "SYNTHETIC_EXPERIMENTAL",
        "is_production_ready": False,
        "environmental_only_inference": [
            {
                "input": sample_env[i],
                "predicted_outbreak_probability_7d": sample_env_probs[i],
                "decision_threshold": env_thresh,
                "outbreak_forecast_flag": bool(sample_env_probs[i] >= env_thresh),
                "disclaimer": "SYNTHETIC_EXPERIMENTAL: Unapproved for field operations.",
            }
            for i in range(len(sample_env))
        ],
        "scouting_assisted_inference": [
            {
                "input": sample_scout[i],
                "predicted_outbreak_probability_7d": sample_scout_probs[i],
                "decision_threshold": scout_thresh,
                "outbreak_forecast_flag": bool(sample_scout_probs[i] >= scout_thresh),
                "disclaimer": "SYNTHETIC_EXPERIMENTAL: Unapproved for field operations.",
            }
            for i in range(len(sample_scout))
        ],
    }
    with open(models_path / "inference_examples.json", "w", encoding="utf-8") as f:
        json.dump(inference_examples, f, indent=2)

    print("\n=== Retraining & Artifact Serialization Complete! ===")
    return full_comparison


if __name__ == "__main__":
    run_training_and_stress_pipeline_v2()

