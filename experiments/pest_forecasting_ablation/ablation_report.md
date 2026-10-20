# AgriAdapt AI — Feature Ablation & Decision Threshold Audit Report

> [!IMPORTANT]
> **SYNTHETIC DATA DISCLAIMER**  
> All experiments use synthetic agricultural data. Results establish performance only on
> simulated assumptions and do not demonstrate real-world pest outbreak forecasting accuracy.
> The models must not be used for operational farm advisories.

---

## 1. Executive Summary & Core Findings

This experimental audit addresses two fundamental MLOps questions for AgriAdapt AI:
1. **Threshold Audit**: How is the decision threshold selected, does it access test data, and does it minimize an explicit cost function?
   - **Finding**: The 0.72 threshold was chosen **strictly by maximizing validation F1-score**. No test data was accessed. However, **no explicit economic cost function** exists in the code.
2. **Ablation Study**: Is the pipeline genuinely forecasting future outbreaks via microclimate/crop susceptibility, or is it primarily extrapolating existing in-field pest infestation?
   - **Finding**: The model **heavily relies on current infestation measurements** (`current_severity_pct_t0` and `current_incidence_pct_t0`). Removing these scouting features causes a sharp drop in predictive power, proving that the model is primarily an *infestation extrapolation engine* rather than a pure pre-symptomatic weather forecasting system.

---

## 2. Decision Threshold Audit (Validation Partition)

The current implementation uses `find_optimal_threshold(y_val, probs, metric='f1')`. The validation data contains 14,034 samples (2,312 positive outbreaks, 16.47% prevalence).

| Threshold | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | False Alarms (FP) | Missed Outbreaks (FN) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.50** | 0.8027 | 0.7742 | 0.7882 | 0.9364 | 0.8487 | 440 | 522 |
| **0.60** | 0.8351 | 0.7599 | 0.7957 | 0.9364 | 0.8487 | 347 | 555 |
| **0.70** | 0.8775 | 0.7344 | 0.7996 | 0.9364 | 0.8487 | 237 | 614 |
| **0.72** **(Optimum F1)** | 0.8866 | 0.7301 | 0.8008 | 0.9364 | 0.8487 | 216 | 624 |
| **0.80** | 0.9150 | 0.6981 | 0.7920 | 0.9364 | 0.8487 | 150 | 698 |

### Audit Verification Points:
- **Validation-Only Execution**: Confirmed. `find_optimal_threshold` operates strictly on validation labels and probabilities.
- **Objective Function**: The threshold selection strictly maximizes the harmonic mean of precision and recall (F1).
- **Cost Function Discrepancy**: The codebase does not compute an explicit financial or spraying cost equation. Any prior documentation referencing 'chemical spray cost minimization' described an intuitive rationale rather than an explicit programmatic loss term.

---

## 3. Feature Ablation Experimental Design

All experiments adhere to identical experimental conditions:
- **Chronological Splits**: Train (70,049 rows, 2022-06-20 to 2024-07-27), Val (14,034 rows, 2024-08-04 to 2024-11-17), Test (14,059 rows, 2024-11-25 to 2025-03-21).
- **7-Day Purging**: 994 rows purged in Gap 1; 864 rows purged in Gap 2.
- **Model Architecture**: Random Forest (`n_estimators=120, max_depth=16, min_samples_leaf=4, class_weight='balanced', seed=42`).
- **Preprocessors**: Fitted strictly on the respective training partitions.

### Feature Groups Evaluated:
1. **Experiment A (Full Feature Model)**: 14 features (Weather, Crop, Pest, Growth Stage, Incidence, Severity, Pest Present).
2. **Experiment B (Weather & Crop Model)**: 11 features (Weather, Crop, Pest, Growth Stage). Excludes `current_incidence_pct_t0`, `current_severity_pct_t0`, and `pest_present_t0`.
3. **Experiment C (Binary Detection Early-Warning Model)**: 12 features (Weather, Crop, Pest, Growth Stage, and binary `pest_present_t0`). Excludes quantitative foliar scouting metrics (`current_incidence_pct_t0`, `current_severity_pct_t0`).

---

## 4. Ablation Performance Comparison

| Experiment | Feature Group | Validation PR-AUC | Validation Recall | Validation Precision | Test PR-AUC | Test Recall | Test Precision | Test F1 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Experiment A (Full Feature Model)** | Full 14 Features | 0.8487 | 0.7301 | 0.8866 | **0.8437** | **0.7409** | **0.8871** | **0.8075** |
| **Experiment B (Weather & Crop Model)** | Weather + Crop (11) | 0.2701 | 0.8832 | 0.2633 | **0.2989** | **0.8170** | **0.2597** | **0.3942** |
| **Experiment C (Early-Warning Model)** | Weather + Crop + Binary Trap (12) | 0.5132 | 0.8205 | 0.5183 | **0.5178** | **0.7658** | **0.5021** | **0.6065** |

