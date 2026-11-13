# AgriAdapt AI — Kharif 2027 Field Surveillance Workflow Validation

**Document ID:** `AGRI-VAL-WORKFLOW-2027-V1`  
**Version:** 1.0.0  
**Phase:** 17  
**Scope:** End-to-End Operational Workflow Validation for the Prospective Kharif 2027 Sentinel Pilot  
**Target Coverage:** 20 Sentinel Plots across 4 Maharashtra Districts (Nagpur, Amravati, Yavatmal, Jalgaon)  
**Current Operational Status:** WORKFLOW VALIDATED IN SIMULATION. **Sentinel plots remain in STANDBY / NOT RECRUITED.**

---

## 1. Executive Summary & Objective

Before deploying scouts or equipment to rural Maharashtra farm plots for Kharif 2027, the end-to-end data acquisition, validation, review, and provenance pipeline must be rigorously verified. Field operations in Vidarbha and Marathwada face harsh operational realities: intermittent 4G cellular connectivity, extreme monsoon waterlogging in deep vertisols (*black cotton soils*), high scout turnover, and complex cryptic pest symptoms.

This document presents the **comprehensive workflow validation** for the Kharif 2027 sentinel pilot. It validates every stage of the surveillance lifecycle — from sentinel plot demarcation and farmer consent to mobile entry, biological validation, human expert audit, and cryptographic provenance — supported by 14 automated simulation test scenarios.

---

## 2. Complete Field Pilot Architecture & Lifecyle

```
[ PHASE A: Sentinel Registration & Consent ]
  │  • 20 smallholder plots (1.0–2.5 acres) identified across Nagpur, Amravati, Yavatmal, Jalgaon.
  │  • Bilingual informed consent signed; pseudonymous IDs generated (`MAH-NGP-KAT-001`, `FMR-NGP-9E2A8F`).
  │  • GPS boundary polygon digitized (4+ vertices, $\le 3\text{ m}$ precision).
  ▼
[ PHASE B: Equipment & Trap Setup (Weeks 1–4 Baseline) ]
  │  • Pheromone delta traps installed at canopy height (+30 cm); GPS coordinates logged.
  │  • 8 accredited scouts equipped with standardized 10x lenses, dissection knives, PPE, and mobile app.
  │  • Baseline lure Cycle 1 installed (21-day replacement schedule established).
  ▼
[ PHASE C: Weekly Field Scouting (Weeks 5–20 Intensive) ]
  │  • Fixed Wednesday visit schedule ($\pm 48\text{ hour}$ weather contingency window: Mon–Fri).
  │  • Diagonal "W" transects (5 stations $\times$ 4 plants = 20 plants/plot).
  │  • Destructive green boll dissections (20 bolls/acre) & maize whorl dissections.
  │  • Pheromone trap catch counts (daily during emergence surges; weekly baseline).
  │  • Geotagged macro damage & trap liner photographs captured with on-device SHA-256 hash.
  ▼
[ PHASE D: Mobile Data Ingestion & Edge Validation ]
  │  • Local encrypted SQLite caching on Android device.
  │  • Automated client/server schema validation (physical bounds, biological compatibility).
  │  • Duplicate detection: rejection of duplicate field/date/pest entries (HTTP 409 Conflict).
  │  • Missing observation handling: severe weather disruptions logged as `NULL` (zero imputation strictly barred).
  ▼
[ PHASE E: Human Entomological Expert Audit & Provenance ]
  │  • Regional entomologists review weekly batches via web dashboard.
  │  • Audit actions: `APPROVE` (`KVK_EXPERT_VALIDATED`), `REJECT` (`REJECTED`), `CORRECT_FIELDS`.
  │  • Immutable audit trail logged to `surveillance_audit_log.json` with cryptographic audit IDs.
  ▼
[ PHASE F: Quarantined Analytical Staging ]
  │  • Validated records stored in staging area; barred from production ML training until full pilot completion.
```

---

## 3. Pseudonymous Identifier Taxonomy

To protect farmer identity, ensure compliance with the Digital Personal Data Protection (DPDP) Act, and prevent land parcel identification, the system enforces a strict hierarchical pseudonymization standard:

### 3.1 Sentinel Field Identifier (`field_id`)
$$\text{Format: } \mathbf{MAH}\text{-}\{\text{DISTRICT\_CODE}\}\text{-}\{\text{TALUKA\_CODE}\}\text{-}\{\text{PLOT\_SERIAL}\}$$
- Examples: `MAH-NGP-KAT-001` (Nagpur, Katol Taluka, Plot 01); `MAH-YAV-DAR-004` (Yavatmal, Darwha Taluka, Plot 04).
- District Codes: `NGP` (Nagpur), `AMR` (Amravati), `YAV` (Yavatmal), `JAL` (Jalgaon).

