# Phase 22 — End-to-End Pest Forecasting Application Integration, Monitoring & Retraining Report

**Project:** AgriAdapt AI / Pest Outbreak Early Warning MLOps System  
**Phase:** 22 — End-to-End Application Integration, Monitoring & Retraining  
**Date:** November 17, 2026  
**Status:** Completed & Rigorously Verified  

---

## 1. Executive Summary

Phase 22 successfully connects the Version 2.0 experimental multi-crop pest outbreak forecasting pipeline into the operational AgriAdapt AI software stack. Prior to this phase, Version 2.0 existed as an isolated experimental ML training and staging architecture (Phase 21). 

In Phase 22, the following full-lifecycle components were integrated and verified:
1. **FastAPI Endpoints:** Implemented dedicated `/api/v1/pest-forecasting/predict`, `/model-info`, and `/example` endpoints supported by safe, thread-safe artifact loading in `PestForecastingService`. Supports both `ENVIRONMENTAL_ONLY` and `SCOUTING_ASSISTED` configurations, with strict physical bounds validation and mandatory `SYNTHETIC_EXPERIMENTAL` labeling.
2. **Interactive UI Integration:** Built and integrated `ExperimentalPestForecastingSection.jsx` within the frontend, allowing farmers to run real-time inference against the FastAPI backend, switch between pipeline modes, prefill verified ICAR field scenarios, inspect calibrated decision thresholds, and review predicted outbreak probabilities.
3. **Prometheus Telemetry:** Instrumented custom Prometheus metrics (`pest_prediction_requests_total`, `pest_prediction_latency_seconds`, `pest_prediction_errors_total`, `pest_model_info`, `pest_model_drift`). Scrapes verified via `/metrics` endpoint.
4. **Grafana Dashboards:** Extended `grafana/dashboards/agri_dashboard.json` with 5 new monitoring panels dedicated to experimental pest forecasting request rates, P95 latencies, error rates, model version governance, and microclimatic feature drift.
5. **Controlled Retraining Architecture:** Built `backend/ml/pest_retrain_trigger.py` and exposed `/monitoring/pest-retrain/*` endpoints. Enforces the Scientific Readiness Gate: supervised retraining is strictly blocked until $\ge 500$ authentic prospective field surveillance records exist. Controlled experimental retraining updates candidates with PR-AUC gates and SHA-256 integrity, with strict production isolation.
6. **Full Verification:** Executed 217 backend tests (215 passed, 2 skipped due to optional sample PDFs, 0 failed) and all 4 frontend Vitest tests.

---

## 2. Files Created and Modified

### Modified Files:
1. `backend/app/main.py`:
   - Registered `pest_forecasting_router` under `/api/v1`.
   - Initialized and eagerly loaded `PestForecastingService` on `app.state`.
   - Enhanced `/health` endpoint to expose `pest_forecasting_available` and `pest_forecasting_version`.
2. `backend/app/core/metrics.py`:
   - Registered pest forecasting Prometheus telemetry:
     - `pest_prediction_requests_total` (Counter: `configuration`, `status`)
     - `pest_prediction_latency_seconds` (Histogram: `configuration`)
     - `pest_prediction_errors_total` (Counter: `error_type`)
     - `pest_model_info` (Gauge: `model_version`, `configuration`, `framework`, `is_synthetic`, `is_production_ready`)
     - `pest_model_drift` (Gauge: `feature`, `metric`)
3. `backend/app/schemas/crop.py`:
   - Added optional fields `pest_forecasting_available` and `pest_forecasting_version` to `HealthResponse`.
4. `backend/app/schemas/__init__.py`:
   - Exported `PestForecastingRequest`, `PestForecastingResponse`, `PestModelInfoResponse`, and `SCIENTIFIC_PEST_DISCLAIMER`.
5. `backend/app/services/__init__.py`:
   - Exported `PestForecastingService`.
6. `backend/app/api/__init__.py`:
   - Exported `pest_forecasting_router`.
7. `backend/app/api/monitoring.py`:
   - Added `PestRetrainRequest` schema.
   - Added `GET /monitoring/pest-retrain/status` (readiness gate summary).
   - Added `GET /monitoring/pest-retrain/history` (audit trail).
   - Added `POST /monitoring/pest-retrain/trigger` (controlled background execution).
8. `frontend/src/services/api.js`:
   - Added `pestForecastingApi`: `modelInfo()`, `predict()`, and `example()`.
9. `frontend/src/components/EnvironmentalPestRiskSection.jsx`:
   - Integrated engine mode segmented toggle (`biophysical` vs `ml-forecasting`).
   - Dynamically mounts `ExperimentalPestForecastingSection`.
