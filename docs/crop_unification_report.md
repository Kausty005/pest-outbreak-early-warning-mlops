# 🌾 Crop List Extraction, Model Comparison & Centralized Configuration Report

**Project**: AgriAdapt AI — Pest Outbreak Early Warning MLOps Platform  
**Date**: October 20, 2026  
**Status**: Step 1–6 Complete · Awaiting User Review & Approval for Common Crop List  

---

## 1. Executive Summary

This report establishes the single source of truth for crop names, canonical identifiers, model mappings, and pest outbreak prediction eligibility across the **AgriAdapt AI MLOps Platform**.

Before adding the new **Pest Early Outbreak Detection Model**, we inspected the active models, inference code, datasets, and schemas across the repository. We extracted every supported crop, established a canonical naming convention, resolved naming discrepancies (such as *Maize vs. Corn* and *Rice vs. Paddy*), created a centralized configuration [`config/crops.json`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/config/crops.json), implemented a query interface [`backend/app/core/crop_catalog.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/core/crop_catalog.py), added preliminary pest inference schemas and API endpoints, and validated all 34 backend tests, frontend builds, and standalone inference scripts with **100% backward compatibility**.

---

## 2. Actual Crop List Extracted from Existing Project

Across the entire repository, exactly **24 distinct crops** are referenced across the models, datasets, schemas, and preview indicators.

### 2.1 Crop Prediction Model (22 Crops)
Extracted directly from the training dataset [`Crop_recommendation.csv`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/Crop_recommendation.csv), dataset audit records, and model classes:
- **Cereals**: `rice`, `maize`
- **Fibers & Cash Crops**: `cotton`, `jute`
- **Pulses**: `chickpea`, `kidneybeans`, `pigeonpeas`, `mothbeans`, `mungbean`, `blackgram`, `lentil`
- **Fruits**: `pomegranate`, `banana`, `mango`, `grapes`, `watermelon`, `muskmelon`, `apple`, `orange`, `papaya`
- **Plantation**: `coconut`, `coffee`
*(All 22 classes contain exactly 100 observations each in the 2,200-row dataset; labels are lowercase)*.

### 2.2 Fertilizer Recommendation Model (7 Supported Crop Variants across 4 Base Crops)
Extracted directly from the serialized model [`models/fertilizer_model.joblib`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/models/fertilizer_model.joblib), [`models/fertilizer_model_metadata.json`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/models/fertilizer_model_metadata.json), and [`models/fertilizer_feature_schema.json`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/models/fertilizer_feature_schema.json):
1. `Rice`
2. `Wheat`
3. `Sugarcane`
4. `Kharif Maize`
5. `Rabi Maize`
6. `Kharif Rice`
7. `Rice-Rabi`

*Note*: In the unified advisory pipeline ([`backend/app/api/advisory.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/api/advisory.py)), any crop not matching these 7 variants falls back to the baseline `Rice` curve rather than failing.

### 2.3 Pesticide Recommendation Model (Status: No Dedicated ML Model)
- **Status**: There is currently **no dedicated ML pesticide recommendation model** in the codebase (0 files or serialized artifacts exist for chemical spray recommendation).
- **Rule-Based Agroclimatic Pest Risk Preview**: [`backend/app/api/advisory.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/api/advisory.py) implements `evaluate_pest_risk_preview()`, which screens temperature, humidity, and rainfall against 3 specific target crops:
  1. `cotton`: Screens for **Pink Bollworm & American Bollworm** (*Helicoverpa armigera*)
  2. `rice` / `paddy`: Screens for **Yellow Stem Borer & Brown Planthopper (BPH)**
  3. `maize` / `corn`: Screens for **Fall Armyworm** (*Spodoptera frugiperda*)
  - *All other crops*: Receive a general ambient pest multiplication watch.
- **Contract & Roadmap**: [`backend/app/schemas/integration.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/schemas/integration.py) defines `PestAdvisoryContract`, and [`README.md`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/README.md) defines the Phase 1–7 roadmap for time-series pest risk forecasting (XGBoost classifier for 7-day outbreak probability).

---

## 3. Comparison Matrix Across All Models

The table below consolidates all 24 crops, showing canonical IDs, model support, and eligibility for the future pest outbreak model:

