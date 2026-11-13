# AgriAdapt AI — Kharif 2027 Sentinel Pilot Operational Readiness Dashboard

**Document ID:** `AGRI-DASH-PILOT-2027-V1`  
**Version:** 1.0.0  
**Phase:** 17  
**Status Date:** November 2026  
**Target Deployment Window:** Kharif 2027 (June 15 – October 31, 2027; SMW 24–43)  
**Governance Standard:** Evidence-based status tracking. **Zero planned activities displayed as completed.**

---

## 1. Master Operational Readiness Matrix

The following table provides the comprehensive operational readiness status across all nine critical pilot preparation tracks:

| Track ID | Preparation Track | Responsible Authority | Evidence-Based Status | Current Ground Reality & Blocking Dependencies |
|:---:|:---|:---|:---:|:---|
| **TRK-01** | **Institutional Authorization** | University Registrar & Lead Academic PI | **PENDING AUTHORIZATION** | 6 institutional packages compiled (`docs/institutional_submission_checklists.md`). Internal academic supervisor review underway. **0 applications dispatched.** |
| **TRK-02** | **Field Partner Recruitment** | KVK Extension Liaisons & Project Lead | **PREPARED / NOT STARTED** | Partner onboarding framework defined (`docs/kharif_2027_pilot_operational_checklist.md`). **0 partner organizations contracted.** |
| **TRK-03** | **Field Scout Accreditation** | Lead Entomologist (Dr. PDKV / CICR) | **PREPARED / NOT STARTED** | 3-day curriculum and testing criteria formalized. **0 scouts hired, trained, or issued badges.** |
| **TRK-04** | **Farmer Informed Consent** | KVK Field Officers & Legal Officer | **PREPARED / NOT STARTED** | Bilingual Marathi/English consent templates printed. **0 farmers consented.** |
| **TRK-05** | **Sentinel-Field Enrollment** | GIS Specialist & Field Supervisors | **PREPARED / NOT STARTED** | 20-plot sampling design specified across 4 districts (5 per district). **0 field GPS polygons demarcated.** |
| **TRK-06** | **Equipment & Trap Readiness** | Logistics & Procurement Manager | **PREPARED / NOT STARTED** | Delta traps, lures (Cycles 1–7), PPE, and kits specified. **0 traps procured or deployed.** |
| **TRK-07** | **Data Collection Readiness** | Mobile Engineering & Ingestion Team | **READY (Software) / STANDBY (Field)** | Mobile app, offline SQLite sync, and REST endpoints validated in 14 simulation tests. **0 live observations recorded.** |
| **TRK-08** | **Data Validation Readiness** | MLOps Data Architect & QA Team | **READY** | Automated schema validation, bounds checking, biological compatibility, and duplicate rejection fully tested. |
| **TRK-09** | **Researcher Review Readiness** | Institutional Entomologists & QA | **READY (Workflow Operational)** | Review API (`/pest-surveillance/review`), audit logging (`surveillance_audit_log.json`), and dashboard active. |

---

## 2. District-by-District Operational Readiness

| District Name | Target Sentinel Plots | Agro-Climatic Zone & Soil | Target Host Crops & Pests | Local Institutional Partner | Local Scout Allocation | Operational Deployment Status |
|:---|:---:|:---|:---|:---|:---:|:---:|
| **Nagpur** | 5 | Vidarbha Vertisols / Sub-Humid | Cotton (Pink Bollworm, *H. armigera*), Soybean (*S. litura*) | KVK Selsura / Nagpur & ICAR-CICR | 2 Scouts (Planned) | `PREPARED / NOT STARTED` |
| **Amravati** | 5 | Vidarbha Vertisols / Semi-Arid | Soybean (*S. litura*, Girdle Beetle), Cotton | KVK Durgapur (Dr. PDKV) | 2 Scouts (Planned) | `PREPARED / NOT STARTED` |
| **Yavatmal** | 5 | Southern Vidarbha / Rainfed | Cotton (Pink Bollworm High Endemic Zone) | KVK Yavatmal (Dr. PDKV) | 2 Scouts (Planned) | `PREPARED / NOT STARTED` |
| **Jalgaon** | 5 | Khandesh Alluvium / Tapi Basin | Cotton (Intensive Bt Belt), Maize (Fall Armyworm) | KVK Pal / Jalgaon | 2 Scouts (Planned) | `PREPARED / NOT STARTED` |
| **TOTAL** | **20** | **4 Distinct Agro-Climatic Zones** | **Cotton, Soybean, Maize, Rice** | **6 Candidate Institutions** | **8 Scouts (Planned)** | **STANDBY / PRE-DEPLOYMENT** |

---

## 3. Software Capability vs Field Deployment Comparison

```
========================================================================================================================
AGRIADAPT AI — CAPABILITY vs GROUND REALITY COMPARISON (PHASE 17)
========================================================================================================================
Component Dimension                 Software Engine Status      Field Ground Truth Status     ML Modeling Readiness
------------------------------------------------------------------------------------------------------------------------
Sentinel Plot Registry              VALIDATED (Schema & API)    0 plots enrolled              BLOCKED
Farmer Consent System               VALIDATED (Bilingual DUA)   0 farmers consented           BLOCKED
Scout Mobile Ingestion              VALIDATED (SQLite + Sync)   0 scouts deployed             BLOCKED
Biological Compatibility Engine     VALIDATED (15 combinations) 0 real observations           BLOCKED
Duplicate Observation Blocker       VALIDATED (HTTP 409)        0 duplicates in production    BLOCKED
Photo Cryptographic Hashing         VALIDATED (SHA-256 EXIF)    0 field photos stored         BLOCKED
Human Entomologist Audit            VALIDATED (REST API)        0 expert reviews conducted    BLOCKED
Economic Threshold Gating           VALIDATED (32 unit tests)   5 ETLs at RETRIEVED           BLOCKED
Supervised ML Training Pipeline     GATED / HARD-BLOCKED        0 verified outbreak labels    BLOCKED
========================================================================================================================
Summary: Software infrastructure is 100% operationally ready; field ground truth is 0% deployed.
========================================================================================================================
```

---

## 4. Operational Sign-Off Prerequisites

Before any sentinel plot can transition from `PREPARED / NOT STARTED` to `ACTIVE`:
1. [ ] Bilateral institutional data-sharing agreement executed with at least one university/KVK.
2. [ ] University Ethics Committee approval for smallholder farmer study.
3. [ ] Field scout hiring, 3-day practical accreditation workshop, and exam certification ($\ge 85\%$).
4. [ ] Signed farmer consent forms on file in University Registrar vault.
5. [ ] Pheromone traps and 7-cycle lure kits delivered to district staging offices.