10. `frontend/src/__tests__/App.test.jsx`:
    - Added comprehensive mocks and tests for pest forecasting UI navigation and mode switching.
11. `grafana/dashboards/agri_dashboard.json`:
    - Extended dashboard from 6 to 11 panels, adding panels 7 through 11 for experimental pest forecasting telemetry.

### Created Files:
1. `backend/app/schemas/pest_forecasting.py`:
   - Defined `PestForecastingRequest` with biophysical validation (`min_temp <= max_temp`, `r7 <= r14`, and required scouting fields for `SCOUTING_ASSISTED`).
   - Defined `PestForecastingResponse` and `PestModelInfoResponse`.
2. `backend/app/services/pest_forecasting_service.py`:
   - Thread-safe loader for Version 2.0 joblib pipelines, schema JSONs, and calibration thresholds.
   - Computes outbreak probabilities, applies calibrated decision thresholds (0.32 for environmental, 0.82 for scouting), determines warnings, and records Prometheus metrics.
3. `backend/app/api/pest_forecasting.py`:
   - FastAPI routes for model metadata, example payloads, and inference execution.
4. `backend/ml/pest_retrain_trigger.py`:
   - Readiness gate checking, refusal auditing in `logs/pest_retrain_log.jsonl`, candidate staging, PR-AUC gate validation, SHA-256 verification, and experimental ledger promotion.
5. `frontend/src/components/ExperimentalPestForecastingSection.jsx`:
   - Rich React component providing configuration switching, interactive form controls, ICAR scenario prefilling, visual outbreak risk meter, threshold comparison, and scientific disclaimers.
6. `tests/test_api_pest_forecasting.py`:
   - Integration tests for metadata, examples, predictions, bounds validation, and error handling (6 tests).
7. `tests/test_pest_prometheus_metrics.py`:
   - Verification of counters, histograms, info gauges, and drift gauges on `/metrics` (2 tests).
8. `tests/test_pest_retraining_trigger.py`:
   - Verification of readiness gate refusal, audit persistence, and controlled experimental retraining (4 tests).

---

## 3. FastAPI API Integration Details

### Endpoints Implemented

| Endpoint | Method | Description | Response Status |
|---|---|---|---|
| `/api/v1/pest-forecasting/model-info` | GET | Returns active model metadata, feature schemas, thresholds, and readiness status | 200 OK |
| `/api/v1/pest-forecasting/example` | GET | Returns verified sample payload for `ENVIRONMENTAL_ONLY` or `SCOUTING_ASSISTED` | 200 OK |
| `/api/v1/pest-forecasting/predict` | POST | Executes 7-day outbreak forecast; records Prometheus telemetry | 200 OK / 422 / 503 |
| `/api/v1/monitoring/pest-retrain/status` | GET | Evaluates Scientific Readiness Gate data sufficiency | 200 OK |
| `/api/v1/monitoring/pest-retrain/history` | GET | Returns audit trail of retraining trigger attempts | 200 OK |
| `/api/v1/monitoring/pest-retrain/trigger` | POST | Controlled retraining; rejects unauthorized production runs | 200 OK |

### Request and Response Guarantees
- **Configuration Modes:**
  - `ENVIRONMENTAL_ONLY`: Ingests 13 macro-climatic & topsoil features (`district`, `crop`, `pest`, `growth_stage`, 7d temperatures, humidity, rainfall, topsoil moisture, dry days).
  - `SCOUTING_ASSISTED`: Ingests 18 features (all 13 environmental features plus `scout_incidence_pct`, `scout_severity_pct`, `trap_catch_count`, `days_since_scouting`, `pest_present`).
- **Data Validation:** Pydantic validators reject thermodynamic violations ($T_{\min} > T_{\max}$ or 7-day rainfall > 14-day rainfall) and reject `SCOUTING_ASSISTED` payloads missing in-field scouting observations.
- **Scientific Disclaimers:** Every response mandates `classification="SYNTHETIC_EXPERIMENTAL"`, `is_production_ready=False`, and an un-bypassable disclaimer string.

---

## 4. Frontend Integration Details

### Architecture & User Experience
The user interface preserves the existing design language while integrating the new capability:
- Integrated a segmented mode control at the top of the **Pest Surveillance** tab:
  - Mode A: **ICAR Biophysical Favorability (Rule-Based EFI)** (preserves existing 568-line biophysical evaluation).
  - Mode B: **Experimental 7-Day ML Outbreak Forecasting (v2.0)** (mounts `ExperimentalPestForecastingSection`).
