# Phase 11 — Field Surveillance Pilot Activation and First Authentic Data Acquisition Report

**Project:** AgriAdapt AI / Pest Outbreak Early Warning MLOps  
**Component:** Field Surveillance Pilot Activation, Direct Data Entry & Batch CSV Validation Workflow  
**Target Region:** Maharashtra, India (Nagpur, Amravati, Yavatmal, Jalgaon)  
**Authors:** Senior Data Engineer, Agricultural Machine Learning Engineer, Plant Pathologist, and MLOps Architect  
**Date:** November 13, 2026  
**Status:** **PHASE 11 COMPLETE — INTERFACE & BATCH WORKFLOW OPERATIONAL — SUPERVISED ML TRAINING BLOCKED**

---

## Executive Summary

Phase 11 moves the AgriAdapt AI pest surveillance architecture from passive design to active operational readiness. Prior to Phase 11, the project possessed a standardized schema, alignment logic, and draft institutional requests, but lacked practical mechanisms for field scouts or research partners to enter observations, upload batches, run validation, or conduct entomological reviews.

Through Phase 11:
1. **Acquisition Framework Gaps Closed:** Implemented a full-stack field surveillance infrastructure featuring a dedicated FastAPI router (`/api/v1/pest-surveillance`), Pydantic schemas, and a rich React interface (`FieldSurveillanceSection.jsx`).
2. **Updated Kharif 2027 Pilot Schedule:** Replaced the elapsed 2026 pilot dates with an operational roadmap centered on **Kharif 2027** (June 15 – November 15, 2027), supported by preparatory institutional engagement during December 2026 – May 2027.
3. **Submission-Ready Institutional Packages:** Expanded the institutional portfolio to include 4 new targeted collaboration packages for **KVK Nagpur**, **KVK Yavatmal**, **Dr. PDKV Akola**, and **VNMKV Parbhani**, alongside the statewide CROPSAP and ICAR-CICR packages.
4. **Field Data Entry & Batch CSV Validation:** Built dual ingestion pathways: (a) single-observation form with real-time biological compatibility, geographic boundary, and physical range checks; and (b) batch CSV upload with SHA-256 provenance, duplicate detection, and structural validation reporting.
5. **Human Review & Audit Trail:** Implemented an immutable human review workflow (`HumanReviewAuditEntry`) allowing KVK experts to inspect, approve, reject, or correct observations. Newly entered records default strictly to `UNVERIFIED` or `DRAFT` and are **never automatically verified**.
6. **Data Acquisition Progress Dashboard:** Deployed a real-time progress dashboard displaying true ground truth metrics. It reports **0** across all metrics (zero authentic observations received, zero synthetic records), maintaining complete transparency.
7. **Scientific Readiness Gate Enforced:** Documented multi-criteria thresholds (independent fields, $\ge 250$ positive outbreak events, verified negative windows, temporal and spatial leakage isolation) that must be satisfied before supervised ML model training can be unblocked.

---

## 1. Audit of the Acquisition Framework & Implementation Gaps

Prior to Phase 11, an audit of `src/data_ingestion/pest_surveillance/` identified the following implementation gaps:

| Component | Status Prior to Phase 11 | Implementation Action in Phase 11 |
| :--- | :--- | :--- |
| **Backend Surveillance API** | Missing (Pipeline existed only as CLI / script modules) | Implemented `backend/app/api/pest_surveillance.py` with 5 endpoints (`/dashboard`, `/records`, `/upload-csv`, `/review`). |
| **Frontend Entry Interface** | Missing (Only Farm Dashboard, Advisory, and EFI tabs existed) | Built `frontend/src/components/FieldSurveillanceSection.jsx` and added dedicated **🔍 Field Surveillance** tab in main navigation. |
| **Batch CSV Upload Engine** | Script-only loader | Implemented automated multipart CSV upload with cryptographic SHA-256 hashing and raw archive isolation (`data/raw/pest_surveillance/`). |
| **Human Review Workflow** | Conceptual schema in Phase 10 | Implemented interactive review modal with immutable audit logging (`surveillance_audit_log.json`). |
| **Pilot Timing Alignment** | Outdated (July–October 2026 window had elapsed) | Formulated updated **Kharif 2027** timeline and preparatory schedule. |
| **Institutional Requests** | Statewide only (CROPSAP, ICAR-CICR) | Authored 4 specialized local packages for KVKs and regional agricultural universities. |

