# AgriAdapt AI — Synthetic Pest Forecasting Dataset Version 2.0 Audit & Specification Report
**Document Reference:** `docs/phase20_synthetic_dataset_v2_report.md`  
**Phase:** 20 Follow-up — Synthetic Dataset Improvement, Experimental Retraining & Metric Verification  
**Dataset File:** `data/experimental/synthetic_pest_forecasting_v2.csv` (16.2 MB)  
**Generator:** `src/pest_forecasting/synthetic_generator_v2.py` (Seed: 42)  
**SHA-256 Checksum:** `f8fd7212724576849e3fad0086c4a13bbac0dfd940b622db8d1eb1b4445937e2`  
**Classification:** `SYNTHETIC_EXPERIMENTAL_V2`  
**Status:** COMPLETE & AUDITED  

---

## 1. Executive Summary & Purpose

In response to the Phase 20 experimental audit, a completely separate, versioned synthetic dataset (`synthetic_pest_forecasting_v2.csv`) was generated to address the structural and biological weaknesses of the original synthetic benchmark.

The original synthetic dataset was preserved intact at `data/synthetic_multicrop_pest_forecasting.csv` alongside all Phase 19 artifacts. The new dataset introduces realistic biophysical weather-hydrology dynamics, latent pest population trajectories, intermittent scouting observation processes, and a rigorously formulated forward target without synchronous feature leakage.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                    VERSION 1.0 vs VERSION 2.0 DATASET COMPARISON                 │
├───────────────────────────────┬──────────────────────────────────────────────────┤
│ Aspect                        │ Version 1.0 (Phase 19)   │ Version 2.0 (Phase 20) │
├───────────────────────────────┼──────────────────────────┼───────────────────────┤
│ Target Generation             │ Threshold on future obs  │ Latent pop max L_{t+7}│
│ Scouting Availability         │ Perfect daily scouting   │ Intermittent (7-14d)  │
│ Scouting Lag Tracking         │ None                     │ days_since_scouting   │
│ Scout Detection Noise         │ None (Deterministic)     │ Imperfect detection   │
│ Soil Moisture Dynamics        │ Absent                   │ Hydrologic balance    │
│ Environmental Correlation (r) │ Weak (|r| = 0.01 - 0.08) │ Strong (|r| = 0.22 - 0.39)│
│ Observation Volume            │ 100,000 records          │ 100,000 records       │
│ Feature Columns               │ 17 columns               │ 21 columns            │
│ Target Prevalence             │ 16.91% outbreaks         │ 10.50% outbreaks      │
│ Operational Role              │ Experimental Benchmark   │ Experimental Benchmark│
└───────────────────────────────┴──────────────────────────┴───────────────────────┘
```

---

## 2. Audit of the Original Synthetic Generator (Version 1.0 Weaknesses)

An empirical audit of `data/synthetic_multicrop_pest_forecasting.csv` revealed six fundamental methodological limitations:

1. **Synchronous Scouting Momentum Leakage:**
   - In Version 1.0, current scouting incidence (`current_incidence_pct_t0`) had a Pearson correlation of **$r = +0.7458$** with the target `outbreak_within_7d`.
   - The model learned that fields with 8% incidence today almost always reached 10% (ETL) within 7 days simply through existing larval feeding, functioning as an *infestation momentum extrapolator* rather than an *early-warning sensor*.
2. **Artificial Perfect Daily Scouting:**
   - Version 1.0 assumed that an entomological scout conducted exhaustive sampling (dissecting bolls or counting plants) every single calendar day on every single farm with zero measurement error.
   - In real-world commercial farming in Maharashtra, scouts visit sentinel fields intermittently (typically once every 7 to 10 days).
3. **Decoupled Environmental Physics:**
   - Environmental covariates in Version 1.0 exhibited negligible predictive relationship with future outbreaks ($|r| \le 0.08$). When scouting variables were excluded, model PR-AUC collapsed from $0.84$ to $0.28$, barely exceeding random baseline prevalence.
4. **Absence of Latent Pest Biological State:**
   - Version 1.0 lacked an internal biological state variable. Pest outbreaks were generated via static rules rather than modeling the differential growth and survival of egg, larval, pupal, and adult life stages under thermal constraints.
5. **Missing Soil Moisture Hydrology:**
   - Soil moisture was absent from the feature set. Rainfall was modeled as simple rolling cumulative totals without accounting for infiltration, runoff, dry-spell persistence, or evapotranspiration.
6. **Cross-Partition Field Generalization Risk:**
   - Although partitioned chronologically, the 913 simulated fields in Version 1.0 lacked explicit tracking of scouting lag or harvest fallow cycles.

---

## 3. Biophysical Architecture of Version 2.0

The Version 2.0 generator (`src/pest_forecasting/synthetic_generator_v2.py`) implements a transparent biophysical simulation engine:

```mermaid
flowchart TD
    subgraph Environment["Continuous Biophysical Weather & Soil Hydrology"]
        W1["Daily Temperature & RH<br/>(Diurnal cycle + AR(1) noise)"]
        W2["Rainfall Markov Model<br/>(Monsoon vs Dry season)"]
        W3["Soil Water Balance<br/>(Inflow - Evaporation - Drainage)"]
    end

    subgraph Crop_Phenology["Host Plant Phenological Calendar"]
        C1["Annual Sowing with Farmer Jitter"]
        C2["Thermal Degree-Day Advancement"]
        C3["Stage-Dependent Organ Susceptibility w_stage"]
    end

    subgraph Latent_Biology["Unobserved Latent Pest Population (L_t)"]
        B1["Thermal Beta Curve f(T)"]
        B2["Humidity Suitability g(RH)"]
        B3["Larval Wash-off & Natural Mortality"]
        B4["Differential Growth: L_{t+1} = L_t · exp(r_t)"]
    end

    subgraph Observation_Layer["Intermittent Scouting & Trap Monitoring (t_0)"]
        O1["Scouting Visits Every 7-14 Days"]
        O2["Pheromone Trap Catch (Poisson)"]
        O3["Imperfect Scout Detection (Cryptic larvae)"]
        O4["Days Since Last Scouting Tracking"]
    end

    subgraph Future_Target["Forward 7-Day Target Generation [t_0+1, t_0+7]"]
        T1["Future Latent Population Trajectory"]
        T2["Outbreak Label: max_{k=1..7} (L_{t_0+k}) >= ETL"]
    end

    W1 --> B1
    W1 --> B2
    W2 --> B3
    W2 --> W3
    W3 --> C2
    C1 --> C2 --> C3
    B1 --> B4
    B2 --> B4
    B3 --> B4
    C3 --> B4
    B4 --> O1 --> O2 & O3 & O4
    B4 --> T1 --> T2
