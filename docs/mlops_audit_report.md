# 📋 AgriAdapt AI — MLOps Pipeline Comprehensive Audit Report

**Date of Audit:** October 27, 2026  
**Auditor:** Senior MLOps Engineer (Antigravity)  
**Repository:** `pest-outbreak-early-warning-mlops`  
**Execution Environment:** Windows (PowerShell), Python 3.11.9, Node.js v22.13.1  

---

## 1. Executive Summary

This audit assesses the end-to-end MLOps pipeline covering data validation, model training, MLflow experiment tracking, artifact versioning, DVC data versioning, model promotion/rollback, drift monitoring, and backend/frontend integration.

While the core statistical and machine learning engines (Crop Selection and Fertilizer Regressor) and FastAPI endpoints are well-designed and feature-rich, **several critical architectural gaps, path inconsistencies, and unverified assumptions exist in the MLOps pipeline lifecycle**. Specifically:
- DVC was never initialized in the repository (`.dvc/` was absent despite `dvc.yaml`).
- Training stage directly overwrote production artifacts without candidate isolation or validation checks.
- The promotion and rollback ledger (`backend/ml/model_registry.py`) only updated JSON files without atomically replacing physical model files or supporting true binary rollbacks.
- Drift monitoring silently substituted synthetic data when logs were missing, reporting artificial drift as real production alerts without data-source provenance.
- CI workflow ran test suites without ensuring model artifacts or dataset locations were prepared.
- Fertilizer DVC stage ran a dummy `print()` command rather than validating artifacts and schemas.

---

## 2. Pipeline Architecture & Execution Flow

### System Components

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA & EXPERIMENT LIFECYCLE                     │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Raw Dataset (data/raw/Crop_recommendation.csv)                      │
│      ↓                                                                 │
│ 2. Schema Validation & Audit (backend/ml/data_validation.py)           │
│      ↓                                                                 │
│ 3. Feature Engineering & Selection (backend/ml/feature_engineering.py) │
│      ↓                                                                 │
│ 4. Cross-Validation & Candidate Fitting (backend/ml/train.py)          │
│    - Candidates: Random Forest, Extra Trees, (XGBoost if installed)    │
│    - Baseline vs. Domain-Engineered features                           │
│      ↓                                                                 │
│ 5. Held-Out Evaluation (backend/ml/evaluate.py)                        │
│      ↓                                                                 │
│ 6. Candidate Artifact Staging (Isolated candidate version & metadata)   │
│      ↓                                                                 │
│ 7. MLflow Experiment Logging (Parameters, Metrics, Artifacts)          │
│      ↓                                                                 │
│ 8. Safe Promotion Gate (backend/ml/model_registry.py)                  │
│    - Validates minimum metrics & candidate integrity                   │
│    - Atomic replacement of production artifact                         │
│    - Versioned backup for rollback capability                          │
│      ↓                                                                 │
│ 9. Serving & Health API (FastAPI backend/app/main.py)                 │
│      ↓                                                                 │
│ 10. Prediction Logging (JSONL audit trail backend/ml/prediction_logger)│
│      ↓                                                                 │
│ 11. Drift Monitoring (backend/ml/drift_monitor.py: KS-Test / Evidently)│
│      ↓                                                                 │
│ 12. Automated Retrain Trigger (backend/ml/retrain_trigger.py)          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Implemented vs. Merely Configured / Documented

| Feature / Component | Status | Reality vs. Configuration |
|---|---|---|
| **DVC Pipeline Execution** | ⚠️ Broken Config | `dvc.yaml` was written, but DVC was never initialized (`.dvc/` missing). Running `dvc repro` returned `ERROR: you are not inside of a DVC repository`. |
| **Dataset Tracking** | ⚠️ Mismatch | `Crop_recommendation.csv` existed only in root; `dvc.yaml` and `tests/test_monitoring.py` expected it at `data/raw/Crop_recommendation.csv`. |
| **Fertilizer DVC Verification** | ❌ Mock / Placeholder | Stage `fertilizer_artifacts` executed `python -c "print('Tracking fertilizer model artifacts')"`, verifying nothing. |
| **Atomic Model Promotion** | ❌ Incomplete | `train.py` directly wrote to `backend/artifacts/crop_model.joblib`. `model_registry.py` only updated a JSON ledger without checking files or copying candidate binaries. |
| **True Model Rollback** | ❌ Non-functional | `rollback()` in `model_registry.py` updated `production_version` in `deployment_ledger.json` with the comment: *"Artifact deployment remains an operator action"*. No file restore was executed. |
| **MLflow Experiment Tracking** | ⚠️ Partially Implemented | Configured in `train.py` via `--mlflow`, but lacked tracking URI configuration, failed without local server guidance, and registration had no local fallback. |
| **Drift Monitoring Provenance** | ⚠️ Misleading Fallback | `load_prediction_log()` silently fell back to `_synthetic_drift_sample()` if no logs existed, presenting synthetic shifts as actual input data drift. |
| **Automated Retrain Trigger CLI** | ❌ Buggy Integration | `train.py` stdout printed only version & selected model; `retrain_trigger.py` expected full metadata with `evaluation_metrics` to compute promotion, causing `KeyError`. |
| **Pest Early Warning** | ✅ Rule-based (Documented) | Appropriately implemented as rule-based agroclimatic risk indicators; roadmap properly notes that future time-series forecasting requires dedicated labeled datasets. |
| **Crop Recommendation Inference** | ✅ Operational | FastAPI endpoint `/api/v1/crop/recommend` returns top-3 candidate crops with input bounds validation. |
| **Fertilizer Regressor Inference** | ✅ Operational | Standalone ensemble model loaded from `models/fertilizer_model.joblib` predicts N, P2O5, K2O and commercial bags. |
| **FastAPI Backend & React Frontend** | ✅ Operational | FastAPI backend and React Vite dashboard run smoothly. |