---

## 2. Updated Maharashtra Pilot Timeline (Kharif 2027)

Because the 2026 Kharif crop cycle has concluded, attempting to retrospectively execute a 2026 field pilot is physically impossible. We have established an updated prospective operational roadmap:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 MAHARASHTRA FIELD SURVEILLANCE TIMELINE                     │
├──────────────────────────┬──────────────────────────────────────────────────┤
│ Phase / Timeframe        │ Operational Milestone & Activities               │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Preparatory Phase I      │ Institutional Request Dispatch                   │
│ (Dec 2026 – Feb 2027)    │ Complete academic credentials; supervisor sign-  │
│                          │ off; formal dispatch to CROPSAP, CICR, PDKV,     │
│                          │ VNMKV, and KVKs.                                 │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Preparatory Phase II     │ Sentinel Plot Selection & Scout Training         │
│ (Mar 2027 – May 2027)    │ Finalize 20 sentinel farm agreements across      │
│                          │ Nagpur, Amravati, Yavatmal, Jalgaon; scout       │
│                          │ calibration on sampling and digital data entry.  │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Ingestion Gate Check     │ Historical Ingestion Window                      │
│ (Ongoing upon receipt)   │ Ingest any historical CSVs provided by institutes│
│                          │ through the batch CSV validation workflow.       │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Kharif 2027 Field Pilot  │ 16 Weekly Longitudinal Field Scouting Visits     │
│ (June 15 – Oct 31, 2027) │ Continuous sampling across 20 sentinel plots     │
│                          │ (320 visits total). Pheromone trap catch logging │
│                          │ every 3 days; green boll dissections weekly.     │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ Review & Labeling Audit  │ Data Verification & Labeling Run                 │
│ (Nov 1 – Nov 30, 2027)   │ Entomological audit of all records; execute      │
│                          │ forward-window [T+1, T+7] ETL labeling logic.   │
├──────────────────────────┼──────────────────────────────────────────────────┤
│ ML Readiness Gate Check  │ Final Sufficiency & Leakage Evaluation           │
│ (Dec 2027)               │ Assess sample size, class balance, and spatial   │
│                          │ isolation before unlocking Phase 12 training.    │
└──────────────────────────┴──────────────────────────────────────────────────┘
```

---

## 3. Institutional Engagement Packages

We prepared six complete, submission-ready collaboration request packages. Each includes clear academic affiliation placeholders, explicit requested variables, and legally sound privacy and non-commercial covenants:

1. **Statewide Crop Pest Surveillance Project (CROPSAP):**
   - File: `docs/institutional_data_request_cropsap.md`
   - Target: Commissionerate of Agriculture, Maharashtra (Pune).
   - Scope: Historical village-level scouting CSVs (Kharif 2021–2024).
2. **ICAR - Central Institute for Cotton Research (ICAR-CICR):**
   - File: `docs/institutional_data_request_icar_cicr.md`
   - Target: Director & Crop Protection Division, Nagpur.
   - Scope: Bollworm pheromone trap catches, rosette flower counts, and green boll dissection records.
3. **Krishi Vigyan Kendra (KVK), Nagpur:**
   - File: `docs/institutional_data_request_kvk_nagpur.md`
   - Target: Senior Scientist & Head, KVK Nagpur (CICR Campus).
   - Scope: On-Farm Trial (OFT) and Front-Line Demonstration (FLD) records for cotton and soybean.
4. **Krishi Vigyan Kendra (KVK), Yavatmal:**
   - File: `docs/institutional_data_request_kvk_yavatmal.md`
   - Target: Senior Scientist & Head, KVK Yavatmal (PDKV Campus).
   - Scope: Intensive cotton bollworm scouting records from Yavatmal talukas (Darwha, Pusad, Ghatanji).
5. **Dr. Panjabrao Deshmukh Krishi Vidyapeeth (PDKV), Akola:**
   - File: `docs/institutional_data_request_pdkv_akola.md`
   - Target: Director of Research & Dept. of Agricultural Entomology.
   - Scope: University research station data and entomological threshold validation.
6. **Vasantrao Naik Marathwada Krishi Vidyapeeth (VNMKV), Parbhani:**
   - File: `docs/institutional_data_request_vnmkv_parbhani.md`
   - Target: Director of Research & Dept. of Agricultural Entomology.
   - Scope: Fall Armyworm (*Spodoptera frugiperda*) monitoring data in maize and cotton IPM trials.

> [!IMPORTANT]
> **GOVERNANCE NOTICE:** None of these packages have been transmitted. Formal dispatch requires user authorization, completed supervisor details, and departmental seal.

---

## 4. Field Data Collection Interface

We implemented a full-featured, responsive data collection interface:
- **Backend Router:** `backend/app/api/pest_surveillance.py` registered at `/api/v1/pest-surveillance`.
- **Frontend Component:** `frontend/src/components/FieldSurveillanceSection.jsx`.
- **Navigation:** Integrated into `frontend/src/App.jsx` under the **🔍 Field Surveillance** tab.

### 4.1 Data Entry Validation Engine
The interface enforces rigorous client-side and server-side validation:
- **Mandatory Field Enforcement:** Observation date, district, crop, pest, observer ID, and at least one quantitative metric (incidence %, severity %, trap catch count, or affected plant count) are mandatory for submitted records.
- **Biological Compatibility Checks:** Enforces valid crop-pest pairs (e.g. Cotton + Pink Bollworm, Soybean + Tobacco Caterpillar, Maize + Fall Armyworm). Any invalid pairing (e.g. Rice + Pink Bollworm) is immediately blocked with an HTTP 422 error and descriptive alert.
- **Geographic Boundary Checks:** Latitude ($15.6^\circ$ to $22.1^\circ\text{ N}$) and Longitude ($72.6^\circ$ to $80.9^\circ\text{ E}$) are strictly validated against Maharashtra boundaries.
- **Physical Range Bounds:** Incidence and severity are bounded within $[0.0, 100.0]\%$; days since sowing bounded within $[0, 365]$; plants sampled $\ge 1$.
- **Draft Mode:** Observers can save incomplete observations with `is_draft: true`, storing them with status `"DRAFT"` without failing mandatory constraints.
- **Zero Auto-Verification:** Submitted records strictly default to `"UNVERIFIED"`, requiring formal review before entering the validated pool.

---

## 5. Batch CSV Upload and Quality Review Workflow

For institutional datasets or field spreadsheets, the platform provides a secure batch upload pipeline:

```
[ Uploaded CSV File ]
         │
         ▼
