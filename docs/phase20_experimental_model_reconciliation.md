# AgriAdapt AI — Phase 20: Experimental Model Metric Reconciliation Report

**Document ID:** `AGRI-RECON-METRICS-2027-V1`  
**Version:** 1.0.0  
**Phase:** 20  
**Audit Target:** Discrepancy between reported Test Set size ($N=13,588$) and Confusion Matrix sums ($N=14,059$) in Phase 19  
**Reconciliation Status:** **RESOLVED & MATHEMATICALLY PROVEN**  
**Classification:** `EXPERIMENT AUDIT & RECONCILIATION`

---

## 1. Executive Summary & Root-Cause Discovery

During the Phase 20 pre-readiness audit, an anomaly in the Phase 19 documentation was flagged:
- Phase 19 documentation stated the chronological test set partition size was $N = 13,588$.
- However, the confusion matrices for all evaluated models summed to $N = 14,059$:
  * Full LightGBM: $\text{TP} (1,756) + \text{FP} (254) + \text{FN} (610) + \text{TN} (11,439) = \mathbf{14,059}$
  * Environmental Random Forest: $\text{TP} (1,845) + \text{FP} (5,134) + \text{FN} (521) + \text{TN} (6,559) = \mathbf{14,059}$
  * Environmental Logistic Regression: $\text{TP} (2,160) + \text{FP} (6,213) + \text{FN} (206) + \text{TN} (5,480) = \mathbf{14,059}$

### Root-Cause Finding:
An independent programmatic audit of `data/synthetic_multicrop_pest_forecasting.csv` and `models/experimental_synthetic_pest/experiment_comparison_summary.json` established:
1. **The Code and JSON Artifacts Were 100% Consistent:** The code `src/pest_forecasting/dataset.py` split the 100,000-record dataset into:
   * **Train Split:** 70,049 samples (2022-06-20 to 2024-07-27)
   * **Purge Gap 1:** 994 samples (Embargo: 2024-07-28 to 2024-08-03)
   * **Validation Split:** 14,034 samples (2024-08-04 to 2024-11-17)
   * **Purge Gap 2:** 864 samples (Embargo: 2024-11-18 to 2024-11-24)
   * **Test Split:** **14,059 samples** (2024-11-25 to 2025-03-21)
   * **Exact Total:** $70,049 + 994 + 14,034 + 864 + 14,059 = \mathbf{100,000}$
2. **The Clerical Discrepancy:** The number "13,588" originated from an earlier preliminary split ratio calculation before final date sorting and 7-day embargo boundary alignment were applied. While `train.py` and `experiment_comparison_summary.json` correctly evaluated and stored metrics on the actual $14,059$ test samples, the prose in the Phase 19 Markdown reports inadvertently retained the preliminary draft figure ($13,588$).
3. **No Metric Distortion:** All models were evaluated on the **exact same 14,059 test records**. No records were duplicated, and no test data was leaked into threshold tuning.

---

