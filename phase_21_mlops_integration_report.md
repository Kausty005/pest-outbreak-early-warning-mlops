# Phase 21 — Core Pest Forecasting MLOps Integration Report

**Project:** AgriAdapt AI / Pest Outbreak Early Warning MLOps System  
**Phase:** 21 — Core Pest Forecasting MLOps Integration  
**Date:** November 17, 2026  
**Status:** Completed & Verified  

---

## 1. Executive Summary

Phase 21 establishes an end-to-end, reproducible, experimental MLOps pipeline for Version 2.0 pest forecasting in AgriAdapt AI. Prior to this phase, Version 2.0 pest forecasting operated with manual training invocations, lacked MLflow tracking of training vs. validation vs. test splits, lacked DVC stage reproducibility for Version 2.0 artifacts, and was disconnected from automated candidate staging, SHA-256 integrity verification, versioned backup, and atomic rollback in the model registry.

During Phase 21, the following core MLOps components were integrated and strictly verified:
1. **MLflow Tracking Integration:** Integrated into `src/pest_forecasting/train_v2.py`. Simultaneously tracks `ENVIRONMENTAL_ONLY` and `SCOUTING_ASSISTED` experiments, logs model parameters, hyperparameters, and dataset SHA-256 checksums, separates training, validation, and test metrics (PR-AUC, F1, ROC-AUC, Precision, Recall, False Alarm Burden, False Positive Rate), and logs model pipelines and JSON artifacts.
2. **DVC Pipeline Stage:** Added `train_pest_forecasting_v2` to `dvc.yaml` tracking all 6 code and data dependencies and 9 model and evaluation outputs with explicit `cache: false` (to honor Git versioning of experimental assets), maintaining complete consistency with `dvc.lock`.
3. **Model Registry Integration:** Integrated pest candidate lifecycle management into `backend/ml/model_registry.py` with candidate staging, unique version generation (`pest-v2-<timestamp>-<hash>`), SHA-256 checksum verification, evaluation-based validation gates, automated backups, physical rollback, and ledger auditing.
4. **Strict Production Isolation:** Enforced hard blocking preventing synthetic-data-trained models from ever being promoted to production, preserving the 11 scientific readiness gate checks without compromise.
5. **Full System Verification:** Executed 205 backend tests (203 passed, 2 skipped due to optional PDFs, 0 failed) and all frontend tests (3 passed).

---

## 2. Files Created and Modified

### Modified Files:
1. `backend/ml/model_registry.py`:
   - Updated `validate_candidate` to reject any model trained on synthetic data or marked `is_synthetic: true` from production promotion.
   - Implemented `validate_pest_candidate`: enforces model version formatting, minimum validation PR-AUC thresholds (>= 0.70 for scouting, >= 0.50 for environmental), SHA-256 checksum verification against `checksums.sha256`, and blocks production promotion.
   - Implemented `stage_pest_candidate`: copies experimental artifacts into `models/candidates/<candidate_version>/`, computes SHA-256 hashes for all binaries and metadata, writes `checksums.sha256`, and writes `candidate_metadata.json`.
   - Implemented `promote_pest_experimental_candidate`: performs atomic promotion into `models/experimental/pest_forecasting/v2/`, creates a versioned backup of previous models into `models/backups/<prev_version>/`, and updates `models/pest_deployment_ledger.json`.
   - Implemented `rollback_pest_experimental`: physically restores model binaries and metadata from `models/backups/<target_version>` or `models/candidates/<target_version>`, verifies SHA-256 integrity post-restoration, and updates the deployment ledger.
   - Implemented `read_pest_ledger` and `_write_pest_ledger` helper utilities.

2. `src/pest_forecasting/train_v2.py`:
   - Added `_log_to_mlflow_v2` helper function: logs tags (`model_domain`, `feature_configuration`, `dataset_classification`, `is_production_ready: false`), parameters, hyperparameters, dataset SHA-256 checksum, separate training metrics (`train_*`), validation metrics (`val_*`), test metrics (`test_*`), and stress test metrics.
   - Added evaluation of training split metrics (`evaluate_predictions(y_train, y_train_pred, y_train_prob)`) to enable train vs. test generalization tracking.
   - Added `--quick` execution mode with stratified 5% sampling (`df.sample(frac=0.05, random_state=42).sort_values("date")`) ensuring chronological purge boundaries remain valid.
   - Added CLI arguments `--mlflow`, `--mlflow-tracking-uri`, `--mlflow-experiment`, `--register-candidate`, and `--promote-experimental`.
   - Connected post-training candidate staging and experimental promotion to `backend.ml.model_registry`.

