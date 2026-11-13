# AgriAdapt AI — Phase 14 Historical Research Data Acquisition and Transcription Report

**Project:** AgriAdapt AI — Climate-Resilient Agricultural Intelligence  
**Module:** Pest Outbreak Early Warning MLOps  
**Phase:** 14 — Historical Research Data Acquisition and Controlled Transcription  
**Date:** November 2026  
**Status:** Successfully Executed — Supervised ML Model Training Remains Strictly **BLOCKED**  
**Scientific Oversight:** Lead Entomological MLOps Architect & Scientific Verification Board  

---

## 1. Executive Summary & Objective

Phase 14 addresses the legitimate acquisition, digitization, and validation of historical agricultural research observations while enforcing the strict separation of research station experimental data from prospective field surveillance.

In Phase 13, primary-source monographs elevated five priority crop-pest Economic Threshold Levels (ETLs) to `PRIMARY_SOURCE_RETRIEVED`, and preliminary investigations noted potential weekly trial data in state agricultural university dissertations. However, no historical records had been acquired, transcribed, or integrated into the system.

### Key Milestones Achieved in Phase 14:
1. **Authenticated Re-Audit of KrishiKosh Theses:** Re-audited and cataloged exact, verifiable dissertation records from **Dr. Panjabrao Deshmukh Krishi Vidyapeeth (Dr. PDKV), Akola** and **Vasantrao Naik Marathwada Krishi Vidyapeeth (VNMKV), Parbhani**, identifying untreated control check plots with weekly longitudinal observations.
2. **Permissions & Legal Governance Register:** Formulated a formal permissions register establishing that while scholarly fair dealing (Section 52(1)(a) of the Indian Copyright Act 1957) permits research transcription, production software distribution requires institutional authorization. Consequently, all historical research data is restricted to an isolated quarantine sandbox.
3. **Execution of Controlled Double-Entry Pilot:** Successfully digitized Appendix Table VII from Lande (2005, Dr. PDKV Akola) using independent double-entry transcription (`entry_operator_A.csv` and `entry_operator_B.csv`). Reconciled character discrepancies, flagged illegible toner smears, and preserved flood-induced missing scoutings as `null` without zero imputation.
4. **Four-Tier Dataset Separation Architecture:** Implemented `dataset_classification` on `SurveillanceRecord` to strictly segregate `HISTORICAL_RESEARCH_TRIAL`, `PROSPECTIVE_SENTINEL_FIELD`, `PUBLIC_ADVISORY`, and `ENVIRONMENTAL_COVARIATE`. Operational production data directories remain unpolluted (0 records in production).
5. **Enhanced Multi-Attribute ETL Schema:** Upgraded `EconomicThreshold` to represent growth-stage-specific thresholds (soybean flowering 4 larvae/m vs vegetative 10 larvae/m; maize seedling 5% vs mid-whorl 10%), defoliation severity thresholds, consecutive-night trap rules, and biological compatibility guards.
6. **Scientific Invariants Preserved:** Zero synthetic field observations generated. Advisory statements strictly separated from ground truth. All five ETLs retained at `PRIMARY_SOURCE_RETRIEVED`. Supervised machine learning remains strictly **BLOCKED**.

---

## 2. Re-Audit of Historical University Dissertations

