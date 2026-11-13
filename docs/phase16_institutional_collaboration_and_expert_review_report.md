# Phase 16 — Institutional Collaboration Activation, Expert ETL Review, and Production Safeguards Report

**Project:** AgriAdapt AI  
**Module:** Pest Outbreak Early Warning MLOps  
**Phase:** 16  
**Version:** 1.0.0  
**Date:** November 2026  
**Status:** COMPLETE / SCIENTIFIC & OPERATIONAL AUDIT FINALIZED  
**Production Surveillance Status:** **EMPTY (0 records in `data/processed/pest_surveillance/`)**  
**Supervised ML Training Status:** **STRICTLY BLOCKED**

---

## 1. Executive Summary

Phase 16 executed the operational and governance activation for institutional data access and expert agronomic review in AgriAdapt AI. Building upon the historical evidence audit and sentinel pilot specifications established in Phase 15, Phase 16 formalized the administrative submission packages, structured the independent entomologist review workflow, instituted hardened algorithmic production safeguards in the labeling engine, and detailed the operational onboarding procedures for prospective field partnerships.

### Core Achievements of Phase 16:
1. **Institutional Collaboration Package Audit:** Audited all six target institutional dossiers across Maharashtra (CROPSAP Maharashtra, ICAR-CICR Nagpur, Dr. PDKV Akola, VNMKV Parbhani, KVK Nagpur, KVK Yavatmal). Verified official contacts, administrative endorsements, letterhead requirements, and follow-up timelines. Reconfirmed that **zero requests have been submitted**.
2. **Prioritized Submission Checklists (`docs/institutional_submission_checklists.md`):** Formulated concise, actionable submission dossiers for CROPSAP Maharashtra and ICAR-CICR Nagpur, incorporating student investigator introductions, supervisor placeholders, technical proposals, non-commercial research use undertakings, farmer privacy provisions, and strict separation between research data access and production software redistribution.
3. **Independent Entomologist Review Workflow & Register (`docs/entomologist_review_tracking_register.md`):** Established a standardized tracking registry and evaluation dossier (`docs/etl_expert_review_package.md`) across all five target crop-pest combinations with verbatim primary-source thresholds, growth stage rules, sampling denominators, consecutive-night mandates, and explicit questions requiring expert sign-off. Reconfirmed that **zero expert approvals have been granted**.
4. **ETL Governance & Algorithmic Production Safeguards (`surveillance_labeling.py`):**
   - Hardened the consecutive-night trap catch evaluation: verified that when $req > 1$, isolated single-night catches cannot trigger an action threshold.
   - Guarded against missing-data zero imputation: when forward scouting visits lack quantitative measurements, the engine safely returns `MISSING_MEASUREMENTS` with $Y=\text{None}$, strictly preventing missing data from becoming pseudo-zero non-outbreak labels.
   - Formalized production label gating: all labels emitted in research mode from unapproved (`PRIMARY_SOURCE_RETRIEVED`) thresholds strictly carry `production_eligible=False`.
   - Expanded unit test coverage in `tests/test_surveillance_pipeline.py` to **32 passing tests** (144 total tests repository-wide).
5. **Historical Data Access Feasibility Study (`docs/historical_surveillance_data_access_requirements.md`):** Investigated data models of CROPSAP and ICAR-CICR, defining essential lookback covariates ($[T-6, T]$) and forward outcomes ($[T+1, T+7]$), and establishing clear boundaries between commercial extension scouting and research station micro-plot dynamics.
6. **Kharif 2027 Field Onboarding Blueprint (`docs/kharif_2027_pilot_operational_checklist.md`):** Added complete operational workflows covering scout onboarding, RACI matrix, data quality escalation, weekly syncs, missed visits, photo evidence with SHA-256 hashes, audit trails, and farmer consent. All sentinel plots remain on `STANDBY`.
7. **Institutional Collaboration Activation Dashboard:** Compiled an empirical readiness tracking dashboard showing that all six packages are in `DRAFT READY / PRE-SUBMISSION` status.

---

## 2. Institutional Collaboration Package Audit & Status

### 2.1 Institutional Inventory & Verification Summary