### 3.2 Farmer Pseudonymous Identifier (`farmer_id`)
$$\text{Format: } \mathbf{FMR}\text{-}\{\text{DISTRICT\_CODE}\}\text{-}\{\text{HEX\_HASH}_{1..6}\}$$
- Examples: `FMR-NGP-9E2A8F`, `FMR-YAV-4B1C09`.
- Generated as: $\text{SHA-256}(\text{Farmer Legal Name} + \text{Survey Plot No.} + \text{Salt})[:6]$.
- Stored exclusively in an air-gapped, encrypted lookup table accessible only by the University Institutional Registrar.

### 3.3 Scout Pseudonymous Identifier (`observer_id`)
$$\text{Format: } \mathbf{SCT}\text{-}\{\text{DISTRICT\_CODE}\}\text{-}\{\text{SERIAL}_{1..2}\}$$
- Examples: `SCT-NGP-01`, `SCT-AMR-02`.
- Tracks individual scouting records, training accreditation certificates, and audit trails.

---

## 4. Species-Specific Sampling Protocols & Biological Separation

The field observation schema (`SurveillanceRecord`) rigorously segregates distinct biological quantities. Combining disparate measurements (e.g. adding trap catches to boll infestation percentages) is strictly forbidden.

| Target Crop & Pest | Scouting Methodology | Primary Sampling Unit | Quantitative Metric Recorded | Sampling Denominator & Effort | Stage-Specific Rules | Action Threshold Trigger |
|:---|:---|:---|:---|:---|:---|:---:|
| **Cotton — Pink Bollworm** (*P. gossypiella*) | Destructive green boll dissection & rosette flower counting. | Medium green bolls (20–25 days old) & flower buds. | • `pest_incidence_pct` (%)<br>• `trap_catch_count` (moths/night) | 20 green bolls per plot (4 per station across 5 'W' stations); 1 delta trap/acre. | • Squaring/Flowering: rosette flowers.<br>• Boll development: destructive boll slicing. | $\ge 10.0\%$ boll damage OR $\ge 8.0$ moths/night for 3 consecutive nights. |
| **Cotton — American Bollworm** (*H. armigera*) | Whole plant inspection along diagonal 'W' transect. | Squares, terminals, and developing bolls. | • `pest_incidence_pct` (%)<br>• `plants_affected` / `plants_sampled` (larvae/plant)<br>• `trap_catch_count` | 20–25 randomly selected plants; 1 delta trap/acre. | • Squaring to boll opening.<br>• Counts larvae instars I–III. | $\ge 1.0$ larva/plant OR $\ge 5.0\%$ square damage OR $\ge 5$ moths/night (2 nights). |
| **Soybean — Tobacco Caterpillar** (*S. litura*) | Ground cloth shake sheet beat method & visual defoliation index. | 1-meter crop row length & whole plant canopy. | • `pest_severity_pct` (defoliation %)<br>• `plants_affected` / `plants_sampled` (larvae/m row) | 5 random 1-meter rows along diagonal transect; 1 trap/acre. | • Pre-flowering: 20% defol / 10 larvae/m.<br>• Flowering: strictly 4 larvae/m row. | $\ge 20\%$ defoliation OR $\ge 10$ larvae/m row ($\ge 4$ at bloom). |
| **Rice — Brown Planthopper** (*N. lugens*) | Lower stem base / water meniscus visual counting. | Individual rice hill (clump of culms). | • `plants_affected` / `plants_sampled` (hoppers/hill)<br>• `pest_incidence_pct` | 20 hills sampled diagonally across flooded paddy. | • Tillering: 5–10 hoppers/hill.<br>• Booting/heading: 15–20 hoppers/hill. | $\ge 10$ hoppers/hill (tillering) or $\ge 20$ (heading). |
| **Maize — Fall Armyworm** (*S. frugiperda*) | Whorl inspection for leaf pinholes/frass & destructive whorl unrolling. | Central whorl and growing point. | • `pest_incidence_pct` (% whorls damaged)<br>• `trap_catch_count` (moths/night) | 5 stations $\times$ 20 consecutive plants (100 total plants); 1 trap/acre. | • Seedling (V1–V4): 5% whorl damage.<br>• Mid-whorl (V5–V8): 10% whorl damage. | $\ge 5.0\%$ damage (early) or $\ge 10.0\%$ (mid-whorl) OR $\ge 5$ moths/night. |

---

## 5. End-to-End Simulation Test Verification

To validate software functionality without entering synthetic observations into production storage, a dedicated test module (`tests/test_field_pilot_workflow_simulation.py`) was executed. All 14 scenarios passed successfully:

| Scenario ID | Test Function Name | Tested Condition | Expected Behavior | Verification Status |
|:---:|:---|:---|:---|:---:|
| **SIM-01** | `test_simulation_valid_field_observation_submission` | Standard valid field submission with pseudonyms & photo hash. | Ingested successfully with HTTP 200; verification status defaults to `UNVERIFIED`. | **PASSED** |
| **SIM-02** | `test_simulation_duplicate_observation_submission` | Second submission on same date/field/crop/pest under different ID. | Blocked with **HTTP 409 Conflict** and duplicate error details. | **PASSED** |
| **SIM-03** | `test_simulation_missing_required_measurements` | Observation submitted with all measurement fields `None`. | Blocked with **HTTP 422 Unprocessable Entity**. | **PASSED** |
| **SIM-04** | `test_simulation_invalid_coordinates` | Coordinates outside Maharashtra bounds (e.g. New Delhi lat=28.61). | Blocked with **HTTP 422 Unprocessable Entity**. | **PASSED** |
| **SIM-05** | `test_simulation_biologically_incompatible_crop_pest` | Submitting Pink Bollworm on Rice. | Blocked with **HTTP 422 Unprocessable Entity**. | **PASSED** |
| **SIM-06** | `test_simulation_missing_photographs_warning` | Observation submitted without `photo_evidence_sha256`. | Ingested with HTTP 200; returns explicit `"Missing photo evidence"` warning. | **PASSED** |
| **SIM-07** | `test_simulation_unverified_scout_submission_dashboard_state` | Unverified submission dashboard reflection. | `unverified_records_count` increments; `verified_records_count` remains 0. | **PASSED** |
| **SIM-08** | `test_simulation_reviewer_rejection` | Expert reviewer rejects record due to specimen misidentification. | Status transitions to `REJECTED`; audit entry logged with justification. | **PASSED** |
| **SIM-09** | `test_simulation_reviewer_approval` | Expert reviewer approves valid destructive boll dissection record. | Status transitions to `KVK_EXPERT_VALIDATED`; verified count increments. | **PASSED** |
| **SIM-10** | `test_simulation_missed_weekly_visit_no_zero_imputation` | Flood disruption prevents visit; forward window has zero records. | Label engine returns `UNOBSERVED_FUTURE_WINDOW` ($Y=\text{None}$). Zero-imputation barred. | **PASSED** |
| **SIM-11** | `test_simulation_late_submission_warning` | Observation conducted >3 days prior to submission date. | Ingested with HTTP 200; returns explicit `"Late submission warning"`. | **PASSED** |
| **SIM-12** | `test_simulation_csv_batch_import_mixed_valid_invalid` | Batch CSV containing 2 valid, 1 duplicate, 1 out-of-bounds, 1 mismatch row. | 2 rows ingested, 3 rows rejected, 1 duplicate flagged in validation report. | **PASSED** |
| **SIM-13** | `test_simulation_audit_log_integrity` | Correction applied to field observation. | Chronological, immutable audit record appended to `surveillance_audit_log.json`. | **PASSED** |
| **SIM-14** | `test_simulation_production_isolation_guarantee` | Production file integrity audit. | `data/processed/pest_surveillance/` contains strictly **0 production records**. | **PASSED** |

---

## 6. Operational Failure Modes & Mitigation Matrix

| Operational Failure Mode | Root Cause | Impact on Data Pipeline | Enforced Platform Mitigation |
|:---|:---|:---|:---|
| **Severe Monsoon Flooding** | Torrential rainfall ($>100\text{ mm}$) turns Vertisols impassable for 5+ days. | Missed scouting visit during critical squaring or boll development. | Mandatory $\pm 48\text{ hour}$ window. If inaccessible past Friday, record is logged as `MISSED_VISIT_WATERLOGGING`. Zero-imputation strictly barred. |
| **Scout Specimen Misidentification** | Cryptic early instars (e.g. *H. armigera* vs *S. litura* neonates) look similar. | Inaccurate pest incidence records entered. | Mandatory macro photo capture with SHA-256 hash. Weekly expert entomologist review via audit dashboard before validation. |
| **Pheromone Trap Damage / Dislodgement** | High winds, stray cattle, or wild boars knock down delta trap. | Corrupted or unobserved trap catch counts. | Scout logs `TRAP_DISLODGED` with invalid flag. Trap replaced within 24 hours. Catch counts for disrupted days are excluded. |
| **Farmer Retraction / Consent Withdrawal** | Host farmer decides to discontinue trial participation mid-season. | Longitudinal time series broken for that specific field. | Immediate quarantine of field ID; historical data retained only for anonymized retrospective study; future scouting visits terminated. |
| **Rural Mobile Network Failure** | Remote village lacks 4G cellular signal for multiple days. | Real-time upload failure. | Encrypted local SQLite on-device storage. Automatic background sync with exponential retry backoff upon re-entering signal coverage. |

---

## 7. Operational Readiness Declaration

The field surveillance software workflow is **fully validated and operational in simulation**. In accordance with scientific integrity guidelines, no actual scouting or field activation will commence until institutional agreements and ethical clearances are formalized.

