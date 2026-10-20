# AgriAdapt AI — Synthetic Pest Outbreak Forecaster Model Comparison

> [!IMPORTANT]
> **SYNTHETIC DATA DISCLAIMER**
> All training and evaluation results are based on entirely synthetic agricultural data.
> They demonstrate pipeline functionality and performance on simulated assumptions only.
> They do not establish real-world pest outbreak forecasting accuracy and must not be used
> for operational farm advisories.

## 1. Dataset Chronological Partitions & Purge Strategy

- **Train Set**: 70,049 records (2022-06-20 to 2024-07-27) — Outbreak rate: 16.98%
- **Gap 1 (Purged)**: 994 records (7-day embargo preventing train target forward overlap into validation)
- **Validation Set**: 14,034 records (2024-08-04 to 2024-11-17) — Outbreak rate: 16.47%
- **Gap 2 (Purged)**: 864 records (7-day embargo preventing validation target forward overlap into test)
- **Test Set (Held-Out)**: 14,059 records (2024-11-25 to 2025-03-21) — Outbreak rate: 16.83%

## 2. Validation Set Model Comparison

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | PR-AUC | Train Sec | False Alarms (FP) | Missed Outbreaks (FN) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline_Dummy** | 0.8353 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.1647 | 0.13s | 0 | 2,312 |
| **Logistic_Regression** | 0.9281 | 0.7831 | 0.7794 | 0.7813 | 0.9326 | 0.7826 | 1.22s | 499 | 510 |
| **Random_Forest** | 0.9315 | 0.8027 | 0.7742 | 0.7882 | 0.9364 | 0.8487 | 1.6s | 440 | 522 |
| **Hist_Gradient_Boosting** | 0.9248 | 0.7662 | 0.7824 | 0.7742 | 0.9327 | 0.8478 | 5.09s | 552 | 503 |

## 3. Selected Model Test Performance

- **Selected Winner**: `Random_Forest`
- **Optimal Decision Threshold (tuned strictly on Validation)**: `0.72`

| Metric | Default Threshold (0.50) | Tuned Threshold |
| :--- | :---: | :---: |
| **Accuracy** | 0.9267 | 0.9405 |
| **Precision** | 0.7845 | 0.8871 |
| **Recall** | 0.7785 | 0.7409 |
| **F1-Score** | 0.7815 | 0.8075 |
| **ROC-AUC** | 0.9268 | 0.9268 |
| **PR-AUC** | 0.8437 | 0.8437 |
| **False Alarms (FP)** | 506 | 223 |
| **Missed Outbreaks (FN)** | 524 | 613 |

## 4. Operational Risk Trade-off Rationale

- **False Negatives (Missed Outbreaks)**: Represents the most severe risk in agriculture, as untreated outbreaks cause widespread crop failure and severe economic losses to farmers.
- **False Positives (Unnecessary Alerts)**: Represents unnecessary chemical spray cost, labor expenditure, and potential pesticide residue or environmental impact.
- Tuning the decision threshold on validation data allowed calibrating recall and precision to balance early warning coverage against excessive false alarms.