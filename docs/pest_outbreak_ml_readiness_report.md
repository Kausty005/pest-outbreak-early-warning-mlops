# Pest Outbreak ML Readiness Report

**Project:** AgriAdapt AI — Pest Outbreak Early Warning MLOps  
**Prepared by:** AgriAdapt AI Research Team  
**Status:** ⚠️ NOT ML-READY — Supervised training blocked pending authentic surveillance data  
**Date:** November 2026 (Updated Phase 10)

---

> [!CAUTION]
> **This project does NOT currently have a trained, validated pest outbreak prediction model.** The Environmental Favorability Index (EFI) engine is an experimental heuristic tool — it is NOT a machine learning model and its outputs are NOT calibrated outbreak probabilities.

---

## 1. Infrastructure Readiness

| Component | Status | Notes |
|---|---|---|
| Environmental data ingestion pipeline | ✅ **READY** | Open-Meteo + ERA5-Land (612 records) |
| Public advisory intelligence pipeline | ✅ **READY** | 49 records, 10 documents, 3 languages, verbatim quotes |
| DVC data versioning | ✅ **READY** | Stages configured |
| Surveillance data schema (Pydantic, 28 cols) | ✅ **READY** | Bounds, compatibility validated |
| Provenance & SHA-256 integrity | ✅ **READY** | Per-file hash log |
| Geospatial alignment (Haversine, 60 km limit) | ✅ **READY** | 4-station grid |
| IMD SMW temporal alignment | ✅ **READY** | Causal [T-6, T] window |
| Forward 7-day ETL labeling | ✅ **READY** | Zero lookahead; active negatives |
| ETL verification status governance | ✅ **READY** | PARTIALLY_VERIFIED for all 5 pairs |
| Test suite | ✅ **119 passed, 0 failed** | Pytest 119 passed; Vitest 4 passed |
| Backend API (FastAPI) | ✅ **READY** | EFI & Public Advisory endpoints live |
| Frontend (React) | ✅ **READY** | EFI & Public Advisory UI tabs active |
| MLflow experiment tracking | ✅ **READY** | Local tracking server |

---

## 2. Environmental Data Availability

| Item | Value |
|---|---|
| **Records available** | 612 daily records |
| **Districts covered** | Nagpur, Amravati, Yavatmal, Jalgaon |
| **Period** | 1 June 2023 – 31 October 2023 (Kharif 2023) |
| **Weather source** | Open-Meteo Historical Weather API |
| **Soil moisture source** | Copernicus ERA5-Land (topsoil volumetric water) |
| **Features computed** | Temperature (mean/max/min), humidity, rainfall, soil moisture, GDD, rolling 3/7/14-day averages |
| **Sufficiency for ML training** | ❌ **INSUFFICIENT ALONE** — Environmental data without matching surveillance labels cannot train a supervised model |

---

## 3. Pest Surveillance Data Availability

| Item | Value |
|---|---|
| **Authentic records received** | **0** |
| **Verified outbreak labels (label = 1)** | **0** |
| **Verified non-outbreak labels (label = 0)** | **0** |
| **Institutions contacted** | 0 (letters drafted, not yet dispatched) |
| **MoU/NDA signed** | 0 |

> [!IMPORTANT]
> **Supervised ML training is BLOCKED.** No authentic, institutionally sourced pest observation records have been received. Training a model without verified surveillance labels would produce scientifically unjustified predictions.

---

## 4. ETL Scientific Validation Status

