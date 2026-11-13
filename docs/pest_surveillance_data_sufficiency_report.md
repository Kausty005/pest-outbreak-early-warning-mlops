# Authentic Pest Surveillance Data Sufficiency & Feasibility Assessment

**Project:** AgriAdapt AI / Pest Outbreak Early Warning MLOps  
**Component:** Ground-Truth Surveillance Data Sufficiency Assessment  
**Region:** Maharashtra, India (Nagpur, Amravati, Yavatmal, Jalgaon)  
**Author:** Senior Agricultural Machine Learning Engineer & MLOps Architect  
**Date:** November 13, 2026  
**Status:** **SUPERVISED OUTBREAK MODEL TRAINING REMAINS BLOCKED**

---

## 1. Executive Summary & Core Conclusion

Following comprehensive investigation across government agencies (MahaAgri CROPSAP), national research institutes (ICAR-NCIPM, ICAR-CICR), state agricultural universities (Dr. PDKV Akola, VNMKV Parbhani, MPKV Rahuri), and public scientific repositories (ICAR KRISHI, Zenodo, Dryad, Figshare), **no authentic, open-access, longitudinal field pest surveillance records (incidence %, severity %, or pheromone trap catches) are currently downloadable without formal ministerial credentials or institutional data-sharing agreements.**

While the project has successfully acquired and validated **612 daily environmental and ERA5-Land topsoil moisture records** across four Maharashtra districts from June 1, 2023, to October 31, 2023, **zero authentic ground-truth pest surveillance labels exist in the active repository**.

> [!CAUTION]
> **STRICT SCIENTIFIC RESTRICTION:**  
> In accordance with MLOps architectural integrity and biological safety protocols:  
> 1. Supervised pest outbreak model training **must not proceed**.
> 2. Synthetic surrogate labels or rule-based proxies must **never** be substituted for real surveillance.
> 3. Environmental Favorability Index (EFI) scores must **never** be used as training targets or converted into pseudo-outbreak probabilities.

---

## 2. Quantitative Inventory of Repository Assets

| Asset Category | Variable / Source | Quantity | Coverage / Temporal Span | Ground-Truth Authenticity |
| :--- | :--- | :--- | :--- | :--- |
| **Environmental Weather** | Open-Meteo Gridded Archive | 612 rows | June 1, 2023 – Oct 31, 2023 (Nagpur, Amravati, Yavatmal, Jalgaon) | **Authentic Meteorological** (ERA5 / Numerical Model) |
| **Topsoil Moisture (0–7 cm)** | Copernicus ERA5-Land Reanalysis | 612 rows | June 1, 2023 – Oct 31, 2023 (4 district centroids) | **Authentic Physical Edaphic** |
| **Public Agricultural Advisories** | ICAR-CICR, CROPSAP, PDKV, IMD Agrimet | 49 records (10 documents) | Vidarbha & Central Maharashtra (Kharif/Rabi bulletins) | **Authentic Institutional Guidance** (Epistemic intelligence; NOT field surveillance) |
| **Crop Recommendation Model** | Kaggle Crop Recommendation (2,200 rows) | 2,200 rows | Multi-crop soil NPK, pH, climate | **Separate Component** (Preserved, untouched) |
| **Fertilizer Dosage Model** | Indian Soil Nutrient Index Model | 2,000 rows | Soil chemistry & fertilizer recommendations | **Separate Component** (Preserved, untouched) |
| **Maize Leaf Disease Model** | PlantVillage CNN (`.keras`) | 18,000+ imgs | Leaf pathology classification | **Separate Component** (Preserved, untouched) |
| **Field Pest Incidence Records** | CROPSAP / NCIPM Field Scouting | **0 rows** | **None currently ingested** | **MISSING — BLOCKED** |
| **Pheromone Trap Catches** | ICAR-CICR / Field Delta Traps | **0 rows** | **None currently ingested** | **MISSING — BLOCKED** |
| **Authentic Outbreak Labels** | Economic Threshold Exceedances | **0 labels** | **None** | **MISSING — BLOCKED** |

---

## 3. Data Quality & Missingness Analysis

