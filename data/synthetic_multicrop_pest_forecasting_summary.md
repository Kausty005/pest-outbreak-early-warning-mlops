# AgriAdapt AI — Synthetic Multi-Crop Pest Outbreak Forecasting Dataset Summary

> [!IMPORTANT]
> **SYNTHETIC DATA DISCLAIMER**:
> This dataset is **entirely synthetic**, generated via biophysical simulation models for prototype development,
> feature pipeline validation, and benchmark testing. The pest population dynamics, weather patterns, and 7-day
> forward outbreak labels are **simulated assumptions and mathematical approximations**, NOT genuine in-field
> agricultural surveillance observations. This dataset must NOT be used for real farm advisory or operational
> field decisions without validation against real-world ground truth.

---

## 1. Dataset Overview

- **Output File**: `D:/OMKAR/VITP/SEM 5/MLOPS/pest-outbreak-early-warning-mlops/data/synthetic_multicrop_pest_forecasting.csv` (11.34 MB)
- **Total Rows**: **100,000** (Exactly 100,000 field-days)
- **Total Columns**: **17**
- **Simulated Seasons**: 3 Full Seasons (2022, 2023, 2024)
- **Date Range**: 2022-06-20 to 2025-03-21
- **Random Seed**: `42` (100% reproducible)
- **Overall Outbreak Prevalence**: **16.91%** (16,911 positive events)

---

## 2. Simulated Crops and Target Pests

| Crop | Target Pest | Scientific Name | Districts Simulated | Sample Count | Outbreaks | Outbreak Rate |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| **Maize** | Fall armyworm | *Spodoptera frugiperda* | Davanagere, Chhindwara, Belagavi, ... | 16,667 | 2,743 | **16.46%** |
| **Rice** | Brown planthopper | *Nilaparvata lugens* | East Godavari, Thanjavur, Cuttack, ... | 16,667 | 2,772 | **16.63%** |
| **Cotton** | Pink bollworm | *Pectinophora gossypiella* | Nagpur, Amravati, Yavatmal, ... | 16,667 | 3,018 | **18.11%** |
| **Wheat** | Aphids | *Rhopalosiphum padi / Sitobion avenae* | Ludhiana, Karnal, Indore, ... | 16,667 | 2,437 | **14.62%** |
| **Tomato** | Fruit borer | *Helicoverpa armigera* | Kolar, Nashik, Chittoor, ... | 16,666 | 3,693 | **22.16%** |
| **Chickpea** | Pod borer | *Helicoverpa armigera* | Kalaburagi, Akola, Vidisha, ... | 16,666 | 2,248 | **13.49%** |

---

## 3. Feature Schema & Column Definitions

| Column | Type | Physical Unit | Description |
| :--- | :---: | :---: | :--- |
| `field_id` | String | Identifier | Unique anonymized plot/field identifier (e.g. `FLD-MAI-DAV-0012`) |
| `district` | String | Location | Agricultural district in India |
| `crop` | String | Category | Target crop species (Maize, Rice, Cotton, Wheat, Tomato, Chickpea) |
| `pest` | String | Species | Target insect pest species |
| `date` | Date | YYYY-MM-DD | Reference observation date ($t_0$) |
| `growth_stage` | String | Phenology | BBCH/CIMMYT physiological crop growth stage |
| `t7_mean_temp_c` | Float | °C | 7-day rolling mean temperature strictly prior to $t_0$ |
| `t7_min_temp_c` | Float | °C | 7-day minimum temperature prior to $t_0$ |
| `t7_max_temp_c` | Float | °C | 7-day maximum temperature prior to $t_0$ |
| `t7_mean_rh_pct` | Float | % | 7-day rolling mean relative humidity |
| `t7_high_rh_days` | Integer | Days [0, 7] | Count of days in preceding week with $\text{RH} \ge 80\%$ |
| `t7_rainfall_mm` | Float | mm | 7-day cumulative rainfall prior to $t_0$ |
| `t14_rainfall_mm` | Float | mm | 14-day cumulative rainfall prior to $t_0$ |
| `current_incidence_pct_t0` | Float | % | Observed percentage of infested plants/foliage at $t_0$ |
| `current_severity_pct_t0` | Float | % | Observed severity of damage (% tissue loss) at $t_0$ |
| `pest_present_t0` | Binary | 0 or 1 | 1 if symptoms/insects observed at $t_0$, else 0 |
| `outbreak_within_7d` | Binary | 0 or 1 | **Prediction Target**: 1 if field crosses economic threshold during $[t_0+1, t_0+7]$, else 0 |