| # | Canonical ID | Display Name | Crop Prediction Model | Fertilizer Model Support | Existing Pest Preview | Proposed Pest Outbreak Model Eligible? | Category |
|---|---|---|:---:|:---:|:---:|:---:|---|
| 1 | `rice` | Rice (Paddy) | ✅ Yes (`rice`) | ✅ Yes (`Rice`, `Kharif Rice`, `Rice-Rabi`) | ✅ Yes (Stem Borer, BPH) | **✅ Yes (Tier 1 — Primary)** | Cereal |
| 2 | `maize` | Maize (Corn) | ✅ Yes (`maize`) | ✅ Yes (`Kharif Maize`, `Rabi Maize`) | ✅ Yes (Fall Armyworm) | **✅ Yes (Tier 1 — Primary)** | Cereal |
| 3 | `cotton` | Cotton | ✅ Yes (`cotton`) | ⚠️ Fallback to Rice baseline | ✅ Yes (Bollworms) | **✅ Yes (Tier 1 — Primary)** | Fiber / Cash |
| 4 | `wheat` | Wheat | ❌ Absent from CSV | ✅ Yes (`Wheat`) | ⚠️ General watch | **✅ Yes (Tier 2 — Secondary)** | Cereal |
| 5 | `sugarcane` | Sugarcane | ❌ Absent from CSV | ✅ Yes (`Sugarcane`) | ⚠️ General watch | **✅ Yes (Tier 2 — Secondary)** | Cash Crop |
| 6 | `chickpea` | Chickpea (Gram) | ✅ Yes (`chickpea`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | **✅ Yes (Tier 2 — Secondary)** | Pulse |
| 7 | `pigeonpeas` | Pigeonpeas (Tur/Arhar) | ✅ Yes (`pigeonpeas`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | **✅ Yes (Tier 2 — Secondary)** | Pulse |
| 8 | `apple` | Apple | ✅ Yes (`apple`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Fruit |
| 9 | `banana` | Banana | ✅ Yes (`banana`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Fruit |
| 10 | `blackgram` | Blackgram (Urad) | ✅ Yes (`blackgram`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Pulse |
| 11 | `coconut` | Coconut | ✅ Yes (`coconut`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Plantation |
| 12 | `coffee` | Coffee | ✅ Yes (`coffee`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Plantation |
| 13 | `grapes` | Grapes | ✅ Yes (`grapes`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Fruit |
| 14 | `jute` | Jute | ✅ Yes (`jute`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Fiber |
| 15 | `kidneybeans` | Kidney Beans (Rajma) | ✅ Yes (`kidneybeans`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Pulse |
| 16 | `lentil` | Lentil (Masoor) | ✅ Yes (`lentil`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Pulse |
| 17 | `mango` | Mango | ✅ Yes (`mango`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Fruit |
| 18 | `mothbeans` | Moth Beans (Matki) | ✅ Yes (`mothbeans`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Pulse |
| 19 | `mungbean` | Mung Bean (Moong) | ✅ Yes (`mungbean`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Pulse |
| 20 | `muskmelon` | Muskmelon | ✅ Yes (`muskmelon`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Fruit |
| 21 | `orange` | Orange (Citrus) | ✅ Yes (`orange`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Fruit |
| 22 | `papaya` | Papaya | ✅ Yes (`papaya`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Fruit |
| 23 | `pomegranate` | Pomegranate | ✅ Yes (`pomegranate`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Fruit |
| 24 | `watermelon` | Watermelon | ✅ Yes (`watermelon`) | ⚠️ Fallback to Rice baseline | ⚠️ General watch | ⏳ Conditional (Tier 3 Data-Limited) | Fruit |

### 3.1 Model Overlap Categorization
1. **Fully Supported by both Crop & Fertilizer Models**:
   - `rice` (Paddy)
   - `maize` (Corn)
2. **Supported by Crop Prediction + Pest Preview (Lacking Fertilizer Training Data)**:
   - `cotton` (*Flagship pest early-warning target in Maharashtra*)
3. **Supported by Fertilizer Model Only (Lacking Crop Prediction Training Data)**:
   - `wheat`
   - `sugarcane`
4. **Supported by Crop Prediction Model Only**:
   - 19 crops (Pulses and Horticultural fruits/plantation)

---

## 4. Centralized Crop Configuration Created

### 4.1 Master JSON Configuration (`config/crops.json`)
Created [`config/crops.json`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/config/crops.json) containing:
- Canonical ID, Display Name, Scientific Name, and Agricultural Category.
- Comprehensive accepted aliases (`corn` $\to$ `maize`, `paddy` $\to$ `rice`, `kapas` $\to$ `cotton`, `gehun` $\to$ `wheat`, etc.).
- Explicit model support flags and identifiers for each model.
- Pest outbreak eligibility, priority tier, target pest species, required environmental features, and historical surveillance requirements.

### 4.2 Python Interface & Query Engine (`backend/app/core/crop_catalog.py`)
Created [`CropCatalog`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/core/crop_catalog.py) with cached $O(1)$ lookups:
- `resolve_canonical_id(name)`: Maps any alias or model ID to canonical ID.
- `get_crop(name)`: Retrieves full crop specification.
- `get_fertilizer_identifier(name, season)`: Resolves to valid ICAR-IISS fertilizer vocabulary (`Rice`, `Wheat`, `Kharif Maize`, etc.) or fallback baseline.
- `list_pest_eligible_crops(priority)`: Returns candidates for pest outbreak model.

### 4.3 Export Bridge (`src/utils/crop_catalog.py`)
Created [`src/utils/crop_catalog.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/src/utils/crop_catalog.py) to enable standalone scripts and external pipelines to import and query the centralized catalog without coupling.

---

## 5. Preliminary Interface for Future Pest Outbreak Model

To prepare for Phase 2 without training or fabricating models, we established preliminary contracts and API endpoints:

### 5.1 Proposed Pest Outbreak Model Candidates

#### 1. Cotton (`cotton`) — Priority: Tier 1 (Primary)
- **Target Pest Species**: Pink Bollworm (*Pectinophora gossypiella*), American Bollworm (*Helicoverpa armigera*), Whitefly (*Bemisia tabaci*).
- **Economic Threshold Level (ETL)**: $>8$ moths/trap/night for 3 consecutive days, or $10\%$ damaged green bolls / rosette flowers.
- **Required Historical Pest Data**: Dated regional pheromone trap catches (moths/trap/night), field scouting counts, boll damage percentages.
- **Required Weather Features**: Daily $T_{\max}, T_{\min}$ ($25\text{--}34^\circ\text{C}$ accelerates egg incubation), relative humidity ($>70\%$ peak risk), cumulative rainfall, sunshine hours.
- **Data Availability**: High / Ready for Curation via ICAR-CICR Nagpur, ICAR-NBAIR, and Maharashtra State CROPSAP surveillance.

#### 2. Rice (`rice`) — Priority: Tier 1 (Primary)
- **Target Pest Species**: Yellow Stem Borer (*Scirpophaga incertulas*), Brown Planthopper (*Nilaparvata lugens*).
- **Economic Threshold Level (ETL)**: $5\%$ dead hearts / $1$ egg mass/$\text{m}^2$; $5\text{--}10$ BPH/hill.
- **Required Historical Pest Data**: Light trap catches, sweep-net counts, infested tiller percentages.
- **Required Weather Features**: Mean temperature ($26\text{--}32^\circ\text{C}$), sustained relative humidity ($>80\%$), standing water/rainfall.
- **Data Availability**: Moderate / Ready for Curation via ICAR-NRRI Cuttack, AICRIP (ICAR-IIRR Hyderabad).

#### 3. Maize (`maize`) — Priority: Tier 1 (Primary)
- **Target Pest Species**: Fall Armyworm (*Spodoptera frugiperda*), Maize Stem Borer (*Chilo partellus*).
- **Economic Threshold Level (ETL)**: $5\text{--}10\%$ whorl damage / leaf injury rating.
- **Required Historical Pest Data**: Pheromone trap catches (moths/trap/week), visual whorl infestation percentages.
- **Required Weather Features**: Temperature ($24\text{--}32^\circ\text{C}$), relative humidity ($>65\%$), wind speed & direction (for moth dispersal tracking).
- **Data Availability**: Moderate via ICAR-IIMR Ludhiana/Hyderabad and UAS Dharwad.

#### 4. Pulses (Chickpea `chickpea`, Pigeonpeas `pigeonpeas`) — Priority: Tier 2 (Secondary)
- **Target Pest Species**: Gram Pod Borer (*Helicoverpa armigera*), Pod Fly (*Melanagromyza obtusa*).
- **Data Availability**: Requires dedicated surveillance data collection from ICRISAT / ICAR-IIPR Kanpur before training.

### 5.2 Preliminary Pest Endpoints
Integrated into FastAPI [`backend/app/api/pest.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/api/pest.py):
- `GET /api/v1/pest/eligible-crops`: Lists crops eligible for pest modeling with priority tiers and data sources.
- `GET /api/v1/pest/spec/{crop_identifier}`: Returns crop-specific pest species, economic thresholds, and required features.
- `POST /api/v1/pest/preview`: Runs canonical-aware preliminary agroclimatic risk screening.

---

## 6. Files Created and Modified

### Created Files
| File | Purpose |
|---|---|
| [`config/crops.json`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/config/crops.json) | Centralized single source of truth for all 24 crops, aliases, and model support matrix |
| [`backend/app/core/crop_catalog.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/core/crop_catalog.py) | In-memory indexing and resolution engine for canonical crop IDs and model identifiers |
| [`src/utils/crop_catalog.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/src/utils/crop_catalog.py) | Python bridge enabling standalone scripts and model packages to query the catalog |
| [`backend/app/schemas/pest.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/schemas/pest.py) | Pydantic contracts for pest outbreak specifications, preview, and Phase 2 XGBoost model |
| [`backend/app/api/pest.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/api/pest.py) | FastAPI endpoints for pest eligible crops, crop pest specs, and canonical risk preview |
| [`tests/test_crop_catalog.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/tests/test_crop_catalog.py) | Comprehensive 9-test test suite covering catalog loading, aliases, fallbacks, and APIs |

### Modified Files (Minimal & Backward-Compatible)
| File | Modification & Rationale |
|---|---|
| [`backend/app/api/crop.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/api/crop.py) | Added `GET /api/v1/crop/catalog` endpoint to expose canonical crop configuration to clients |
| [`backend/app/api/advisory.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/api/advisory.py) | Enhanced `evaluate_pest_risk_preview` to resolve aliases via `CropCatalog` while maintaining rule logic |
| [`backend/app/schemas/fertilizer.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/schemas/fertilizer.py) | Enhanced `normalize_crop_name` with catalog lookup while preserving exact existing heuristic fallbacks |
| [`backend/app/api/__init__.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/api/__init__.py) | Exported `pest_router` |
| [`backend/app/main.py`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/app/main.py) | Mounted `pest_router` under `/api/v1/pest` |
| [`frontend/src/services/api.js`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/frontend/src/services/api.js) | Added `cropApi.catalog()`, `pestApi.eligibleCrops()`, `pestApi.spec()`, and `pestApi.preview()` |

---

## 7. Validation & Verification Results

All tests and verification checkpoints were executed locally and passed with zero errors:

1. **Python Unit & Integration Tests**:
   - `python -m pytest tests -v`: **34 passed in 13.53s** (25 existing tests + 9 new crop catalog tests).
   - `tests/test_crop_catalog.py`: 9/9 passed.
   - `tests/test_advisory.py`: 2/2 passed.
   - `tests/test_api_fertilizer.py`: 6/6 passed.
   - `tests/test_monitoring.py`: 4/4 passed.
   - `tests/test_features.py`: 4/4 passed.
   - `tests/test_training.py`: 2/2 passed.
   - `tests/test_validation.py`: 5/5 passed.
   - `tests/test_api.py`: 2/2 passed.
2. **Frontend Test Suite & Production Build**:
   - `npm run test` (Vitest): **2/2 passed in 3.01s**.
   - `npm run build` (Vite production bundle): **Built successfully in 775ms**.
3. **Standalone Fertilizer Package Verification**:
   - `python integration_example.py`: Successfully loaded [`models/fertilizer_model.joblib`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/models/fertilizer_model.joblib) and executed single plot prediction, batch DataFrame inference, and strict out-of-bounds input rejection.
4. **MLOps Pipeline Verification**:
   - [`dvc.yaml`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/dvc.yaml) stages (`train_crop_model`, `fertilizer_artifacts`, `monitor_drift`) verified against active files in [`data/raw/Crop_recommendation.csv`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/data/raw/Crop_recommendation.csv) and [`backend/artifacts/`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/backend/artifacts/).

---

## 8. Limitations & Crops Requiring Additional Data

1. **Wheat & Sugarcane Absence in Crop Prediction**:
   Wheat and Sugarcane are fully supported by the ICAR-IISS fertilizer model, but are **not present** in `Crop_recommendation.csv`. Recommending them as primary crop selections would require augmenting the crop dataset with agroclimatic profiles for northern and subtropical zones.
2. **Cotton Absence in Fertilizer Model**:
   Cotton is the primary cash crop in Maharashtra and the primary focus for pest early-warning (Bollworm), but it was not part of the ICAR-IISS district GFR dataset used to train [`models/fertilizer_model.joblib`](file:///d:/OMKAR/VITP/SEM%205/MLOPS/pest-outbreak-early-warning-mlops/models/fertilizer_model.joblib). The unified advisory pipeline currently falls back to the baseline Rice nutrient curve for cotton. Training a dedicated cotton fertilizer regressor using Soil Health Card cotton baselines is recommended in a future iteration.
3. **Pest Outbreak Data Requirements**:
   A single dataset cannot be generalized across crops. For instance, rice yellow stem borer dynamics cannot predict cotton pink bollworm. Outbreak prediction models must be trained separately per crop using crop-specific pest incidence records:
   - **Cotton**: Requires dated pheromone trap catches from Maharashtra CROPSAP / ICAR-CICR Nagpur.
   - **Rice**: Requires light-trap and hopper count surveillance from ICAR-NRRI / AICRIP.
   - **Maize**: Requires whorl infestation damage ratings from ICAR-IIMR / UAS Dharwad.
   - **Horticultural crops & pulses**: Currently lack standardized, open regional time-series trap records in India; flagged as Tier 3 (data-limited) until dedicated surveillance streams are integrated.