[ SHA-256 Provenance Hashing ] ──► Compute 64-char hash; isolate copy in data/raw/pest_surveillance/
         │
         ▼
[ Schema & Boundary Validation ] ──► Check columns against SurveillanceRecord; verify bounds & biology
         │
         ▼
[ Duplicate Detection Engine ] ──► Flag identical (Date, District, Village, Crop, Pest, Method) tuples
         │
         ▼
[ Quality Validation Report ] ──► Total rows, valid rows, invalid rows, duplicates, error details
         │
         ▼
[ Queue Ingestion (UNVERIFIED) ] ──► Valid records appended to data/processed/pest_surveillance/
         │
         ▼
[ Human Review Queue ] ──► Entomologist reviews notes, approves (KVK_EXPERT_VALIDATED) or rejects
         │
         ▼
[ Immutable Audit Trail ] ──► Logs review action, reviewer ID, timestamp, and justification
```

---

## 6. Data Quality Reporting Before Label Generation

Every batch processed through `/api/v1/pest-surveillance/upload-csv` generates a standardized `SurveillanceUploadResponse` capturing comprehensive metrics:

- **Volume:** `total_rows_processed`, `valid_rows_count`, `invalid_rows_count`.
- **Integrity:** `duplicates_detected`, `file_sha256`.
- **Validation Audit:** `validation_passed` (boolean), `passed_checks`, `failed_checks`, `errors` list.

### Strict Status Distinctions:
1. `DRAFT`: Incomplete field scout entry; excluded from validation calculations.
2. `UNVERIFIED`: Valid format, but pending entomologist review; **cannot generate outbreak labels**.
3. `FIELD_SCOUT_VERIFIED`: Confirmed by field supervisor.
4. `KVK_EXPERT_VALIDATED`: Confirmed by agricultural university or KVK entomologist; **eligible for forward-window outbreak labeling**.
5. `REJECTED`: Invalid, corrupted, or biologically implausible entry; quarantined with audit notes.

---

## 7. Review of Economic Threshold Level (ETL) Verification Blockers

In Phase 7, all five registered ETL pairs in `surveillance_labeling.py` were categorized as `PARTIALLY_VERIFIED`. To ensure transparency before any future labeling occurs, we constructed the primary source verification matrix:

| Crop & Pest Species | Implemented Threshold Value | Current Status | Primary Source Required | Secondary Reference Currently Cited | Missing Primary Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cotton — Pink Bollworm** (*P. gossypiella*) | 10% rosette flowers or 10% damaged green bolls; OR 8–10 moths/trap/night | `PARTIALLY_VERIFIED` | ICAR-CICR Official Technical Bulletin (Dr. K.R. Kranthi et al.) | ICAR-CICR Nagpur Pink Bollworm Advisory (2019–2021 edition) | Original printed monograph page citation and official CICR advisory circular number. |
| **Cotton — American Bollworm** (*H. armigera*) | 5% damaged squares/fruiting bodies or 1 larva/plant; OR 5 moths/trap/night | `PARTIALLY_VERIFIED` | ICAR-NCIPM Cotton IPM Package (CPMS Guidelines) | NCIPM Technical Guidelines for Kharif Cotton | Specific page/table number from official NCIPM Pusa Campus publication. |
| **Soybean — Tobacco Caterpillar** (*S. litura*) | 20–25% defoliation; OR 10 larvae/m row; OR 10 moths/trap/night | `PARTIALLY_VERIFIED` | ICAR-IISR Indore Soybean Package of Practices | ICAR-IISR Indore IPM Advisory & NCIPM Soybean Advisory | Original IISR technical bulletin volume and year of threshold adoption. |
| **Rice — Brown Planthopper** (*N. lugens*) | 10 planthoppers/hill at tillering; 15–20 hoppers/hill at heading | `PARTIALLY_VERIFIED` | ICAR-NRRI Cuttack Rice Pest Advisory | ICAR-CRRI / IRRI Rice Knowledge Bank | Direct NRRI technical bulletin citation specifying Maharashtra rainfed ecosystem limits. |
| **Maize — Fall Armyworm** (*S. frugiperda*) | 10% damaged whorls (mid-whorl V4–V8); 5% at seedling; OR 5 moths/trap/night | `PARTIALLY_VERIFIED` | FAO FAMEWS Field Manual (2018) & ICAR-IIMR Ludhiana FAW Advisory | FAO FAMEWS Field Manual & PPQS India FAW Guidelines | Specific Indian PPQS/IIMR gazette notification confirming 10% whorl damage ETL for Peninsular India. |

> [!NOTE]
> In accordance with our labeling safety invariant, `PARTIALLY_VERIFIED` thresholds are permitted for research validation, but any `UNVERIFIED` threshold immediately blocks label generation (`label_status = "ETL_UNVERIFIED"`). Thresholds will **not** be upgraded to `VERIFIED` until original institutional bulletins are physically retrieved and archived.

---

## 8. Data Acquisition Progress Dashboard

The live progress dashboard is exposed via `GET /api/v1/pest-surveillance/dashboard` and displayed in the frontend:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 LIVE DATA ACQUISITION PROGRESS DASHBOARD                    │
├─────────────────────────────────────────┬───────────────────────────────────┤
│ Metric                                  │ Value (Current Ground Truth)      │
├─────────────────────────────────────────┼───────────────────────────────────┤
│ Total Authentic Records Received        │ 0 (Zero authentic records)        │
│ Unique Monitored Sentinel Fields        │ 0 (Target: 20 plots)              │
│ Verified Records (KVK Validated)        │ 0                                 │
│ Unverified Records Pending Review       │ 0                                 │
│ Draft Incomplete Entries                │ 0                                 │
│ Verified Positive Outbreak Windows (1)  │ 0                                 │
│ Verified Active Negative Windows (0)    │ 0                                 │
│ Synthetic Records Allowed               │ False (Strictly Enforced)         │
│ Supervised Outbreak Model Training      │ BLOCKED                           │
└─────────────────────────────────────────┴───────────────────────────────────┘
```