- **Authentic Surveillance Observations:** 0
- **Districts Represented in Surveillance:** 0 (4 districts present in environmental data only)
- **Talukas / Villages with Verified Field Plots:** 0
- **Crop-Pest Combinations with Verified Labels:** 0
- **Missing Value Percentage for Surveillance Targets:** **100.0%**
- **Positive Outbreak Labels ($y=1$):** 0
- **Verified Negative Scouting Visits ($y=0$):** 0
- **Class Imbalance Ratio:** Undetermined (undefined over empty set)

---

## 4. Leakage Risks in Longitudinal Agricultural Forecasting

Training early-warning models on agricultural time series involves critical leakage risks that this pipeline explicitly guards against:

### 4.1 Temporal Lookahead Leakage
- **Risk:** Calculating features using data occurring after time $T$, or using scouting records from day $T+3$ to predict day $T$.
- **Pipeline Guard:** The `surveillance_temporal_alignment` module enforces strict causal windows: antecedent features are computed strictly over $[T-6, T]$. Labels are computed strictly over the forward window $[T+1, T+7]$.

### 4.2 Spatial Cross-Contamination
- **Risk:** Linking a pest observation in Hingna Taluka (Nagpur) with weather from Yavatmal, or associating a district-centroid weather point with a farm 80 km away across a distinct agro-ecological microclimate.
- **Pipeline Guard:** The `surveillance_geospatial_alignment` module enforces Haversine distance thresholds: observations $> 60$ km from environmental stations are rejected as `SPATIAL_MISMATCH`.

### 4.3 Negative Sampling Fallacy (False-Negative Poisoning)
- **Risk:** Assuming that on days where no surveillance was reported, pest incidence was zero.
- **Scientific Reality:** An uninspected field does not mean zero pests; pests multiply silently until scouting detects them. Defaulting unobserved dates to $y = 0$ poisons the classifier with false negatives.
- **Pipeline Guard:** The `surveillance_labeling` module labels an event as negative ($y = 0$) **only if verified scouting occurred in the forward window and confirmed sub-ETL levels**. All unmonitored days remain strictly `None` / `NaN`.

---

## 5. Minimum Data Requirements for an Initial Supervised Model

Before any supervised machine learning classifier (e.g. XGBoost, Random Forest, or LightGBM) can be scientifically trained, the following minimum requirements must be satisfied:

1. **Multi-Season Temporal Coverage:** Minimum of **3 full growing seasons** (e.g. Kharif 2021, Kharif 2022, Kharif 2023) to prevent the model from memorizing a single year's monsoon anomaly.
2. **Sample Size:** Minimum **2,500 to 5,000 authentic scouting observations** collected across at least 10–15 distinct talukas.
3. **Class Representation:** Minimum **250 to 500 documented positive outbreak events** (where scouting incidence or trap catches exceeded official ICAR/NCIPM Economic Threshold Levels).
4. **Spatial Resolution:** Field coordinates located within **$\le 15$ km** of localized weather stations or high-resolution gridded reanalysis cells ($0.1^\circ \times 0.1^\circ$).
5. **Species Isolation:** Models must be trained per crop-pest pair (e.g. separate models for Cotton Pink Bollworm vs Soybean Tobacco Caterpillar), never pooled into an undifferentiated generic "pest" target.

---

## 6. Official Roadmap to Model Training

```
[ Phase 6 Ingestion Pipeline Ready ]
  (surveillance_sources, schema, loader, validation, alignment, labeling)
                  │
                  ▼
[ Institutional Data Acquisition ]
  Execute MoU / Data Sharing Agreement with MahaAgri CROPSAP (Pune)
  or ICAR-CICR (Nagpur) for Vidarbha Kharif scouting records (2021–2024)
                  │
                  ▼
[ Pipeline Execution & Ingestion ]
  Ingest raw CSV exports ──► Validate bounds ──► Geospatial matching ──► Labeling
                  │
                  ▼
[ Sufficiency Gate Check ]
  Verify: >= 2,500 records, >= 250 positive ETL events, zero lookahead leakage
                  │
                  ▼
[ Supervised Early-Warning ML Model Training ]
  Train, cross-validate with Spatial-Temporal GroupKFold, track in MLflow
```