| Crop-Pest Pair | ETL (Incidence %) | ETL (Trap Catch) | Verification Status | Notes |
|---|---|---|---|---|
| Cotton — Pink Bollworm | 10% rosette/bolls | 8 moths/trap/night | **PARTIALLY_VERIFIED** | Consistent with ICAR-CICR advisories and multiple secondary sources; original 2021 bulletin not independently obtained |
| Cotton — American Bollworm | 5% square damage / 1 larva/plant | 5 moths/trap/night | **PARTIALLY_VERIFIED** | Consistent with ICAR-NCIPM CPMS and TNAU guidelines; original NCIPM document not independently obtained |
| Soybean — Tobacco Caterpillar | 20% defoliation | 10 moths/trap/night | **PARTIALLY_VERIFIED** | Consistent with ICAR-IISR Indore and ICAR-IIGR advisories; range is 20–25% across sources |
| Rice — Brown Planthopper | 10 hoppers/hill (tillering) | None (no pheromone ETL) | **PARTIALLY_VERIFIED** | 10/hill is lower bound; range 5–20/hill by growth stage; ICAR-CRRI advisories referenced |
| Maize — Fall Armyworm | 10% whorl damage (V4-V8) | 5 moths/trap/night | **PARTIALLY_VERIFIED** | FAO FAMEWS and PPQS India guidelines confirm stage-specific thresholds |

> **Labeling safety rule (Phase 7):** Any ETL downgraded to `UNVERIFIED` will cause `compute_forward_outbreak_label()` to return `label_status="ETL_UNVERIFIED"` and `outbreak_label_7d=None`, preventing scientifically unsupported label generation.

---

## 5. Labeling Methodology Assessment

### 5.1 Forward Window Design

The 7-day forward window [T+1, T+7] is scientifically appropriate for:

| Pest | Biological Justification | Window Adequacy |
|---|---|---|
| Pink Bollworm | Egg-to-neonate larva period ~5–7 days; flower infection to detection lag ~3–5 days | ✅ Adequate |
| American Bollworm | Egg incubation 3–5 days; rapid early larval damage | ✅ Adequate |
| Tobacco Caterpillar | Gregarious hatching → mass defoliation within 5–7 days of egg mass eclosion | ✅ Adequate |
| Brown Planthopper | Population build-up can be rapid (2–3 days at hopperburn threshold); 7-day window may undercount hopper cycles | ⚠️ Borderline — BPH population dynamics faster than weekly scouting interval |
| Fall Armyworm | Egg to 1st-instar ~3 days; visible whorl damage within 5–7 days | ✅ Adequate |

> **Limitation noted for BPH:** A 7-day forward window for Brown Planthopper may insufficiently capture the full population explosion cycle. If and when BPH surveillance data is obtained, consider also computing a 14-day label as an alternative target.

### 5.2 Active Negative Sampling Principle

The labeling protocol enforces **active negative sampling**: a label of `0` (non-outbreak) is assigned only when a verified field scouting visit in the [T+1, T+7] window reports sub-ETL levels. Absence of a record is coded as `None` (unobserved). This prevents the common machine learning pitfall of treating missing data as confirmed negatives.

---

## 6. Minimum Dataset Requirements and Caveats

### 6.1 Estimated Requirements

The following estimates were computed for a district-level binary classifier using Random Forest or Gradient Boosting with ~12–15 features:

| Requirement | Minimum Estimate | Preferred | Basis |
|---|---|---|---|
| Total scouting visits | 2,500 | 5,000+ | Rule of thumb: ~200 records/feature for robust generalization |
| Positive outbreak events (label=1) | 250 | 500+ | Minimum ~10% positive event rate for binary classification |
| Consecutive Kharif seasons | 2 | 3 | For temporal generalization across inter-annual weather variability |
| Districts | 4 | 7+ | Spatial generalization across Vidarbha/Khandesh agro-climatic zones |
| Talukas with ≥10 visits each | 10 | 15+ | To reduce spatial autocorrelation bias |

### 6.2 Caveats

> [!WARNING]
> The numbers above are **heuristic estimates**, not formally validated sample-size calculations. The actual required dataset size depends on:
> - **Positive event prevalence** — If outbreaks occur in <5% of observations, the positive class is severely imbalanced and standard precision-recall analysis on 2,500 records may be insufficient.
> - **Spatial autocorrelation** — Adjacent taluka observations on the same day are not independent. Effective sample size is smaller than raw record count. Spatial cross-validation (leave-one-district-out) is mandatory.
> - **Temporal autocorrelation** — Weekly records within the same season are serially correlated. Temporal hold-out validation (leave-one-season-out) is mandatory.
> - **Feature dimensionality** — Adding more derived features beyond ~15 without increasing record count risks overfitting.
>
> A formal statistical power analysis (e.g., using `MLDataSize` or Monte Carlo simulation with pilot data) should be performed once an initial dataset of ≥500 records is available.

