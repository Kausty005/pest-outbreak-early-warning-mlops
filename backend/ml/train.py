"""Reproducible, leakage-safe experiment runner for crop recommendation."""
from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split

from .data_validation import FEATURE_COLUMNS, TARGET_COLUMN, load_valid_dataset
from .evaluate import classification_metrics, feature_importance
from .feature_engineering import FeatureConfig, make_model_pipeline
from .model_registry import promote_candidate, stage_candidate, sha256_file
from .xgboost_model import LabelEncodedClassifier

LOGGER = logging.getLogger(__name__)
RANDOM_SEED = 42


@dataclass(frozen=True)
class TrainingConfig:
    test_size: float = 0.2
    random_seed: int = RANDOM_SEED
    cv_folds: int = 5
    parallel_jobs: int = 1
    model_names: tuple[str, ...] = ("random_forest", "extra_trees", "xgboost")
    quick: bool = False
    promote: bool = False
    min_macro_f1: float = 0.90
    min_f1_improvement: float = 0.0
    mlflow_enabled: bool = False
    mlflow_tracking_uri: str | None = None
    mlflow_experiment: str = "crop-recommendation"
    mlflow_register_model: bool = False


@dataclass
class CandidateResult:
    configuration: str
    model_name: str
    cv_macro_f1_mean: float
    cv_macro_f1_std: float
    best_params: dict[str, Any]
    training_seconds: float
    model_size_bytes: int
    test_metrics: dict[str, Any]
    pipeline: Any = field(repr=False)

    def summary(self) -> dict[str, Any]:
        return {
            "configuration": self.configuration,
            "model": self.model_name,
            "cv_macro_f1_mean": self.cv_macro_f1_mean,
            "cv_macro_f1_std": self.cv_macro_f1_std,
            "best_params": self.best_params,
            "training_seconds": self.training_seconds,
            "model_size_bytes": self.model_size_bytes,
            "test_metrics": self.test_metrics,
        }


def _model_definitions(quick: bool) -> dict[str, tuple[Any, dict[str, list[Any]]]]:
    estimators: dict[str, tuple[Any, dict[str, list[Any]]]] = {
        "random_forest": (
            RandomForestClassifier(random_state=RANDOM_SEED, n_jobs=-1, class_weight=None),
            {
                "model__n_estimators": [40] if quick else [200],
                "model__max_depth": [None, 20],
                "model__min_samples_leaf": [1] if quick else [1, 2],
            },
        ),
        "extra_trees": (
            ExtraTreesClassifier(random_state=RANDOM_SEED, n_jobs=-1, class_weight=None),
            {
                "model__n_estimators": [40] if quick else [200],
                "model__max_depth": [None, 20],
                "model__min_samples_leaf": [1] if quick else [1, 2],
            },
        ),
    }
    try:
        from xgboost import XGBClassifier

        estimators["xgboost"] = (
            LabelEncodedClassifier(
                XGBClassifier(
                    random_state=RANDOM_SEED,
                    n_estimators=50 if quick else 200,
                    n_jobs=-1,
                    eval_metric="mlogloss",
                    tree_method="hist",
                )
            ),
            {
                "model__estimator__max_depth": [4] if quick else [4, 6],
                "model__estimator__learning_rate": [0.1] if quick else [0.05, 0.1],
                "model__estimator__subsample": [1.0],
            },
        )
    except ImportError:
        LOGGER.info("xgboost is not installed; skipping optional model comparison")
    return estimators


def _serialize_size_bytes(value: Any) -> int:
    from io import BytesIO

    buffer = BytesIO()
    joblib.dump(value, buffer)
    return buffer.tell()