- **Interactive Capabilities:**
  - One-click configuration toggle between `🌱 Environmental Only` and `🔍 Scouting Assisted`.
  - Dynamic scouting inputs appear only when `SCOUTING_ASSISTED` is active.
  - "Load ICAR Field Sample Scenario" button instantly populates realistic agroclimatic values.
  - Submits live HTTP request to FastAPI `/api/v1/pest-forecasting/predict` without mocks.
  - Renders a color-coded probability gauge bar with a calibrated decision threshold marker.
  - Distinct warning badges: `🚨 OUTBREAK WARNING` (exceeds threshold) vs `✅ NORMAL RISK` (below threshold).
  - Transparent model governance details: algorithm name, version, target tier, and prominent amber scientific disclaimer.

---

## 5. Prometheus Scrape & Metrics Verification

The backend exposes metrics at `/metrics` using `prometheus_client`. All metrics were scraped and verified via HTTP:

```
# HELP pest_prediction_requests_total Total experimental pest forecasting prediction requests
# TYPE pest_prediction_requests_total counter
pest_prediction_requests_total{configuration="environmental_only",status="success"} 1.0
pest_prediction_requests_total{configuration="scouting_assisted",status="success"} 1.0

# HELP pest_prediction_latency_seconds Experimental pest forecasting inference latency in seconds
# TYPE pest_prediction_latency_seconds histogram
pest_prediction_latency_seconds_bucket{configuration="environmental_only",le="0.25"} 1.0
pest_prediction_latency_seconds_count{configuration="environmental_only"} 1.0
pest_prediction_latency_seconds_sum{configuration="environmental_only"} 0.148377

# HELP pest_model_info Active experimental pest forecasting model metadata
# TYPE pest_model_info gauge
pest_model_info{configuration="ENVIRONMENTAL_ONLY",framework="scikit-learn",is_production_ready="false",is_synthetic="true",model_version="pest-v2.0.0-experimental-synthetic"} 1.0
pest_model_info{configuration="SCOUTING_ASSISTED",framework="scikit-learn",is_production_ready="false",is_synthetic="true",model_version="pest-v2.0.0-experimental-synthetic"} 1.0

# HELP pest_model_drift Experimental pest forecasting feature distribution drift indicator
# TYPE pest_model_drift gauge
pest_model_drift{feature="temperature_anomaly",metric="abs_diff"} 3.0
pest_model_drift{feature="humidity_anomaly",metric="abs_diff"} 8.4
```

---

## 6. Grafana Dashboard Verification

The provisioned dashboard file `grafana/dashboards/agri_dashboard.json` was extended with 5 specialized panels:
1. **Panel 7: Pest Forecasting Request Rate (Experimental)** (`timeseries`, gridPos: `24y x 12w x 8h`)
   - Expression A: `rate(pest_prediction_requests_total{configuration="environmental_only",status="success"}[5m])`
   - Expression B: `rate(pest_prediction_requests_total{configuration="scouting_assisted",status="success"}[5m])`
2. **Panel 8: Pest Forecasting Latency P95 (Experimental)** (`timeseries`, gridPos: `24y x 12w x 8h`)
   - Expression A: `histogram_quantile(0.95, rate(pest_prediction_latency_seconds_bucket{configuration="environmental_only"}[5m]))`
   - Expression B: `histogram_quantile(0.95, rate(pest_prediction_latency_seconds_bucket{configuration="scouting_assisted"}[5m]))`
3. **Panel 9: Pest Forecasting Error Rate (Experimental)** (`timeseries`, gridPos: `32y x 8w x 8h`)
   - Expression A: `rate(pest_prediction_errors_total[5m])`
   - Expression B: `rate(pest_prediction_requests_total{status="error"}[5m])`
4. **Panel 10: Pest Model Version & Governance (Experimental)** (`stat`, gridPos: `32y x 8w x 8h`)
   - Expression: `pest_model_info`
5. **Panel 11: Pest Feature Drift Monitoring (Experimental)** (`stat`, gridPos: `32y x 8w x 8h`)
   - Expression: `pest_model_drift`

All panel descriptions and titles explicitly highlight `EXPERIMENTAL (SYNTHETIC)` to prevent operational confusion with production crop/fertilizer metrics.

---

## 7. Retraining Implementation & Gate Enforcement

The retraining orchestrator `backend/ml/pest_retrain_trigger.py` enforces controlled model updates:
1. **Scientific Readiness Gate Check:** Inspects authentic field observations count. If authentic multi-season observations are $< 500$, retraining is rejected:
   - Status: `REJECTED_BY_READINESS_GATE`
   - Refusal reason: `Retraining blocked by Scientific Readiness Gate: Insufficient authentic records: 0 acquired (minimum required: 500).`
   - Appended to `logs/pest_retrain_log.jsonl` for audit compliance.