| Institution ID & Entity | Verified Authority & Portals | Academic Endorsements Required | Research-Use vs Production-Use Scope | Expected Review Timeline & Follow-Up | Dispatch Status |
|:---|:---|:---|:---|:---|:---:|
| **INST-01: CROPSAP Maharashtra** | Commissioner of Agriculture, Central Bldg, Pune (`cropsap.maharashtra.gov.in`) | Lead PI, Faculty Supervisor, Dean of Academic Affairs, HOD | **Research:** Retrospective validation & thesis.<br>**Production:** Barred without commercial addendum. | 30-day Technical Committee review; Registrar follow-up. | **DRAFT READY / NOT DISPATCHED** |
| **INST-02: ICAR-CICR Nagpur** | Director / Head of Crop Protection, Panjri Farm, Wardha Rd, Nagpur (`cicr.icar.gov.in`) | Lead PI, Collaborating Entomologist, University Registrar | **Research:** Mechanistic threshold transition modeling.<br>**Production:** Barred; station data air-gapped. | 45-day PME Cell review; joint research charter. | **DRAFT READY / NOT DISPATCHED** |
| **INST-03: KVK Nagpur** | Senior Scientist & Head, KVK Selsura / Nagpur (Dr. PDKV) | Lead PI, Faculty Advisor, KVK Extension Specialist | **Research:** 5 sentinel plots longitudinal scouting.<br>**Production:** Shared risk alerts for extension. | 21-day Directorate of Extension review. | **DRAFT READY / NOT DISPATCHED** |
| **INST-04: KVK Yavatmal** | Senior Scientist & Head, KVK Yavatmal (Dr. PDKV) | Lead PI, Faculty Advisor, KVK Plant Protection Scientist | **Research:** 5 high-pressure sentinel plots.<br>**Production:** Emergency alert escalation ($2\times\text{ETL}$). | 21-day regional review. | **DRAFT READY / NOT DISPATCHED** |
| **INST-05: Dr. PDKV Akola** | Director of Research / Head, Dept. of Entomology, Akola (`pdkv.ac.in`) | Lead PI, University Registrar, Head of Entomology | **Research:** Dissertation digitization & verification.<br>**Production:** Barred without bilateral IP agreement. | 60-day Academic Council & Faculty Board review. | **DRAFT READY / NOT DISPATCHED** |
| **INST-06: VNMKV Parbhani** | Director of Research / Head, Dept. of Entomology, Parbhani (`vnmkv.ac.in`) | Lead PI, University Registrar, Head of Entomology | **Research:** Marathwada surveillance & threshold review.<br>**Production:** Barred from proprietary distribution. | 60-day Research Advisory Committee (RAC) review. | **DRAFT READY / NOT DISPATCHED** |

### 2.2 Prioritized Submission Checklists (CROPSAP & ICAR-CICR)
As detailed in `docs/institutional_submission_checklists.md`, comprehensive application packages have been compiled for CROPSAP Maharashtra and ICAR-CICR Nagpur. Each package includes:
1. **Student Introduction:** Identity and academic department credentials of the lead student investigator.
2. **Supervisor Placeholders:** Standardized placeholders (`[SUPERVISOR_NAME_PLACEHOLDER]`, `[HOD_NAME_PLACEHOLDER]`) awaiting institutional review.
3. **Formal Request Letters:** Tailored letters citing specific research objectives and non-commercial academic scope.
4. **Target Data Requirements:** Specific historical date ranges (Kharif 2018–2024 for CROPSAP; 2015–2024 for CICR) and target pest complexes.
5. **Farmer Privacy Protections:** Mandatory stripping of farmer personal data (PII) and 3 km spatial aggregation of model outputs.
6. **Air-Gapped Retention Controls:** Strict encryption, access limitations, and zero commercial software bundling.

---

## 3. Independent Entomologist Review Workflow & Register

### 3.1 Status of Economic Threshold Levels (ETLs)
All five target crop-pest thresholds remain at **`PRIMARY_SOURCE_RETRIEVED`**:

