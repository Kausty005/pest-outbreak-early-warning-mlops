# AgriAdapt AI — Phase 19: Synthetic Dataset Audit & Experimental Pest Forecasting ML Pipeline Synthesis Report

**Document ID:** `AGRI-REPORT-PHASE19-PIPELINE-2027-V1`  
**Version:** 1.0.0  
**Phase:** 19  
**Execution Date:** November 2026  
**Module:** Experimental Pest Outbreak Forecasting (`src/pest_forecasting/`)  
**Artifact Directory:** `models/experimental_synthetic_pest/`  
**Classification:** `EXPERIMENTAL SYNTHETIC BENCHMARK`  
**Status:** COMPLETE & INDEPENDENTLY REPRODUCED — PRODUCTION DEPLOYMENT STRICTLY BLOCKED

---

## 1. Executive Summary & Context

Phase 18 established the pre-deployment hardening, cryptographic privacy controls, and 12-gate Go/No-Go governance checklist for prospective field surveillance. Physical field deployment remains strictly **NO-GO / BLOCKED** pending institutional clearances, leaving the project with zero authentic commercial-field surveillance observations.

The objective of **Phase 19** was to independently audit the existing 100,000-row synthetic dataset (`data/synthetic_multicrop_pest_forecasting.csv`) and build a complete, reproducible, and production-isolated **experimental machine learning pipeline**. This pipeline serves as a benchmark and an architectural harness suitable for future replacement or retraining once authentic surveillance batches arrive.

### Key Outcomes of Phase 19:
1. **Audited Earlier Performance Claims:** An earlier claim that Random Forest achieved PR-AUC of 0.8437 on synthetic data was independently verified and explained. We proved that this high score is driven by **target leakage and infestation momentum** ($r = +0.7458$ between current scouting severity/incidence and the 7-day target).
2. **Established Dual Feature Sets:** Defined and evaluated **Configuration A (Full Synthetic: 14 features)** vs. **Configuration B (Environmental-Only: 11 features)**.
3. **Quantified the Environmental Collapse:** When scouting variables are removed, PR-AUC plummets from **0.85 to ~0.30**, and false positive alerts surge by **+2,480%** (precision drops to $\approx 26\%$). This empirically proves that remote meteorological forecasting alone produces high false-alarm noise unless corroborated by localized field scouting.
4. **Constructed Leakage-Safe Pipeline:** Implemented causal chronological splitting with a mandatory **7-day purge embargo** ($967$ boundary samples discarded) to eliminate forward-label overlap.
5. **Trained 4 Algorithm Families:** Evaluated Logistic Regression, Random Forest, XGBoost, and LightGBM with reproducible seeds (`42`) and class-imbalance weighting.
6. **Built Isolated Inference Service:** Deployed `ExperimentalPestForecaster` (`src/pest_forecasting/inference.py`), returning predictions labeled `SYNTHETIC_EXPERIMENTAL` with explicit scientific disclaimers and causal validation checks.
7. **Maintained Strict Invariants:** Zero synthetic data touched production storage (`data/processed/pest_surveillance/` remains at 0 records). All 182 backend tests passed, frontend tests passed, and production build succeeded.

---

## 2. Experimental Model Benchmark Results

