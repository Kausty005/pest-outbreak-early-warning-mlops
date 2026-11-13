# AgriAdapt AI — Phase 19: Synthetic Model Evaluation & Sliced Performance Analysis

**Document ID:** `AGRI-EVAL-SYNTHETIC-SLICES-2027-V1`  
**Version:** 1.0.0  
**Phase:** 19  
**Evaluation Scope:** Sliced Crop/Pest Analysis, Calibration Assessment, and Brier Score Audit  
**Evaluation Partition:** Chronological Test Split ($N=14,059$, 2024-11-25 to 2025-03-21)  
**Governing Standard:** IEEE 2830 / ISO 24029 Assessment of Machine Learning Robustness  
**Status:** `SYNTHETIC BENCHMARK EVALUATION ONLY`

---

## 1. Executive Summary

In classification for imbalanced agricultural risk forecasting, reporting accuracy alone is deceptive:
- In our test set ($N=14,059$), the outbreak prevalence is **$16.83\%$** ($2,366$ positive outbreak events; $11,693$ negative events).
- A trivial dummy model that predicts zero ($0$) for every sample achieves an apparent accuracy of **$83.17\%$**, while failing to detect a single pest outbreak ($\text{Recall} = 0.0$, $\text{F1} = 0.0$).

This document provides a comprehensive evaluation of the experimental models, featuring Precision-Recall AUC (PR-AUC), Brier Score, Expected Calibration Error (ECE), and sliced sub-population performance across crops and pests.

---