## 2. Definitive Chronological Partition Reconciliation

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        RECONCILED CHRONOLOGICAL PARTITIONS (SEED = 42, EMBARGO = 7 DAYS)               │
├────────────────────┬──────────┬─────────────┬─────────────┬──────────────┬──────────────┬──────────────┤
│ Partition          │ Count    │ % of Total  │ Start Date  │ End Date     │ Outbreaks    │ Outbreak %   │
├────────────────────┼──────────┼─────────────┼─────────────┼──────────────┼──────────────┼──────────────┤
│ **Train Set**      │ 70,049   │ 70.05%      │ 2022-06-20  │ 2024-07-27   │ 11,833       │ 16.89%       │
│ Purge Embargo 1    │ 994      │ 0.99%       │ 2024-07-28  │ 2024-08-03   │ — (Purged)   │ —            │
│ **Validation Set** │ 14,034   │ 14.03%      │ 2024-08-04  │ 2024-11-17   │ 2,366        │ 16.86%       │
│ Purge Embargo 2    │ 864      │ 0.86%       │ 2024-11-18  │ 2024-11-24   │ — (Purged)   │ —            │
│ **Test Set**       │ **14,059**│ 14.06%     │ 2024-11-25  │ 2025-03-21   │ **2,366**    │ **16.83%**   │
├────────────────────┼──────────┼─────────────┼─────────────┼──────────────┼──────────────┼──────────────┤
│ **Total**          │ 100,000  │ 100.00%     │ 2022-06-20  │ 2025-03-21   │ 16,911       │ 16.91%       │
└────────────────────┴──────────┴─────────────┴─────────────┴──────────────┴──────────────┴──────────────┘
```

### 2.1 Test Set Ground-Truth Class Distribution:
- **Actual Positive Outbreaks ($Y=1$):** **$2,366$** (Prevalence: $16.83\%$)
- **Actual Negative Non-Outbreaks ($Y=0$):** **$11,693$** (Percentage: $83.17\%$)
- **Total Test Records:** $2,366 + 11,693 = \mathbf{14,059}$

### 2.2 Proof of Consistency Across Confusion Matrices:
For every evaluated model, $\text{TP} + \text{FN}$ equals exactly the positive ground truth ($2,366$), and $\text{FP} + \text{TN}$ equals exactly the negative ground truth ($11,693$):
- **LightGBM (Full):** $\text{TP} (1,756) + \text{FN} (610) = 2,366; \quad \text{FP} (254) + \text{TN} (11,439) = 11,693$. Sum = **14,059**.
- **Random Forest (Full):** $\text{TP} (1,733) + \text{FN} (633) = 2,366; \quad \text{FP} (199) + \text{TN} (11,494) = 11,693$. Sum = **14,059**.
- **XGBoost (Full):** $\text{TP} (1,792) + \text{FN} (574) = 2,366; \quad \text{FP} (300) + \text{TN} (11,393) = 11,693$. Sum = **14,059**.
- **Logistic Regression (Full):** $\text{TP} (1,768) + \text{FN} (598) = 2,366; \quad \text{FP} (367) + \text{TN} (11,326) = 11,693$. Sum = **14,059**.
- **Logistic Regression (Env):** $\text{TP} (2,160) + \text{FN} (206) = 2,366; \quad \text{FP} (6,213) + \text{TN} (5,480) = 11,693$. Sum = **14,059**.
- **Random Forest (Env):** $\text{TP} (1,845) + \text{FN} (521) = 2,366; \quad \text{FP} (5,134) + \text{TN} (6,559) = 11,693$. Sum = **14,059**.
- **XGBoost (Env):** $\text{TP} (2,008) + \text{FN} (358) = 2,366; \quad \text{FP} (5,720) + \text{TN} (5,973) = 11,693$. Sum = **14,059**.
- **LightGBM (Env):** $\text{TP} (2,101) + \text{FN} (265) = 2,366; \quad \text{FP} (6,040) + \text{TN} (5,653) = 11,693$. Sum = **14,059**.

---

## 3. Recalculated Metric Audit

Every metric was re-verified directly against the saved pipeline artifacts on the exact $14,059$ test samples:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                   RECONCILED OUT-OF-TIME TEST METRICS (ALL 8 MODELS ON EXACT N = 14,059)               │
├────────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬────────┬────────┤
│ Model & Config     │ PR-AUC   │ ROC-AUC  │ F1 Tuned │ Precision│ Recall   │ Brier    │ ECE    │ Thresh │
├────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼────────┼────────┤
│ **FULL SYNTHETIC (14 Features)**                                                                       │
│ • LogisticRegression│ 0.7840   │ 0.9236   │ 0.7856   │ 0.8281   │ 0.7473   │ 0.0899   │ 0.1471 │ 0.61   │
│ • Random Forest    │ 0.8399   │ 0.9264   │ **0.8064**│ **0.8970**│ 0.7325   │ **0.0750**│ 0.1295 │ 0.75   │
│ • XGBoost          │ **0.8507**│ **0.9285**│ 0.8039   │ 0.8566   │ **0.7574**│ 0.0771   │ 0.1220 │ 0.71   │
│ • LightGBM (Best)  │ 0.8483   │ 0.9266   │ 0.8026   │ 0.8736   │ 0.7422   │ 0.0790   │ 0.1256 │ 0.77   │
├────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┼────────┼────────┤
│ **ENVIRONMENTAL-ONLY (11 Features)**                                                                  │
│ • Logistic (Best)  │ 0.2778   │ 0.7163   │ **0.4023**│ 0.2580   │ **0.9129**│ 0.2308   │ 0.2824 │ 0.39   │
│ • Random Forest    │ 0.3127   │ 0.7243   │ 0.3949   │ **0.2644**│ 0.7798   │ **0.2031**│ 0.2679 │ 0.49   │
│ • XGBoost          │ 0.3027   │ 0.7228   │ 0.3979   │ 0.2598   │ 0.8487   │ 0.2157   │ 0.2668 │ 0.43   │
│ • LightGBM         │ **0.3164**│ **0.7291**│ 0.3999   │ 0.2581   │ 0.8880   │ 0.2196   │ 0.2751 │ 0.42   │
└────────────────────┴──────────┴─────────────┴──────────┴──────────┴──────────┴──────────┴────────┴────────┘
```

---

## 4. Sub-Population Slice Sample Sizes Reconciliation

The sliced test samples also sum to exactly $14,059$:
- **Chickpea (Pod borer):** $4,572$ samples ($622$ outbreaks, prevalence $13.60\%$)
- **Tomato (Fruit borer):** $4,032$ samples ($976$ outbreaks, prevalence $24.21\%$)
- **Wheat (Aphids):** $5,455$ samples ($768$ outbreaks, prevalence $14.08\%$)
- **Exact Sum:** $4,572 + 4,032 + 5,455 = \mathbf{14,059}$ samples.
- **Exact Outbreak Sum:** $622 + 976 + 768 = \mathbf{2,366}$ positive events.

---

## 5. Audit Conclusion & Resolution

1. **Resolution:** The true out-of-time test set size is formally established as **$N = 14,059$**.
2. **Discrepancy Remediation:** All Phase 19 markdown documentation has been reconciled and corrected.
3. **Reproducibility Guarantee:** The test split is fully deterministic and independently reproducible using `src/pest_forecasting/dataset.py:chronological_split_with_purging(df, purge_days=7)`.

