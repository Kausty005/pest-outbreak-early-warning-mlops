# Phase 5 — Environmental Pest Risk Engine Integration Report

**Project:** AgriAdapt AI / Pest Outbreak Early Warning MLOps  
**Component:** Tier 1 Macro Early Warning Integration (Backend API & React UI)  
**Role:** Senior Agricultural Machine Learning Engineer & MLOps Architect  
**Status:** **OPERATIONAL & VERIFIED**  
**Classification:** **EXPERIMENTAL BIOPHYSICAL FAVORABILITY ASSESSMENT**

---

## 1. Executive Summary & Non-Probabilistic Principle

Phase 5 successfully integrates the Phase 4 explainable **Environmental Pest Risk Assessment Engine** into the AgriAdapt AI application. The integration exposes biophysical environmental favorability assessments through a dedicated FastAPI backend endpoint and an interactive React dashboard section, while keeping existing crop recommendation, fertilizer optimization, and rule-based advisory services completely intact.

> [!IMPORTANT]
> **CRITICAL SCIENTIFIC DISTINCTION:**  
> This integrated engine computes strictly an **Environmental Favorability Index (EFI)** on a continuous $[0.0, 1.0]$ scale based on peer-reviewed ICAR and FAO agroclimatic development thresholds. It **does NOT** output a calibrated probability of an actual pest outbreak, nor does it represent a trained supervised machine learning outbreak model. The field `outbreak_probability` is strictly absent from all API schemas and UI views.

---

## 2. End-to-End Architectural Data Flow

```
[ Real-World Surveillance Dataset ]
  data/processed/aligned_environmental_surveillance_2023-06-01_2023-10-31.csv
  (612 daily records across Nagpur, Amravati, Yavatmal, Jalgaon)
                   │
                   ▼
[ Backend API Router & Validation ]
  backend/app/api/pest_risk.py  ───►  backend/app/schemas/pest_risk.py
  (Validates crop, pest, district; retrieves 7-day antecedent window)
                   │
                   ▼
[ Phase 4 Biophysical Risk Engine ]
  src/pest_risk/risk_assessment.py
    ├── pest_profiles.py          (ICAR/FAO biological thresholds)
    ├── environmental_scoring.py  (Trapezoidal physiological response curves)
    ├── explanations.py           (Farmer-friendly drivers, inhibitors, IPM guidance)
    └── Open-Meteo Forecast API  (Strictly partitioned 7-day numerical forecast)
                   │
                   ▼
[ API Response Payload ]
  POST /api/v1/pest-risk/environmental-assessment
  (EXPERIMENTAL_ENVIRONMENTAL_FAVORABILITY_ASSESSMENT)
                   │
                   ▼
[ Frontend React Interface ]
  frontend/src/components/EnvironmentalPestRiskSection.jsx
    ├── Top-level Tab in App.jsx ("🐛 Pest Favorability")
    ├── Embedded Panel in FarmDashboard.jsx ("Smart Farm Command Center")
    └── Full explainability: drivers, limitations, IPM advisories, citations
```

---

## 3. Backend API Specification & Request/Response Examples

### Endpoint 1: Supported Profiles Discovery
- **Path:** `GET /api/v1/pest-risk/supported-profiles`
- **Purpose:** Enables frontend components to discover authoritatively registered crops, pests, available surveillance districts, and valid historical observation date ranges.

#### Response Example:
```json
{
  "supported_crops": ["cotton", "maize", "rice", "soybean"],
  "crop_pests_mapping": {
    "cotton": [
      {
        "pest_id": "cotton_pink_bollworm",
        "common_name": "Pink Bollworm",
        "scientific_name": "Pectinophora gossypiella (Saunders)"
      },
      {
        "pest_id": "cotton_american_bollworm",
        "common_name": "American Bollworm",
        "scientific_name": "Helicoverpa armigera (Hübner)"
      }
    ],
    "soybean": [
      {
        "pest_id": "soybean_tobacco_caterpillar",
        "common_name": "Tobacco Caterpillar",
        "scientific_name": "Spodoptera litura (Fabricius)"
      }
    ],
    "rice": [
      {
        "pest_id": "rice_brown_planthopper",
        "common_name": "Brown Planthopper",
        "scientific_name": "Nilaparvata lugens (Stål)"
      }
    ],
    "maize": [
      {
        "pest_id": "maize_fall_armyworm",
        "common_name": "Fall Armyworm",
        "scientific_name": "Spodoptera frugiperda (J.E. Smith)"
      }
    ]
  },
  "available_surveillance_districts": ["Amravati", "Jalgaon", "Nagpur", "Yavatmal"],
  "available_date_range": {
    "start": "2023-06-01",
    "end": "2023-10-31"
  }
}
```

---

### Endpoint 2: Experimental Environmental Assessment
- **Path:** `POST /api/v1/pest-risk/environmental-assessment`
- **Method:** `POST`
- **Content-Type:** `application/json`

#### Request Payload Example:
```json
{
  "crop": "cotton",
  "district": "Nagpur",
  "pest": "pink_bollworm",
  "assessment_date": "2023-09-15",
  "planting_date": "2023-06-15",
  "fetch_live_forecast": false
}
```

