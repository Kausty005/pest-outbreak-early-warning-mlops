# 🌾 AgriAdapt AI — Agricultural Intelligence & MLOps Platform

An integrated, production-grade agricultural decision support and MLOps platform combining:
1. **🌱 Crop Selection Engine**: Multi-class classifier (Random Forest, Extra Trees, XGBoost) recommending optimal crops based on soil nutrients ($N, P, K, \text{pH}$) and agroclimatic readings (temperature, humidity, rainfall).
2. **🧪 Fertilizer Optimization Engine**: Multi-target weighted ensemble regressor ($\text{RF} + \text{ExtraTrees} + \text{GBDT}$) predicting elemental macronutrient dosages ($N, P_2O_5, K_2O$ in $\text{kg/ha}$) and commercial fertilizer bag equivalents (Urea, DAP, MOP) calibrated to Indian Soil Health Card nutrient indices and ICAR-IISS agroclimatic baselines.
3. **🌾 Unified Advisory & Pest Early-Warning**: Orchestrated advisory workflow linking crop selection to nutrient sizing and preliminary agroclimatic pest outbreak risk indicators (e.g., Cotton Bollworm, Rice Stem Borer, Maize Fall Armyworm).
4. **🔄 Adaptive MLOps Lifecycle**: DVC data versioning, MLflow experiment tracking, Docker Compose containerization, optional PostgreSQL audit persistence, automated CI testing, and drift-monitoring hooks for continuous learning.

---

## 1. Project Architecture & Directory Layout

```
mark2/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── crop.py              # GET /api/v1/crop/schema, /model-info, POST /recommend
│   │   │   ├── fertilizer.py        # GET /api/v1/fertilizer/schema, /model-info, /example, POST /recommend
│   │   │   └── advisory.py          # POST /api/v1/advisory/unified (Crop -> Fertilizer -> Pest Risk)
│   │   ├── core/                    # Settings (config.py), structured logging
│   │   ├── db/                      # SQLAlchemy models (Farm, CropPrediction, FertilizerPrediction, ModelMetadata)
│   │   ├── schemas/                 # Pydantic v2 validation contracts (crop, fertilizer, integration)
│   │   ├── services/                # CropModelService, FertilizerModelService, prediction persistence
│   │   └── main.py                  # FastAPI application with unified lifespan & /health
│   ├── ml/
│   │   ├── data_validation.py       # Auditing & schema validation for crop data
│   │   ├── feature_engineering.py   # Shared scikit-learn transformers
│   │   ├── train.py                 # Crop model training, cross-validation, and selection
│   │   ├── evaluate.py              # Holdout evaluation & confusion matrix
│   │   └── fertilizer.py            # Fertilizer model prediction interface & utilities
│   └── artifacts/                   # Serialized model containers & metadata
│       ├── crop_model.joblib
│       ├── metadata.json
│       ├── fertilizer_model.joblib
│       ├── fertilizer_model_metadata.json
│       └── fertilizer_feature_schema.json
├── data/
│   ├── raw/                         # Crop_recommendation.csv (tracked with DVC)
│   └── processed/
├── frontend/                        # Modern React + Vite Dashboard
│   ├── src/
│   │   ├── components/              # FarmInputForm, FertilizerSection, UnifiedAdvisorySection, Navbar
│   │   ├── services/api.js          # Unified HTTP client for crop, fertilizer, advisory, health
│   │   ├── styles/global.css        # Clean styling, responsive grid, status badges, nutrient cards
│   │   └── App.jsx                  # Tabbed navigation (Crop, Fertilizer, Unified Advisory)
│   ├── package.json
│   └── vite.config.js
├── models/                          # Standalone redistributable fertilizer model package
│   ├── fertilizer_model.joblib
│   ├── fertilizer_model_metadata.json
│   └── fertilizer_feature_schema.json
├── src/                             # Standalone inference wrapper for backward compatibility
│   ├── models/model.py
│   └── models/predict.py
├── tests/                           # Unified Pytest suite (21 test cases)
│   ├── test_api.py                  # Crop API endpoints & invalid bounds
│   ├── test_api_fertilizer.py       # Fertilizer API endpoints, schemas & error rejection
│   ├── test_advisory.py             # Unified end-to-end advisory & pest scenario tests
│   ├── test_features.py             # Feature engineering tests
│   ├── test_training.py             # Leakage-safe training tests
│   └── test_validation.py           # Data integrity audit tests
├── docker-compose.yml               # Multi-service compose (API, Frontend, PostgreSQL, MLflow)
├── Dockerfile                       # Python 3.10 production container
├── dvc.yaml                         # Data version control pipeline
├── integration_example.py           # Standalone verification demo script
├── requirements.txt                 # Unified project dependencies
└── pyproject.toml                   # Ruff & tool configs
```