---

## 7. Phased Data Acquisition Strategy

### Dataset A — Pilot (Target: 6–12 months post letter dispatch)

| Goal | Acquire records from CROPSAP or ICAR-CICR for 1–2 Kharif seasons, 2 districts |
|---|---|
| Use | Pilot model training with spatial leave-one-out cross-validation |
| Minimum | 500 total records, ≥50 positive events |
| Expected model quality | Low-medium reliability; high uncertainty bands |
| Appropriate use | Research exploration; NOT for farmer-facing alerts |

### Dataset B — Expanded (Target: 12–24 months)

| Goal | Acquire records from multiple CROPSAP districts and ≥2 SAU research stations |
|---|---|
| Use | Full model training, evaluation, and robustness testing |
| Minimum | 2,500 records, ≥250 positive events, ≥3 seasons |
| Expected model quality | Medium reliability; publishable metrics |
| Appropriate use | Research validation; controlled pilot with extension advisors |

### Dataset C — Generalised (Target: 24–36 months)

| Goal | Multi-district, multi-season dataset with joint CROPSAP + ICAR validation |
|---|---|
| Use | Operational model deployment with seasonal retraining |
| Minimum | 5,000+ records, ≥500 positive events, 4+ seasons |
| Expected model quality | High reliability with calibrated uncertainty estimates |
| Appropriate use | Farmer-facing advisory (with explicit uncertainty communication) |

---

## 8. Existing Components — Preservation Status

The following system components are **operational and must not be modified**:

| Component | Status | Location |
|---|---|---|
| Environmental Pest Risk Engine (EFI) | ✅ OPERATIONAL | `src/pest_risk/` |
| Pest Risk API endpoint | ✅ OPERATIONAL | `backend/app/api/pest_risk.py` |
| Public Advisory Ingestion Pipeline | ✅ OPERATIONAL | `src/data_ingestion/public_advisories/` |
| Public Advisory API endpoint | ✅ OPERATIONAL | `backend/app/api/public_advisories.py` |
| Maize Leaf Disease CNN classifier | ✅ OPERATIONAL | `backend/app/api/` (separate) |
| Fertilizer Prediction Model | ✅ OPERATIONAL | `backend/app/api/fertilizer.py` |
| Unified Advisory Endpoint | ✅ OPERATIONAL | `backend/app/api/advisory.py` |
| Frontend (React) | ✅ OPERATIONAL | `frontend/src/` |

---

## 9. What Must NOT Happen

> [!CAUTION]
> The following actions are explicitly prohibited before authentic surveillance data is obtained:
>
> 1. **Training a supervised outbreak prediction model on EFI-derived pseudo-labels or synthetic data.**
> 2. **Labelling EFI scores as "outbreak probability" or "outbreak prediction" in any user-facing output.**
> 3. **Merging `origin/omkar` model artifacts into `main` without prior data provenance audit.**
> 4. **Generating or using synthetic surrogate surveillance labels (even for prototype exploration).**
> 5. **Presenting interim research findings as a validated model without independent evaluation.**

---

## 10. Summary Verdict

| Dimension | Status |
|---|---|
| Data infrastructure | ✅ Ready |
| Environmental data | ✅ Partial (Kharif 2023, 4 districts only) |
| Surveillance data | ❌ Absent — BLOCKED |
| ETL scientific basis | ⚠️ Partially Verified — requires original source retrieval |
| Supervised ML training | ❌ **BLOCKED** |
| Experimental EFI tool | ✅ Operational (clearly labelled as experimental) |
| **Overall ML Readiness** | ❌ **NOT READY** |

**Next milestone to unblock training:** Receipt of ≥500 authentic surveillance records (Dataset A) under a signed institutional MoU, followed by ETL primary source verification.