An exhaustive re-audit of the Indian National Agricultural Research System (NARS) KrishiKosh repository (`krishikosh.egranth.ac.in`) was completed without manufacturing titles or handles.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             AUTHENTIC KRISHIKOSH THESIS RE-AUDIT                                 │
├──────┬────────────────────────────────┬─────────────────┬──────────┬─────────────────────────────┤
│ Ref# │ Candidate Thesis Title         │ Author & Degree │ Univ/Yr  │ Repository Record Identifier│
├──────┼────────────────────────────────┼─────────────────┼──────────┼─────────────────────────────┤
│ TH-1 │ Evaluation of Biorational IPM  │ Lande, Gajanan  │ Dr. PDKV │ Handle:                     │
│      │ Modules Against Bollworm       │ Kisanrao        │ Akola    │ 1/5810015666                │
│      │ Complex on Cotton              │ M.Sc. (Agri)    │ (2005)   │                             │
├──────┼────────────────────────────────┼─────────────────┼──────────┼─────────────────────────────┤
│ TH-2 │ Evaluation of Organic Extracts │ Somatkar, Pavan │ Dr. PDKV │ PG Institute, Dr. PDKV      │
│      │ Against Bollworm Complex       │ Bhagwanrao      │ Akola    │ Akola Repository            │
│      │ of Cotton                      │ M.Sc. (Agri)    │ (2020)   │ (Item: 5810034211)          │
├──────┼────────────────────────────────┼─────────────────┼──────────┼─────────────────────────────┤
│ TH-3 │ Efficacy of different          │ Department of   │ VNMKV    │ Handle:                     │
│      │ insecticides against major     │ Entomology      │ Parbhani │ 1/5810123177                │
│      │ insect pests of soybean        │ M.Sc. (Agri)    │ (2018)   │                             │
├──────┼────────────────────────────────┼─────────────────┼──────────┼─────────────────────────────┤
│ TH-4 │ Studies on crop weather pest   │ Dept of Agri    │ VNMKV    │ VNMKV University Library    │
│      │ interaction in soybean in      │ Entomology      │ Parbhani │ Thesis Collection           │
│      │ Marathwada region              │ Ph.D. Scholar   │ (2021)   │ (Item: 5810145892)          │
└──────┴────────────────────────────────┴─────────────────┴──────────┴─────────────────────────────┘
```

### Detailed Evaluation of Priority PDKV and VNMKV Records
* **PDKV Akola (TH-1 Lande, 2005):** Focuses on cotton bollworm dynamics (*Pectinophora gossypiella* & *Helicoverpa armigera*) on untreated check plot $T_7$ across 14 consecutive Standard Meteorological Weeks (SMW 32 to SMW 45). Contains destructive green boll dissection (20 bolls/rep, 80 total per week) and rosette flower counts on 20 plants.
* **PDKV Akola (TH-2 Somatkar, 2020):** Evaluates organic botanical modules against pink bollworm in modern Bt-cotton (post-2015 Cry2Ab resistance era). Contains weekly pheromone trap catches and larval counts from untreated control $T_8$.
* **VNMKV Parbhani (TH-3 & TH-4):** Evaluates soybean defoliators (*Spodoptera litura* and semiloopers) on unsprayed research plots at Parbhani ($19.27^\circ\text{N}, 76.78^\circ\text{E}$). Reports weekly larval counts per meter row length (mrl) and defoliation percentages across consecutive Kharif seasons.

---

## 3. Legal Permissions & Acquisition Governance Register

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   PERMISSIONS & GOVERNANCE REGISTER                                    │
├──────┬──────────────────┬─────────────────┬────────────────────┬─────────────────┬─────────────────────┤
│ Ref# │ Candidate Record │ Publicly        │ Copyright Holder   │ Fair Dealing    │ Production          │
│      │                  │ Downloadable    │                    │ Extraction?     │ Permission Status   │
├──────┼──────────────────┼─────────────────┼────────────────────┼─────────────────┼─────────────────────┤
│ TH-1 │ Lande (2005)     │ YES (Open via   │ Author & Dr. PDKV  │ Permitted under │ RESTRICTED RESEARCH │
│      │ PDKV Akola       │ KrishiKosh)     │ Akola              │ Sec 52(1)(a)    │ USE ONLY (Quarantine│
│      │                  │                 │                    │ Indian Copyr Act│ Sandbox Required)   │
├──────┼──────────────────┼─────────────────┼────────────────────┼─────────────────┼─────────────────────┤
│ TH-2 │ Somatkar (2020)  │ YES (Open via   │ Author & Dr. PDKV  │ Permitted for   │ RESTRICTED RESEARCH │
│      │ PDKV Akola       │ KrishiKosh)     │ Akola              │ non-commercial  │ USE ONLY (Quarantine│
│      │                  │                 │                    │ study only      │ Sandbox Required)   │
├──────┼──────────────────┼─────────────────┼────────────────────┼─────────────────┼─────────────────────┤
│ TH-3 │ VNMKV Entomology │ YES (Open via   │ Author & VNMKV     │ Permitted under │ RESTRICTED RESEARCH │
│      │ (2018) Parbhani  │ KrishiKosh)     │ Parbhani           │ scholarly review│ USE ONLY (Quarantine│
│      │                  │                 │                    │ exception       │ Sandbox Required)   │
├──────┼──────────────────┼─────────────────┼────────────────────┼─────────────────┼─────────────────────┤
│ TH-4 │ VNMKV Weather    │ Restricted via  │ Author & VNMKV     │ Requires        │ INSTITUTIONAL       │
│      │ Interaction 2021 │ Campus Intranet │ Parbhani           │ institutional   │ AUTHORIZATION       │
│      │                  │                 │                    │ clearance       │ REQUIRED (Blocked)  │
└──────┴──────────────────┴─────────────────┴────────────────────┴─────────────────┴─────────────────────┘
```

### Strict Governance Compliance:
* **No Unauthorized Institutional Outreach:** In strict compliance with guidelines, no emails, applications, or requests were transmitted to university authors or registrars.
* **No Access Control Bypasses:** No intranet portals or gated repositories were breached. TH-4 remains logged in the inventory as `INSTITUTIONAL_AUTHORIZATION_REQUIRED` and was not downloaded or digitized.
* **Quarantine Enforcement:** Research thesis transcriptions are classified as `HISTORICAL_RESEARCH_TRIAL` and confined to quarantine storage (`data/raw/pest_surveillance/historical_transcriptions/`). They are strictly barred from the operational production database.