```

### 3.1. Continuous Weather & Soil Hydrology
- **Temperature:** Modeled with an annual seasonal harmonic, diurnal amplitude ($T_{\min} = T_{\text{mean}} - 0.45\Delta, T_{\max} = T_{\text{mean}} + 0.55\Delta$), and $\text{AR}(1)$ temporal autocorrelation ($\phi = 0.78$) reflecting synoptic weather systems.
- **Monsoon Rainfall:** Generated via a two-state Markov chain:
  - Monsoon period (June 10 to October 2): $P(\text{rain}|\text{dry}) = 0.32$, $P(\text{rain}|\text{rain}) = 0.58$, scale = $18.0\text{ mm}$.
  - Non-monsoon period: $P(\text{rain}|\text{dry}) = 0.04$, scale = $6.0\text{ mm}$.
- **Soil Hydrology:**
  $$S_{t} = \text{clip}\left(S_{t-1} + \min(0.15, \text{Rain}_t \cdot 0.004) - 0.008 \cdot \frac{T_t}{30} \cdot \left(1 - \frac{\text{RH}_t}{120}\right), 0.11, 0.44\right)$$

### 3.2. Biological Profiles & Latent Population Dynamics
Six crop-pest complexes were simulated using entomological thermal parameters from published literature (Fand et al., 2021; ICAR-CICR protocols):
1. **Cotton / Pink bollworm** (*Pectinophora gossypiella*): $T_{\text{base}} = 12.0^\circ\text{C}, T_{\text{opt}} = 28.0^\circ\text{C}, T_{\max} = 38.0^\circ\text{C}$.
2. **Soybean / Tobacco caterpillar** (*Spodoptera litura*): $T_{\text{base}} = 10.5^\circ\text{C}, T_{\text{opt}} = 28.5^\circ\text{C}, T_{\max} = 35.5^\circ\text{C}$.
3. **Maize / Fall armyworm** (*Spodoptera frugiperda*): $T_{\text{base}} = 10.0^\circ\text{C}, T_{\text{opt}} = 27.5^\circ\text{C}, T_{\max} = 36.0^\circ\text{C}$.
4. **Rice / Brown planthopper** (*Nilaparvata lugens*): $T_{\text{base}} = 11.5^\circ\text{C}, T_{\text{opt}} = 26.5^\circ\text{C}, T_{\max} = 32.5^\circ\text{C}$ (Strict high-RH requirement $\ge 75\%$).
5. **Chickpea / Pod borer** (*Helicoverpa armigera*): $T_{\text{base}} = 10.0^\circ\text{C}, T_{\text{opt}} = 23.5^\circ\text{C}, T_{\max} = 32.0^\circ\text{C}$ (Rabi cool-season profile).
6. **Tomato / Fruit borer** (*Helicoverpa armigera*): $T_{\text{base}} = 10.0^\circ\text{C}, T_{\text{opt}} = 25.0^\circ\text{C}, T_{\max} = 34.0^\circ\text{C}$.

Latent pest population ($L_t$) evolves daily:
$$r_t = 0.35 \cdot \mu_{\text{temp}}(T_t) \cdot \mu_{\text{rh}}(\text{RH}_t) \cdot w_{\text{stage}}(t) - 0.12 - \text{washoff}(R_t)$$
$$L_{t+1} = \text{clip}\left(L_t \cdot \exp(r_t + \xi_t), 0.02, 12.0\right)$$

### 3.3. Intermittent Observation Process
- Scouts visit fields intermittently every 7 to 12 days.
- When $L_t < 1.2$, pests are cryptic: 90% of visits record 0% incidence and 0 moths/trap.
- When $L_t \ge 1.2$, imperfect detection applies: scouts have a detection probability $P_{\text{detect}} = \min(0.95, 0.45 + 0.12 L_t)$.
- Between visits, previous observations persist, but `days_since_scouting` increments each day ($0, 1, 2, \dots, 12$), explicitly signaling observation age to downstream ML pipelines.

### 3.4. Target Formulation ($t+7$)
The target `outbreak_within_7d` is calculated by inspecting the maximum latent population over the prospective 7-day window $[t_0+1, t_0+7]$:
$$\text{outbreak\_within\_7d} = \begin{cases} 1 & \text{if } \max_{k=1..7} (L_{t_0+k}) \ge \text{ETL}_{\text{latent}} \\ 0 & \text{otherwise} \end{cases}$$
Because $L_{t_0+k}$ is determined by the environmental drivers between $t_0+1$ and $t_0+7$, environmental conditions directly dictate whether a latent population flares into an outbreak or collapses.

---

## 4. Quantitative Dataset Architecture & Schema

| # | Column Name | Data Type | Physical Range | Description & Availability |
| :-: | :--- | :--- | :--- | :--- |
| **01** | `field_id` | String | `FLD-V2-XXX-NNNN` | Unique sentinel field identifier (576 fields) |
| **02** | `district` | String | 8 Districts | Maharashtra Vidarbha & Khandesh districts |
| **03** | `crop` | String | 6 Crops | Cotton, Soybean, Maize, Rice, Chickpea, Tomato |
| **04** | `pest` | String | 6 Pests | Primary pest complex species |
| **05** | `date` | String (ISO) | `2023-06-07` to `2025-12-30` | Observation cutoff date ($t_0$) |
| **06** | `growth_stage` | String | 4–6 stages/crop | Phenological stage of host crop |
| **07** | `t7_mean_temp_c` | Float64 | $[16.81, 41.51]^\circ\text{C}$ | 7-day rolling mean air temperature |
| **08** | `t7_min_temp_c` | Float64 | $[10.04, 36.13]^\circ\text{C}$ | 7-day rolling minimum temperature |
| **09** | `t7_max_temp_c` | Float64 | $[22.49, 48.56]^\circ\text{C}$ | 7-day rolling maximum temperature |
| **10** | `t7_mean_rh_pct` | Float64 | $[41.68, 96.77]\%$ | 7-day rolling mean relative humidity |
| **11** | `t7_high_rh_days` | Int64 | $[0, 7]$ days | Days in past week with $\text{RH} \ge 80\%$ |
| **12** | `t7_rainfall_mm` | Float64 | $[0.0, 237.6]\text{ mm}$ | 7-day cumulative rainfall |
| **13** | `t14_rainfall_mm` | Float64 | $[0.0, 410.0]\text{ mm}$ | 14-day cumulative rainfall |
| **14** | `t7_mean_soil_moisture` | Float64 | $[0.11, 0.44]\,\text{m}^3/\text{m}^3$ | 7-day rolling volumetric soil moisture |
| **15** | `t7_consecutive_dry_days` | Int64 | $[0, 7]$ days | Consecutive days with rain $< 1\text{ mm}$ in past 7d |
| **16** | `days_since_scouting` | Int64 | $[0, 12]$ days | Days elapsed since most recent scouting visit |
| **17** | `scout_incidence_pct` | Float64 | $[0.0, 100.0]\%$ | Most recent observed plant incidence |
| **18** | `scout_severity_pct` | Float64 | $[0.0, 35.0]\%$ | Most recent observed tissue damage severity |
| **19** | `trap_catch_count` | Float64 | $[0.0, 47.0]$ adults | Most recent pheromone/light trap catch |
| **20** | `pest_present` | Int64 | $\{0, 1\}$ | Binary presence indicator ($74.0\%$ 0, $26.0\%$ 1) |
| **21** | `outbreak_within_7d` | Int64 | $\{0, 1\}$ | **TARGET:** Future outbreak in $[t_0+1, t_0+7]$ ($10.50\%$) |

---

## 5. Statistical & Correlation Analysis

```
Pearson Correlation Matrix with Target (outbreak_within_7d):
┌──────────────────────────────────────┬───────────────────────────────┐
│ Feature                              │ Pearson Correlation (r)       │
├──────────────────────────────────────┼───────────────────────────────┤
│ scout_incidence_pct                  │ +0.7768 (Scouting signal)     │
│ scout_severity_pct                   │ +0.7702 (Scouting signal)     │
│ trap_catch_count                     │ +0.7635 (Trap signal)         │
│ pest_present                         │ +0.5085 (Detection indicator) │
│ t7_consecutive_dry_days              │ +0.3043 (Prolonged dry spell) │
│ t7_mean_soil_moisture                │ -0.2170 (High soil moisture)  │
│ t7_high_rh_days                      │ -0.2529 (Excessive monsoon RH)│
│ t7_rainfall_mm                       │ -0.2702 (Larval wash-off)     │
│ t7_mean_rh_pct                       │ -0.2838 (Humidity inhibition) │
│ t14_rainfall_mm                      │ -0.3272 (Cumulative wetness)  │
│ t7_min_temp_c                        │ -0.3743 (Night chilling)      │
│ t7_mean_temp_c                       │ -0.3919 (Mean heat stress)    │
│ t7_max_temp_c                        │ -0.3922 (Lethal peak heat)    │
│ days_since_scouting                  │ +0.0083 (Independent)         │
└──────────────────────────────────────┴───────────────────────────────┘
```

The environmental variables in Version 2.0 now exhibit strong, physically explainable relationships with future pest outbreaks ($|r| = 0.22 - 0.39$), providing genuine meteorological predictive signals for the Environmental-Only pipeline.

---

## 6. Scientific Governance & Production Disclaimers

> [!CAUTION]
> **SYNTHETIC_EXPERIMENTAL_V2 CLASSIFICATION**  
> `data/experimental/synthetic_pest_forecasting_v2.csv` is an experimental research dataset designed for MLOps pipeline benchmarking, algorithmic stress testing, and feature engineering comparisons.
> 
> - It is **strictly prohibited** from being used to train commercial operational models.
> - It must **never** be merged with authentic field surveillance data (`data/processed/pest_surveillance/`).
> - The production readiness gate remains strictly **`BLOCKED`** pending authentic commercial surveillance acquisition.

