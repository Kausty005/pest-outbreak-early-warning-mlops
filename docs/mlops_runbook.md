# MLOps Operations Runbook

**Project:** Pest Outbreak Early Warning MLOps  
**Version:** 1.0 (post-audit)  
**Audience:** On-call engineers, MLOps team

---

## Table of Contents

1. [Starting the Stack](#1-starting-the-stack)
2. [Running the Full Test Suite](#2-running-the-full-test-suite)
3. [Reproducing the DVC Pipeline](#3-reproducing-the-dvc-pipeline)
4. [Training and Promoting a New Model](#4-training-and-promoting-a-new-model)
5. [Rolling Back a Promotion](#5-rolling-back-a-promotion)
6. [Checking Drift and Retrain Status](#6-checking-drift-and-retrain-status)
7. [Verifying Production Model Integrity](#7-verifying-production-model-integrity)
8. [Troubleshooting Common Issues](#8-troubleshooting-common-issues)

---

## 1. Starting the Stack

### Prerequisites
- Python 3.11+
- pip packages installed: `pip install -r requirements.txt`

### Backend API
```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```
API docs available at: http://localhost:8000/docs

### Frontend
```powershell
# From project root (if using a dev server)
cd frontend
# open index.html directly in browser, or serve with:
python -m http.server 3000
```

---

## 2. Running the Full Test Suite

```powershell
# From project root
python -m pytest tests/ -v --tb=short

# Run a specific module
python -m pytest tests/test_model_registry.py -v

# Run with coverage (if pytest-cov is installed)
python -m pytest tests/ --cov=backend --cov-report=term-missing
```

**Expected outcome:** 44 passed, 0 failed.

---

## 3. Reproducing the DVC Pipeline

```powershell
# Check current status (no re-run if already up to date)
dvc status

# Force full pipeline re-execution
dvc repro

# View pipeline DAG
dvc dag
```

### DVC Stages
| Stage | Script | Output |
|---|---|---|
| `train_crop_model` | `backend/ml/train.py` | `crop_model.joblib`, `metadata.json` |
| `fertilizer_artifacts` | `backend/ml/fertilizer_pipeline.py` | `fertilizer_model.joblib`, `fertilizer_feature_schema.json` |
| `monitor_drift` | `backend/ml/drift_monitor.py` | drift report JSON |

---

## 4. Training and Promoting a New Model

### Step 1 — Train
```powershell
python backend/ml/train.py --data-path data/crop_recommendation.csv --min-macro-f1 0.90
```

On success, the script prints:
```
[TRAIN] Candidate staged: backend/artifacts/candidates/crop-<timestamp>-<git-sha>/
[TRAIN] Macro F1: 0.XXXX (threshold: 0.90)
```

### Step 2 — Validate Candidate
```python
from backend.ml.model_registry import ModelRegistry

registry = ModelRegistry()
registry.validate_candidate("crop-<timestamp>-<git-sha>")  # raises ValueError if thresholds not met
```

### Step 3 — Promote to Production
```python
registry.promote("crop-<timestamp>-<git-sha>")
```

The registry will:
- Acquire a process-level promotion lock.
- Verify SHA-256 checksum against the training manifest.
- Backup the current production model.
- Atomically replace `crop_model.joblib`.
- Append an entry to `deployment_ledger.json`.
- Release the lock.

### Step 4 — Verify
```powershell
python -c "import json; print(json.load(open('backend/artifacts/deployment_ledger.json'))['production_version'])"
```

---

## 5. Rolling Back a Promotion

```python
from backend.ml.model_registry import ModelRegistry

registry = ModelRegistry()
registry.rollback()  # restores the most recent backup
```

Rollbacks are recorded in `deployment_ledger.json` under `"action": "rollback"`.

If no backup exists, the rollback raises `FileNotFoundError` with a clear message.

---

## 6. Checking Drift and Retrain Status

### Via API
```powershell
# Check monitoring status
curl http://localhost:8000/monitoring/status

# Get latest drift report
curl http://localhost:8000/monitoring/drift
```

### Via Script
```python
from backend.ml.drift_monitor import DriftMonitor

monitor = DriftMonitor()
report = monitor.check(reference_data, current_data)
print(report)
# Fields: drift_detected, psi_score, feature_scores, data_source, is_synthetic
```

### Retrain Guard
Synthetic drift events (`is_synthetic: true`) are **automatically suppressed** and will not trigger retraining. A warning is logged:
```
WARNING: Suppressing retrain: drift event is from synthetic data
```

---

## 7. Verifying Production Model Integrity

```powershell
# Compute live checksum
python -c "
import hashlib, json
digest = hashlib.sha256(open('backend/artifacts/crop_model.joblib','rb').read()).hexdigest()
ledger = json.load(open('backend/artifacts/deployment_ledger.json'))
meta   = json.load(open('backend/artifacts/metadata.json'))
print('Disk SHA-256    :', digest)
print('Ledger SHA-256  :', ledger['production_sha256'])
print('Metadata SHA-256:', meta['artifact_sha256'])
print('MATCH' if digest == ledger['production_sha256'] == meta['artifact_sha256'] else 'MISMATCH — ALERT')
"
```

Expected output:
```
Disk SHA-256    : b43da7dfcbee56ce9f5061509cc5e06d480e841995d0721b2a95c5610937f3d8
Ledger SHA-256  : b43da7dfcbee56ce9f5061509cc5e06d480e841995d0721b2a95c5610937f3d8
Metadata SHA-256: b43da7dfcbee56ce9f5061509cc5e06d480e841995d0721b2a95c5610937f3d8
MATCH
```

---

## 8. Troubleshooting Common Issues

### MLflow MemoryError on import
**Symptom:** `MemoryError: Out of memory interning an attribute name` when importing mlflow.

**Cause:** Known bug in `databricks-sdk` on low-RAM machines (< 4 GB free).

**Fix:**
```powershell
pip install "databricks-sdk<0.30"
```
Or use the training script — it gracefully catches MLflow failures and continues.

### Promotion Lock Stale
**Symptom:** `RuntimeError: Promotion already in progress` even when no promotion is running.

**Cause:** A previous promotion crashed without cleaning up the lock file.

**Fix:** The lock auto-expires after 60 seconds. Wait, or manually delete:
```powershell
Remove-Item backend/artifacts/.promotion.lock -Force
```

### DVC Status Shows Modified Outputs
**Symptom:** `dvc status` shows a stage as modified unexpectedly.

**Fix:** Re-run the pipeline:
```powershell
dvc repro
```
If outputs are intentionally different (e.g., after retraining), commit the updated `.dvc` files:
```powershell
dvc add backend/artifacts/crop_model.joblib
git add backend/artifacts/crop_model.joblib.dvc
git commit -m "chore: update production model artifact"
```

### Test Failures After Model Retrain
**Symptom:** `test_training.py` fails with macro F1 below threshold.

**Cause:** Dataset or feature engineering change reduced model quality.

**Fix:** Investigate with:
```powershell
python backend/ml/train.py --data-path data/crop_recommendation.csv --min-macro-f1 0.0
```
This runs without threshold enforcement and prints per-class F1 scores to identify the regressing class.

### FastAPI 422 on `/predict`
**Symptom:** Prediction endpoint returns 422 Unprocessable Entity.

**Cause:** Request body missing required fields or wrong types.

**Fix:** Check required schema at http://localhost:8000/docs — all 7 input features must be present as numbers.