---

## 4. Existing Working Features

1. **Crop Recommendation Classifier**:
   - Stratified dataset validation with SHA-256 integrity checksums.
   - Dual feature configurations (baseline vs domain-engineered NPK ratios, temperature-humidity interactions).
   - Sklearn pipeline with Random Forest and Extra Trees candidate models.
   - Holdout evaluation reporting accuracy, macro-F1, weighted-F1, per-class metrics, and confusion matrix.
2. **Fertilizer Optimization Regressor**:
   - Calibrated multi-target ensemble (`RF + ExtraTrees + GBDT`) in `models/fertilizer_model.joblib`.
   - Nutrient index transformations (`[1.0, 3.0]`) and commercial bag calculations (Urea, DAP, MOP).
   - Standalone inference working via `integration_example.py` and backend API `/api/v1/fertilizer/recommend`.
3. **Unified Advisory Orchestrator**:
   - Seamless workflow from soil readings $\to$ crop recommendation $\to$ fertilizer sizing $\to$ preliminary pest risk rating.
4. **FastAPI Web Service**:
   - Unified lifespan loading, CORS middleware, `/health` reporting, `/docs` OpenAPI schema.
5. **Interactive Dashboard**:
   - 5-zone IoT smart farm field monitor, crop selection form, fertilizer calculator, unified advisory card, and MLOps drift dashboard tab.

---

## 5. Detailed Inventory of Defects & Gaps

### Defect 1: DVC Not Initialized & Stage Path Inconsistencies
- **Location:** `.dvc/`, `dvc.yaml`
- **Symptom:** Running `dvc status` or `dvc repro` fails with `ERROR: you are not inside of a DVC repository`.
- **Cause:** `.dvc` directory was never initialized.
- **Dependency Inconsistency:** In `dvc.yaml`, `fertilizer_artifacts` stage specifies `backend/artifacts/fertilizer_model.joblib`, but the artifact resides in `models/fertilizer_model.joblib`.

### Defect 2: Premature Overwrite of Production Model During Training
- **Location:** `backend/ml/train.py:287-289`
- **Symptom:** Running `python -m backend.ml.train` immediately overwrites `backend/artifacts/crop_model.joblib` and `backend/artifacts/metadata.json` regardless of whether the model passed evaluation criteria or was promoted.
- **Cause:** Direct output to the production artifact directory instead of isolated candidate staging (`backend/artifacts/candidates/<version>/`).

### Defect 3: Incomplete Promotion and Rollback in `model_registry.py`
- **Location:** `backend/ml/model_registry.py`
- **Symptom:** Promotion and rollback only append records to `deployment_ledger.json`. The physical `.joblib` model file remains unchanged during rollback, meaning production inference still executes the old/new model.
- **Cause:** Absence of atomic file operations (`os.replace`, backup rotation, candidate validation).

### Defect 4: Retrain Trigger KeyError on Promotion
- **Location:** `backend/ml/retrain_trigger.py:90`, `backend/ml/train.py:324`
- **Symptom:** Retrain trigger crashes with `KeyError: 'evaluation_metrics'` during `maybe_promote()`.
- **Cause:** `train.py` prints `{ "model_version": ..., "selected_model": ... }` to stdout, which `retrain_trigger.py` parses as `new_metadata`. When `maybe_promote` accesses `new_metadata["evaluation_metrics"]["macro_f1"]`, it fails.