def train_from_dataframe(
    frame: pd.DataFrame,
    audit: dict[str, Any],
    config: TrainingConfig | None = None,
) -> tuple[CandidateResult, list[CandidateResult], dict[str, Any]]:
    """Tune on stratified folds of training data and only then assess the held-out test set."""
    config = config or TrainingConfig()
    X = frame[FEATURE_COLUMNS]
    y = frame[TARGET_COLUMN]
    class_counts = y.value_counts()
    if class_counts.min() < max(2, config.cv_folds):
        raise ValueError("Every class needs at least cv_folds observations for stratified cross-validation")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.test_size, stratify=y, random_state=config.random_seed
    )
    cv = StratifiedKFold(n_splits=config.cv_folds, shuffle=True, random_state=config.random_seed)
    definitions = _model_definitions(config.quick)
    selected_names = [name for name in config.model_names if name in definitions]
    if not selected_names:
        raise ValueError("No requested model is available")

    all_results: list[CandidateResult] = []
    for feature_label, feature_config in (
        ("baseline", FeatureConfig(enabled=False)),
        ("engineered", FeatureConfig(enabled=True)),
    ):
        for model_name in selected_names:
            estimator, grid = definitions[model_name]
            search = GridSearchCV(
                estimator=make_model_pipeline(estimator, feature_config),
                param_grid=grid,
                scoring="f1_macro",
                cv=cv,
                # One process by default keeps the pipeline portable in constrained CI
                # environments. Operators may opt into parallel CV explicitly.
                n_jobs=config.parallel_jobs,
                refit=True,
                return_train_score=False,
            )
            started = time.perf_counter()
            search.fit(X_train, y_train)
            seconds = time.perf_counter() - started
            prediction = search.best_estimator_.predict(X_test)
            labels = [str(value) for value in search.best_estimator_.classes_]
            all_results.append(
                CandidateResult(
                    configuration=feature_label,
                    model_name=model_name,
                    cv_macro_f1_mean=float(search.best_score_),
                    cv_macro_f1_std=float(search.cv_results_["std_test_score"][search.best_index_]),
                    best_params={key: _json_safe(value) for key, value in search.best_params_.items()},
                    training_seconds=round(seconds, 4),
                    model_size_bytes=_serialize_size_bytes(search.best_estimator_),
                    test_metrics=classification_metrics(y_test, prediction, labels),
                    pipeline=search.best_estimator_,
                )
            )
    winner = max(all_results, key=lambda result: result.cv_macro_f1_mean)
    split = {
        "method": "stratified_train_test_split",
        "random_seed": config.random_seed,
        "test_size": config.test_size,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "cv_folds": config.cv_folds,
    }
    return winner, all_results, split


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    return value


