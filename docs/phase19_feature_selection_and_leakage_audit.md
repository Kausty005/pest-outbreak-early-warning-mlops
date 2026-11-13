# AgriAdapt AI — Phase 19: Feature Selection, Causality & Target Leakage Audit

**Document ID:** `AGRI-FEAT-LEAKAGE-AUDIT-2027-V1`  
**Version:** 1.0.0  
**Phase:** 19  
**Scope:** Rigorous Feature Engineering, Pre-Prediction Availability, and Temporal Partitioning Audit  
**Classification:** EXPERIMENTAL MLOPS GOVERNANCE  

---

## 1. Executive Summary

A core objective of Phase 19 is establishing a scientifically honest, leakage-safe feature engineering pipeline for pest outbreak forecasting. In time-series and epidemiological machine learning, data leakage frequently inflates benchmark metrics, creating a false impression of predictive competence that collapses in real-world deployment.

This audit establishes:
1. **The Dual Experimental Feature Architecture:** Clear demarcation between **Configuration A (Full Synthetic)** and **Configuration B (Environmental-Only)**.
2. **Feature Inclusion/Exclusion Rationale:** Justification for every feature based on prediction-time availability.
3. **The 7-Day Purge Embargo Mechanism:** Mathematical proof of why standard chronological splitting without an embargo creates label overlap leakage across partitions.
4. **Causal Horizon Verification:** Verification that zero future weather or post-outbreak observations contaminate training features.

---

## 2. Dual Experimental Feature Configurations

```
┌────────────────────────────────────────────────────────────────────────┐
│               FEATURE CONFIGURATION COMPARISON MATRIX                  │
├────────────────────────────┬────────────────────┬──────────────────────┤
│ Feature Attribute          │ FULL SYNTHETIC     │ ENVIRONMENTAL-ONLY   │
│                            │ (Configuration A)  │ (Configuration B)    │
├────────────────────────────┼────────────────────┼──────────────────────┤
│ Feature Count              │ **14 Features**    │ **11 Features**      │
│ Categorical Context        │ District, Crop,    │ District, Crop,      │
│                            │ Pest, Growth Stage │ Pest, Growth Stage   │
│ 7-Day Past Weather         │ Mean/Min/Max Temp, │ Mean/Min/Max Temp,   │
│                            │ Mean RH, Rain,     │ Mean RH, Rain,       │
│                            │ High RH Days       │ High RH Days         │
│ 14-Day Past Weather        │ 14-day Rain        │ 14-day Rain          │
│ In-Field Scouting Inputs   │ **Incidence %,**   │ **STRICTLY EXCLUDED**│
│                            │ **Severity %,**    │                      │
│                            │ **Pest Present**   │                      │
│ Prediction-Time Scenario   │ Scout actively in  │ Advance remote early │
│                            │ field measuring    │ warning (AWS/sat     │
│                            │ destructive damage │ weather + phenology) │
│ Outbreak Detection Role    │ Infestation        │ Pre-infestation      │
│                            │ momentum tracker   │ environmental sensor │
└────────────────────────────┴────────────────────┴──────────────────────┘
```

---

## 3. Deep Feature Rationale & Availability Analysis

### 3.1 Features Included in Environmental-Only Configuration (11 Features)

| Feature | Type | Source & Timing | Agronomic Justification for Inclusion |
|:---|:---:|:---|:---|
| `district` | Categorical | Geolocation / Metadata | Encodes macro-climatic zone, elevation, and historical regional pest endemicity. |
| `crop` | Categorical | Farm Master Registry | Determines host plant species, tissue biochemistry, and pest susceptibility profile. |
| `pest` | Categorical | Target Advisory Profile | Establishes target insect biology, thermal thresholds, and diapause characteristics. |
| `growth_stage` | Categorical | Sowing-Date / Phenology Model | Pests target specific organs (e.g. FAW targets whorls; PBW targets squares/bolls). Readily modeled from sowing date and GDD. |
| `t7_mean_temp_c` | Continuous | Automated Weather Station / Reanalysis | Governs poikilothermic insect metabolic rate and degree-day physiological accumulation. |
| `t7_min_temp_c` | Continuous | Automated Weather Station / Reanalysis | Nocturnal minimum temperatures control egg survival and adult flight cessation. |
| `t7_max_temp_c` | Continuous | Automated Weather Station / Reanalysis | Diurnal extremes (>38°C) induce heat-induced egg mortality or larval diapause. |
| `t7_mean_rh_pct` | Continuous | Automated Weather Station / Reanalysis | High humidity (>70%) is critical for soft-bodied sucking pests and lepidopteran egg hatching. |
| `t7_high_rh_days` | Discrete | Automated Weather Station / Reanalysis | Duration of persistent humidity is more predictive of fungal pathogens and pest flare than single-day spikes. |
| `t7_rainfall_mm` | Continuous | Rain Gauge / Gridded IMD Data | Heavy rains physically wash off early instar larvae, whereas light showers promote flush vegetative growth. |
| `t14_rainfall_mm` | Continuous | Rain Gauge / Gridded IMD Data | 14-day cumulative rainfall captures antecedent soil moisture and crop vegetative canopy vigor. |

