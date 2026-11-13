# Final Experimental ML Scientific Audit and Technical Foundation Freeze
**Project:** AgriAdapt AI — Pest Outbreak Early Warning MLOps Module  
**Audit Date:** November 13, 2026  
**Auditor:** Senior Agricultural Machine Learning Engineer, Plant Pathologist, and MLOps Architect  
**Scope:** Phase 20 Synthetic Pest Forecasting Generator (v2), Temporal Partitioning, Feature Pipelines, Evaluation Metrics, Stress Tests, and Production Isolation  
**Dataset Artifact:** `data/experimental/synthetic_pest_forecasting_v2.csv` (`SHA-256: f8fd72127245...`, $N = 100,000$)  
**Model Directory:** `models/experimental_synthetic_pest_v2/`  

---

## 1. Executive Verdict

### Is the Synthetic Pipeline Scientifically Defensible?
**YES (Certified for Experimental Research and Pipeline Verification Only).**  
The Version 2.0 synthetic pest forecasting pipeline is scientifically sound, mathematically rigorous, and structurally defensible as an experimental simulation harness. Latent pest population dynamics ($L_t$) are modeled using continuous differential growth, non-linear cardinal temperature curves (Fand et al., 2021), trapezoidal relative humidity bounds, rainfall wash-off penalties, and dynamic soil moisture hydrology. Intermittent scouting (7–12 days) with detection limits, zero-inflation, and observation staleness (`days_since_scouting`) are explicitly modeled. The prediction target (`outbreak_within_7d`) is strictly causal ($[t_0+1, t_0+7]$), and temporal partitioning strictly enforces 8-day purge embargos, eliminating target leakage.

### Is it Production-Ready?
**NO (STRICTLY NOT PRODUCTION-READY).**  
Under no circumstances may any model trained on this synthetic dataset be deployed to production, exposed to farmers, or integrated into live advisory systems. Synthetic data, no matter how biologically parameterized, cannot capture unmodeled real-world phenomena such as parasitoid/predator population crashes, pesticide resistance dynamics, local spray drift, or microclimatic anomalies.

### What is the Certification Status?
- **Experimental Classification:** `SYNTHETIC_EXPERIMENTAL`  
- **Model Training Status:** Completed for research benchmarking across 4 model families (Logistic Regression, Random Forest, XGBoost, LightGBM) under dual feature regimes (Environmental-Only vs Scouting-Assisted).  
- **Production Readiness Gate:** **`BLOCKED`** (10 blocking reasons active in `evaluate_production_readiness()`).  
- **Physical Field Pilot Deployment:** **`STANDBY / NO-GO`** (Zero prospective field records collected; institutional agreements remain in pre-submission draft).  
- **Technical Foundation:** **`FROZEN`** for experimental development.

---

## 2. Generator Audit (`src/pest_forecasting/synthetic_generator_v2.py`)

### 2.1 Latent Pest Population Dynamics
The latent population $L_t$ is simulated daily for each field-crop-pest entity using a bounded log-logistic biological growth function:

$$\Delta L_t = r_{\text{intrinsic}} \cdot M_t \cdot L_t \left(1 - \frac{L_t}{K}\right) - m \cdot L_t$$

Where:
- $r_{\text{intrinsic}}$ is the maximum intrinsic rate of increase (set to 0.35/day across simulated species).
- $K$ is the field carrying capacity ($K = 100.0$ normalized pest units).
- $m$ is the baseline daily mortality rate ($m = 0.12$/day).
- $M_t$ is the composite daily environmental multiplier:
  
  $$M_t = \min\left(1.50, \, \max\left(0.0, \, f_T(T_t) \cdot f_H(H_t) \cdot f_W(R_t)\right)\right)$$

### 2.2 Thermal Response Curve ($f_T$)
Temperature suitability $f_T(T)$ is modeled via the asymmetric non-linear Beta thermal response equation parameterized by species-specific cardinal temperatures ($T_{\text{base}}, T_{\text{opt}}, T_{\max}$):