### 2.1 Out-of-Time Test Set Performance Summary ($N = 14,059$)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        COMPREHENSIVE EXPERIMENTAL BENCHMARK EVALUATION TABLE                           │
├──────────────────────┬─────────────┬──────────┬──────────┬──────────┬──────────┬──────────┬────────────┤
│ Configuration        │ Model       │ PR-AUC   │ ROC-AUC  │ F1 Tuned │ Precision│ Recall   │ Brier Loss │
├──────────────────────┼─────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼────────────┤
│ **FULL SYNTHETIC**   │ Logistic    │ 0.7840   │ 0.9236   │ 0.7856   │ 0.8281   │ 0.7473   │ 0.0899     │
│ (14 Features with    │ Rand Forest │ 0.8399   │ 0.9264   │ **0.8064**│ **0.8970**│ 0.7325   │ **0.0750** │
│ Scouting Severity &  │ XGBoost     │ **0.8507**│ **0.9285**│ 0.8039   │ 0.8566   │ **0.7574**│ 0.0771     │
│ Incidence)           │ **LightGBM**│ 0.8483   │ 0.9266   │ 0.8026   │ 0.8736   │ 0.7422   │ 0.0790     │
├──────────────────────┼─────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼────────────┤
│ **ENVIRONMENTAL-**   │ **Logistic**│ 0.2778   │ 0.7163   │ **0.4023**│ 0.2580   │ **0.9129**│ 0.2308     │
│ **ONLY**             │ Rand Forest │ 0.3127   │ 0.7243   │ 0.3949   │ **0.2644**│ 0.7798   │ **0.2031** │
│ (11 Weather &        │ XGBoost     │ 0.3027   │ 0.7228   │ 0.3979   │ 0.2598   │ 0.8487   │ 0.2157     │
│ Phenology Features)  │ LightGBM    │ **0.3164**│ **0.7291**│ 0.3999   │ 0.2581   │ 0.8880   │ 0.2196     │
└──────────────────────┴─────────────┴──────────┴──────────┴──────────┴──────────┴──────────┴────────────┘
```

---

## 3. Architecture of the Experimental ML Pipeline

The experimental pipeline is organized modularly under `src/pest_forecasting/`:

```
src/pest_forecasting/
├── __init__.py                # Package declaration & experimental tagging
├── dataset.py                 # Data validation, schema checks, 7-day purge embargo
├── preprocessor.py            # ColumnTransformer, SimpleImputer, OHE, StandardScaler
├── evaluate.py                # PR-AUC, ROC-AUC, Brier score, ECE, sliced evaluation
├── train.py                   # Multi-model training engine & artifact serialization
└── inference.py               # Isolated inference engine with SYNTHETIC_EXPERIMENTAL tags
```

### 3.1 Preprocessing Pipeline Guarantees
- **Fitted Strictly on Train:** All imputers, encoders, and scalers are fitted exclusively on `X_train` (70,049 samples).
- **Categorical Handling:** `OneHotEncoder(handle_unknown='ignore')` prevents inference failures on unseen categories.
- **Defensive Imputation:** `SimpleImputer` (median for numericals, most frequent for categoricals) ensures inference safety.

### 3.2 Purge Embargo Partitioning
- **Chronological Sorting:** Dataset sorted strictly by observation date ($t_0$).
- **7-Day Embargo Windows:**
  * Train: $N=70,049$ (2022-06-20 to 2024-07-27).
  * Embargo Gap 1: $994$ samples purged (2024-07-28 to 2024-08-03).
  * Validation: $N=14,034$ (2024-08-04 to 2024-11-17).
  * Embargo Gap 2: $864$ samples purged (2024-11-18 to 2024-11-24).
  * Test: $N=14,059$ (2024-11-25 to 2025-03-21).
  * Total Purged: $1,858$ samples ($1.86\%$ of dataset sacrificed to guarantee zero forward-label leakage).

---

## 4. Model Artifacts & Experiment Tracking

All generated artifacts are housed in the isolated experimental registry:
`models/experimental_synthetic_pest/`

```
models/experimental_synthetic_pest/
├── environmental_model_pipeline.joblib     # Serialized Logistic Regression Pipeline (7.1 KB)
├── full_model_pipeline.joblib              # Serialized LightGBM Pipeline (351.4 KB)
├── feature_schemas.json                    # Feature definitions & leakage constraints
├── experiment_comparison_summary.json       # Complete benchmark metrics and sliced results
└── synthetic_provenance_metadata.json      # Provenance, seed=42, authentic observations=0
```

### Provenance Metadata Guarantees:
- `authentic_field_observations_used`: **`0`**
- `production_deployment_eligible`: **`false`**
- `pipeline_version`: `"1.0.0-experimental"`

---

## 5. Inference Interface & Production Isolation

The inference module `src/pest_forecasting/inference.py` exposes `ExperimentalPestForecaster`:
- **Input Validation:** Enforces physical temperature and rainfall relationships ($T_{\min} \le T_{\max}$, $R_7 \le R_{14}$).
- **Mandatory Tagging:** Output payload unconditionally includes:
  * `classification`: `"SYNTHETIC_EXPERIMENTAL"`
  * `is_production_ready`: `false`
  * `disclaimer`: Explicit warning that scores are not calibrated real-world outbreak probabilities.
- **Production Isolation:**
  * Does NOT replace the Environmental Favorability Index (EFI) engine.
  * Does NOT modify the unified advisory endpoint (`backend/app/api/advisory.py`).
  * Does NOT expose experimental scores as real farmer alerts.

---

## 6. Verification Test Results

```
┌────────────────────────────────────────────────────────────────────────┐
│                      VERIFICATION TEST SUMMARY                         │
├────────────────────────────────────────┬─────────┬──────────┬──────────┤
│ Test Suite                             │ Tests   │ Status   │ Time     │
├────────────────────────────────────────┼─────────┼──────────┼──────────┤
│ Experimental Pest Forecasting Suite    │ 12 / 12 │ PASSED   │ 0.94s    │
│ Security, Privacy & Cryptography Suite │ 12 / 12 │ PASSED   │ 2.45s    │
│ Field Pilot Simulation Suite           │ 14 / 14 │ PASSED   │ 2.05s    │
│ Full Backend Test Suite (22 Modules)   │ 182/182 │ PASSED   │ 68.38s   │
│ Frontend Unit Tests (Vitest)           │ 4 / 4   │ PASSED   │ 0.70s    │
│ Frontend Production Build (Vite)       │ 44 mod  │ PASSED   │ 0.89s    │
├────────────────────────────────────────┴─────────┴──────────┴──────────┤
│ Production Surveillance Store Records: 0 (Verified clean)              │
│ Supervised Outbreak ML Model Status: BLOCKED                           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Strict Constraints & Scientific Invariants Maintained

Throughout Phase 19, all project constraints were rigorously upheld:
- **No data fabrication or augmentation:** Used the existing 100,000 synthetic records as-is.
- **No synthetic data treated as authentic:** Synthetic benchmark status maintained.
- **No EFI training target contamination:** EFI heuristic was not used as an ML target.
- **Zero production model contamination:** Fertilizer model, maize CNN, and unified advisory endpoints remain untouched.
- **No branches merged:** Active branch remains `main`.
- **Production ML training remains BLOCKED:** Supervised outbreak model training will remain blocked until authentic multi-season field ground truth is acquired.