| Code | Crop & Target Pest | Implemented Threshold Summary | Primary Source Citation | Software Registry Key | Verification Tier |
|:---:|:---|:---|:---|:---|:---:|
| `REV-2027-01` | **Cotton — Pink Bollworm** (*P. gossypiella*) | 10% rosette flowers or 10% green boll damage; OR 8–10 moths/trap/night for 3 consecutive nights. | ICAR-CICR Ext. Bulletin 42, p. 16. | `("cotton", "pink_bollworm")` | `PRIMARY_SOURCE_RETRIEVED` |
| `REV-2027-02` | **Cotton — American Bollworm** (*H. armigera*) | 1 larva/plant or 5–10% square damage; OR 5 moths/trap/night for 2 consecutive nights. | DCD & ICAR-CICR IPM Manual, p. 23. | `("cotton", "american_bollworm")` | `PRIMARY_SOURCE_RETRIEVED` |
| `REV-2027-03` | **Soybean — Tobacco Caterpillar** (*S. litura*) | 20% defoliation (vegetative) / 10% (flowering); 10 larvae/m row; 10 moths/trap/night. | ICAR-IISR Bulletin 58, p. 12. | `("soybean", "tobacco_caterpillar")` | `PRIMARY_SOURCE_RETRIEVED` |
| `REV-2027-04` | **Rice — Brown Planthopper** (*N. lugens*) | 5–10 hoppers/hill (tillering), 15–20 (booting/heading). No trap threshold. | ICAR-NRRI Bulletin 108, p. 46. | `("rice", "brown_planthopper")` | `PRIMARY_SOURCE_RETRIEVED` |
| `REV-2027-05` | **Maize — Fall Armyworm** (*S. frugiperda*) | 5% damage (seedling), 10% (mid-whorl), 20% (late whorl); 5 moths/trap/night. | FAO FAMEWS Manual Table 2.1. | `("maize", "fall_armyworm")` | `PRIMARY_SOURCE_RETRIEVED` |

### 3.2 Review Tracking Register (`docs/entomologist_review_tracking_register.md`)
A formal tracking register has been created to log external expert reviews. Criteria include reviewer credentials, institutional affiliation, conflict of interest declaration, numerical evaluation (1–5 scale), technical commentary, and signed documentary proof.
- **Reviews Completed:** 0
- **Expert Approvals Documented:** 0
- **Operational Promotion:** Blocked until accredited third-party sign-offs are archived.

---

## 4. Algorithmic Production Safeguards & Regression Testing

### 4.1 Implementation Upgrades in `surveillance_labeling.py`

#### 1. Consecutive-Night Action Threshold Enforcement
Action thresholds requiring consecutive nights (e.g. 3 consecutive nights for Pink Bollworm, 2 consecutive nights for American Bollworm) now strictly mandate that `max_consecutive >= req_nights`. An isolated single observation exceeding the moth threshold does not satisfy the streak requirement and will not trigger an outbreak.

#### 2. Missing Measurements Cannot Become Zero Labels
When a scouting visit is recorded in the forward window ($[T+1, T+7]$) but all quantitative fields (`pest_incidence_pct`, `trap_catch_count`, `pest_severity_pct`, `plants_affected`) are missing (`None`), the window is not treated as a sub-ETL negative outcome. The engine returns:
`label_status = "MISSING_MEASUREMENTS"` and `outbreak_label_7d = None`.

#### 3. Production Label Generation Gating (`production_eligible`)
The `OutbreakLabelResult` dataclass now includes an explicit boolean attribute:
`production_eligible: bool = (etl.verification_status == "VERIFIED")`.
In research/exploratory mode (`require_fully_verified_etl=False`), labels may be computed against `PRIMARY_SOURCE_RETRIEVED` thresholds for exploratory analysis, but `production_eligible` is strictly set to `False`. When `require_fully_verified_etl=True` (production mode), label computation is halted with `label_status = "ETL_NOT_PRODUCTION_VERIFIED"`.

### 4.2 Unit & Integration Test Suite Verification
Three new dedicated regression tests were added to `tests/test_surveillance_pipeline.py`:
1. `test_single_night_trap_catch_does_not_satisfy_consecutive_nights_etl`: Verified that a single night trap catch of 12.0 moths on Pink Bollworm does not trigger an outbreak when $req=3$.
2. `test_missing_measurements_in_forward_window_cannot_become_zero_label`: Verified schema validation rejection and engine fallback to `MISSING_MEASUREMENTS`.
3. `test_primary_source_retrieved_not_production_eligible`: Verified that `production_eligible` is strictly `False` for `PRIMARY_SOURCE_RETRIEVED` thresholds.

**Test Suite Results:**
- `tests/test_surveillance_pipeline.py`: **32 passed** (up from 29).
- Total Backend Test Suite: **144 passed** across 19 test modules.
- Frontend Test Suite: **4 passed** (`frontend/src/__tests__/App.test.jsx`).
- Frontend Production Build: Clean build completed (0 errors).