def _comparison_markdown(metadata: dict[str, Any]) -> str:
    rows = [
        "# Model comparison and evaluation",
        "",
        "The winner was selected by mean macro F1 on training-only stratified CV. Held-out test metrics are reported for assessment and were not used as the selection rule.",
        "",
        "| Configuration | Model | CV macro F1 | Held-out macro F1 | Accuracy | Training seconds | Model bytes |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for result in metadata["comparison"]:
        metric = result["test_metrics"]
        rows.append(
            f"| {result['configuration']} | {result['model']} | {result['cv_macro_f1_mean']:.4f} | "
            f"{metric['macro_f1']:.4f} | {metric['accuracy']:.4f} | {result['training_seconds']:.2f} | {result['model_size_bytes']} |"
        )
    rows.extend(
        [
            "",
            "## Selected candidate",
            "",
            f"- Version: `{metadata['model_version']}`",
            f"- Model: `{metadata['selected_model']['model']}`",
            f"- Feature configuration: `{metadata['selected_model']['configuration']}`",
            f"- Held-out macro F1: `{metadata['evaluation_metrics']['macro_f1']:.4f}`",
            "",
            "Model scores exposed by the API are classifier scores, not independently calibrated real-world crop-success probabilities.",
        ]
    )
    return "\n".join(rows) + "\n"


def _log_to_mlflow(metadata: dict[str, Any], artifacts_dir: Path, config: TrainingConfig, pipeline: Any) -> None:
    if not config.mlflow_enabled:
        return
    try:
        import mlflow
        import mlflow.sklearn
    except ImportError:
        LOGGER.warning("MLflow was requested but is unavailable; continuing without MLflow logging")
        metadata["mlflow"] = {"status": "unavailable", "reason": "mlflow package not installed"}
        return

    tracking_uri = (
        config.mlflow_tracking_uri
        or os.getenv("MLFLOW_TRACKING_URI")
        or str((PROJECT_ROOT / "mlruns").resolve() if "PROJECT_ROOT" in globals() else (artifacts_dir.parent / "mlruns").resolve())
    )
    # Ensure local filesystem paths (especially Windows drive paths like C:\) use standard file:// URI
    if not (
        tracking_uri.startswith("http://")
        or tracking_uri.startswith("https://")
        or tracking_uri.startswith("file:")
        or tracking_uri.startswith("sqlite:")
        or tracking_uri.startswith("postgresql:")
        or tracking_uri.startswith("mysql:")
    ):
        tracking_uri = Path(tracking_uri).resolve().as_uri()

    try:
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(config.mlflow_experiment)
        with mlflow.start_run(run_name=metadata["model_version"]) as run:
            mlflow.log_params(
                {
                    "selected_model": metadata["selected_model"]["model"],
                    "feature_configuration": metadata["selected_model"]["configuration"],
                    "dataset_checksum": metadata["dataset"]["checksum_sha256"],
                    "cv_folds": metadata["split"]["cv_folds"],
                    "test_size": config.test_size,
                    "random_seed": config.random_seed,
                }
            )
            mlflow.log_metrics(
                {
                    "test_accuracy": metadata["evaluation_metrics"]["accuracy"],
                    "test_macro_f1": metadata["evaluation_metrics"]["macro_f1"],
                    "test_weighted_f1": metadata["evaluation_metrics"]["weighted_f1"],
                    "cv_macro_f1_mean": metadata["selected_model"]["cv_macro_f1_mean"],
                    "cv_macro_f1_std": metadata["selected_model"]["cv_macro_f1_std"],
                }
            )
            for name in ("metadata.json", "evaluation_report.md", "crop_model.joblib"):
                p = artifacts_dir / name
                if p.exists():
                    mlflow.log_artifact(str(p))
            mlflow.sklearn.log_model(pipeline, artifact_path="model")
            if config.mlflow_register_model:
                try:
                    mlflow.register_model(f"runs:/{run.info.run_id}/model", "crop-recommendation")
                except Exception as reg_exc:
                    LOGGER.warning("MLflow model registry candidate registration warning: %s", reg_exc)

            metadata["mlflow"] = {
                "status": "tracked",
                "run_id": run.info.run_id,
                "tracking_uri": tracking_uri,
                "experiment": config.mlflow_experiment,
            }
            LOGGER.info("MLflow run %s logged successfully to %s", run.info.run_id, tracking_uri)
    except Exception as exc:
        LOGGER.warning("MLflow logging failed: %s", exc)
        metadata["mlflow"] = {"status": "failed", "error": str(exc), "tracking_uri": tracking_uri}


def run_training(
    dataset_path: str | Path,
    artifacts_dir: str | Path,
    config: TrainingConfig | None = None,
) -> dict[str, Any]:
    config = config or TrainingConfig()
    frame, audit = load_valid_dataset(dataset_path)
    winner, comparison, split = train_from_dataframe(frame, audit.to_dict(), config)
    artifacts = Path(artifacts_dir)
    artifacts.mkdir(parents=True, exist_ok=True)
    created = datetime.now(timezone.utc)
    checksum_short = (audit.checksum_sha256 or "unknown")[:12]
    model_version = f"crop-{created.strftime('%Y%m%dT%H%M%SZ')}-{checksum_short}"
    selected = winner.summary()
    metadata = {
        "model_version": model_version,
        "created_at": created.isoformat(),
        "training_dataset": str(Path(dataset_path).resolve()),
        "dataset": audit.to_dict(),
        "feature_schema": {"input_features": FEATURE_COLUMNS, "feature_order": FEATURE_COLUMNS},
        "preprocessing_configuration": FeatureConfig(enabled=winner.configuration == "engineered").to_dict(),
        "class_labels": [str(label) for label in winner.pipeline.classes_],
        "split": split,
        "selected_model": {key: value for key, value in selected.items() if key not in {"test_metrics"}},
        "evaluation_metrics": winner.test_metrics,
        "feature_importance": feature_importance(winner.pipeline),
        "comparison": [result.summary() for result in comparison],
        "runtime": {"python": platform.python_version()},
        "deployment_status": "candidate",
    }

    report_md = _comparison_markdown(metadata)

    # 1. Stage candidate safely in candidates/<model_version>/
    candidate_dir = stage_candidate(artifacts, winner.pipeline, metadata, report_md)
    metadata["candidate_dir"] = str(candidate_dir)
    metadata["artifact_sha256"] = sha256_file(candidate_dir / "crop_model.joblib")

    # 2. Check if candidate should be promoted to production
    prod_exists = (artifacts / "crop_model.joblib").exists()
    should_promote = config.promote or (not prod_exists)

    if should_promote:
        try:
            promote_candidate(
                artifact_dir=artifacts,
                candidate_metadata=metadata,
                candidate_source_dir=candidate_dir,
                min_macro_f1=config.min_macro_f1,
                min_macro_f1_improvement=config.min_f1_improvement,
            )
            metadata["deployment_status"] = "production"
            LOGGER.info("Candidate %s promoted to production.", model_version)
        except Exception as exc:
            LOGGER.warning("Candidate promotion skipped/rejected: %s", exc)
            metadata["deployment_status"] = "candidate"
            metadata["promotion_error"] = str(exc)
            if not prod_exists:
                raise
    else:
        metadata["deployment_status"] = "candidate"
        LOGGER.info("Candidate %s staged. Production model retained without overwrite.", model_version)

    _log_to_mlflow(metadata, artifacts if should_promote else candidate_dir, config, winner.pipeline)
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="Path to Crop_recommendation.csv")
    parser.add_argument("--artifacts-dir", default="backend/artifacts", help="Destination for model artifacts")
    parser.add_argument("--quick", action="store_true", help="Use smaller grids for CI or smoke testing")
    parser.add_argument("--promote", action="store_true", help="Promote candidate to production if validation gates pass")
    parser.add_argument("--min-macro-f1", type=float, default=0.90, help="Minimum macro F1 required for promotion")
    parser.add_argument("--min-f1-improvement", type=float, default=0.0, help="Required macro F1 improvement over deployed model")
    parser.add_argument("--mlflow", action="store_true", help="Log enabled run to the configured MLflow tracking URI")
    parser.add_argument("--mlflow-tracking-uri", default=None, help="MLflow tracking URI (default: local mlruns)")
    parser.add_argument(
        "--register-mlflow",
        action="store_true",
        help="Register the MLflow artifact as a candidate; does not promote it to production",
    )
    parser.add_argument("--cv-folds", type=int, default=5)
    parser.add_argument("--jobs", type=int, default=1, help="Parallel cross-validation jobs (default: 1)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    metadata = run_training(
        args.dataset,
        args.artifacts_dir,
        TrainingConfig(
            quick=args.quick,
            promote=args.promote,
            min_macro_f1=args.min_macro_f1,
            min_f1_improvement=args.min_f1_improvement,
            cv_folds=args.cv_folds,
            parallel_jobs=args.jobs,
            mlflow_enabled=args.mlflow,
            mlflow_tracking_uri=args.mlflow_tracking_uri,
            mlflow_register_model=args.register_mlflow,
        ),
    )
    print(json.dumps(metadata, indent=2, default=_json_safe))


if __name__ == "__main__":
    main()
