# AgriAdapt AI — Historical Research Data Quality Assessment (Lande 2005)

**Module:** Pest Outbreak Early Warning MLOps  
**Dataset Reference:** Lande, G. K. (2005) Appendix Table VII (`HISTORICAL_RESEARCH_TRIAL`)  
**Host Institution:** Dr. Panjabrao Deshmukh Krishi Vidyapeeth (Dr. PDKV), Akola, Maharashtra  
**Target Pest & Crop:** Cotton Pink Bollworm (*Pectinophora gossypiella*) on Cotton (*G. hirsutum*, cv. PKV-Rajat)  
**Quarantine Path:** `data/raw/pest_surveillance/historical_transcriptions/reconciled_transcription.csv`  
**Assessment Date:** November 2026  
**Auditor:** Agricultural Machine Learning Architecture & Biometrics Group  

---

## 1. Executive Summary & Critical Biometric Disclaimer

In Phase 14, an untreated control plot ($T_7$) from an M.Sc. dissertation (Lande, 2005, Dr. PDKV Akola) was digitized via a controlled double-entry protocol, yielding 13 weekly observations across 14 Standard Meteorological Weeks (SMW 32 to SMW 45) for Kharif 2004.

> [!CAUTION]
> ### CRITICAL BIOMETRIC & MACHINE LEARNING INVARIANT
> **13 observations from one experimental plot over a single growing season DO NOT constitute 13 independent outbreak events.**
> 
> In epidemiologic and biometrical terms, these 13 observations represent a **single, temporally autocorrelated realization of an insect population trajectory**. 
> - Computing machine learning metrics (such as train-test accuracy, precision, recall, ROC-AUC, or F1-score) on these 13 rows would be pseudoscientific, mathematically fraudulent, and severely distorted by temporal leakage.
> - This dataset is strictly classified as a **Quarantined Exploratory Benchmark**. It is authorized solely for verifying ingestion pipeline parsing, validating $[T-6, T] \rightarrow [T+1, T+7]$ lagging mechanics, and evaluating missing-data protocols.
> - **Supervised predictive model training on this dataset is STRICTLY PROHIBITED.**

---