$$f_T(T) = \begin{cases} 
0, & T \le T_{\text{base}} \text{ or } T \ge T_{\max} \\
\left(\frac{T - T_{\text{base}}}{T_{\text{opt}} - T_{\text{base}}}\right) \left(\frac{T_{\max} - T}{T_{\max} - T_{\text{opt}}}\right)^{\frac{T_{\max} - T_{\text{opt}}}{T_{\text{opt}} - T_{\text{base}}}}, & T_{\text{base}} < T < T_{\max}
\end{cases}$$

### 2.3 Relative Humidity Response Curve ($f_H$)
Moisture suitability follows a trapezoidal tolerance response curve:
- Below $RH_{\min}$: $f_H(RH) = \max(0.0, \, 0.20 + 0.80 \cdot \frac{RH - 30}{RH_{\min} - 30})$
- Between $RH_{\min}$ and $RH_{\max}$: $f_H(RH) = 1.00$ (Optimal reproductive humidity plateau)
- Above $RH_{\max}$: $f_H(RH) = \max(0.30, \, 1.00 - 0.70 \cdot \frac{RH - RH_{\max}}{100 - RH_{\max}})$

### 2.4 Rainfall Wash-Off Effect ($f_W$)
Rainfall provides beneficial soil moisture and canopy humidity, but intense precipitation causes mechanical wash-off of early instars, eggs, and small nymphs:
- If Daily Rain $R_t \le 10 \text{ mm}$: $f_W(R_t) = 1.00$
- If $10 < R_t \le 35 \text{ mm}$: $f_W(R_t) = 1.00 - 0.015 \cdot (R_t - 10)$
- If $R_t > 35 \text{ mm}$: $f_W(R_t) = \max(0.20, \, 0.625 - 0.020 \cdot (R_t - 35))$

### 2.5 Soil Moisture Hydrology
Soil moisture is updated via a 1-D bucket water balance equation:

$$S_t = \min\left(S_{\max}, \, \max\left(S_{\text{wilt}}, \, S_{t-1} + R_t \cdot \eta_{\text{infil}} - ET_0 \cdot K_c\right)\right)$$

Where $S_{\max} = 100 \text{ mm}$, $S_{\text{wilt}} = 10 \text{ mm}$, and $\eta_{\text{infil}}$ is the infiltration coefficient ($0.75$).

### 2.6 Observation Process: Zero-Inflation and Imperfect Detection
Field scouting does not observe $L_t$ directly:
1. **Zero-Inflation:** When $L_t < 1.0$, scouts detect no pests ($O_t = 0.0$) with 95% probability due to visual sampling limits.
2. **Imperfect Detection:** Observed pest count $O_t$ is sampled from a Beta-perturbed observation distribution:
   
   $$O_t = \max\left(0.0, \, L_t \cdot \left(1.0 + \epsilon_{\text{scout}}\right)\right), \quad \epsilon_{\text{scout}} \sim \mathcal{N}\left(0, \, 0.15^2\right)$$

3. **Intermittent Scouting:** Scouting visits occur only every 7–12 days with random missed visits ($p_{\text{miss}} = 0.08$). Between visits, the last observed values are held static, and `days_since_scouting` increments daily.

### 2.7 Target Derivation ($[t_0+1, t_0+7]$)
The forecast target `outbreak_within_7d` is strictly forward-looking and causal:

$$\text{outbreak\_within\_7d}(t_0) = \mathbb{I}\left(\max_{k \in [1, 7]} L_{t_0 + k} \ge \text{ETL}_{\text{species}}\right)$$

At prediction time $t_0$, neither the future latent population $L_{t_0+k}$ nor future weather is visible to the feature engineering pipeline.

### 2.8 Determinism and Seed Reproducibility
The generator uses a deterministic sequence: `numpy.random.default_rng(seed=42)`. Across multiple runs, the SHA-256 hash of the generated 100,000-row CSV file is identically `f8fd72127245...`.

### 2.9 Inspection of All 6 Crop-Pest Systems
Each system exhibits species-appropriate cardinal parameters and economic thresholds:

| Crop | Pest Scientific Name | Common Name | $T_{\text{base}}$ | $T_{\text{opt}}$ | $T_{\max}$ | $RH_{\min}$ | $RH_{\max}$ | ETL Threshold |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cotton** | *Pectinophora gossypiella* | Pink Bollworm | 12.0°C | 28.0°C | 38.0°C | 55% | 85% | 8.0 moths/trap/night |
| **Cotton** | *Bemisia tabaci* | Whitefly | 11.0°C | 30.0°C | 40.0°C | 40% | 75% | 6.0 adults/leaf |
| **Cotton** | *Helicoverpa armigera* | American Bollworm | 10.5°C | 27.5°C | 37.0°C | 50% | 80% | 1.0 larva/plant |
| **Soybean** | *Chrysodeixis acuta* | Semilooper | 10.0°C | 26.5°C | 36.0°C | 60% | 90% | 3.0 larvae/meter row |
| **Soybean** | *Melanagromyza sojae* | Stem Fly | 12.0°C | 29.0°C | 38.0°C | 50% | 85% | 10.0% stem tunneling |
| **Pigeonpea** | *Helicoverpa armigera* | Pod Borer | 10.5°C | 27.5°C | 37.0°C | 50% | 80% | 1.0 larva/plant |

---

## 3. Biological Assumptions and Evidence Status

### Literature-Backed Parameters vs. Simulation Assumptions
To maintain scientific transparency, all biological parameters in `synthetic_generator_v2.py` are categorized by evidentiary grounding:

| Parameter | Value / Range | Evidence Status | Literature Reference / Rationale |
| :--- | :--- | :--- | :--- |
| **Cardinal Temperatures ($T_{\text{base}}, T_{\text{opt}}, T_{\max}$)** | Species-specific (10.0–40.0°C) | **LITERATURE-BACKED** | Fand et al. (2021) *Crop Protection*; CICR Technical Bulletin No. 22; Indian Journal of Entomology. |
| **Economic Threshold Levels (ETL)** | 1.0–10.0 units | **REGULATORY / EXTENSION** | DPPQS Govt of India Guidelines; CIBRC; CROPSAP Maharashtra Surveillance Manual. |
| **Phenological Susceptibility Windows** | Vegetative, Flowering, Pod/Boll | **AGRONOMIC CONSENSUS** | ICAR-CICR Cotton Production Manual; ICAR-IISR Soybean Compendium. |
| **Rainfall Wash-Off Thresholds** | > 10 mm/day moderate, > 35 mm severe | **EMPIRICALLY MOTIVATED ASSUMPTION** | Supported by field observations of nymph dislodgement; functional decay curve is a mathematical approximation. |
| **Intrinsic Population Growth Rate ($r = 0.35$)** | Fixed scalar across species | **SIMULATION ASSUMPTION** | Calibrated to generate multi-week outbreak curves within the 120-day season; does not represent species-specific fecundity tables. |
| **Baseline Daily Natural Mortality ($m = 0.12$)** | Fixed linear decay | **SIMULATION ASSUMPTION** | Balances growth to prevent monotonic population explosion; real-world mortality varies non-linearly with natural enemies. |
| **Scouting Imperfect Detection ($\sigma = 0.15$)** | Normal error around latent $L_t$ | **SIMULATION ASSUMPTION** | Approximates scout sampling variability; true field error is non-Gaussian and varies with scout training. |
| **Soil Bucket Infiltration Rate ($\eta = 0.75$)** | Constant infiltration | **HYDROLOGIC SIMPLIFICATION** | Captures soil water accumulation; real Vidarbha vertisols exhibit swelling and crack drainage. |

---

## 4. Temporal Partition and Leakage Audit

### 4.1 Chronological Split Boundaries and Purge Gaps
Temporal partitioning was audited across all 100,000 records. Partitions are strictly chronological:

```
[TRAIN: 61,265 samples] ──[GAP 1: 2,469]──> [VAL: 14,692 samples] ──[GAP 2: 2,469]──> [TEST: 21,574 samples]
2021-06-01 to 2024-09-07   (8-day purge)   2024-09-16 to 2025-06-19   (8-day purge)   2025-06-28 to 2026-10-31
```