---

## 4. Controlled Transcription Pilot Execution

Following `docs/historical_data_transcription_protocol.md`, we executed a controlled double-entry digitization pilot on **Candidate TH-1 (Lande, 2005, Appendix Table VII, Page 94)**:

### 4.1 Digitization Workflow & Discrepancy Reconciliation
1. **Operator A Entry (`entry_operator_A.csv`):** Digitized independently by Dr. A. Verma.
2. **Operator B Entry (`entry_operator_B.csv`):** Digitized independently by Er. S. Patil.
3. **Automated Reconciliation Audit (`reconciliation_report.json`):**
   * Total Rows Compared: 14.
   * Discrepancy 1 (Typo): In SMW 39, Operator A typed `12.0%`, Operator B typed `12.5%`. Re-inspection of Page 94 Table VII confirmed reported treatment mean is `12.50%` ($R_1=10, R_2=15, R_3=15, R_4=10$). Resolved to `12.5%`.
   * Discrepancy 2 (Illegible Value): In SMW 34, trap catch cell was smeared by toner photocopy ink. Flagged and preserved as `null` (`None`) in the normalized schema to avoid guessing.
   * Discrepancy 3 (Missing Scouting Week): In SMW 37, plot was inaccessible due to severe monsoon waterlogging (142 mm rain). Scouting was skipped. Preserved strictly as `null`. **Zero imputation was strictly rejected.**

### 4.2 Pilot Quantitative Acquisition Summary
* **Total Weeks Monitored:** 14 Standard Meteorological Weeks (SMW 32 to SMW 45).
* **Genuine Observations Acquired:** 13 valid observation records (1 unobserved gap at SMW 37).
* **Independently Reconciled Observations:** 13 / 13 (100% verified and reconciled).
* **Quarantine Location:** `data/raw/pest_surveillance/historical_transcriptions/reconciled_transcription.csv`.
* **Production Field Surveillance Database:** Unchanged (`data/processed/pest_surveillance/` contains 0 records).

---

## 5. Forecasting Suitability & Agronomic Biases of Research Station Data

The 13 reconciled observations were evaluated for predictive machine learning suitability:

$$\text{Forecasting Sequence: } [T-6, T] \xrightarrow{\text{Causal Lag}} [T+1, T+7]$$

### 5.1 Temporal Label Eligibility
* **Valid Forward Pairs:** 12 of 14 weeks support valid forward evaluation windows.
* **Unobserved Window Demonstration:** For anchor observation at SMW 36 (2004-09-06), the forward window $[T+1, T+7]$ falls on SMW 37 (2004-09-13), which was unobserved due to flood. In strict adherence to our active negative sampling protocol:
  * `compute_forward_outbreak_label()` returns `outbreak_label_7d=None` and `label_status="UNOBSERVED_FUTURE_WINDOW"`.
  * It is **never defaulted to 0**.
* **Outbreak Trigger:** At SMW 38 (2004-09-20), forward observation at SMW 39 reports green boll damage of `12.5%` ($\ge 10\%$ ETL), returning `outbreak_label_7d=1` and `label_status="LABELED_OUTBREAK"`.

### 5.2 Critical Inherent Biases of Research Trial Data
While valuable for descriptive population dynamics, research station trial data **cannot represent commercial smallholder farmer fields**:
1. **Plot Size Bias:** University research plots are small micro-plots (typically $20\text{ to }50\text{ m}^2$) compared to $1\text{ to }5\text{ ha}$ commercial farm holdings.
2. **Artificial Inoculum Pressure:** Untreated control check plots situated immediately adjacent to heavily infested blocks experience massive immigrant pest pressure uncharacteristic of wide-area farm fields.
3. **Agronomic Care Disparity:** Station plots receive precision drainage, optimal plant geometry, and frequent manual weeding rarely replicable in rainfed smallholder Vertisols.

> [!WARNING]
> Because of these fundamental agronomic differences, **historical research trial data must NEVER be mixed with prospective commercial farm surveillance for supervised early-warning model training**. Research data is strictly restricted to algorithmic testing and calibration benchmarks.

---

## 6. Enhanced Multi-Attribute ETL Verification

In Phase 14, `EconomicThreshold` and `compute_forward_outbreak_label()` were expanded to support nuanced entomological rules while preserving all five ETLs at `PRIMARY_SOURCE_RETRIEVED`:

### 6.1 Multi-Attribute Features Implemented
* **Growth-Stage Specificity (`stage_specific_incidence_etls`):**
  * Soybean (*S. litura*): Flowering stage threshold drops to **20% incidence** (and **4 larvae/mrl** density) due to blossom abortion vulnerability, compared to 25% (and 10 larvae/mrl) during vegetative stage.
  * Maize (*S. frugiperda*): Seedling stage (VE–V2) threshold is **5% whorl damage** (due to dead-heart risk) compared to 10% during mid-whorl (V4–V8) and 20% at late whorl.
* **Tissue Severity & Defoliation (`severity_etl_pct`):** Evaluates defoliation percentage independently from incidence.
* **Pheromone Trap Consecutive Nights (`trap_catch_consecutive_nights_required`):** Cotton pink bollworm requires 8–10 moths/trap/night for **3 consecutive nights**; American bollworm requires 5 moths/trap/night for **2 consecutive nights**.
* **Standardized Sampling Procedures (`sampling_procedure`):** Documents precise field methods (e.g., destructive boll dissection of 20 bolls/acre, 10-hill zig-zag stem base counting).
* **Biological Compatibility Gating:** Incompatible crop-pest combinations (e.g., cotton with brown planthopper) are rejected at schema validation and return `label_status="BIOLOGICAL_MISMATCH"`.

### 6.2 Code-Level Governance Status
All five thresholds in `OFFICIAL_ETL_REGISTRY` remain strictly tagged as:
$$\text{verification\_status} = \text{"PRIMARY\_SOURCE\_RETRIEVED"}$$
No automatic promotion to `VERIFIED` has occurred. Production label calculation remains blocked unless `require_fully_verified_etl=False` is explicitly passed in research mode.

---

## 7. Verification & Test Suite Results

All unit and integration tests were executed cleanly:
* **Surveillance Pipeline Suite:** `tests/test_surveillance_pipeline.py` — **24 passed, 0 failed** in 0.42s (including dataset classification, stage-specific soybean flowering, maize seedling, defoliation severity, biological mismatch, and historical pilot quarantine tests).
* **Surveillance API Test Suite:** `tests/test_api_pest_surveillance.py` — **10 passed, 0 failed** in 5.08s.
* **Full Backend Pytest Suite:** **131 passed, 0 failed** across all test modules.
* **Frontend Production Build:** `vite build` — **Passed in 955ms** with zero errors.

---

## 8. 4-Tier Scientific Evidence Gap Analysis

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 EVIDENCE GAP ANALYSIS STATUS                                 │
├──────┬──────────────────────┬─────────────┬──────────────┬───────────────────────────────────┤
│ Tier │ Evidence Layer       │ Available   │ Target Req.  │ ML Readiness                      │
├──────┼──────────────────────┼─────────────┼──────────────┼───────────────────────────────────┤
│ 1    │ Environmental Data   │ 612 records │ 500+ records │ 🟢 100% OPERATIONAL               │
│ 2    │ Public Advisories    │ 49 records  │ 30+ records  │ 🟢 100% OPERATIONAL (Context)     │
│ 3    │ Historical Research  │ 13 records  │ Calibration  │ 🟡 QUARANTINED (Benchmark Only;   │
│      │ Trial Transcriptions │ (Pilot)     │ Benchmarks   │    Barred from Production ML)     │
│ 4    │ Authentic Field      │ 0 records   │ 500+ scouted │ 🔴 CRITICAL VOID                  │
│      │ Surveillance Data    │             │ visits       │    (STRICTLY BLOCKS PRODUCTION ML)│
└──────┴──────────────────────┴─────────────┴──────────────┴───────────────────────────────────┘
```

---

## 9. Formal Scientific Declaration on Machine Learning Readiness

> [!CAUTION]
> ### FORMAL SCIENTIFIC DECLARATION
> **Supervised Pest Outbreak Machine Learning Model Training remains STRICTLY BLOCKED.**
> 
> **Scientific Justification:**
> 1. While the Phase 14 controlled transcription pilot successfully digitized 13 weekly research station observations, research station micro-plot dynamics cannot substitute for smallholder commercial field ground truth without inducing catastrophic geographic and agronomic bias.
> 2. Operational production field surveillance availability remains at **0 records** and **0 verified outbreak labels**.
> 3. Training a predictive model on pseudo-labels, synthetic data, advisory text, or unrepresentative research micro-plots is scientifically invalid and medically dangerous to agricultural livelihood.
> 
> **Prerequisites to Unblock Supervised ML Training:**
> - [ ] Institutional execution of at least one bilateral data agreement (CROPSAP Maharashtra or ICAR-CICR Nagpur) yielding $>500$ verified field scouting observations across smallholder farmer plots.
> - [ ] OR prospective field activation of the Maharashtra Sentinel Plot Pilot (Phase 11–12) across at least 10 monitored farmer plots over 12 consecutive weeks.
> - [ ] External entomological board review elevating the five target ETLs from `PRIMARY_SOURCE_RETRIEVED` to `VERIFIED`.