---

## 2. API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Reports health status for both Crop and Fertilizer models plus persistence |
| `GET` | `/api/v1/crop/schema` | Field specifications and broad validation bounds for crop inputs |
| `GET` | `/api/v1/crop/model-info` | Crop model version, held-out test metrics, and checksum |
| `POST` | `/api/v1/crop/recommend` | Recommends top-3 candidate crops with uncalibrated classifier scores |
| `GET` | `/api/v1/fertilizer/schema` | Feature schema and nutrient indices definitions $[1.0, 3.0]$ |
| `GET` | `/api/v1/fertilizer/model-info` | Multi-target weighted ensemble details (RF + ExtraTrees + GBDT) |
| `GET` | `/api/v1/fertilizer/example` | Returns verified sample plot input (Maharashtra Rice) |
| `POST` | `/api/v1/fertilizer/recommend` | Computes elemental dosages ($N, P_2O_5, K_2O$ in $\text{kg/ha}$) and commercial bags (Urea, DAP, MOP) |
| `POST` | `/api/v1/advisory/unified` | **Unified Workflow**: Runs crop recommendation $\to$ maps to fertilizer sizing $\to$ evaluates pest risk watchlist |

---

## 3. Quick-Start Guide

### Step 1: Environment Setup
Ensure Python 3.10+ and Node.js 18+ are available:

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Run the API Server
Start the unified FastAPI backend:

```bash
uvicorn backend.app.main:app --reload --port 8000
```
Interactive OpenAPI documentation will be accessible at `http://localhost:8000/docs`.

### Step 3: Run the Frontend Dashboard
In a separate terminal window:

```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

### Step 4: Run Containerized Environment (Optional)
Run the full stack via Docker Compose:

```bash
docker compose up --build
```
To enable optional PostgreSQL audit persistence:
```bash
PERSISTENCE_ENABLED=true docker compose --profile persistence up --build
```

---

## 4. Verification & Testing

### Python Backend Tests
Run the comprehensive Pytest suite (21 unit and integration tests):

```bash
python -m pytest tests -v
```

### Frontend Tests & Production Build
Run the Vitest test suite and Vite build:

```bash
cd frontend
npm run test
npm run build
cd ..
```

### Standalone Fertilizer Package Verification
Verify standalone inference:

```bash
python integration_example.py
```

---

## 5. Next Step: Pest Outbreak Early-Warning System (Phase 1–7 Roadmap)

With the Crop Selection and Fertilizer Optimization pipelines seamlessly unified, the platform is ready for the **Pest Outbreak Early-Warning System Using MLOps**:

1. **Phase 1 — Ingestion & Ground Truth**:
   - Collect dated regional pest incidence records (ICAR-NBAIR / Bhuvan) and match with daily weather data (NASA POWER: temperature, precipitation, humidity, solar radiation) for Maharashtra (e.g., Cotton Bollworm).
   - Label binary outbreak events ($1 = \text{infestation threshold exceeded within next 7 days}$).
2. **Phase 2 — ML Model Training**:
   - Chronological time-series split (prevent future leakage).
   - Train XGBoost classifier against Logistic Regression baseline; evaluate PR-AUC, Recall, and Brier calibration.
3. **Phase 3 — MLOps Pipeline Integration**:
   - Add pest training stage to `dvc.yaml`.
   - Log runs, hyperparameters, ROC/PR curves to MLflow.
4. **Phase 4 — Serving**:
   - Mount `/api/v1/pest/predict` on FastAPI returning 7-day outbreak probability and risk category.
5. **Phase 5 — Continuous Monitoring**:
   - Implement Evidently drift detection comparing reference weather distribution against incoming batches.
6. **Phase 6 — Adaptive Retraining**:
   - Automated candidate retraining trigger on detected distribution shift; champion/challenger comparison before promotion.
7. **Phase 7 — Innovation Evaluation**:
   - Quantify detection delay, recovery time, and prediction stability comparing static vs. adaptive models.