2. **Controlled Experimental Execution:** When `force_experimental=True` is provided for authorized experimental pipeline benchmarking:
   - Executes `src.pest_forecasting.train_v2` with `--quick`.
   - Stages candidate in `models/candidates/pest-v2-<timestamp>-retrained`.
   - Generates and verifies SHA-256 checksum manifest (`checksums.sha256`).
   - Verifies PR-AUC meets gates ($\ge 0.70$ scouting, $\ge 0.50$ environmental).
   - Enforces target tier is strictly `experimental`; synthetic models attempting production promotion are hard-rejected.
   - Automatically backs up active models to `models/backups/` and atomically updates experimental baseline.
   - Records promotion event in `models/pest_deployment_ledger.json`.

---

## 8. Service & Docker Verification

| Service | Host / Port | Verification Command / URL | Status | Details |
|---|---|---|---|---|
| **Backend API (FastAPI)** | `http://127.0.0.1:8000` | `http://127.0.0.1:8000/health` | **UP (Active)** | Serves crop, fertilizer, pest risk, and experimental pest forecasting |
| **Frontend UI (Vite / React)** | `http://127.0.0.1:5173` | `http://127.0.0.1:5173` | **UP (Active)** | Real-time command center, multi-farmer estates, pest forecasting UI |
| **Prometheus Exporter** | `http://127.0.0.1:8000/metrics` | HTTP Scrape | **UP (Active)** | Exposes `pest_*` counters, histograms, gauges |
| **Prometheus Config** | `./prometheus.yml` | File syntax validation | **VALID** | Targets `host.docker.internal:8000` at `/metrics` with 10s interval |
| **Grafana Dashboard** | `./grafana/dashboards/agri_dashboard.json` | JSON schema validation | **VALID** | 11 panels configured with Prometheus datasource |
| **Docker Compose** | `docker-compose.yml` | Service definitions | **CONFIGURED** | Ready for containerization; Docker Desktop engine stopped locally |

---

## 9. Test Verification Results

### Summary of Executed Test Suites

| # | Command Executed | Target Scope | Result | Summary |
|---|---|---|---|---|
| 1 | `npm test -- --run` (in `frontend/`) | Frontend Vitest Test Suite | **PASSED** | 4 passed in 5.97s |
| 2 | `npm run build` (in `frontend/`) | Frontend Production Build | **PASSED** | 0 errors, 44 modules transformed in 954ms |
| 3 | `python -m pytest tests/test_api_pest_forecasting.py -v` | Pest Forecasting API Tests | **PASSED** | 6 passed in 1.45s |
| 4 | `python -m pytest tests/test_pest_prometheus_metrics.py -v` | Prometheus Telemetry Scrape Tests | **PASSED** | 2 passed in 0.85s |
| 5 | `python -m pytest tests/test_pest_retraining_trigger.py -v` | Retraining Gate & Workflow Tests | **PASSED** | 4 passed in 17.57s |
| 6 | `python -m pytest tests/test_api_pest_forecasting.py tests/test_experimental_pest_forecasting.py tests/test_experimental_pest_forecasting_v2.py tests/test_pest_mlflow_tracking.py tests/test_pest_model_registry.py tests/test_pest_prometheus_metrics.py tests/test_pest_readiness_gate.py tests/test_pest_retraining_trigger.py tests/test_pest_risk_engine.py -v` | Complete Pest Testing Suite | **PASSED** | 66 passed in 107.78s |
| 7 | `python -m pytest tests -v` | Complete Backend Test Suite | **PASSED** | 215 passed, 2 skipped (optional sample PDFs), 0 failed in 187.24s |

---

## 10. Remaining Blockers for Production Deployment

In accordance with Phase 20, 21, and 22 scientific guidelines:
1. **Prospective Commercial Field Surveillance Data Required:** The models are trained on biophysical synthetic simulations (`synthetic_pest_forecasting_v2.csv`). Operational deployment as production advisories remains blocked until at least 500 authentic multi-season field records are acquired.
2. **Scientific Readiness Gate:** `src/pest_risk/production_readiness_gate.py` evaluates to `BLOCKED`. This gate is hard-coded and cannot be bypassed.
3. **Pesticide / Commercial Decision Safeguards:** All UI components, API payloads, and MLflow tags enforce `SYNTHETIC_EXPERIMENTAL` labeling and `is_production_ready: false` to ensure experimental predictions are never confused with certified agricultural advisories.