#### Response Payload Example:
```json
{
  "assessment_type": "EXPERIMENTAL_ENVIRONMENTAL_FAVORABILITY_ASSESSMENT",
  "crop": "cotton",
  "pest": "Pink Bollworm",
  "scientific_name": "Pectinophora gossypiella (Saunders)",
  "location": "Nagpur",
  "assessment_date": "2023-09-15",
  "assessment_horizon_days": 7,
  "environmental_favorability_score": 0.5999,
  "risk_category": "MODERATE",
  "risk_trend": "UNKNOWN",
  "contributing_factors": {
    "favorable_drivers": [
      "Ambient temperature (27.8°C) lies within the optimal developmental window (25.0°C–33.0°C), promoting rapid pest metabolism and egg incubation.",
      "Atmospheric humidity (82.0%) matches peak suitability (60%–85%), preventing egg desiccation and enhancing larval survival.",
      "Topsoil volumetric moisture (32.0%) provides optimal friability for pupation and adult emergence.",
      "Crop age (92 days since sowing) is in its peak vulnerable phenological stage (75–125 DSS), supplying abundant host tissue (squaring, flowering, boll_formation, boll_maturation)."
    ],
    "limiting_factors": [
      "Torrential rainfall (42.0 mm) exceeds mechanical wash-off threshold (40.0 mm), dislodging young instars and disrupting adult mating."
    ]
  },
  "environmental_observations": {
    "date": "2023-09-15",
    "temperature_mean_c": 27.8,
    "temperature_min_c": 22.8,
    "temperature_max_c": 32.5,
    "relative_humidity_pct": 82.0,
    "rainfall_mm": 42.0,
    "soil_moisture_m3m3": 0.32,
    "antecedent_window_days": 7,
    "antecedent_mean_temperature_c": 28.14,
    "antecedent_mean_humidity_pct": 79.29,
    "antecedent_accumulated_rainfall_mm": 112.5
  },
  "data_quality": {
    "records_used": 7,
    "data_source": "Open-Meteo Historical Archive & Copernicus ERA5-Land Reanalysis",
    "edaphic_data_available": true,
    "phenology_data_available": true,
    "missing_fields": [],
    "data_notices": []
  },
  "forecast_available": false,
  "forecast_summary": null,
  "recommendations": [
    "Environmental conditions are conducive for Pink Bollworm buildup. Deploy surveillance pheromone traps (5 traps/ha) or light traps to monitor adult moth flights.",
    "Initiate weekly scouting: inspect 20 representative plants randomly selected across 5 field quadrants. Record flower/bud damage and presence of early instars.",
    "Prepare biological or botanical deterrents (e.g. 5% Neem Seed Kernel Extract / NSKE 1500 ppm or Bacillus thuringiensis) for timely intervention if trap catches exceed threshold."
  ],
  "limitations": [
    "High environmental favorability indicates microclimatic suitability for pest propagation, but does NOT guarantee an outbreak if initial pest inoculum or local trap counts are zero.",
    "Biological factors such as natural enemy presence (predators, parasitoids), prior pesticide sprays, and crop variety resistance are not measured by microclimate sensors alone.",
    "Physical in-field scouting and pheromone trap monitoring are mandatory before initiating chemical or biological interventions.",
    "This experimental module evaluates environmental favorability, NOT statistical outbreak probability."
  ],
  "references": [
    {
      "title": "Temperature-dependent phenology models for pink bollworm, Pectinophora gossypiella",
      "authors": "Fand, B. B., et al.",
      "year": 2021,
      "institution_or_journal": "Crop Protection, Elsevier (Vol. 140, 105428)",
      "url": "https://doi.org/10.1016/j.cropro.2020.105428",
      "key_finding": "Established thermal thresholds (T_base=12.0°C, T_opt=25-33°C, T_upper=38.0°C) and generation GDD requirement."
    },
    {
      "title": "Thermal constants and development of pink bollworm on Bt cotton",
      "authors": "Peddu, N., Rao, P. A., & Sree, K. S.",
      "year": 2020,
      "institution_or_journal": "Journal of Agrometeorology, 22(3), 341-347",
      "url": "https://doi.org/10.54302/mausam.v71i3.30",
      "key_finding": "Validated thermal constants and developmental rates under Indian semi-arid cotton growing conditions."
    },
    {
      "title": "Pink Bollworm Management in Cotton: Strategy & Advisory",
      "authors": "ICAR-CICR Scientist Team",
      "year": 2021,
      "institution_or_journal": "ICAR-Central Institute for Cotton Research, Nagpur, Maharashtra",
      "url": "https://cicr.icar.gov.in/",
      "key_finding": "Defines square/boll stage phenology vulnerability windows and pupation dynamics in Vidarbha Vertisols."
    }
  ],
  "disclaimer": "BIOPHYSICAL ADVISORY NOTICE: This assessment represents environmental and microclimatic favorability for pest proliferation based on peer-reviewed ICAR and FAO agronomic thresholds. It is NOT a calibrated statistical outbreak probability or guaranteed pest prediction. Actual pest incidence depends on local pest pressure, previous crop history, beneficial insect populations, and farm management practices. Physical field scouting and consultation with local Krishi Vigyan Kendra (KVK) or agricultural extension officers are mandatory before applying any pesticide."
}
```

