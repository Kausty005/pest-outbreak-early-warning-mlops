# AgriAdapt AI — Phase 19: Experimental Model Comparison & Benchmark Report

**Document ID:** `AGRI-EXP-MODEL-COMPARE-2027-V1`  
**Version:** 1.0.0  
**Phase:** 19  
**Models Evaluated:** Logistic Regression, Random Forest, XGBoost, LightGBM  
**Dataset:** `data/synthetic_multicrop_pest_forecasting.csv` (100,000 synthetic rows)  
**Evaluation Protocol:** Out-of-Time Chronological Holdout (7-Day Purged Embargo)  
**Test Set Size:** 14,059 samples (2024-11-25 to 2025-03-21)  
**Classification:** `SYNTHETIC BENCHMARK EXPERIMENT`  
**Scientific Warning:** All metrics reflect synthetic biophysical simulation dynamics and cannot establish real-world predictive competence.

---

## 1. Executive Summary

We evaluated four standard classification algorithms across two feature configurations:
1. **FULL SYNTHETIC FEATURE SET (14 Features):** Weather covariates + In-field scouting observations (`incidence`, `severity`, `presence`).
2. **ENVIRONMENTAL-ONLY FEATURE SET (11 Features):** Weather covariates + Crop phenology strictly excluding all scouting variables.

All models were trained on the initial 70,049 samples (2022-06-20 to 2024-07-27), tuned on 14,034 validation samples (2024-08-04 to 2024-11-17), and tested on 14,059 out-of-time test samples (2024-11-25 to 2025-03-21). A **7-day purge embargo** separated each partition to prevent forward-looking label leakage.

---

## 2. Comprehensive Model Comparison Matrix

### 2.1 Configuration A: Full Synthetic Feature Set (14 Features)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        FULL SYNTHETIC FEATURE SET (TEST SET EVALUATION: N=14,059)                      │
├────────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬────────┬────────┤
│ Algorithm          │ PR-AUC   │ ROC-AUC  │ F1 Tuned │ Precision│ Recall   │ Brier    │ ECE    │ Thresh │
├────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼────────┼────────┤
│ LogisticRegression │ 0.7840   │ 0.9236   │ 0.7856   │ 0.8281   │ 0.7473   │ 0.0899   │ 0.1471 │ 0.61   │
│ Random Forest      │ 0.8399   │ 0.9264   │ **0.8064**│ **0.8970**│ 0.7325   │ **0.0750**│ 0.1295 │ 0.75   │
│ XGBoost            │ **0.8507**│ **0.9285**│ 0.8039   │ 0.8566   │ **0.7574**│ 0.0771   │ 0.1220 │ 0.71   │
│ LightGBM (Selected)│ 0.8483   │ 0.9266   │ 0.8026   │ 0.8736   │ 0.7422   │ 0.0790   │ 0.1256 │ 0.77   │
└────────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴────────┴────────┘
```

#### Confusion Matrices (Full Synthetic Configuration — Tuned Threshold):
- **Random Forest:** $\text{TP} = 1,733, \quad \text{FP} = 199, \quad \text{FN} = 633, \quad \text{TN} = 11,494$ (False Alarm Rate: $1.7\%$)
- **XGBoost:** $\text{TP} = 1,792, \quad \text{FP} = 300, \quad \text{FN} = 574, \quad \text{TN} = 11,393$
- **LightGBM:** $\text{TP} = 1,756, \quad \text{FP} = 254, \quad \text{FN} = 610, \quad \text{TN} = 11,439$
- **Logistic Regression:** $\text{TP} = 1,768, \quad \text{FP} = 367, \quad \text{FN} = 598, \quad \text{TN} = 11,326$

---

### 2.2 Configuration B: Environmental-Only Feature Set (11 Features)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                     ENVIRONMENTAL-ONLY FEATURE SET (TEST SET EVALUATION: N=14,059)                     │
├────────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬────────┬────────┤
│ Algorithm          │ PR-AUC   │ ROC-AUC  │ F1 Tuned │ Precision│ Recall   │ Brier    │ ECE    │ Thresh │
├────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼────────┼────────┤
│ Logistic (Selected)│ 0.2778   │ 0.7163   │ **0.4023**│ 0.2580   │ **0.9129**│ 0.2308   │ 0.2824 │ 0.39   │
│ Random Forest      │ 0.3127   │ 0.7243   │ 0.3949   │ **0.2644**│ 0.7798   │ **0.2031**│ 0.2679 │ 0.49   │
│ XGBoost            │ 0.3027   │ 0.7228   │ 0.3979   │ 0.2598   │ 0.8487   │ 0.2157   │ 0.2668 │ 0.43   │
│ LightGBM           │ **0.3164**│ **0.7291**│ 0.3999   │ 0.2581   │ 0.8880   │ 0.2196   │ 0.2751 │ 0.42   │
└────────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴────────┴────────┘
```