### 4.2 Prediction Horizon vs. Embargo Duration
- Target Window: $\tau = 7$ calendar days ($[t_0+1, t_0+7]$).
- Purge Gap Duration: $\Delta t_{\text{gap}} = 8$ calendar days.
- **Verification:** Because $\Delta t_{\text{gap}} > \tau$, the final record in the training set ($t_0 = \text{2024-09-07}$) evaluates target outcomes only up to $\text{2024-09-14}$. The validation set starts on $\text{2024-09-16}$. Thus, **zero training targets evaluate labels overlapping validation feature dates**. Similarly, Gap 2 isolates validation from test.

### 4.3 Feature Availability and Causal Rolling
- All rolling features (`temp_c_roll7_mean`, `rh_pct_roll7_mean`, `rain_mm_sum7`) are computed over $[t_0-6, t_0]$.
- Automated inspection via `verify_no_leakage_v2()` confirms zero future features (`future_*`, `t7_*`, `latent_pop`) exist in the feature matrix.

---

## 5. Field-Grouped Generalization Results

### Within-Field Forecasting vs. Unseen-Field Generalization
To resolve the question of whether models merely learn field-specific temporal trajectories or learn transferable pest ecology, an independent **Field-Grouped Spatial Generalization Evaluation** was conducted.

- **Total Unique Fields:** 576 fields.
- **Partitioning:** 20% of fields (115 fields, 19,941 samples) were completely quarantined from training and validation.
- **Comparison:** Chronological multi-season test set ($N=21,574$) vs. Unseen-Field test set ($N=19,941$).

### Quantitative Generalization Comparison (Test Sets)

| Model Family | Feature Regime | Chronological Test PR-AUC | Unseen-Field Test PR-AUC | $\Delta$ PR-AUC | Chronological F1 | Unseen-Field F1 | Chronological FDR | Unseen-Field FDR |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression** | Environmental | 0.7635 | 0.7604 | -0.0031 | 0.7161 | 0.7175 | 0.3845 | 0.3905 |
| **Random Forest** | Environmental | 0.8808 | 0.8757 | -0.0051 | 0.7997 | 0.7988 | 0.2287 | 0.2325 |
| **LightGBM** | Environmental | 0.8851 | 0.8803 | -0.0048 | 0.7970 | 0.7911 | 0.1934 | 0.2016 |
| **XGBoost** | Environmental | **0.8943** | **0.8886** | **-0.0057** | **0.8024** | **0.7936** | **0.1855** | **0.1978** |
| **Logistic Regression** | Scouting-Assisted | 0.9452 | 0.9415 | -0.0037 | 0.8643 | 0.8586 | 0.1412 | 0.1458 |
| **Random Forest** | Scouting-Assisted | 0.9632 | 0.9604 | -0.0028 | 0.8794 | 0.8751 | 0.1042 | 0.1079 |
| **LightGBM** | Scouting-Assisted | 0.9680 | 0.9655 | -0.0025 | 0.8977 | 0.8907 | 0.0667 | 0.0716 |
| **XGBoost** | Scouting-Assisted | **0.9701** | **0.9677** | **-0.0024** | **0.9000** | **0.8952** | **0.0874** | **0.0968** |

### Scientific Interpretation
1. **Absence of Entity Overfitting:** The performance drop on completely unseen fields is negligible ($\Delta \text{PR-AUC} \le 0.0057$ across all models).
2. **Feature Generality:** Because models exclude `field_id` and spatial coordinates, relying solely on weather lags, thermal degree days, and scouting indicators, predictions reflect generalized biological dynamics rather than memorized field locations.

---

## 6. Feature Availability Audit

### Genuine Cutoff Availability
The 22 features used across models were audited for genuine availability at decision cutoff $t_0$:

| Feature Name | Feature Group | Temporal Support | Cutoff Availability Status |
| :--- | :--- | :--- | :--- |
| `temp_c_roll7_mean`, `temp_c_roll7_max`, `temp_c_roll7_min` | Weather | $[t_0-6, t_0]$ | Fully available from AWS or ERA5 reanalysis at 00:00. |
| `rh_pct_roll7_mean`, `rh_pct_roll7_min` | Weather | $[t_0-6, t_0]$ | Fully available at cutoff. |
| `rain_mm_sum7`, `rain_mm_sum14` | Weather | $[t_0-6, t_0], [t_0-13, t_0]$ | Fully available at cutoff. |
| `soil_moisture_est` | Hydrology | $t_0$ | Computed from preceding water balance up to $t_0$. |
| `gdd_cumulative` | Phenology | Planting to $t_0$ | Fully available at cutoff. |
| `temp_rh_interaction`, `rain_rh_stress` | Interaction | Derived at $t_0$ | Fully available at cutoff. |
| `crop`, `district`, `growth_stage_code` | Static / Categorical | $t_0$ | Fully available at cutoff. |
| `last_scouted_severity_pct`, `last_scouted_incidence_pct` | Scouting | Most recent visit $\le t_0$ | Fully available; held static from last observation. |
| `days_since_scouting` | Scouting Metadata | $t_0 - t_{\text{last\_visit}}$ | Fully available; counter increments daily. |
| `weekly_trap_catch` | Pheromone Trap | Cumulative catch to $t_0$ | Fully available at cutoff. |

### Environmental Feature Isolation
The Environmental-Only model pipeline utilizes exactly 15 features. Automated schema verification confirms it contains zero scouting severity, incidence, trap catch, or scouting metadata columns.

---

## 7. Corrected Metric Definitions and Empirical Values

### 7.1 Mathematical Separation of Metrics
To prevent ambiguities observed in earlier informal documentation, all metrics are mathematically defined:

$$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$

$$\text{False Discovery Rate (FDR)} = \frac{\text{FP}}{\text{TP} + \text{FP}} = 1 - \text{Precision}$$

$$\text{False Positive Rate (FPR)} = \frac{\text{FP}}{\text{FP} + \text{TN}}$$

$$\text{Recall (True Positive Rate)} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$

$$\text{False Negative Rate (FNR)} = \frac{\text{FN}}{\text{TP} + \text{FN}} = 1 - \text{Recall}$$

$$\text{Average Precision (PR-AUC)} = \sum_{n} (R_n - R_{n-1}) P_n$$

$$\text{Brier Score} = \frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$$

$$\text{Expected Calibration Error (ECE)} = \sum_{b=1}^{B} \frac{|B_b|}{N} \left|\text{acc}(B_b) - \text{conf}(B_b)\right|$$

> **Resolution of Ambiguity:** The term "False Alarm Rate" was previously conflated with FPR. In operational pest surveillance, when an alert fires, farmers ask: *"If the system warns me, what is the probability it is wrong?"* This quantity is mathematically the **False Discovery Rate (FDR)** ($\text{FP}/(\text{TP}+\text{FP})$), **not** the False Positive Rate (FPR) ($\text{FP}/(\text{TN}+\text{FP})$). Both are now computed and reported separately.

### 7.2 Full Metric Table: Chronological Test Set ($N = 21,574$, Outbreaks = 2,052, Baseline Prevalence = 9.51%)

| Feature Set | Model | Tuned Thresh | PR-AUC | ROC-AUC | Precision | Recall | F1 Score | FDR ($1-\text{P}$) | FPR | FNR ($1-\text{R}$) | Brier Score | ECE |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Environmental** | Logistic Regression | 0.77 | 0.7635 | 0.9754 | 0.6155 | 0.8557 | 0.7161 | 0.3845 | 0.0544 | 0.1443 | 0.0617 | 0.0418 |
| **Environmental** | Random Forest | 0.81 | 0.8808 | 0.9882 | 0.7713 | 0.8304 | 0.7997 | 0.2287 | 0.0251 | 0.1696 | 0.0415 | 0.0249 |
| **Environmental** | LightGBM | 0.88 | 0.8851 | 0.9886 | 0.8066 | 0.7876 | 0.7970 | 0.1934 | 0.0199 | 0.2124 | 0.0396 | 0.0210 |
| **Environmental** | **XGBoost** | **0.51** | **0.8943** | **0.9892** | **0.8145** | **0.7909** | **0.8024** | **0.1855** | **0.0191** | **0.2091** | **0.0248** | **0.0175** |
| **Scouting-Assisted** | Logistic Regression | 0.83 | 0.9452 | 0.9934 | 0.8588 | 0.8700 | 0.8643 | 0.1412 | 0.0146 | 0.1300 | 0.0335 | 0.0284 |
| **Scouting-Assisted** | Random Forest | 0.77 | 0.9632 | 0.9959 | 0.8958 | 0.8636 | 0.8794 | 0.1042 | 0.0102 | 0.1364 | 0.0216 | 0.0152 |
| **Scouting-Assisted** | LightGBM | 0.88 | 0.9680 | 0.9961 | 0.9333 | 0.8647 | 0.8977 | 0.0667 | 0.0065 | 0.1353 | 0.0219 | 0.0148 |
| **Scouting-Assisted** | **XGBoost** | **0.45** | **0.9701** | **0.9964** | **0.9126** | **0.8876** | **0.9000** | **0.0874** | **0.0090** | **0.1124** | **0.0134** | **0.0112** |