## 2. Systematic 13-Dimension Data Quality Evaluation

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              LANDE (2005) DATA QUALITY EVALUATION MATRIX                               │
├──────┬────────────────────────────┬─────────────────────────────┬──────────────────────────────────────┤
│ #    │ Dimension                  │ Audit Finding               │ Quality Grade & Impact               │
├──────┼────────────────────────────┼─────────────────────────────┼──────────────────────────────────────┤
│ 1    │ Observation Count          │ 13 valid rows               │ 🔴 Insufficient for ML training      │
│ 2    │ Temporal Span              │ 14 SMWs (SMW 32 to SMW 45)  │ 🟢 Covers flowering through picking  │
│ 3    │ Missing Data Preserved     │ 1 missing week (SMW 37)     │ 🟢 100% compliant (Zero-fill blocked)│
│ 4    │ Measurement Completeness   │ Damage %, flowers, traps    │ 🟢 Multi-attribute complete          │
│ 5    │ Sampling Methodology       │ Destructive boll dissection │ 🟢 High agronomic rigor (20 bolls/rep│
│ 6    │ Experimental Plot Size     │ 25.92 m² micro-plot         │ 🔴 Micro-plot bias (Not a farm field)│
│ 7    │ Treatment History          │ Untreated check (T7, 4 reps)│ 🟢 Natural pest progression          │
│ 8    │ Control Integrity          │ Bordered by chemical trials │ 🟡 Edge-effect spray drift risk      │
│ 9    │ Geographic Diversity       │ 1 station (CRS Akola)       │ 🔴 Zero spatial variance (1 point)   │
│ 10   │ Multi-Year Coverage        │ 1 single season (2004)      │ 🔴 Zero inter-annual climate variance│
│ 11   │ Pest-Genotype Relevance    │ Conventional non-Bt hybrid  │ 🟡 Pre-Bollgard-II resistance era    │
│ 12   │ Descriptive Utility        │ Population phenology curves │ 🟢 HIGH (Excellent agronomic curves) │
│ 13   │ Predictive ML Suitability  │ 0 cross-field samples       │ 🔴 UNUSABLE for supervised ML        │
└──────┴────────────────────────────┴─────────────────────────────┴──────────────────────────────────────┘
```

---

### Detailed Findings by Dimension

### 1. Observation Count & Sample Size
* **Finding:** Exactly 13 observations across the season.
* **Evaluation:** Standard statistical learning theory mandates hundreds to thousands of spatially independent observation sequences to learn the joint probability density $P(\text{Outbreak} \mid \text{Weather}_{T-6:T})$. Thirteen rows provide essentially zero degrees of freedom after accounting for auto-correlation.

### 2. Temporal Span & Granularity
* **Finding:** 14 Standard Meteorological Weeks (SMW 32 to SMW 45), corresponding to calendar dates August 9, 2004, to November 8, 2004.
* **Evaluation:** Granularity is exactly weekly (7-day intervals). The observation period captures the entire reproductive phenology: squaring (42 DAS), early bloom (49 DAS), peak flowering (56 DAS), green boll development (63–84 DAS), boll opening (112–119 DAS), and harvest (126–133 DAS).

### 3. Missing Observation Handling
* **Finding:** Exactly one missing scouting cycle occurred at **SMW 37 (September 13, 2004)**.
* **Root Cause:** Meteorological records confirm heavy monsoon precipitation (142.4 mm) during that week, resulting in severe waterlogging of Vertisol Plot 4 that prevented researchers from entering the field without damaging the soil structure.
* **Compliance:** The transcription protocol strictly preserved SMW 37 as missing (`None` / null). In downstream labeling, an anchor observation at SMW 36 correctly resolves to `label_status="UNOBSERVED_FUTURE_WINDOW"` and `outbreak_label_7d=None`. Zero imputation was strictly blocked.

### 4. Measurement Completeness & Attributes
* **Finding:** The dataset captures:
  * Green boll damage percentage (Mean of 4 replications, 20 dissected bolls per replication = 80 bolls total).
  * Rosetted flower percentage (20 plants visual scouting during bloom).
  * Daily and weekly pheromone trap catches (moths/trap/night).
  * Crop growth stage tokens and days after sowing (DAS).
* **Evaluation:** Agronomically complete for pink bollworm, capturing both visual flower symptoms and destructive internal carpel damage.

### 5. Sampling Methodology
* **Finding:** Destructive green boll sampling adhering to ICAR-CICR recommended protocols. Twenty mature bolls (approx. 20–25 days old) were sampled randomly per replication, sliced longitudinally, and examined under illuminated magnifiers for internal locule damage and larvae.
* **Evaluation:** Agronomically sound. Far superior to external visual examination, which fails to detect bore holes sealed by plant sap.

### 6. Experimental Plot Size & Micro-Plot Effect
* **Finding:** Documented experimental plot dimensions are $5.4\text{ m} \times 4.8\text{ m} \approx 25.92\text{ m}^2$ per replication (gross plot area). Total untreated check area across 4 replications is approximately $103.68\text{ m}^2$ ($0.01\text{ ha}$).
* **Evaluation:** Severe micro-plot effect. Pheromone plume dynamics, larval dispersion, and adult moth movement operate differently over a $25\text{ m}^2$ micro-plot than across a commercial $2\text{ to }5\text{ ha}$ rainfed farm holding.

### 7. Treatment History & Untreated Control Status
* **Finding:** Assigned as Treatment $T_7$ (Untreated Control Check Plot). Zero chemical insecticides, bio-pesticides, or mating disruption pheromones were applied to this plot throughout the Kharif season.
* **Evaluation:** Preserves natural host–pest biological interaction without insecticide-induced mortality masking environmental favorability.

### 8. Border Effects & Chemical Spray Proximity
* **Finding:** The experiment used a Randomized Block Design (RBD) with 7 treatments replicated 4 times across a single field block.
* **Evaluation:** Potential edge effect and chemical drift. Untreated plots were separated from insecticidally treated plots ($T_1$ through $T_6$, including spinosad, indoxacarb, and neem formulations) by buffer rows of only 1.2 meters. While researchers took precautions, localized spray drift and pest movement from treated plots into the untreated check can alter local density.

### 9. Geographic Representativeness
* **Finding:** Single fixed geographic coordinate: Central Research Station (CRS) Field Plot No. 4, Dr. PDKV Akola ($20.704^\circ\text{N}, 77.029^\circ\text{E}$).
* **Evaluation:** Zero geographic diversity. The dataset contains no spatial variance across the 4 priority Maharashtra districts (Nagpur, Amravati, Yavatmal, Jalgaon) and cannot capture topographical or regional rainfall gradients.

### 10. Multi-Year & Climatic Coverage
* **Finding:** Single Kharif season (2004–2005).
* **Evaluation:** Zero inter-annual variance. The dataset represents only one specific weather realization (Kharif 2004 monsoon profile). It cannot train a model to distinguish drought-year dynamics from excess-rainfall years.

### 11. Pest Genotype & Host Variety Context
* **Finding:** Host crop variety is PKV-Rajat (*G. hirsutum*), a conventional non-transgenic hybrid released by Dr. PDKV Akola. The trial took place in 2004, prior to the widespread commercial adoption of Bollgard-II (Cry1Ac + Cry2Ab) Bt cotton in Vidarbha.
* **Evaluation:** Modern Vidarbha cotton fields cultivate Bt-transgenic hybrids where pink bollworm has developed field resistance. While the baseline ETL (10% damaged green bolls) remains identical, early-season oviposition behavior and larval survival on conventional cotton differ somewhat from modern resistant populations on Bt cotton.

### 12. Descriptive & Agronomic Calibration Utility
* **Evaluation:** **HIGH.** The dataset provides clear, empirical evidence of the natural progression of pink bollworm:
  * Low early incidence ($<2.5\%$) during squaring and early flowering (SMW 32–35).
  * Rapid escalation to $8.75\%$ by SMW 38.
  * Crossing the 10% Economic Threshold Level at SMW 39 ($12.5\%$).
  * Peaking at $28.75\%$ damage during boll opening (SMW 43).
  * This empirical curve is highly valuable for testing whether early-warning risk scores elevate 7 to 14 days prior to SMW 39.

### 13. Supervised Machine Learning Suitability
* **Evaluation:** **STRICTLY UNUSABLE FOR SUPERVISED ML.**
  * Cannot be partitioned into train/test sets without massive data leakage.
  * Does not provide independent negative and positive outbreak instances.
  * Overfitting to 13 points would result in severe model failure in real commercial fields.

---

## 3. Conclusion and Prescribed Usage Boundary

| Permitted Use | Prohibited Use |
| :--- | :--- |
| Ingestion pipeline parsing tests | Supervised classifier training |
| Schema validation & field constraint tests | Feature selection or importance scoring |
| SMW temporal alignment verification | Train/test split accuracy calculation |
| $[T-6, T] \rightarrow [T+1, T+7]$ lag logic testing | Generating commercial outbreak alerts |
| Descriptive phenological curve visualization | Claiming "ML model validation" |

> **Final Assessment:** The Lande (2005) dataset is an exemplary **test fixture and calibration benchmark**, but must remain strictly quarantined away from the production training pipeline.