#### Confusion Matrices (Environmental-Only Configuration — Tuned Threshold):
- **Logistic Regression:** $\text{TP} = 2,160, \quad \text{FP} = \mathbf{6,213}, \quad \text{FN} = 206, \quad \text{TN} = 5,480$
- **Random Forest:** $\text{TP} = 1,845, \quad \text{FP} = \mathbf{5,134}, \quad \text{FN} = 521, \quad \text{TN} = 6,559$
- **XGBoost:** $\text{TP} = 2,008, \quad \text{FP} = \mathbf{5,720}, \quad \text{FN} = 358, \quad \text{TN} = 5,973$
- **LightGBM:** $\text{TP} = 2,101, \quad \text{FP} = \mathbf{6,040}, \quad \text{FN} = 265, \quad \text{TN} = 5,653$

---

## 3. Comparative Architectural Analysis

### 3.1 The Performance Collapse: Full vs. Environmental
When in-field scouting variables (`current_incidence_pct_t0`, `current_severity_pct_t0`, `pest_present_t0`) are removed:
1. **PR-AUC drops by 63%:** From $0.8483$ to $0.3164$ in LightGBM, and from $0.8399$ to $0.3127$ in Random Forest.
2. **False Positives Surge by $+2,480\%$:** In Random Forest, false positive alerts surge from $199$ to $5,134$.
3. **Precision Collapses:** Precision drops from $89.70\%$ down to $26.44\%$. Roughly **3 out of every 4 automated outbreak alerts are false alarms**.
4. **Brier Score Degrades:** Prediction uncertainty increases nearly threefold, from $0.0750$ to $0.2031$.

### 3.2 Algorithm Behavioral Observations
- **Gradient Boosting (LightGBM & XGBoost):**
  - Fastest training time and highest PR-AUC ($0.8507$ XGBoost, $0.8483$ LightGBM in Full; $0.3164$ LightGBM in Environmental).
  - Handles one-hot sparse categorical columns seamlessly.
- **Random Forest:**
  - Highest precision ($89.70\%$ Full, $26.44\%$ Environmental) and lowest Brier score ($0.0750$ Full, $0.2031$ Environmental).
  - Produces conservative probability distributions that resist extreme confidence outliers.
- **Logistic Regression:**
  - Fast linear baseline with competitive ROC-AUC ($0.9236$ Full, $0.7163$ Environmental).
  - Tends to prioritize recall over precision under class weighting, resulting in higher false alarm counts.

---

## 4. Experiment Tracking & Artifact Isolation

All models and reproducible experiment summaries are archived in the experimental model registry:
- **Registry Location:** `models/experimental_synthetic_pest/`
- **Full Model Artifact:** `models/experimental_synthetic_pest/full_model_pipeline.joblib` (LightGBM Pipeline, 351 KB)
- **Environmental Model Artifact:** `models/experimental_synthetic_pest/environmental_model_pipeline.joblib` (Logistic Regression Pipeline, 7.1 KB)
- **Feature Schemas:** `models/experimental_synthetic_pest/feature_schemas.json`
- **Summary Metrics:** `models/experimental_synthetic_pest/experiment_comparison_summary.json`
- **Provenance Record:** `models/experimental_synthetic_pest/synthetic_provenance_metadata.json`

**Production Safety Assurance:** No production model artifacts (`models/fertilizer_model.joblib`, `models/maize_disease/`) were modified, overwritten, or referenced during this benchmark.

