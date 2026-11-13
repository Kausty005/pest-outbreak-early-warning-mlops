# AgriAdapt AI — Phase 19: Synthetic Multi-Crop Pest Forecasting Dataset Audit

**Document ID:** `AGRI-DATA-SYNTHETIC-AUDIT-2027-V1`  
**Version:** 1.0.0  
**Phase:** 19  
**Dataset File:** `data/synthetic_multicrop_pest_forecasting.csv` (11.34 MB)  
**Generation Seed:** 42  
**Classification:** `SYNTHETIC BENCHMARK DATASET AUDIT`  
**Governing Principle:** Synthetic benchmark records must NEVER be conflated with authentic field surveillance observations.

---

## 1. Executive Summary

This document presents an independent, empirical data audit of `data/synthetic_multicrop_pest_forecasting.csv`. 

An earlier experiment claimed that a Random Forest model achieved a Test PR-AUC of **0.8437** on this dataset, but its performance collapsed to **0.2989** when scouting severity and incidence variables were excluded.

Our independent empirical audit confirms this phenomenon:
1. **The Dataset Structure:** Exactly 100,000 rows and 17 columns spanning 3 simulated growing years (2022-06-20 to 2025-03-21) across 24 agricultural districts and 6 crop-pest systems.
2. **Data Cleanliness:** 0 missing values, 0 duplicate rows, and strict adherence to physical bounds ($T_{\min} \le T_{\max}$, $R_{7} \le R_{14}$, $\text{RH} \in [0, 100]$).
3. **Class Imbalance:** Overall outbreak prevalence is **16.91%** (16,911 positive outbreak events; 83,089 negative non-outbreak windows).
4. **Target Leakage Discovery:** The in-field scouting variables `current_incidence_pct_t0` and `current_severity_pct_t0` exhibit an immense linear correlation of **$r = 0.7458$** with `outbreak_within_7d`. Because pest population growth is continuous, observing high pest damage at $t_0$ makes an outbreak in the next 7 days virtually certain.
5. **Prediction-Time Unavailability:** In practical agricultural operations, farmers and extension officers require warnings 7 to 14 days **before** widespread visual damage occurs. Treating current scouting damage as an input feature turns the model into an *infestation momentum extrapolator* rather than an *environmental early-warning forecaster*.

---