3. `dvc.yaml`:
   - Added `train_pest_forecasting_v2` stage.
   - Registered dependencies:
     - `data/experimental/synthetic_pest_forecasting_v2.csv`
     - `src/pest_forecasting/dataset_v2.py`
     - `src/pest_forecasting/preprocessor_v2.py`
     - `src/pest_forecasting/evaluate.py`
     - `src/pest_forecasting/train_v2.py`
     - `backend/ml/model_registry.py`
   - Registered outputs (`cache: false`):
     - `models/experimental/pest_forecasting/v2/environmental_model_pipeline.joblib`
     - `models/experimental/pest_forecasting/v2/full_model_pipeline.joblib`
     - `models/experimental/pest_forecasting/v2/feature_schemas.json`
     - `models/experimental/pest_forecasting/v2/model_config.json`
     - `models/experimental/pest_forecasting/v2/partition_metadata.json`
     - `models/experimental/pest_forecasting/v2/synthetic_provenance_metadata.json`
     - `models/experimental/pest_forecasting/v2/stress_test_results.json`
     - `models/experimental/pest_forecasting/v2/experiment_comparison_summary.json`
     - `models/experimental/pest_forecasting/v2/inference_examples.json`

4. `dvc.lock`:
   - Updated with exact MD5 hashes for all dependencies and tracked outputs of the `train_pest_forecasting_v2` stage.

5. `tests/test_dvc_pipeline.py`:
   - Added assertions verifying that `train_pest_forecasting_v2` stage exists in `dvc.yaml`, contains all required dependencies, and declares the 9 output artifacts.

### Created Files:
1. `tests/test_pest_mlflow_tracking.py`:
   - 3 integration tests covering:
     - Training pipeline with MLflow tracking disabled (`test_pest_training_without_mlflow`).
     - Training pipeline with local MLflow tracking enabled (`test_pest_training_with_local_mlflow_tracking`), validating parameters, tags, separate train/val/test metrics, and artifacts across both experiment branches.
     - Fault-tolerance and honest failure logging when MLflow tracking server is unreachable (`test_pest_training_with_unreachable_mlflow_reports_honest_failure`).

2. `tests/test_pest_model_registry.py`:
   - 5 unit and integration tests covering:
     - Candidate staging and SHA-256 checksum calculation (`test_stage_pest_candidate_computes_sha256_checksums`).
     - Validation gate tamper detection via checksum mismatch (`test_validate_pest_candidate_checksum_tamper_detection`).
     - Validation gate minimum PR-AUC thresholds (`test_validate_pest_candidate_pr_auc_thresholds`).
     - Strict rejection of synthetic-data-trained models for production promotion (`test_strict_production_promotion_block_for_synthetic_models`).
     - Atomic experimental promotion with automatic backup and physical rollback (`test_experimental_promotion_with_automatic_backup_and_rollback`).

---

## 3. MLflow Implementation Details

### Experiment Tracking Architecture
The pest forecasting pipeline Version 2.0 (`src/pest_forecasting/train_v2.py`) trains two distinct model configurations:
1. `ENVIRONMENTAL_ONLY`: Uses only temperature, humidity, precipitation, wind, leaf wetness, and rolling aggregates. Does not require scouting data at inference time.
2. `SCOUTING_ASSISTED`: Ingests environmental features plus historical field scouting observations (past nymph/adult counts, damage indices, trap catches).

MLflow tracks both experiments under the experiment name (`pest-forecasting-v2` by default or user-specified `--mlflow-experiment`).

### Logged Metadata & Parameters
For each run, the pipeline records:
- **Tags:**
  - `model_domain`: `"pest_forecasting"`
  - `feature_configuration`: `"ENVIRONMENTAL_ONLY"` or `"SCOUTING_ASSISTED"`
  - `dataset_classification`: `"SYNTHETIC_EXPERIMENTAL_V2"`
  - `is_production_ready`: `"false"`
  - `pipeline_version`: `"2.0.0"`
- **Parameters:**
  - `model_type`: `"LogisticRegression"`
  - `random_seed`: `42`
  - `dataset_path`: Resolved dataset path
  - `dataset_checksum_sha256`: SHA-256 hash of the training dataset CSV
  - `train_samples`, `val_samples`, `test_samples`: Exact sample counts per split
  - Hyperparameters from `LogisticRegression` (`C`, `penalty`, `solver`, `max_iter`, `class_weight`)
  - `optimal_threshold`: Decision threshold calibrated on validation PR curve

