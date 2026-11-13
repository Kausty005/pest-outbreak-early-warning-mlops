# AgriAdapt AI — Definitive Dataset Registry (Phase 20)
**Document Reference:** `docs/phase20_dataset_registry.md`  
**Phase:** 20 — Final Data Foundation Integration, Experiment Reconciliation and Readiness Verification  
**Status:** COMPLETE & AUDITED  
**Date:** November 2026  
**Classification:** Internal Scientific & Governance Standard  

---

## 1. Executive Summary & Purpose

The AgriAdapt AI Pest Outbreak Early Warning platform maintains a strict multi-stream data foundation. To prevent severe methodological flaws—specifically data leakage, pseudo-replication, label distortion, and the conflation of simulation with biological ground truth—each data stream is strictly categorized, cryptographically hashed, and isolated within its designated operational boundary.

This registry serves as the authoritative, definitive catalog of all datasets existing within the repository as of the completion of Phase 20.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           AGRIADAPT AI DATA FOUNDATION                            │
├──────────────────────────┬──────────────────────────┬────────────────────────────┤
│   COVARIATE FOUNDATION   │  SITUATIONAL INTELLIGENCE│   EXPERIMENTAL BENCHMARK   │
│  612 Environmental Obs   │   49 Public Advisories   │   100,000 Synthetic Rows   │
│  (Open-Meteo & ERA5)     │   (SAUs & KVK Bulletins) │   (Seed 42 / LightGBM RF)  │
│  [FEATURE STORE READY]   │   [QUALITATIVE CONTEXT]  │   [EXPERIMENTAL USE ONLY]  │
├──────────────────────────┴──────────────────────────┴────────────────────────────┤
│   HISTORICAL ARCHIVE (QUARANTINED)       │  PROSPECTIVE FIELD SURVEILLANCE       │
│   13 Weekly Trial Observations           │  0 Commercial Scouting Records        │
│   (Lande 2005 · Akola Research Farm)     │  (Kharif 2027 Field Pilot Planned)    │
│   [STRICT RESEARCH QUARANTINE]           │  [PRODUCTION ML TRAINING: BLOCKED]    │
└──────────────────────────────────────────┴───────────────────────────────────────┘
```

---

## 2. Definitive Dataset Master Register

| Dataset ID | Name / Description | File Location | Source Authority | Cryptographic SHA-256 Checksum | Record Count | Dataset Classification | Permitted Use | Label Availability ($Y \in \{0, 1\}$) | Production Eligibility |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`DS-ENV-001`** | Aligned Environmental Covariates (2023) | `data/processed/aligned_environmental_surveillance_2023-06-01_2023-10-31.csv` | Open-Meteo API & Copernicus ERA5-Land Reanalysis | `50c9945e7765846d8db2a4d131cdd66f022d0ceac930827822c3dbcaf1b69866` | 612 rows | `COVARIATE_STORE` | Environmental favorability heuristic, feature lagging | None (Covariates only) | **ELIGIBLE** (As feature inputs only) |
| **`DS-ADV-002`** | Public Pest Advisories Corpus | `data/processed/public_advisories/extracted_advisories.json` | VNMKV, Dr. PDKV, KVK Nagpur/Yavatmal | `372294a8c0df1ec6a4393dfe040eed452ebf86eed0aefcbc5a83be4002b8d20b` | 49 records | `QUALITATIVE_INTELLIGENCE` | Qualitative risk triaging, extension alert corroboration | None (Text mentions only; NOT ground truth) | **DISALLOWED** (Must never be used as ML labels) |
| **`DS-HIST-003`** | Historical Research Trial Observations | `data/raw/pest_surveillance/historical_transcriptions/reconciled_transcription.csv` | Dr. PDKV Akola M.Sc. Thesis (Lande, 2005) | `0538eac35824e0513596ee2fd9365ddbee7dd0f62db451a5d65d8f6b988aaf93` | 13 weekly rows | `HISTORICAL_RESEARCH_TRIAL` | Phenology calibration, historical ETL benchmark | Non-standard research counts (0 commercial labels) | **QUARANTINED** (Isolated from production store) |
| **`DS-SYNT-004`** | Multicrop Synthetic Pest Forecasting Benchmark | `data/synthetic_multicrop_pest_forecasting.csv` | AgriAdapt Synthetic Simulation Engine (Seed 42) | `58e849439aa6e2f4330a9aaf44405025aa0414ef0c7cd6c6a936640af5c1c49d` | 100,000 rows | `SYNTHETIC_BENCHMARK` | Pipeline benchmarking, algorithm comparison, CI/CD | Synthetic simulated target (`outbreak_within_7d`) | **DISALLOWED** (Strictly experimental; no field deployment) |
| **`DS-SURV-005`** | Prospective Commercial Field Surveillance Store | `data/processed/pest_surveillance/field_surveillance_records.json` | Kharif 2027 Sentinel Scout Pilot & Institutional DUAs | *Pending store creation upon first field entry* | 0 rows | `PROSPECTIVE_SURVEILLANCE` | Supervised model training, operational outbreak alerting | Ground truth labels ($Y=1, Y=0$) upon acquisition | **MANDATORY** (Gate requires $\ge 500$ records to unblock) |

---

## 3. Deep-Dive Dataset Profiles

### 3.1. `DS-ENV-001`: Aligned Environmental Covariates
- **Temporal Horizon:** June 1, 2023 to October 31, 2023 (153 consecutive calendar days per district).
- **Spatial Coverage:** 4 core Vidarbha/Khandesh districts: Nagpur, Amravati, Yavatmal, Jalgaon ($4 \times 153 = 612$ records).
- **Core Parameters (10 Continuous Signals):**
  - Daily minimum, maximum, and mean 2-meter air temperature ($^\circ\text{C}$).
  - Daily minimum, maximum, and mean relative humidity ($\%$) at 2 meters.
  - Daily accumulated precipitation ($\text{mm}$).
  - Daily mean wind speed at 10 meters ($\text{km/h}$).
  - Daily volumetric soil moisture at 0–7 cm depth ($\text{m}^3/\text{m}^3$).
  - Daily 7-day rolling precipitation accumulation ($\text{mm}$).
- **Validation Audit:**
  - Missingness: 0.00% across all 612 records.
  - Physical Bounds: Temperature $[18.2^\circ\text{C}, 42.1^\circ\text{C}]$, Relative Humidity $[41.0\%, 98.5\%]$, Soil Moisture $[0.11, 0.44\,\text{m}^3/\text{m}^3]$. All within agro-climatological bounds.
- **Role in Platform:** Ingested into `src/pest_risk/environmental_heuristic.py` to compute Environmental Favorability Index (EFI) heuristic values for farmers and extension workers.

### 3.2. `DS-ADV-002`: Public Pest Advisories Corpus
- **Temporal Horizon:** Kharif 2023 to Rabi 2024 agricultural seasons.
- **Source Agencies:** Vasantrao Naik Marathwada Krishi Vidyapeeth (VNMKV) Parbhani, Dr. Panjabrao Deshmukh Krishi Vidyapeeth (Dr. PDKV) Akola, KVK Nagpur, KVK Yavatmal, and Agromet Advisory Services.
- **Granularity:** 49 structured JSON advisory objects parsed from regional agro-bulletins.
- **Data Modality:** Unstructured agronomic Marathi/English text mapped to crop, pest mention, alert severity level, advisory recommendations, and issue date.
- **Scientific Caveat:** Advisory bulletins are issued to prevent damage; they reflect regional weather alerts and subjective scout feedback across broad agro-zones. They **do not** reflect field-level economic threshold exceedance at a specific GPS coordinate. Converting an advisory alert into an $Y=1$ training label creates severe circular logic.

### 3.3. `DS-HIST-003`: Quarantined Historical Research Trials
- **Origin:** Dr. PDKV Akola Postgraduate Dissertation: *Studies on Seasonal Incidence and Management of Cotton Bollworms in Vidarbha* (Lande, G.K., 2005; Advisor: Dr. U.S. Satpute). Appendix Table VII.
- **Experimental Design:** Research trial conducted on Dr. PDKV Central Farm, Akola during Kharif 2004–2005 (13 consecutive standard meteorological weeks: SMW 32 to SMW 44). Unsprayed experimental plots under randomized block design.
- **Transcription Integrity:** Digitized via independent double-blind operator entry (`Operator A` vs `Operator B`).
  - Total Discrepancies: 0 fields out of 104 data points ($0.00\%$ discrepancy rate).
  - SHA-256 Checksum: `0538eac35824e0513596ee2fd9365ddbee7dd0f62db451a5d65d8f6b988aaf93`.
- **Reason for Quarantine:** Single research plot, single season, single location ($N=13$). Highly valuable for phenological validation, but unsuitable for training generalized machine learning models. Quarantined in `data/raw/pest_surveillance/historical_transcriptions/` to prevent contamination of the production training pipeline.

### 3.4. `DS-SYNT-004`: Multicrop Synthetic Pest Forecasting Benchmark
- **Record Volume:** 100,000 synthetic rows across 3 crop-pest archetypes:
  - Chickpea / *Helicoverpa armigera*: 32,521 rows (32.52%)
  - Tomato / *Tuta absoluta*: 28,688 rows (28.69%)
  - Wheat / *Sitobion avenae*: 38,791 rows (38.79%)
- **Target Variable:** `outbreak_within_7d` ($Y \in \{0, 1\}$). Overall positive prevalence: 16.89% (16,892 positive events).
- **Data Partitions (Purged Chronological Splitting with Embargoes):**
  - **Train:** 70,049 rows (2022-06-20 to 2024-07-27; Outbreak rate: 16.89%).
  - **Purge Gap 1:** 994 rows (2024-07-28 to 2024-08-03).
  - **Validation:** 14,034 rows (2024-08-04 to 2024-11-17; Outbreak rate: 16.86%).
  - **Purge Gap 2:** 864 rows (2024-11-18 to 2024-11-24).
  - **Test:** 14,059 rows (2024-11-25 to 2025-03-21; Outbreak rate: 16.83%; 2,366 positives, 11,693 negatives).
- **Experimental Models Trained:**
  - Full Pipeline (LightGBM): PR-AUC 0.9405, ROC-AUC 0.9576, Test Precision 0.8736, Test Recall 0.7422 (Thresh 0.77).
  - Environmental Pipeline (Random Forest): PR-AUC 0.3541, ROC-AUC 0.6548, Test Precision 0.2644, Test Recall 0.7798 (Thresh 0.49).
- **Governance Constraint:** Strictly labeled `SYNTHETIC_EXPERIMENTAL`. Cannot be used to issue production pesticide recommendations.

### 3.5. `DS-SURV-005`: Prospective Commercial Field Surveillance Store
- **Current Status:** 0 authentic records acquired. Store file `data/processed/pest_surveillance/field_surveillance_records.json` remains completely empty.
- **Pilot Design:** Kharif 2027 Field Surveillance Pilot across 4 districts (Nagpur, Amravati, Yavatmal, Jalgaon), 20 sentinel fields, 16 weekly visits ($N \ge 320$ prospective observations).
- **Target Complexes:** Cotton Pink Bollworm, Cotton American Bollworm, Soybean Tobacco Caterpillar, Rice Brown Planthopper, Maize Fall Armyworm.
- **Readiness Gate:** The platform enforces an automated gate (`src/pest_risk/production_readiness_gate.py`) requiring $\ge 500$ authentic multi-season observations, $\ge 50$ positive labels, $\ge 200$ negative windows, and 5 verified ETLs before production training can be unlocked.

---

## 4. Data Isolation & Contamination Defense Matrix

To guarantee scientific rigor, the platform enforces strict data isolation boundaries. Cross-contamination between datasets is prevented by automated pipeline checks:

| Source Dataset | Can Merge into Feature Store? | Can Serve as Training Target ($Y$)? | Can Be Mixed into Field Records? | Architectural Enforcement Mechanism |
| :--- | :---: | :---: | :---: | :--- |
| **`DS-ENV-001` (Environmental)** | **YES** | **NO** | **NO** | Covariate table keyed by `(district, date)`. No outcome labels present. |
| **`DS-ADV-002` (Advisories)** | **NO** | **NO** | **NO** | Kept in `data/processed/public_advisories/`. Explicit rejection in `surveillance_labeling.py`. |
| **`DS-HIST-003` (Research Trials)** | **NO** | **NO** | **NO** | Quarantined in `data/raw/pest_surveillance/historical_transcriptions/`. Physical directory isolation. |
| **`DS-SYNT-004` (Synthetic)** | **NO** | **NO** (Prod) | **NO** | Pipeline tagged `is_synthetic=True`. Readiness gate Criterion 11 scans for contamination and blocks training if detected. |
| **`DS-SURV-005` (Field Scouting)** | **YES** | **YES** (When ready) | **N/A** | Dedicated JSON store with SHA-256 provenance, scout credentials, and farmer consent IDs. |

---

## 5. Audit & Compliance Certification

- **Audited By:** AgriAdapt AI Lead MLOps Architect & Scientific Governance Committee
- **Verification Date:** November 13, 2026
- **Status:** **APPROVED & CERTIFIED**
- **Next Review Date:** Prior to Kharif 2027 Pilot Activation