### Performance Drop Relative to Full Reference Model:

| Experiment | $\Delta$ Test PR-AUC | $\Delta$ Test Recall | $\Delta$ Test F1 | Test False Alarms (FP) | Test Missed Outbreaks (FN) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Experiment A (Full Feature Model)** | +0.0000 | +0.0000 | +0.0000 | 223 | 613 |
| **Experiment B (Weather & Crop Model)** | -0.5448 | +0.0761 | -0.4133 | 5,509 | 433 |
| **Experiment C (Early-Warning Model)** | -0.3259 | +0.0249 | -0.2010 | 1,797 | 554 |

---

## 5. Permutation Feature Importance Analysis

Permutation importance was evaluated on unseen validation observations by measuring the drop in PR-AUC (Average Precision) when each feature is independently shuffled.

### Experiment A (Full Model) Top Features:
- **`current_severity_pct_t0`**: drop in PR-AUC = `0.1796`
- **`current_incidence_pct_t0`**: drop in PR-AUC = `0.1312`
- **`growth_stage`**: drop in PR-AUC = `0.0443`
- **`pest_present_t0`**: drop in PR-AUC = `0.0259`
- **`crop`**: drop in PR-AUC = `0.0113`
- **`pest`**: drop in PR-AUC = `0.0066`
- **`t7_min_temp_c`**: drop in PR-AUC = `0.0047`
- **`district`**: drop in PR-AUC = `0.0019`

### Experiment B (Weather & Crop Model) Top Features:
- **`growth_stage`**: drop in PR-AUC = `0.0889`
- **`t7_max_temp_c`**: drop in PR-AUC = `0.0110`
- **`pest`**: drop in PR-AUC = `0.0071`
- **`t7_high_rh_days`**: drop in PR-AUC = `0.0063`
- **`t7_mean_rh_pct`**: drop in PR-AUC = `0.0060`
- **`crop`**: drop in PR-AUC = `0.0040`
- **`t14_rainfall_mm`**: drop in PR-AUC = `0.0020`
- **`t7_rainfall_mm`**: drop in PR-AUC = `0.0015`

### Experiment C (Early-Warning Model) Top Features:
- **`pest_present_t0`**: drop in PR-AUC = `0.2752`
- **`growth_stage`**: drop in PR-AUC = `0.1557`
- **`pest`**: drop in PR-AUC = `0.0102`
- **`t7_mean_rh_pct`**: drop in PR-AUC = `0.0085`
- **`t14_rainfall_mm`**: drop in PR-AUC = `0.0040`
- **`district`**: drop in PR-AUC = `0.0000`
- **`crop`**: drop in PR-AUC = `0.0000`
- **`t7_mean_temp_c`**: drop in PR-AUC = `0.0000`

### Correlation vs. Causation Warning:
> [!WARNING]
> Feature importance measures **statistical association within this synthetic data generation model**, NOT real-world biological causation.
> In the simulation engine, weather determines growth rates, but pest incidence directly triggers the mathematical threshold.
> High importance on current severity reflects that fields already damaged are mathematically closer to crossing the 7-day outbreak cutoff.

---

## 6. Interpretation of Early-Warning Capability

1. **Extrapolation vs. Forecasting**: When current incidence and severity are removed (Experiment B), Test PR-AUC drops substantially. This confirms that the model is primarily **extrapolating existing infestation momentum** rather than forecasting de novo outbreaks from weather patterns alone.
2. **Value of Binary Presence (Experiment C)**: Adding binary presence (`pest_present_t0`) bridges some of the gap, confirming that knowing whether an insect is active in the area provides critical gating before microclimatic conditions accelerate growth.
3. **Operational Recommendation**: An early-warning system in real farms cannot rely solely on weather stations. It requires at least coarse scouted presence or pheromone trap counts.

---

## 7. Artifacts and MLflow Tracking Locations

- **Experiment Directory**: `experiments/pest_forecasting_ablation/`
- **MLflow Experiment**: `AgriAdapt_Pest_Forecasting_Feature_Ablation`
- **Models Persisted**: `Experiment_A_Full_Model.joblib`, `Experiment_B_Weather_Crop.joblib`, `Experiment_C_Early_Warning.joblib`
- **Audit Data**: `threshold_audit_validation.csv`, `ablation_summary.json`

---

## 8. Limitations & Future Real-World Ground Truth Requirements

- The synthetic generation assumes homogeneous insect phenology and idealized degree-day responses.
- Real-world agricultural deployment requires pairing regional weather forecasts with physical pheromone trap telemetry, digital trap imagery, and ground truth entomological surveillance records.