## 2. In-Depth Metric Analysis: Full vs. Environmental

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               COMPREHENSIVE PERFORMANCE SUMMARY (BEST PIPELINES ON TEST)               │
├──────────────────────────────┬────────────────────────────┬────────────────────────────┤
│ Metric                       │ FULL SYNTHETIC             │ ENVIRONMENTAL-ONLY         │
│                              │ (LightGBM Pipeline)        │ (Logistic Regression Pipe) │
├──────────────────────────────┼────────────────────────────┼────────────────────────────┤
│ Optimal Decision Threshold   │ **0.77**                   │ **0.39**                   │
│ PR-AUC (Area under PR curve) │ **0.8483**                 │ **0.2778** (-67.2%)        │
│ ROC-AUC                      │ **0.9266**                 │ **0.7163** (-22.7%)        │
│ F1-Score (Tuned)             │ **0.8026**                 │ **0.4023** (-49.9%)        │
│ Precision                    │ **0.8736** (87.4%)         │ **0.2580** (25.8%)         │
│ Recall                       │ **0.7422** (74.2%)         │ **0.9129** (91.3%)         │
│ Brier Score Loss             │ **0.0790**                 │ **0.2308** (High uncert.)  │
│ Expected Calibration Error   │ **0.1256**                 │ **0.2824**                 │
│ True Positives (TP)          │ 1,756                      │ 2,160                      │
│ False Positives (FP)         │ **254**                    │ **6,213** (+2,346% alerts) │
│ False Negatives (FN)         │ 610                        │ 206                        │
│ True Negatives (TN)          │ 11,439                     │ 5,480                      │
└──────────────────────────────┴────────────────────────────┴────────────────────────────┘
```

---

## 3. Probability Calibration & Brier Score Assessment

### 3.1 Understanding the Brier Score
The Brier Score measures the mean squared difference between predicted probabilities $\hat{p}_i$ and actual binary outcomes $y_i \in \{0, 1\}$:
$$\text{BS} = \frac{1}{N}\sum_{i=1}^N (\hat{p}_i - y_i)^2$$
- A lower Brier score indicates sharper, better-calibrated probability estimates.
- **Full Synthetic Model ($\text{BS} = 0.0790$):** High confidence in separating safe vs. vulnerable fields due to known current damage levels.
- **Environmental-Only Model ($\text{BS} = 0.2308$):** Reflects high epistemic uncertainty; meteorological variables alone cannot precisely distinguish which specific fields will flare up when microclimate data is noisy.

### 3.2 Expected Calibration Error (ECE)
ECE measures whether a predicted probability of $70\%$ corresponds to a true $70\%$ event frequency:
- Full Synthetic ECE: **$12.56\%$**
- Environmental-Only ECE: **$28.24\%$**
The environmental model systematically over-predicts risk when tuned for high recall, as weather conditions favorable to pests frequently occur without resulting in an actual pest explosion (e.g. due to natural predation or absence of initial inocula).

---

## 4. Sliced Sub-Population Performance (Crop & Pest Breakdown)

The out-of-time test partition (October 2024 to March 2025) captures the Rabi season and late-season crop flushes. The three crops represented in this temporal window are **Chickpea**, **Tomato**, and **Wheat**:

### 4.1 Sliced Results: Full Synthetic Configuration (LightGBM)

| Crop / Pest Slice | Test Samples | Actual Outbreaks | Prevalence | PR-AUC | ROC-AUC | F1 | Precision | Recall | Brier |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Chickpea / Pod borer** | 4,572 | 622 | 13.60% | **0.8051** | 0.9025 | 0.7931 | 90.52% | 70.58% | 0.0725 |
| **Tomato / Fruit borer** | 4,032 | 976 | 24.21% | **0.9144** | 0.9542 | 0.8401 | 85.71% | 82.38% | 0.0912 |
| **Wheat / Aphids** | 5,455 | 768 | 14.08% | **0.7761** | 0.9041 | 0.7572 | 87.39% | 66.80% | 0.0755 |

#### Insights on Full Model:
- **Tomato / Fruit borer** achieved the highest PR-AUC ($0.9144$) and F1 ($0.8401$) due to higher baseline prevalence ($24.21\%$) and rapid, distinctive vegetative-to-fruiting transition.
- **Wheat / Aphids** had lower recall ($66.80\%$) because simulated aphid colonization events have lower baseline incidence thresholds that are sensitive to small temperature fluctuations.

---

### 4.2 Sliced Results: Environmental-Only Configuration (Logistic Regression)

| Crop / Pest Slice | Test Samples | Actual Outbreaks | Prevalence | PR-AUC | ROC-AUC | F1 | Precision | Recall | Brier |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Chickpea / Pod borer** | 4,572 | 622 | 13.60% | **0.1646** | 0.6185 | 0.3155 | 19.14% | 89.71% | 0.2368 |
| **Tomato / Fruit borer** | 4,032 | 976 | 24.21% | **0.3326** | 0.6998 | 0.5087 | 34.60% | 96.00% | 0.2677 |
| **Wheat / Aphids** | 5,455 | 768 | 14.08% | **0.2083** | 0.7016 | 0.3781 | 24.18% | 86.59% | 0.1985 |

#### Insights on Environmental Model:
- Across all three crops, **precision collapses below 35%**:
  * Chickpea: Only $19.14\%$ of alarms are true outbreaks ($80.86\%$ false alarms).
  * Wheat: Only $24.18\%$ of alarms are true outbreaks ($75.82\%$ false alarms).
  * Tomato: Only $34.60\%$ of alarms are true outbreaks ($65.40\%$ false alarms).
- While the model successfully captures high recall ($86\%$ to $96\%$), it achieves this by triggering alerts across vast geographic areas whenever weather conditions enter the biologically favorable range.

---

## 5. Critical Agronomic Interpretation of the Precision-Recall Trade-off

In real-world agricultural early-warning systems, the cost of prediction errors is asymmetrical:
1. **False Negative (Missed Outbreak):** Farmer does not receive warning; pest population explodes; crop sustains catastrophic yield damage.
2. **False Positive (False Alarm):** Farmer receives an alert; scout visits field or farmer sprays biopesticide unnecessarily; incurs labor/chemical cost and risks "cry wolf" advisory fatigue.

### The Problem with 75% False Alarms
In the Environmental-Only model, a precision of $\approx 26\%$ means that **for every 1 true outbreak detected, 3 false alarms are dispatched**.
- If deployed to farmers, frequent unconfirmed alerts destroy farmer trust in extension services.
- If deployed to scouts, it overwhelms scouting teams with unnecessary inspections.

**Conclusion:** Remote meteorological forecasting alone is insufficient for high-precision field alerts. A hybrid approach—using environmental favorability for regional macro-zoning, followed by targeted pheromone trap and scouting confirmation before chemical action—remains the only scientifically sound operational strategy.

---

## 6. Official Disclaimer & Scientific Boundaries

```
╔══════════════════════════════════════════════════════════════════════════╗
║                    MANDATORY SYNTHETIC BENCHMARK DISCLAIMER              ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  1. All performance metrics reported in this document are derived        ║
║     exclusively from synthetic biophysical simulation data.              ║
║  2. These results DO NOT demonstrate real-world predictive validity,     ║
║     biological fidelity, or commercial efficacy.                         ║
║  3. These models must NEVER be exposed as operational farmer alerts.     ║
║  4. Production pest-outbreak model training remains strictly BLOCKED     ║
║     pending authentic multi-season field surveillance ground truth.      ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