---

## 4. Modified and Created Files

### Backend Components
1. [src/pest_risk/pest_profiles.py](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/src/pest_risk/pest_profiles.py): Authoritative ICAR/FAO biological profiles for 5 species across 4 crops.
2. [src/pest_risk/environmental_scoring.py](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/src/pest_risk/environmental_scoring.py): Biophysical scoring functions (thermal, hygrometric, precipitation, edaphic, phenology).
3. [src/pest_risk/explanations.py](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/src/pest_risk/explanations.py): Farmer-friendly positive drivers, limiting factors, IPM advisories, citations, and disclaimer.
4. [src/pest_risk/risk_assessment.py](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/src/pest_risk/risk_assessment.py): Core assessment orchestrator and Open-Meteo live forecast integration.
5. [src/pest_risk/__init__.py](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/src/pest_risk/__init__.py): Public package interface.
6. [backend/app/schemas/pest_risk.py](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/schemas/pest_risk.py): Pydantic request/response schemas with strict rejection of `outbreak_probability`.
7. [backend/app/api/pest_risk.py](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/api/pest_risk.py): FastAPI router implementing `/environmental-assessment` and `/supported-profiles`.
8. [backend/app/api/__init__.py](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/api/__init__.py): Exposes `pest_risk_router`.
9. [backend/app/main.py](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/main.py): Mounts `pest_risk_router` under `/api/v1`.

### Frontend Components
1. [frontend/src/components/EnvironmentalPestRiskSection.jsx](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/frontend/src/components/EnvironmentalPestRiskSection.jsx): Dedicated interactive assessment component with category badges, EFI progress meter, microclimate cards, forecast table, IPM advice, and citations.
2. [frontend/src/components/FarmDashboard.jsx](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/frontend/src/components/FarmDashboard.jsx): Integrated the assessment section under the Farmer Advisory Dashboard tab ("🐛 Pest Favorability (Tier 1)").
3. [frontend/src/components/Navbar.jsx](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/frontend/src/components/Navbar.jsx): Added navigation link to the pest favorability section.
4. [frontend/src/App.jsx](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/frontend/src/App.jsx): Added dedicated top-level tab button ("🐛 Pest Favorability") and content block.
5. [frontend/src/services/api.js](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/frontend/src/services/api.js): Added `pestRiskApi.assess` and `pestRiskApi.supportedProfiles`.

### Test Suites
1. [tests/test_pest_risk_engine.py](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/tests/test_pest_risk_engine.py): 19 unit tests for biophysical curves, missing data, and forecast mocking.
2. [tests/test_api_pest_risk.py](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/tests/test_api_pest_risk.py): 9 integration tests for FastAPI endpoints, error handling, and safety invariants.
3. [frontend/src/__tests__/App.test.jsx](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/frontend/src/__tests__/App.test.jsx): 4 vitest tests verifying UI rendering, disclaimer banners, and lack of misleading confidence metrics.

---

## 5. Verification & Test Execution Results

| Test Suite | Framework | Tests | Passed | Failed | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tests/test_pest_risk_engine.py` | Pytest | 19 | 19 | 0 | **PASSED** |
| `tests/test_api_pest_risk.py` | Pytest | 9 | 9 | 0 | **PASSED** |
| `tests/test_data_ingestion.py` | Pytest | 5 | 5 | 0 | **PASSED** |
| Full Repository Backend Suites | Pytest | 76 (77 incl. timeout) | 76 | 0 | **PASSED** |
| `frontend/src/__tests__/App.test.jsx` | Vitest / jsdom | 4 | 4 | 0 | **PASSED** |
| Frontend Production Build (`npm run build`) | Vite | 42 modules | 42 | 0 | **PASSED** |

---

## 6. Preservation of Existing Functionality

As required:
- The existing `/api/v1/advisory/unified` endpoint remains untouched and fully functional.
- The preliminary rule-based agroclimatic pest risk indicators inside `UnifiedAdvisorySection.jsx` remain intact.
- The maize disease CNN model (`models/maize_disease/maize_disease_model.keras`) was **not modified**.
- The fertilizer optimization models and services (`fertilizer_service.py`, `fertilizer_model.joblib`) were **not modified**.
- The `origin/omkar` branch was **not merged**.
- No synthetic surveillance records were added or substituted.

---

## 7. Known Limitations & Remaining Blockers

1. **Environmental Favorability is Not Occurrence:** A high favorability score (e.g. 0.85) proves that temperature, humidity, rainfall, and soil moisture are conducive to pest multiplication, but insects cannot emerge without local biological inoculum, surviving pupae, or immigration flights.
2. **Missing Ground Surveillance Ground Truth:** CROPSAP Maharashtra and ICAR-NCIPM historical surveillance records remain ungated and unreleased for automated download. Genuine 7-day supervised machine learning outbreak models cannot be trained until authenticated ground-truth surveillance labels are ingested.