---

## 4. Epidemiological Ground Truth Target Formulation

The prediction target `outbreak_within_7d` is calculated **strictly by inspecting the subsequent 7 simulated days** ($[t_0 + 1, t_0 + 7]$):

$$\text{outbreak\_within\_7d} = \begin{cases} 1 & \text{if } \max_{k=1..7} (\text{Severity}_{t_0+k}) \ge \text{ETL}_{\text{sev}} \text{ or } \max_{k=1..7} (\text{Incidence}_{t_0+k}) \ge \text{ETL}_{\text{inc}} \text{ or } \Delta \text{Inc} \ge 10\% \\ 0 & \text{otherwise} \end{cases}$$

### Leakage Prevention Guarantees:
1. **Causal Horizon**: Features contain **zero future weather** and **zero future pest readings**.
2. **Boundary Truncation**: The final 7 days of each simulated field season are **excluded from the dataset**, because their complete forward 7-day monitoring window is incomplete.
3. **History Burn-In**: The first 14 days of each field season are **excluded from the dataset**, ensuring every row has authentic 14-day past weather aggregations.
4. **No Synthetic Shortcuts**: Outbreak labels are **not randomly assigned**; they emerge organically from the interplay of thermal favorability, humidity persistence, stage vulnerability, and field baseline pressure.

---

## 5. Statistical Distribution & Range Audit

```
                             count       mean        std    min    25%    50%    75%     max
t7_mean_temp_c            100000.0  24.991955   4.607108  10.10  22.30  25.80  28.47   35.70
t7_min_temp_c             100000.0  18.797893   5.266934   3.80  15.20  19.70  23.00   30.50
t7_max_temp_c             100000.0  31.188436   4.120707  17.30  29.10  31.90  34.10   42.40
t7_mean_rh_pct            100000.0  71.052395   9.599694  44.64  64.77  70.53  76.90   98.00
t7_high_rh_days           100000.0   1.341790   2.534659   0.00   0.00   0.00   1.00    7.00
t7_rainfall_mm            100000.0  22.155370  26.042704   0.00   0.00  13.80  35.70  214.60
t14_rainfall_mm           100000.0  45.279851  43.256957   0.00   9.20  34.10  70.80  293.70
current_incidence_pct_t0  100000.0   2.254296   4.919339   0.00   0.04   0.31   0.74   20.78
current_severity_pct_t0   100000.0   1.331627   2.906268   0.00   0.02   0.18   0.44   12.42
pest_present_t0           100000.0   0.357690   0.479323   0.00   0.00   0.00   1.00    1.00
outbreak_within_7d        100000.0   0.169110   0.374851   0.00   0.00   0.00   0.00    1.00
```

---

## 6. Validation Audit Report

- **Row Count Check**: **PASSED** (100,000 / 100,000)
- **Missing Value Check**: **PASSED** (0 nulls found across all 17 columns)
- **Temporal Sequence Check**: **PASSED** (Sorted chronologically from 2022-06-20 to 2025-03-21)
- **Physical Range Checks**: **PASSED** (All 11 numerical and categorical columns strictly within biological limits)
- **Causal Consistency Check**: **PASSED** (`t14_rainfall_mm >= t7_rainfall_mm` holds for 100.0% of records)
