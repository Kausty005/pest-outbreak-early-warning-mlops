"""Reproducible, leakage-free training, evaluation, and MLflow tracking pipeline."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .dataset import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    DatasetSplits,
    SplitMetadata,
    chronological_split,
    load_and_validate_dataset,
    verify_no_leakage,
)
from .evaluate import (
    EvaluationMetrics,
    evaluate_predictions,
    find_optimal_threshold,
    plot_confusion_matrix,
)
from .preprocessor import build_model_pipeline

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


@dataclass
class PipelineConfig:
    data_path: str = "data/synthetic_multicrop_pest_forecasting.csv"
    artifacts_dir: str = "models/pest_outbreak_forecasting"
    root_model_path: str = "models/synthetic_pest_outbreak_forecaster.joblib"
    summary_doc_path: str = "data/synthetic_multicrop_pest_forecasting_summary.md"
    random_seed: int = 42
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    purge_days: int = 7
    mlflow_experiment: str = "AgriAdapt_Synthetic_Pest_Outbreak_Forecasting"
    mlflow_enabled: bool = True
    quick: bool = False


@dataclass
class ModelResult:
    model_name: str
    pipeline: Pipeline
    val_metrics: EvaluationMetrics
    val_metrics_tuned: EvaluationMetrics | None
    optimal_threshold: float
    training_seconds: float
    test_metrics: EvaluationMetrics | None = None
    test_metrics_tuned: EvaluationMetrics | None = None


def get_candidate_models(config: PipelineConfig) -> dict[str, Any]:
    """Define candidate estimators adhering to reproducible random seeds."""
    seed = config.random_seed
    quick = config.quick

    return {
        "Baseline_Dummy": DummyClassifier(strategy="most_frequent"),
        "Logistic_Regression": LogisticRegression(
            class_weight="balanced",
            max_iter=300 if quick else 1000,
            random_state=seed,
            solver="lbfgs",
        ),
        "Random_Forest": RandomForestClassifier(
            n_estimators=40 if quick else 120,
            max_depth=12 if quick else 16,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=seed,
            n_jobs=-1,
        ),
        "Hist_Gradient_Boosting": HistGradientBoostingClassifier(
            max_iter=50 if quick else 120,
            max_depth=8 if quick else 12,
            min_samples_leaf=20,
            class_weight="balanced",
            random_state=seed,
        ),
    }


def compute_feature_importances(
    pipeline: Pipeline,
    feature_names: list[str],
    top_n: int = 15,
) -> pd.DataFrame:
    """Extract top feature importances from linear or tree-based pipelines."""
    classifier = pipeline.named_steps["classifier"]
    preprocessor = pipeline.named_steps["preprocessor"]

    try:
        transformed_names = list(preprocessor.get_feature_names_out())
    except Exception:
        transformed_names = feature_names

    importances = None
    if hasattr(classifier, "feature_importances_"):
        importances = classifier.feature_importances_
    elif hasattr(classifier, "coef_"):
        importances = np.abs(classifier.coef_[0])

    if importances is not None and len(importances) == len(transformed_names):
        df_imp = pd.DataFrame(
            {"feature": transformed_names, "importance": importances}
        ).sort_values("importance", ascending=False)
        return df_imp.head(top_n)

    return pd.DataFrame()


def run_training_pipeline(config: PipelineConfig | None = None) -> dict[str, Any]:
    """
    Execute end-to-end reproducible training, validation model selection,
    single test evaluation, artifact saving, and MLflow tracking.
    """
    if config is None:
        config = PipelineConfig()

    LOGGER.info("Starting AgriAdapt AI Synthetic Pest Outbreak Training Pipeline...")
    np.random.seed(config.random_seed)

    # 1. Load and strictly validate dataset
    df = load_and_validate_dataset(config.data_path)
    LOGGER.info("Dataset successfully loaded: %d rows, %d columns", len(df), len(df.columns))

    # 2. Chronological split with 7-day purging / embargo
    splits, split_meta = chronological_split(
        df,
        train_ratio=config.train_ratio,
        val_ratio=config.val_ratio,
        purge_days=config.purge_days,
    )
    LOGGER.info(
        "Chronological splits created: Train=%d (%s to %s), Val=%d (%s to %s), Test=%d (%s to %s), Purged=%d",
        len(splits.X_train),
        split_meta.train_start_date,
        split_meta.train_end_date,
        len(splits.X_val),
        split_meta.val_start_date,
        split_meta.val_end_date,
        len(splits.X_test),
        split_meta.test_start_date,
        split_meta.test_end_date,
        split_meta.total_purged_count,
    )

    # 3. Setup MLflow
    mlflow_active = False
    if config.mlflow_enabled:
        try:
            import mlflow
            mlflow.set_experiment(config.mlflow_experiment)
            mlflow_active = True
            LOGGER.info("MLflow active. Experiment: %s", config.mlflow_experiment)
        except Exception as exc:
            LOGGER.warning("Could not initialize MLflow: %s. Continuing locally.", exc)

    artifacts_path = Path(config.artifacts_dir)
    artifacts_path.mkdir(parents=True, exist_ok=True)

    # 4. Train candidates and evaluate on Validation set
    candidate_estimators = get_candidate_models(config)
    results: dict[str, ModelResult] = {}

    for name, estimator in candidate_estimators.items():
        LOGGER.info("Training candidate model: %s...", name)
        pipe = build_model_pipeline(estimator)

        t_start = time.time()
        pipe.fit(splits.X_train, splits.y_train)
        duration = time.time() - t_start

        # Validation prediction
        if hasattr(pipe, "predict_proba"):
            val_probs = pipe.predict_proba(splits.X_val)[:, 1]
        else:
            val_probs = None

        val_preds_default = pipe.predict(splits.X_val)
        val_metrics_default = evaluate_predictions(
            y_true=splits.y_val,
            y_pred=val_preds_default,
            y_prob=val_probs,
            model_name=name,
            split_name="validation",
            threshold=0.50,
        )

        # Threshold tuning on validation set only
        opt_thresh = 0.50
        val_metrics_tuned = None
        if val_probs is not None and name != "Baseline_Dummy":
            opt_thresh, _ = find_optimal_threshold(splits.y_val.values, val_probs, metric="f1")
            val_preds_tuned = (val_probs >= opt_thresh).astype(int)
            val_metrics_tuned = evaluate_predictions(
                y_true=splits.y_val,
                y_pred=val_preds_tuned,
                y_prob=val_probs,
                model_name=f"{name}_Tuned",
                split_name="validation",
                threshold=opt_thresh,
            )

        results[name] = ModelResult(
            model_name=name,
            pipeline=pipe,
            val_metrics=val_metrics_default,
            val_metrics_tuned=val_metrics_tuned,
            optimal_threshold=opt_thresh,
            training_seconds=round(duration, 2),
        )

        LOGGER.info(
            "[%s] Val PR-AUC: %.4f | Val F1: %.4f | Optimal Thresh: %.2f",
            name,
            val_metrics_default.pr_auc,
            val_metrics_default.f1,
            opt_thresh,
        )

    # 5. Select Best Model based on Validation PR-AUC (Average Precision) and F1
    # PR-AUC evaluates ranking across all positive-class thresholds on imbalanced data.
    def ranking_score(res: ModelResult) -> float:
        return res.val_metrics.pr_auc + (res.val_metrics_tuned.f1 if res.val_metrics_tuned else res.val_metrics.f1)

    winner_name = max(results.keys(), key=lambda k: ranking_score(results[k]))
    winner = results[winner_name]
    LOGGER.info("Winner selected based on validation performance: %s", winner_name)

    # 6. Evaluate selected model ONCE on the held-out Test set
    test_probs = None
    if hasattr(winner.pipeline, "predict_proba"):
        test_probs = winner.pipeline.predict_proba(splits.X_test)[:, 1]

    # Test at default 0.50
    test_preds_default = winner.pipeline.predict(splits.X_test)
    winner.test_metrics = evaluate_predictions(
        y_true=splits.y_test,
        y_pred=test_preds_default,
        y_prob=test_probs,
        model_name=winner_name,
        split_name="test",
        threshold=0.50,
    )

    # Test at validation-tuned threshold
    if test_probs is not None and winner.optimal_threshold != 0.50:
        test_preds_tuned = (test_probs >= winner.optimal_threshold).astype(int)
        winner.test_metrics_tuned = evaluate_predictions(
            y_true=splits.y_test,
            y_pred=test_preds_tuned,
            y_prob=test_probs,
            model_name=f"{winner_name}_Tuned",
            split_name="test",
            threshold=winner.optimal_threshold,
        )

    LOGGER.info(
        "Selected Model Test Results [%s]: PR-AUC=%.4f | ROC-AUC=%.4f | F1=%.4f (Default) | F1=%.4f (Tuned)",
        winner_name,
        winner.test_metrics.pr_auc,
        winner.test_metrics.roc_auc,
        winner.test_metrics.f1,
        winner.test_metrics_tuned.f1 if winner.test_metrics_tuned else winner.test_metrics.f1,
    )

    # 7. Generate and save artifacts
    cm_val = np.array([
        [winner.val_metrics.true_negatives, winner.val_metrics.false_positives],
        [winner.val_metrics.false_negatives, winner.val_metrics.true_positives],
    ])
    cm_val_path = artifacts_path / "confusion_matrix_val_selected.png"
    plot_confusion_matrix(cm_val, winner_name, "validation", cm_val_path)

    cm_test = np.array([
        [winner.test_metrics.true_negatives, winner.test_metrics.false_positives],
        [winner.test_metrics.false_negatives, winner.test_metrics.true_positives],
    ])
    cm_test_path = artifacts_path / "confusion_matrix_test_selected.png"
    plot_confusion_matrix(cm_test, winner_name, "test", cm_test_path)

    # Feature importance
    df_importance = compute_feature_importances(winner.pipeline, FEATURE_COLUMNS)
    importance_csv_path = artifacts_path / "feature_importance.csv"
    if not df_importance.empty:
        df_importance.to_csv(importance_csv_path, index=False)

    # Save model artifacts (both in dedicated directory and suggested root location)
    model_artifact_path = artifacts_path / "synthetic_pest_outbreak_forecaster.joblib"
    joblib.dump(winner.pipeline, model_artifact_path)
    LOGGER.info("Saved winner pipeline to %s", model_artifact_path)

    root_model_path = Path(config.root_model_path)
    root_model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(winner.pipeline, root_model_path)
    LOGGER.info("Saved copy to suggested root artifact path: %s", root_model_path)

    # Generate Model Comparison Report
    comparison_md_path = artifacts_path / "model_comparison_report.md"
    report_content = _build_comparison_report(
        results=results,
        winner_name=winner_name,
        split_meta=split_meta,
        config=config,
    )
    comparison_md_path.write_text(report_content, encoding="utf-8")

    # Generate metadata JSON
    metadata_json_path = artifacts_path / "model_metadata.json"
    meta_dict = {
        "pipeline_name": "AgriAdapt_Synthetic_Pest_Outbreak_Forecasting",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "winner_model": winner_name,
        "optimal_threshold": winner.optimal_threshold,
        "random_seed": config.random_seed,
        "dataset_rows": len(df),
        "split_metadata": asdict(split_meta),
        "feature_columns": FEATURE_COLUMNS,
        "val_metrics": winner.val_metrics.to_dict(),
        "val_metrics_tuned": winner.val_metrics_tuned.to_dict() if winner.val_metrics_tuned else None,
        "test_metrics": winner.test_metrics.to_dict(),
        "test_metrics_tuned": winner.test_metrics_tuned.to_dict() if winner.test_metrics_tuned else None,
    }
    metadata_json_path.write_text(json.dumps(meta_dict, indent=2), encoding="utf-8")

    # 8. MLflow Logging
    if mlflow_active:
        _log_to_mlflow(
            results=results,
            winner_name=winner_name,
            split_meta=split_meta,
            config=config,
            artifacts_path=artifacts_path,
        )

    LOGGER.info("AgriAdapt AI Pest Outbreak Forecasting Pipeline completed successfully.")
    return {
        "winner_model": winner_name,
        "optimal_threshold": winner.optimal_threshold,
        "split_metadata": asdict(split_meta),
        "model_artifact_path": str(model_artifact_path),
        "root_model_path": str(root_model_path),
        "metadata_json_path": str(metadata_json_path),
        "comparison_report_path": str(comparison_md_path),
        "results": {k: v.val_metrics.to_dict() for k, v in results.items()},
        "test_metrics": winner.test_metrics.to_dict(),
        "test_metrics_tuned": winner.test_metrics_tuned.to_dict() if winner.test_metrics_tuned else None,
    }


def _build_comparison_report(
    results: dict[str, ModelResult],
    winner_name: str,
    split_meta: SplitMetadata,
    config: PipelineConfig,
) -> str:
    """Build markdown report comparing models."""
    winner = results[winner_name]
    lines = [
        "# AgriAdapt AI — Synthetic Pest Outbreak Forecaster Model Comparison",
        "",
        "> [!IMPORTANT]",
        "> **SYNTHETIC DATA DISCLAIMER**",
        "> All training and evaluation results are based on entirely synthetic agricultural data.",
        "> They demonstrate pipeline functionality and performance on simulated assumptions only.",
        "> They do not establish real-world pest outbreak forecasting accuracy and must not be used",
        "> for operational farm advisories.",
        "",
        "## 1. Dataset Chronological Partitions & Purge Strategy",
        "",
        f"- **Train Set**: {split_meta.train_count:,} records ({split_meta.train_start_date} to {split_meta.train_end_date}) — Outbreak rate: {split_meta.train_outbreak_rate*100:.2f}%",
        f"- **Gap 1 (Purged)**: {split_meta.purged_gap1_count:,} records (7-day embargo preventing train target forward overlap into validation)",
        f"- **Validation Set**: {split_meta.val_count:,} records ({split_meta.val_start_date} to {split_meta.val_end_date}) — Outbreak rate: {split_meta.val_outbreak_rate*100:.2f}%",
        f"- **Gap 2 (Purged)**: {split_meta.purged_gap2_count:,} records (7-day embargo preventing validation target forward overlap into test)",
        f"- **Test Set (Held-Out)**: {split_meta.test_count:,} records ({split_meta.test_start_date} to {split_meta.test_end_date}) — Outbreak rate: {split_meta.test_outbreak_rate*100:.2f}%",
        "",
        "## 2. Validation Set Model Comparison",
        "",
        "| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | Train Sec | False Alarms (FP) | Missed Outbreaks (FN) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for name, res in results.items():
        vm = res.val_metrics
        lines.append(
            f"| **{name}** | {vm.accuracy:.4f} | {vm.precision:.4f} | {vm.recall:.4f} | "
            f"{vm.f1:.4f} | {vm.roc_auc:.4f} | {vm.pr_auc:.4f} | {res.training_seconds}s | "
            f"{vm.false_positives:,} | {vm.false_negatives:,} |"
        )

    lines.extend([
        "",
        "## 3. Selected Model Test Performance",
        "",
        f"- **Selected Winner**: `{winner_name}`",
        f"- **Optimal Decision Threshold (tuned strictly on Validation)**: `{winner.optimal_threshold:.2f}`",
        "",
        "| Metric | Default Threshold (0.50) | Tuned Threshold |",
        "| :--- | :---: | :---: |",
        f"| **Accuracy** | {winner.test_metrics.accuracy:.4f} | {winner.test_metrics_tuned.accuracy if winner.test_metrics_tuned else winner.test_metrics.accuracy:.4f} |",
        f"| **Precision** | {winner.test_metrics.precision:.4f} | {winner.test_metrics_tuned.precision if winner.test_metrics_tuned else winner.test_metrics.precision:.4f} |",
        f"| **Recall** | {winner.test_metrics.recall:.4f} | {winner.test_metrics_tuned.recall if winner.test_metrics_tuned else winner.test_metrics.recall:.4f} |",
        f"| **F1-Score** | {winner.test_metrics.f1:.4f} | {winner.test_metrics_tuned.f1 if winner.test_metrics_tuned else winner.test_metrics.f1:.4f} |",
        f"| **ROC-AUC** | {winner.test_metrics.roc_auc:.4f} | {winner.test_metrics_tuned.roc_auc if winner.test_metrics_tuned else winner.test_metrics.roc_auc:.4f} |",
        f"| **PR-AUC** | {winner.test_metrics.pr_auc:.4f} | {winner.test_metrics_tuned.pr_auc if winner.test_metrics_tuned else winner.test_metrics.pr_auc:.4f} |",
        f"| **False Alarms (FP)** | {winner.test_metrics.false_positives:,} | {winner.test_metrics_tuned.false_positives if winner.test_metrics_tuned else winner.test_metrics.false_positives:,} |",
        f"| **Missed Outbreaks (FN)** | {winner.test_metrics.false_negatives:,} | {winner.test_metrics_tuned.false_negatives if winner.test_metrics_tuned else winner.test_metrics.false_negatives:,} |",
        "",
        "## 4. Operational Risk Trade-off Rationale",
        "",
        "- **False Negatives (Missed Outbreaks)**: Represents the most severe risk in agriculture, as untreated outbreaks cause widespread crop failure and severe economic losses to farmers.",
        "- **False Positives (Unnecessary Alerts)**: Represents unnecessary chemical spray cost, labor expenditure, and potential pesticide residue or environmental impact.",
        f"- Tuning the decision threshold on validation data allowed calibrating recall and precision to balance early warning coverage against excessive false alarms.",
    ])

    return "\n".join(lines)


def _log_to_mlflow(
    results: dict[str, ModelResult],
    winner_name: str,
    split_meta: SplitMetadata,
    config: PipelineConfig,
    artifacts_path: Path,
) -> None:
    """Log parameters, metrics, plots, and models to MLflow."""
    import mlflow

    winner = results[winner_name]

    with mlflow.start_run(run_name=f"Forecasting_{winner_name}"):
        # 1. Parameters
        mlflow.log_params({
            "selected_model": winner_name,
            "feature_count": len(FEATURE_COLUMNS),
            "feature_list": ",".join(FEATURE_COLUMNS),
            "dataset_filename": Path(config.data_path).name,
            "random_seed": config.random_seed,
            "purge_days": config.purge_days,
            "total_purged_samples": split_meta.total_purged_count,
            "train_start_date": split_meta.train_start_date,
            "train_end_date": split_meta.train_end_date,
            "train_samples": split_meta.train_count,
            "val_start_date": split_meta.val_start_date,
            "val_end_date": split_meta.val_end_date,
            "val_samples": split_meta.val_count,
            "test_start_date": split_meta.test_start_date,
            "test_end_date": split_meta.test_end_date,
            "test_samples": split_meta.test_count,
            "optimal_threshold": winner.optimal_threshold,
        })

        # 2. Metrics for Winner
        val_m = winner.val_metrics
        mlflow.log_metrics({
            "val_accuracy": val_m.accuracy,
            "val_precision": val_m.precision,
            "val_recall": val_m.recall,
            "val_f1": val_m.f1,
            "val_roc_auc": val_m.roc_auc,
            "val_pr_auc": val_m.pr_auc,
            "val_false_positives": val_m.false_positives,
            "val_false_negatives": val_m.false_negatives,
        })

        if winner.val_metrics_tuned:
            vm_t = winner.val_metrics_tuned
            mlflow.log_metrics({
                "val_tuned_precision": vm_t.precision,
                "val_tuned_recall": vm_t.recall,
                "val_tuned_f1": vm_t.f1,
            })

        if winner.test_metrics:
            tm = winner.test_metrics
            mlflow.log_metrics({
                "test_accuracy": tm.accuracy,
                "test_precision": tm.precision,
                "test_recall": tm.recall,
                "test_f1": tm.f1,
                "test_roc_auc": tm.roc_auc,
                "test_pr_auc": tm.pr_auc,
                "test_false_positives": tm.false_positives,
                "test_false_negatives": tm.false_negatives,
            })

        if winner.test_metrics_tuned:
            tm_t = winner.test_metrics_tuned
            mlflow.log_metrics({
                "test_tuned_precision": tm_t.precision,
                "test_tuned_recall": tm_t.recall,
                "test_tuned_f1": tm_t.f1,
            })

        # 3. Log Artifacts
        for art in [
            artifacts_path / "model_comparison_report.md",
            artifacts_path / "model_metadata.json",
            artifacts_path / "confusion_matrix_val_selected.png",
            artifacts_path / "confusion_matrix_test_selected.png",
            artifacts_path / "feature_importance.csv",
            Path(config.summary_doc_path),
        ]:
            if art.exists():
                mlflow.log_artifact(str(art), artifact_path="evaluation")

        # 4. Log Sklearn Model Pipeline
        try:
            mlflow.sklearn.log_model(
                sk_model=winner.pipeline,
                artifact_path="model",
            )
        except Exception as exc:
            LOGGER.warning("Could not log model to MLflow via log_model: %s", exc)