---

### 3.2 Features Excluded from Environmental-Only Configuration

| Excluded Feature | Reason for Exclusion from Configuration B (Environmental-Only) |
|:---|:---|
| `current_incidence_pct_t0` | **Scouting Dependency & Target Leakage:** Measuring % of plants with live larvae requires destructive field sampling at $t_0$. Its +0.7458 correlation with the 7-day target masks environmental signal. |
| `current_severity_pct_t0` | **Scouting Dependency & Target Leakage:** Visual tissue loss % is an outcome of past feeding, not an environmental driver. In advance warning, damage is not yet visible. |
| `pest_present_t0` | **Direct Indicator:** Knowing an insect is already present in the field shortcuts early-warning modeling. |
| `field_id` | **High-Cardinality Identifier:** Specific plot IDs do not generalize to unseen farms; prevents spatial overfitting. |
| `date` | **Spurious Trend Risk:** Using raw timestamps risks learning calendar shortcuts rather than meteorological mechanics. |
| `outbreak_within_7d` | **Prediction Target:** Must never be included as an input. |

---

## 4. The 7-Day Purge Embargo Architecture

A subtle but catastrophic source of data leakage in forward-looking classification is **label window overlap across partition boundaries**.

### 4.1 The Forward-Label Leakage Problem
In this dataset, the target `outbreak_within_7d` for a record on date $t_0$ evaluates the maximum pest severity over the subsequent 7 days:
$$\text{Window}(t_0) = [t_0 + 1, \dots, t_0 + 7]$$

Suppose we perform a naive chronological split at cutoff date $T_{\text{split}}$:
- **Training Set:** All records with date $t \le T_{\text{split}}$.
- **Validation Set:** All records with date $t > T_{\text{split}}$.

Consider the final training sample at $t = T_{\text{split}}$:
$$\text{Window}(T_{\text{split}}) = [T_{\text{split}} + 1, \dots, T_{\text{split}} + 7]$$
Its target label is computed using ground-truth field observations occurring on dates $T_{\text{split}} + 1$ through $T_{\text{split}} + 7$.

However, those exact same dates constitute the first 7 days of the validation set!
The model's training loss gradient is directly optimized against outcomes that occur inside the validation period.

### 4.2 The Purge Embargo Solution (`chronological_split_with_purging`)
To eliminate this overlap, an **embargo gap of at least 7 days** is placed between all partition boundaries:

```
[ TRAIN SPLIT: Dates <= T_train_end ]
     │ (Forward target looks into [T_train_end + 1 .. T_train_end + 7])
     ▼
[ PURGE EMBARGO GAP 1: T_train_end + 1 through T_train_end + 7 ]
  ==> ALL SAMPLES IN THIS 7-DAY WINDOW ARE DISCARDED FROM DATASET
     ▼
[ VALIDATION SPLIT: Dates >= T_train_end + 8 through T_val_end ]
     │ (Forward target looks into [T_val_end + 1 .. T_val_end + 7])
     ▼
[ PURGE EMBARGO GAP 2: T_val_end + 1 through T_val_end + 7 ]
  ==> ALL SAMPLES IN THIS 7-DAY WINDOW ARE DISCARDED FROM DATASET
     ▼
[ TEST SPLIT: Dates >= T_val_end + 8 through T_test_end ]
```

#### Verification Assertions Enforced in Code:
$$\max(\text{Date}_{\text{train}}) + 7\text{ days} < \min(\text{Date}_{\text{val}})$$
$$\max(\text{Date}_{\text{val}}) + 7\text{ days} < \min(\text{Date}_{\text{test}})$$

In our 100,000-record dataset:
- Train Split: **70,049 samples** (2022-06-20 to 2024-07-27).
- Gap 1 Purged: **994 samples** (embargo: 2024-07-28 to 2024-08-03).
- Val Split: **14,034 samples** (2024-08-04 to 2024-11-17).
- Gap 2 Purged: **864 samples** (embargo: 2024-11-18 to 2024-11-24).
- Test Split: **14,059 samples** (2024-11-25 to 2025-03-21).
- Total Purged: **1,858 samples** (1.86% of dataset sacrificed to guarantee zero temporal overlap).

---

## 5. Audit Conclusion

The Phase 19 feature pipeline strictly enforces causal integrity:
- Zero future weather features.
- Zero future pest severity readings.
- Complete isolation of in-field scouting variables in Configuration B.
- Mathematical elimination of boundary leakage via the 7-day purge embargo.