### Separate Split Metrics
To monitor overfitting and generalization gaps, metrics are evaluated and logged separately for each partition:
- **Training Metrics:** `train_pr_auc`, `train_roc_auc`, `train_f1`, `train_precision`, `train_recall`, `train_brier_score`, `train_log_loss`
- **Validation Metrics:** `val_pr_auc`, `val_roc_auc`, `val_f1`, `val_precision`, `val_recall`, `val_brier_score`, `val_log_loss`
- **Test Metrics:** `test_pr_auc`, `test_roc_auc`, `test_f1`, `test_precision`, `test_recall`, `test_false_positive_rate`, `test_false_alarm_burden`, `test_brier_score`, `test_log_loss`
- **Stress Test Metrics:** `stress_test_extreme_weather_f1`, `stress_test_sparse_reporting_f1`

### Artifact Logging
For each run, MLflow persists:
- The serialized scikit-learn pipeline (`mlflow.sklearn.log_model`)
- `feature_schemas.json`
- `model_config.json`
- `partition_metadata.json`
- `synthetic_provenance_metadata.json`
- `experiment_comparison_summary.json`

### Error Resiliency
If MLflow is unreachable or fails during execution (e.g., misconfigured URI or server outage), the pipeline catches the exception, logs an explicit `"failed"` status and error message in the training summary dictionary, and safely completes model generation and local artifact writing without crashing.

---

## 4. DVC Pipeline Implementation Details

### Stage Specification in `dvc.yaml`
```yaml
  train_pest_forecasting_v2:
    cmd: python -m src.pest_forecasting.train_v2 --quick
    deps:
      - data/experimental/synthetic_pest_forecasting_v2.csv
      - src/pest_forecasting/dataset_v2.py
      - src/pest_forecasting/preprocessor_v2.py
      - src/pest_forecasting/evaluate.py
      - src/pest_forecasting/train_v2.py
      - backend/ml/model_registry.py
    outs:
      - models/experimental/pest_forecasting/v2/environmental_model_pipeline.joblib:
          cache: false
      - models/experimental/pest_forecasting/v2/full_model_pipeline.joblib:
          cache: false
      - models/experimental/pest_forecasting/v2/feature_schemas.json:
          cache: false
      - models/experimental/pest_forecasting/v2/model_config.json:
          cache: false
      - models/experimental/pest_forecasting/v2/partition_metadata.json:
          cache: false
      - models/experimental/pest_forecasting/v2/synthetic_provenance_metadata.json:
          cache: false
      - models/experimental/pest_forecasting/v2/stress_test_results.json:
          cache: false
      - models/experimental/pest_forecasting/v2/experiment_comparison_summary.json:
          cache: false
      - models/experimental/pest_forecasting/v2/inference_examples.json:
          cache: false
```

### Reproducibility & Integrity Notes
- **Dependencies:** All data sources, feature extraction logic, preprocessor modules, evaluation scripts, training orchestrator, and registry interfaces are registered as dependencies.
- **Outputs & `cache: false`:** Outputs are versioned directly in Git as experimental artifacts. Setting `cache: false` avoids duplicate storage and SCM tracking collisions.
- **Remote Storage Policy:** No fake DVC remotes are configured. DVC operates entirely through local tracking and lockfile hashes (`dvc.lock`).

---

## 5. Model Registry Integration Details

### Architecture & Lifecycle
The pest forecasting model lifecycle is managed in `backend/ml/model_registry.py`:

```
[Training Pipeline (train_v2.py)]
             │
             ▼
   [Stage Candidate]  ──> models/candidates/pest-v2-<ts>-<hash>/
             │            - Artifacts copied
             │            - checksums.sha256 generated
             │            - candidate_metadata.json written
             ▼
  [Validation Gate]   ──> Checks PR-AUC >= threshold
             │        ──> Re-computes & verifies SHA-256 against checksums.sha256
             │        ──> Rejects target_tier == "production" if is_synthetic == True
             ▼
 [Promote Experimental]──> models/backups/<current_version>/ (Previous backed up)
             │        ──> models/experimental/pest_forecasting/v2/ (Active replaced)
             │        ──> models/pest_deployment_ledger.json (Audit entry appended)
             ▼
    [Rollback]        ──> Restores target version from backups/ or candidates/
                      ──> Verifies SHA-256 integrity of restored files
                      ──> models/pest_deployment_ledger.json (Rollback logged)
```