The dashboard reports **exact real-world values** (0 where no data exists), rejecting synthetic mockups or simulated counters.

---

## 9. Scientific Readiness Criteria for Phase 12 ML Training

A sample count of 500 records is a necessary starting point, but is **not by itself sufficient** to unlock supervised machine learning early-warning model training. 

Before Phase 12 model training can begin, the dataset must satisfy the following multi-criteria readiness gate:

1. **Independent Spatial Footprint:** Minimum of **15–20 geographically distinct sentinel fields** separated by $\ge 15\text{ km}$ across at least 3 distinct agro-ecological zones (to prevent spatial autocorrelation leakage).
2. **Multi-Season Temporal Span:** Minimum of **2 full growing seasons** (or 1 multi-season historical export + 1 prospective pilot season) to ensure models learn climate variability rather than memorizing a single monsoon anomaly.
3. **Class Representation:** Minimum of **$\ge 150$ verified positive outbreak events** ($y = 1$) where scouting incidence or trap catches independently breached official ETLs.
4. **Active Negative Verification:** Minimum of **$\ge 350$ verified negative observation windows** ($y = 0$) backed by documented scouting showing sub-ETL levels.
5. **Species-Specific Isolation:** Models must be trained per crop-pest pair (e.g. separate models for Cotton Pink Bollworm vs Soybean Tobacco Caterpillar), never pooled into a generic target.
6. **Leakage Verification:** Mathematical verification that all features $X_T$ are strictly computed over $[T-6, T]$ and all labels $y_T$ are strictly computed over $[T+1, T+7]$.

