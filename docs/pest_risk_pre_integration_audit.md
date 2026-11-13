# Phase 4 Environmental Pest Risk Engine — Pre-Integration Audit Report

**Date:** November 13, 2026  
**Auditor:** Senior Agricultural Machine Learning Engineer & MLOps Architect  
**Component:** `src/pest_risk/`  
**Status:** **PASSED — VERIFIED & READY FOR INTEGRATION**

---

## 1. Engine Verification Summary

| Verification Item | Requirement | Audit Result | Evidence / Details |
| :--- | :--- | :--- | :--- |
| **Engine Existence & Structure** | Fully modular implementation under `src/pest_risk/` | **PASS** | `pest_profiles.py`, `environmental_scoring.py`, `explanations.py`, `risk_assessment.py`, `__init__.py` |
| **Scientific Profile Grounding** | ICAR, FAO, state agricultural university sources for all thresholds | **PASS** | 5 registered profiles with ICAR-CICR, NCIPM, IISR, NRRI, IIMR, IRRI, FAO citations and URLs |
| **Missing Feature Resilience** | Gracefully handle missing soil moisture or planting dates without distortion | **PASS** | Missing soil moisture sets edaphic sub-score to `None`, dynamically re-weights atmospheric components, emits data notices |
| **Probability vs Favorability** | Strictly evaluate biophysical favorability; never claim outbreak probability | **PASS** | Non-probabilistic `DISCLAIMER_TEXT`, clear category boundaries (`LOW`, `MODERATE`, `HIGH`), zero probability outputs |
| **Automated Test Suite** | 100% test pass rate for all scoring curves, fallbacks, and orchestration | **PASS** | 19/19 unit tests passing (`tests/test_pest_risk_engine.py`), 67/67 overall repository tests passing |

---

## 2. Authoritative Crop-Pest Parameterizations

| Crop | Pest Species | Scientific Name | $T_{\text{base}}$ | $T_{\text{opt}}$ | $RH_{\text{opt}}$ | Wash-off Rain | Pupation in Soil | Primary Citation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cotton** | Pink Bollworm | *Pectinophora gossypiella* | 12.0°C | 25.0–33.0°C | 60–85% | 40.0 mm | Yes (0.15–0.35) | ICAR-CICR Nagpur (Peddu et al., 2020; Fand et al., 2021) |
| **Cotton** | American Bollworm | *Helicoverpa armigera* | 10.5°C | 24.0–34.0°C | 60–80% | 45.0 mm | Yes (0.18–0.38) | ICRISAT & ICAR-NCIPM (Ranga Rao et al., 1989) |
| **Soybean** | Tobacco Caterpillar | *Spodoptera litura* | 10.0°C | 24.0–32.0°C | 70–90% | 55.0 mm | Yes (0.20–0.40) | ICAR-IISR Indore (Prasad & Rao, 2008) |
| **Rice** | Brown Planthopper | *Nilaparvata lugens* | 10.0°C | 25.0–31.0°C | 80–95% | 60.0 mm | No (Canopy base) | IRRI & ICAR-NRRI Cuttack (2021) |
| **Maize** | Fall Armyworm | *Spodoptera frugiperda* | 12.5°C | 24.0–32.0°C | 65–85% | 50.0 mm | Yes (0.18–0.38) | FAO FAMEWS (2020) & ICAR-IIMR (2019) |

---

## 3. Pre-Integration Checklist
- [x] No ML models trained or overwritten.
- [x] Maize leaf disease CNN (`models/maize_disease/maize_disease_model.keras`) preserved intact.
- [x] Fertilizer optimization services untouched.
- [x] Existing `/api/v1/advisory/unified` endpoint preserved without modification.
- [x] `origin/omkar` branch unmerged.
- [x] Real-world processed dataset verified: 612 rows across Nagpur, Amravati, Yavatmal, and Jalgaon (`data/processed/aligned_environmental_surveillance_2023-06-01_2023-10-31.csv`).