---

## 8. Stress-Test Verification

### Methodology
Stress tests were audited to confirm that **modifications occur exclusively at inference time**. Labels $y_{\text{true}}$ are never modified, and models are never retrained on degraded data.

### Baseline vs. Degraded Performance

| Stress Condition | Degradation Mechanism | Scouting Model PR-AUC | Scouting Model F1 | Environmental Model PR-AUC | Environmental Model F1 |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Baseline (Nominal)** | Clean test data | **0.9701** | **0.9000** | **0.8943** | **0.8024** |
| **Scouting Blackout** | Scouting age forced to 21d; severity = 0.0 | **0.4124** (-57.5%) | **0.4350** (-51.7%) | **0.8943** (0.0% impact) | **0.8024** (0.0% impact) |
| **Weather Sensor Noise** | $\mathcal{N}(0, 3^\circ\text{C})$ temp, $\mathcal{N}(0, 15\%)$ RH, $\pm 25\text{ mm}$ rain | **0.9105** (-6.1%) | **0.8410** (-6.6%) | **0.7412** (-17.1%) | **0.6725** (-16.2%) |
| **Extreme Severe Combined** | Weather noise + Scouting blackout | **0.3150** (-67.5%) | **0.3280** (-63.6%) | **0.7412** (-17.1%) | **0.6725** (-16.2%) |

### Key Architectural Takeaway
When scouting data is interrupted (e.g., monsoon road impassability or scout absenteeism), the Scouting-Assisted pipeline suffers severe performance collapse. However, the **Environmental-Only pipeline maintains its 0.8943 PR-AUC**. This demonstrates why a production architecture must maintain an independent environmental fallback pipeline.

---

## 9. Model Inference and Production Isolation Verification

1. **Pipeline Loading and Schema Enforcement:**  
   Both `models/experimental_synthetic_pest_v2/environmental_model_pipeline.joblib` and `full_model_pipeline.joblib` load cleanly via `joblib.load()`. Missing feature columns raise explicit `ValueError` exceptions prior to inference.
2. **Separation from Production Endpoints:**  
   Experimental synthetic pipelines reside in `src/pest_forecasting/` and `models/experimental_synthetic_pest_v2/`. Production advisory endpoints (`backend/app/api/fertilizer.py`, `backend/app/api/advisory.py`) do not import or invoke experimental synthetic artifacts.
3. **Synthetic Disclaimers:**  
   All experimental inference payloads output:
   ```json
   {
     "status": "SYNTHETIC_EXPERIMENTAL",
     "is_production_ready": false,
     "disclaimer": "CRITICAL NOTICE: Output generated by experimental model trained exclusively on synthetic data. NOT FOR OPERATIONAL USE."
   }
   ```
4. **Production Readiness Gate Status:**  
   Execution of `src/pest_risk/production_readiness_gate.py` produces:
   - **Gate Status:** `BLOCKED`
   - **Is Ready For Training:** `False`
   - **Active Blocking Reasons:** 10 (Zero authentic commercial surveillance records; zero verified field labels; 5 ETLs at primary source retrieved).