---

## 10. Regression Testing & System Verification

We executed full regression verification across the entire project repository:

1. **Backend Test Suite (Pytest):**
   - Executed: `python -m pytest tests/`
   - Result: **126 passed, 0 failed** in 49.32s (including 7 new dedicated tests in `tests/test_api_pest_surveillance.py`).
2. **Frontend Test Suite (Vitest):**
   - Executed: `npm --prefix frontend test -- --run`
   - Result: **4 passed, 0 failed** in 8.79s (`src/__tests__/App.test.jsx`).
3. **Frontend Production Build (Vite):**
   - Executed: `npm --prefix frontend run build`
   - Result: **Built cleanly in 967ms** (`dist/assets/index-Bgi8KPav.js`).
4. **Preserved Invariants:**
   - Environmental Favorability Index (EFI) engine: **Unmodified and fully operational.**
   - Public agricultural advisory ingestion: **Unmodified and operational.**
   - Unified advisory endpoint (`/api/v1/advisory/unified`): **Operational.**
   - Fertilizer dosage model & maize CNN classifier: **Preserved and untouched.**
   - Supervised outbreak prediction model training: **Firmly BLOCKED.**

---

## 11. Summary of Deliverables

- `backend/app/schemas/pest_surveillance.py`: Pydantic input/output models for surveillance data.
- `backend/app/api/pest_surveillance.py`: FastAPI endpoints for dashboard, entry, CSV upload, and human review.
- `frontend/src/components/FieldSurveillanceSection.jsx`: Dedicated React interface for surveillance data entry, validation, and review.
- `frontend/src/services/api.js`: Client methods for surveillance endpoints.
- `tests/test_api_pest_surveillance.py`: 7 comprehensive backend API tests.
- `docs/institutional_data_request_kvk_nagpur.md`: Collaboration request for KVK Nagpur.
- `docs/institutional_data_request_kvk_yavatmal.md`: Collaboration request for KVK Yavatmal.
- `docs/institutional_data_request_pdkv_akola.md`: Collaboration request for Dr. PDKV Akola.
- `docs/institutional_data_request_vnmkv_parbhani.md`: Collaboration request for VNMKV Parbhani.
- `docs/phase11_field_surveillance_pilot_activation_report.md`: Complete Phase 11 milestone documentation.