### Defect 5: Unlabeled Synthetic Drift Generation
- **Location:** `backend/ml/drift_monitor.py:30-40`
- **Symptom:** If `logs/prediction_log.jsonl` does not exist or is empty, `load_prediction_log()` silently calls `_synthetic_drift_sample()`. The resulting report marks real production as drifting without labeling that the dataset was synthetic.
- **Cause:** No `data_source` indicator in summary JSON/HTML reports; no minimum sample size guard for genuine prediction logs.

### Defect 6: Missing Verification in Fertilizer DVC Stage
- **Location:** `dvc.yaml:15-24`
- **Symptom:** DVC stage for fertilizer artifacts executes `python -c "print('Tracking fertilizer model artifacts')"`.
- **Cause:** Placeholder command left uncompleted.

### Defect 7: CI Workflow Fails on Clean Checkout
- **Location:** `.github/workflows/ci.yml`
- **Symptom:** `pytest -q` fails in clean CI because `data/raw/Crop_recommendation.csv` and `backend/artifacts/crop_model.joblib` are gitignored and not built or staged before tests run.

---

## 6. Current Model Artifacts & Verified Metadata

### 1. Crop Recommendation Model
- **Primary Artifact Path:** `backend/artifacts/crop_model.joblib`
- **Metadata Path:** `backend/artifacts/metadata.json`
- **Model Version:** `crop-20261027T172006Z-54a5a6e54086`
- **Model Family:** Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`, 40 trees)
- **Features (7):** `N, P, K, temperature, humidity, ph, rainfall`
- **Classes (22):** `apple, banana, blackgram, chickpea, coconut, coffee, cotton, grapes, jute, kidneybeans, lentil, maize, mango, mothbeans, mungbean, muskmelon, orange, papaya, pigeonpeas, pomegranate, rice, watermelon`
- **Cross-Validation Macro-F1:** `0.9937` ($\pm 0.0076$)
- **Held-Out Test Accuracy / Macro-F1:** `0.9932` / `0.9931`
- **Dataset SHA-256 Checksum:** `54a5a6e54086e3f4265fe0aa0b9858fe4e3cb439e7631333bcbe2df412f849b2`

### 2. Fertilizer Optimization Model
- **Primary Artifact Path:** `models/fertilizer_model.joblib`
- **Metadata Path:** `models/fertilizer_model_metadata.json`
- **Feature Schema Path:** `models/fertilizer_feature_schema.json`
- **Model Version:** `1.1.0`
- **Model Family:** Multi-Target Weighted Ensemble (`RandomForest + ExtraTrees + GradientBoosting`)
- **Targets (3):** `target_n_kg_ha, target_p2o5_kg_ha, target_k2o_kg_ha`
- **Validation Ensemble Weights:**
  - $N$: ExtraTrees (0.8008), GradientBoosting (0.1992)
  - $P_2O_5$: RandomForest (0.3679), ExtraTrees (0.6321)
  - $K_2O$: ExtraTrees (1.0000)
- **District Level GFR / Soil Health Card Records:** 2,051 records across 693 districts and 30 Indian states.

---

## 7. Prioritized Action Plan

1. **Phase 2 (DVC Repair):**
   - Initialize DVC repository.
   - Configure consistent dataset dependency at `data/raw/Crop_recommendation.csv`.
   - Implement real fertilizer artifact validation script `backend/ml/fertilizer.py --verify`.
   - Update `dvc.yaml` stages with genuine dependencies and outputs.
2. **Phase 3 & 4 (Reproducible Safe Training & MLflow):**
   - Save training outputs to versioned candidate staging area (`backend/artifacts/candidates/<version>/`).
   - Log parameters, metrics, artifacts to MLflow when enabled, gracefully handling local/disconnected modes.
   - Ensure `train.py` CLI outputs complete metadata for consumption by downstream tools.
3. **Phase 5 (Promotion, Versioning & Rollback):**
   - Implement atomic promotion in `backend/ml/model_registry.py` (candidate validation, metric thresholds, file backup, atomic file replace).
   - Implement verified rollback that physically restores previous `.joblib` and `.json` artifacts.
4. **Phase 6 (Drift Monitoring):**
   - Distinguish real vs synthetic logs with explicit `data_source` provenance metadata.
   - Handle empty logs, malformed JSON lines, and small sample sizes gracefully without deceptive alerts.
   - Keep synthetic drift generation strictly opt-in (`--synthetic` flag).
5. **Phase 7 & 8 (Integration & CI/Testing):**
   - Ensure fertilizer model is accessible in both `models/` and `backend/artifacts/`.
   - Update `ci.yml` to stage dataset and candidate artifacts prior to testing.
   - Add comprehensive unit and integration tests covering promotion, rollback, drift provenance, and DVC stage integrity.