### Strict Synthetic Production Isolation
Under no circumstances can a synthetic-data-trained model be promoted to production:
```python
if is_synthetic and target_tier == "production":
    errors.append(
        "CRITICAL SCIENTIFIC INTEGRITY VIOLATION: Models trained on synthetic data "
        "CANNOT be promoted to production. Synthetic evaluation does not substitute for "
        "real-world surveillance validation."
    )
```
Any invocation of `validate_pest_candidate(..., target_tier="production")` or `validate_candidate(..., target_tier="production")` immediately fails with `passed: False`.

---

## 6. Verification and Execution Results

### Exact Commands Executed and Test Summary

| # | Command Executed | Target Scope | Result | Summary |
|---|------------------|--------------|--------|---------|
| 1 | `python -m pytest tests/test_dvc_pipeline.py -v` | DVC Pipeline Verification | **PASSED** | 2 passed in 0.83s |
| 2 | `python -m pytest tests/test_pest_model_registry.py -v` | Pest Model Registry Unit Tests | **PASSED** | 5 passed in 0.87s |
| 3 | `python -m pytest tests/test_pest_mlflow_tracking.py -v` | MLflow Tracking Integration Tests | **PASSED** | 3 passed in 29.72s |
| 4 | `python -m pytest tests/test_experimental_pest_forecasting.py tests/test_experimental_pest_forecasting_v2.py tests/test_pest_mlflow_tracking.py tests/test_pest_model_registry.py tests/test_pest_readiness_gate.py tests/test_pest_risk_engine.py -v` | Full Pest Forecasting Test Suite | **PASSED** | 54 passed in 38.55s |
| 5 | `python -m pytest tests -v` | Complete Backend Test Suite | **PASSED** | 203 passed, 2 skipped (optional PDFs), 0 failed in 76.55s |
| 6 | `cd frontend; npm test -- --run; cd ..` | Frontend Vitest Suite | **PASSED** | 3 passed in 5.79s |
| 7 | `dvc commit train_pest_forecasting_v2 -f` | DVC Lock Synchronization | **PASSED** | `dvc.lock` fully synchronized |

---

## 7. Components Verified vs. Merely Configured

| Component | Status | Details |
|-----------|--------|---------|
| **V2 MLflow Tracking** | **VERIFIED** | Verified with local MLruns directory; tags, params, train/val/test metrics, and model artifacts logged and inspected via `MlflowClient`. |
| **MLflow Resiliency** | **VERIFIED** | Verified handling of invalid/unreachable MLflow URI; pipeline logs failure honestly without crashing model training. |
| **DVC Stage Definition** | **VERIFIED** | Verified stage syntax, dependency list, and output list in `dvc.yaml` and `dvc.lock`. |
| **DVC Execution** | **VERIFIED** | Stage runs via `python -m src.pest_forecasting.train_v2 --quick`; outputs verified on disk. |
| **Candidate Staging** | **VERIFIED** | Verified candidate creation in `models/candidates/` with exact SHA-256 hash manifest. |
| **Integrity Tamper Detection** | **VERIFIED** | Verified that altering single bytes in a staged artifact triggers checksum failure during validation. |
| **PR-AUC Promotion Gate** | **VERIFIED** | Verified candidate rejection when validation PR-AUC falls below threshold. |
| **Synthetic Production Block** | **VERIFIED** | Verified that synthetic models attempting production promotion are rejected with critical error. |
| **Versioned Backup & Rollback** | **VERIFIED** | Verified atomic backup to `models/backups/`, active file replacement, and byte-for-byte rollback. |
| **Pest Deployment Ledger** | **VERIFIED** | Verified ledger update on promotion and rollback in `models/pest_deployment_ledger.json`. |
| **Production Readiness Gate** | **VERIFIED** | Verified that all 11 scientific readiness criteria remain strictly blocked due to synthetic data. |
| **Remote DVC Storage** | **MERELY CONFIGURED (HONESTLY UNCONFIGURED)** | No remote DVC storage configured; system operates locally as required. |
| **Remote MLflow Server** | **MERELY CONFIGURED** | Can accept `--mlflow-tracking-uri http://...`; verified locally with file-based MLflow backend. |

---

## 8. Remaining Blockers for Production Deployment

As established in the Phase 20 scientific readiness audit and preserved in Phase 21:
1. **Absence of Real-World Field Surveillance Observations:** All models are trained on synthetic data (`synthetic_pest_forecasting_v2.csv`). Production promotion is blocked until authentic multi-year field surveillance records are collected and verified.
2. **Scientific Readiness Gate Status:** The 11 scientific criteria in `src/pest_risk/production_readiness_gate.py` evaluate to `BLOCKED`. This gate is intentionally un-bypassable.
3. **Field Calibration Required:** Real-world false alarm burden and economic intervention thresholds cannot be certified solely on synthetic data distributions.