---

## 10. Audit Corrections Log

| Subsystem / File | Issue Identified | Correction Applied |
| :--- | :--- | :--- |
| `src/pest_forecasting/evaluate.py` | Conflation of False Discovery Rate with False Positive Rate in reporting structures. | Explicitly added `false_discovery_rate`, `false_positive_rate`, and `false_negative_rate` to `EvaluationMetrics` dataclass and evaluation calculations. |
| `src/pest_forecasting/synthetic_generator_v2.py` | Growth and mortality parameters lacked explicit notation distinguishing literature vs assumptions. | Fully documented $r_{\text{intrinsic}}=0.35$ and $m=-0.12$ as calibrated simulation assumptions. |
| `scratch/evaluate_field_grouped.py` | Unseen field generalization had not been quantified to isolate spatial entity memorization. | Executed rigorous 20% unseen-field holdout evaluation across all 4 model families; confirmed $<0.006$ PR-AUC delta. |
| `tests/test_experimental_pest_forecasting_v2.py` | Missing automated assertions for field-grouped artifact and mathematical separation of FDR vs FPR. | Added `test_field_grouped_spatial_evaluation_artifact()` and `test_metric_definitions_fdr_fpr_separation()`. |

---

## 11. Remaining Limitations & Open Questions

1. **Synthetic Data Boundaries:** Synthetic benchmarks prove that the ML algorithms, feature extraction code, and temporal splitting work correctly. They **cannot** prove real-world predictive validity against authentic Indian pest outbreaks.
2. **Missing Authentic Data:** The project currently possesses zero authentic commercial surveillance observations and zero verified field outbreak labels.
3. **Deployment Risks:** Deploying synthetic-trained models to farmers would create high risks of false alarms (unnecessary pesticide sprays, economic loss, chemical resistance) or missed outbreaks (severe crop destruction).
4. **Prerequisites for Operational Release:**
   - Formal execution of institutional Data Use Agreements (CROPSAP, PDKV, VNMKV, ICAR-CICR).
   - Execution of the Kharif 2027 sentinel field pilot.
   - Independent labeling and agronomic validation by certified entomologists.

---

## 12. Exact Test and Build Results

### 12.1 Backend Unit & Integration Tests (Pytest)
- **Command:** `pytest tests/`
- **Result:** **197 passed, 253 warnings in 95.15s (0:01:35)**
- **Coverage:** 24 test modules including API endpoints, surveillance pipelines, DVC configuration, MLflow tracking, security/privacy, and experimental synthetic pipelines.

### 12.2 Frontend Unit Tests (Vitest)
- **Command:** `npm --prefix frontend test -- --run`
- **Result:** **4 passed (1 test file) in 4.27s**

### 12.3 Frontend Production Build (Vite)
- **Command:** `npm --prefix frontend run build`
- **Result:** **Successful build in 752ms** (`dist/index.html` 0.50 kB, `dist/assets/index-ChE8Aqhz.js` 295.16 kB).

---

## 13. Final Production Readiness Status

```
========================================================================================
AGRIADAPT AI — PRODUCTION READINESS AUDIT CERTIFICATION
========================================================================================
Production Model Training Status:   STRICTLY PROHIBITED
Production Advisory Serving:        STRICTLY PROHIBITED
Production Readiness Gate:          BLOCKED (10 / 10 BLOCKING CONDITIONS ACTIVE)
Field Pilot Operational Status:     STANDBY / PRE-DEPLOYMENT NO-GO
Experimental Pipeline Status:       FROZEN & CERTIFIED FOR RESEARCH BENCHMARKING ONLY
========================================================================================
```

**Required Next Steps Before Production Activation:**
1. Secure institutional approval and sign data-sharing DUAs with CROPSAP Maharashtra and ICAR-CICR.
2. Complete expert entomological review of the 5 ETL packages.
3. Deploy the Kharif 2027 field pilot to collect authentic sentinel field observations.
4. Establish certified positive and negative outbreak ground-truth labels from commercial fields.
5. Retrain forecasting models exclusively on verified authentic data with prospective field evaluation.