## 2. Dataset Schema & Column Definitions

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           SYNTHETIC DATASET SCHEMA (17 COLUMNS)                                 │
├──────┬──────────────────────────┬──────────────┬──────────────┬─────────────────────────────────┤
│ Col# │ Column Name              │ Data Type    │ Unit / Range │ Description & Availability      │
├──────┼──────────────────────────┼──────────────┼──────────────┼─────────────────────────────────┤
│  01  │ field_id                 │ Object (str) │ FLD-XXX-NNNN │ Unique synthetic field ID (913) │
│  02  │ district                 │ Object (str) │ 24 Districts │ Administrative district location│
│  03  │ crop                     │ Object (str) │ 6 Crops      │ Crop type                       │
│  04  │ pest                     │ Object (str) │ 6 Pests      │ Target pest species             │
│  05  │ date                     │ Object (str) │ YYYY-MM-DD   │ Observation reference date (t0) │
│  06  │ growth_stage             │ Object (str) │ Phenological │ Physiological crop growth stage │
│  07  │ t7_mean_temp_c           │ Float64      │ [10.1, 35.7] │ 7-day rolling mean temperature  │
│  08  │ t7_min_temp_c            │ Float64      │ [3.8, 30.5]  │ 7-day rolling minimum temp      │
│  09  │ t7_max_temp_c            │ Float64      │ [17.3, 42.4] │ 7-day rolling maximum temp      │
│  10  │ t7_mean_rh_pct           │ Float64      │ [44.6, 98.0] │ 7-day rolling mean humidity (%) │
│  11  │ t7_high_rh_days          │ Int64        │ [0, 7] days  │ Days in past week with RH ≥ 80% │
│  12  │ t7_rainfall_mm           │ Float64      │ [0.0, 214.6] │ 7-day cumulative rainfall (mm)  │
│  13  │ t14_rainfall_mm          │ Float64      │ [0.0, 293.7] │ 14-day cumulative rainfall (mm) │
│  14  │ current_incidence_pct_t0 │ Float64      │ [0.0, 20.8]  │ Scouting % plants infested at t0│
│  15  │ current_severity_pct_t0  │ Float64      │ [0.0, 12.4]  │ Scouting % tissue damage at t0  │
│  16  │ pest_present_t0          │ Int64        │ {0, 1}       │ Scouting binary presence at t0  │
│  17  │ outbreak_within_7d       │ Int64        │ {0, 1}       │ TARGET: Outbreak in [t0+1, t0+7]│
└──────┴──────────────────────────┴──────────────┴──────────────┴─────────────────────────────────┘
```

---

## 3. Quantitative Distribution & Slicing Analysis

### 3.1 Target Distribution and Class Imbalance
- Total Samples: **100,000**
- Class 0 (No Outbreak in next 7 days): **83,089 (83.09%)**
- Class 1 (Outbreak in next 7 days): **16,911 (16.91%)**
- Imbalance Ratio: **$4.91 : 1$** (Approximately 1 outbreak event for every 5 non-outbreak windows).

### 3.2 Crop and Pest System Breakdown

| Crop | Target Pest | Scientific Name | Total Rows | Outbreak Events | Prevalence (%) |
|:---|:---|:---|:---:|:---:|:---:|
| **Chickpea** | Pod borer | *Helicoverpa armigera* | 16,666 | 2,248 | 13.49% |
| **Wheat** | Aphids | *Rhopalosiphum padi* | 16,667 | 2,437 | 14.62% |
| **Maize** | Fall armyworm | *Spodoptera frugiperda* | 16,667 | 2,743 | 16.46% |
| **Rice** | Brown planthopper | *Nilaparvata lugens* | 16,667 | 2,772 | 16.63% |
| **Cotton** | Pink bollworm | *Pectinophora gossypiella* | 16,667 | 3,018 | 18.11% |
| **Tomato** | Fruit borer | *Helicoverpa armigera* | 16,666 | 3,693 | 22.16% |
| **Total** | — | — | **100,000** | **16,911** | **16.91%** |

### 3.3 Temporal and Geographic Coverage
- **Temporal Span:** 2022-06-20 to 2025-03-21 (825 unique observation dates across 3 full annual agricultural cycles).
- **Temporal Ordering:** Sorted monotonically by date.
- **Geographic Spread:** 24 simulated Indian agricultural districts:
  * Maharashtra: Nagpur, Amravati, Yavatmal, Akola, Nashik, Pune.
  * Karnataka: Davanagere, Belagavi, Dharwad, Kalaburagi, Kolar.
  * Andhra Pradesh / Telangana: East Godavari, Chittoor, Karimnagar, Adilabad.
  * Madhya Pradesh: Chhindwara, Indore, Vidisha.
  * Punjab / Haryana / UP: Ludhiana, Karnal, Meerut.
  * West Bengal / Odisha / Tamil Nadu: Burdwan, Cuttack, Thanjavur.
- **Unique Sentinel Fields:** 913 simulated fields.

---

## 4. Synthetic Generation Mechanism & Target Formulation

### 4.1 Biophysical Simulation Architecture
The dataset was produced by `src/data/generate_synthetic_pest_data.py` using biological simulation profiles:
- **Thermal Development Curves:** Daily degree-day accumulation based on species-specific base temperatures ($T_{\text{base}}$) and optimum thermal ranges ($[T_{\text{opt\_min}}, T_{\text{opt\_max}}]$).
- **Humidity and Rain Dynamics:** Stochastic rainfall triggers and high-RH thresholds simulating monsoon surges.
- **Phenological Susceptibility:** Stage-dependent vulnerability weights ($w_{\text{stage}} \in [0.1, 1.0]$) reflecting organ availability (e.g. cotton squaring and boll formation; maize whorl stages).
- **Population Auto-Regressive Drift:** Daily pest population updates follow:
  $$P_{t} = P_{t-1} \cdot \exp\left(r_{\max} \cdot f(T) \cdot g(\text{RH}) \cdot w_{\text{stage}} - m_{\text{natural}}\right)$$

### 4.2 Target Definition ($[t_0+1, t_0+7]$)
The binary target `outbreak_within_7d` is calculated by evaluating field conditions over the forward 7-day window:
$$\text{outbreak\_within\_7d} = \begin{cases} 1 & \text{if } \max_{k=1..7} (\text{Severity}_{t_0+k}) \ge \text{ETL}_{\text{sev}} \\ & \text{ or } \max_{k=1..7} (\text{Incidence}_{t_0+k}) \ge \text{ETL}_{\text{inc}} \\ & \text{ or } \max_{k=1..7} (\text{Incidence}_{t_0+k}) - \text{Incidence}_{t_0} \ge 8.0\% \\ 0 & \text{otherwise} \end{cases}$$

---

## 5. Target Leakage & Prediction-Time Feature Availability Audit

### 5.1 Pearson Correlation Analysis with `outbreak_within_7d`

```
┌──────────────────────────────────────┬───────────────────────────────┐
│ Feature Column                       │ Correlation with Target (r)   │
├──────────────────────────────────────┼───────────────────────────────┤
│ current_incidence_pct_t0             │ +0.7458  (Extreme Momentum)   │
│ current_severity_pct_t0              │ +0.7458  (Extreme Momentum)   │
│ pest_present_t0                      │ +0.4379  (Strong Presence)    │
│ t14_rainfall_mm                      │ +0.0806  (Weak Environmental) │
│ t7_rainfall_mm                       │ +0.0706  (Weak Environmental) │
│ t7_max_temp_c                        │ +0.0672  (Weak Environmental) │
│ t7_mean_temp_c                       │ +0.0653  (Weak Environmental) │
│ t7_min_temp_c                        │ +0.0614  (Weak Environmental) │
│ t7_mean_rh_pct                       │ +0.0337  (Weak Environmental) │
│ t7_high_rh_days                      │ +0.0165  (Weak Environmental) │
└──────────────────────────────────────┴───────────────────────────────┘
```

### 5.2 Critical Finding: The Scouting Momentum Dilemma
The correlation between `current_incidence_pct_t0` / `current_severity_pct_t0` and the forward outbreak label is **+0.7458**.

This explains why an ML model trained on the Full feature set achieves an apparent PR-AUC of 0.84+:
- The model is not learning the biophysical causes of pest flare-ups.
- Instead, it observes that a field with 8% incidence today has a $>85\%$ chance of reaching 10% (ETL) within 7 days simply due to existing larval feeding.
- **Prediction-Time Unavailability:** In practical farming, intensive destructive sampling (dissecting 20 green bolls per field) is not performed daily. An early warning system must provide advisories based on meteorological and satellite data **before** scouts observe damaging infestation levels.

---

## 6. Audit Conclusion & Recommendations

1. **Rejection of Full Model as an Early-Warning Sensor:** Models trained with `current_incidence_pct_t0` and `current_severity_pct_t0` must be classified as **Infestation Momentum Extrapolators**, not Early-Warning Forecasters.
2. **Mandatory Environmental-Only Benchmark:** To establish realistic baseline expectations for remote/meteorological pest forecasting, an **Environmental-Only feature set** excluding all scouting variables must be trained and compared side-by-side.
3. **No Synthetic Contamination:** This synthetic dataset must remain strictly isolated within experimental modules (`src/pest_forecasting/`, `models/experimental_synthetic_pest/`) and must never be merged into production advisory services or authentic surveillance stores.