---

## 5. Historical Institutional Data Access Opportunities

As documented in `docs/historical_surveillance_data_access_requirements.md`:
- **Lookback Feature Requirements ($[T-6, T]$):** ERA5-Land reanalysis weather covariates (daily min/max temperature, relative humidity at 07:00 and 14:00 hrs, cumulative rainfall, degree-day accumulation, and Environmental Favorability Index).
- **Forward Outcome Requirements ($[T+1, T+7]$):** At least one authentic field visit with verified quantitative measurements compared against stage-specific and consecutive-night thresholds.
- **Domain Divergence Boundary:** CROPSAP data reflects commercial smallholder extension with variable farmer chemical spray applications. ICAR-CICR data reflects controlled research station micro-plots with untreated check plots. These data streams must remain separate and never be pooled into an unstratified training set.

---

## 6. Kharif 2027 Field Partnership Onboarding Blueprint

The operational onboarding framework has been integrated into `docs/kharif_2027_pilot_operational_checklist.md`:
- **Scout Onboarding Checklist:** 5-point verification covering academic background, 3-day practical training, offline mobile app testing, calibrated kit issuance, and signed code of conduct.
- **Researcher RACI Matrix:** Clear operational division of responsibilities across Academic PI, Senior Entomologist, MLOps Engineer, District Supervisors, Field Scouts, and Host Farmers.
- **Data Quality Escalation:** Automated bounds validation, quarantined raw staging, expert dashboard review, and 48-hour re-inspection triggers.
- **Submission & Missed Visits:** Weekly Wednesday sync protocol, $\pm 48\text{ hour}$ weather contingency window, and strict logging of missed visits as unobserved `null` without imputation.
- **Cryptographic Photo Verification:** Mandatory close-up damage and trap catch photographs with EXIF GPS metadata and SHA-256 hashes.
- **Data Correction Trails:** Append-only audit history logging previous values, updated values, justifications, and certifying entomologist identities.
- **Consent & Land Access:** Bilingual informed consent and compensation protocols.

**Pilot Status:** All 20 sentinel plots remain on **`STANDBY / PRE-DEPLOYMENT`**. Zero farmers recruited; zero scouts deployed.

---

## 7. Institutional Collaboration Activation Dashboard

```
========================================================================================================================
AGRIADAPT AI — INSTITUTIONAL COLLABORATION ACTIVATION DASHBOARD (PHASE 16)
========================================================================================================================
Institution ID   Target Institution       Draft Ready   Academic Auth   Submitted   Response   DUA Signed   Data Received
------------------------------------------------------------------------------------------------------------------------
INST-01          CROPSAP Maharashtra      YES           PENDING         NO          NO         NO           0 records
INST-02          ICAR-CICR Nagpur         YES           PENDING         NO          NO         NO           0 records
INST-03          KVK Nagpur (Dr. PDKV)    YES           PENDING         NO          NO         NO           0 records
INST-04          KVK Yavatmal (Dr. PDKV)  YES           PENDING         NO          NO         NO           0 records
INST-05          Dr. PDKV Akola           YES           PENDING         NO          NO         NO           0 records
INST-06          VNMKV Parbhani           YES           PENDING         NO          NO         NO           0 records
========================================================================================================================
Overall Institutional Data Acquisition Status: PRE-SUBMISSION STANDBY (0 applications dispatched, 0 datasets received)
========================================================================================================================
```

---

## 8. Formal Scientific & Governance Declarations

In strict accordance with the scientific charter of AgriAdapt AI:
1. **Zero Requests Dispatched:** No emails, letters, phone calls, or digital forms have been submitted to any agricultural institution.
2. **Zero Approvals Fabricated:** No institutional responses, data sharing agreements, or expert approvals have been simulated or fabricated.
3. **ETL Status Preserved:** All five Economic Threshold Levels remain strictly at `PRIMARY_SOURCE_RETRIEVED`.
4. **Quarantine Preserved:** Historical research trial data (Lande, 2005) remains quarantined in raw storage and excluded from production datasets.
5. **Supervised ML Training Remains STRICTLY BLOCKED:** With zero authentic commercial-field surveillance records and zero verified outbreak outcome labels, supervised early-warning model training remains strictly prohibited.

