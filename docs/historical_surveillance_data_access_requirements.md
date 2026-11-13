# AgriAdapt AI — Historical Surveillance Data Access Requirements & Feasibility Analysis

**Document ID:** `AGRI-DATA-REQ-2027-V1`  
**Version:** 1.0.0  
**Target Institutional Repositories:** CROPSAP Maharashtra & ICAR-CICR Nagpur  
**Governance Scope:** Technical Evaluation of Historical Surveillance Data Feasibility  
**Current Holding Status:** **ZERO HISTORICAL RECORDS RECEIVED FROM CROPSAP OR ICAR-CICR.**  
**Status:** TECHNICAL FEASIBILITY STUDY ONLY.

---

## 1. Executive Summary & Objective

To transition from heuristic environmental risk scoring (the Environmental Favorability Index, EFI) to supervised machine learning, an early-warning platform requires paired historical training records:
1. **Preceding Weather & Microclimate Covariates:** Historical environmental observations over a 7-day lookback window ($[T-6, T]$).
2. **Ground-Truth Outbreak Outcome Labels:** Verified field surveillance observations in the forward evaluation window ($[T+1, T+7]$) meeting or exceeding Economic Threshold Levels ($Y \in \{0, 1\}$).

This document analyzes the historical surveillance data repositories maintained by the two principal Maharashtra authorities — **CROPSAP Maharashtra** and **ICAR-CICR Nagpur** — evaluating their data models, field availability, biological granularity, and suitability for commercial vs research forecasting.

---

## 2. Institutional Repository Field Feasibility Comparison

| Data Field / Attribute | Required Role in Early-Warning MLOps | CROPSAP Maharashtra (Commercial Extension Scouting) | ICAR-CICR Nagpur (Experimental Research Station Trials) | Feasibility Assessment for AgriAdapt AI |
|:---|:---|:---:|:---:|:---|
| **Exact Observation Date ($T$)** | **MANDATORY:** Anchors $[T-6, T]$ and $[T+1, T+7]$ windows. | Available (recorded per weekly scouting entry). | Available (daily trap counts; weekly boll dissections). | **High:** Both sources provide calendar dates suitable for temporal alignment. |
| **Spatial Demarcation** | **MANDATORY:** Joins with ERA5-Land weather grid. | Taluka / Village name; GPS in recent digital app versions. | Exact Station Plot GPS coordinates (Nagpur / Coimbatore). | **High:** CICR provides precise plot centroids; CROPSAP provides taluka/village level bounds. |
| **Pest Incidence Percentage** | **CORE LABEL:** Direct comparison with ETL incidence. | Estimated as field incidence % or qualitative class (Low/Med/High). | Quantitative (% rosette flowers, % boll locule damage). | **Moderate to High:** CICR is fully quantitative; CROPSAP requires verification of continuous vs categorical recording. |
| **Destructive Boll Dissections** | **CORE LABEL:** Pink Bollworm cryptic damage ground truth. | Rare in routine scouting (mostly visual symptoms/rosettes). | Systematic (20 to 100 green bolls per replication dissected). | **High for CICR; Low for CROPSAP:** CICR is the gold standard for destructive boll validation. |
| **Pheromone Trap Catches** | **ACTION TRIGGER:** Adult male moth emergence tracking. | Available in select talukas with CROPSAP trap networks. | Continuous daily/weekly records across multi-year trials. | **High:** Crucial for evaluating consecutive-night trap rules ($req=3$). |
| **Crop Growth Stage** | **STAGE-SPECIFIC ETL:** Selects correct threshold (e.g. 5% vs 10%). | Categorical (Vegetative, Flowering, Boll Development). | Precise phenological tracking (Days After Sowing, BBCH scale). | **High:** Both sources document phenology, preventing unstratified threshold evaluation. |
| **Sampling Denominator** | **UNBIASED RATIOS:** Number of plants / bolls sampled ($N$). | Often fixed by SOP (e.g. 20 plants/spot), but sometimes omitted in summary tables. | Explicitly recorded per replication ($N=20, 80$). | **High for CICR; Moderate for CROPSAP:** Ingestion must enforce $N \ge 10$ to prevent small-sample bias. |
| **Farmer Chemical Interventions** | **CONFOUNDER CONTROL:** Sprays suppress pest counts post-$T$. | Not systematically recorded in public advisory extracts. | Fully controlled (Untreated check vs Treated IPM modules). | **Critical Divergence:** Commercial fields have uncontrolled spray history; research trials have pristine untreated checks. |

---

## 3. Essential Feature-to-Label Alignment Schema

To construct a scientifically leak-free supervised dataset, an institutional observation record must satisfy the following mathematical feature-to-label alignment:

```
Temporal Timeline:
[ T - 6 ] ─── [ T - 5 ] ─── [ T - 1 ] ─── [ T ] ─── [ T + 1 ] ─── [ T + 2 ] ─── [ T + 7 ]
│ ◄────── Preceding Feature Window ──────► │   │    │ ◄──── Forward Outcome Window ────► │
│   (Weather Covariates, GDD, RH, EFI)     │   │    │   (Scouted Incidence vs ETL)       │
└──────────────────────────────────────────┘   │    └────────────────────────────────────┘
                                        Anchor Date (T)
```

### 3.1 Essential Features (Lookback $[T-6, T]$)
1. **Daily Mean, Min, Max Temperature:** Degree-day accumulation ($\text{GDD} = \max(0, \bar{T} - T_{base})$).
2. **Relative Humidity (Morning 07:00 and Evening 14:00):** Vapor pressure deficit and spore/larval survival favorability.
3. **Cumulative 7-Day Precipitation:** Soil waterlogging or oviposition washing.
4. **Calculated Environmental Favorability Index (EFI):** Baseline biological suitability prior to observation.
5. **Crop Age (Days After Sowing, DAS):** Host tissue vulnerability.

### 3.2 Essential Outcome Attributes (Forward $[T+1, T+7]$)
1. **At least ONE verified field visit within $[T+1, T+7]$:** If zero visits exist, outcome is `UNOBSERVED` ($Y=\text{None}$).
2. **Quantitative measurement recorded:** Either `pest_incidence_pct`, `trap_catch_count`, `pest_severity_pct`, or `plants_affected / plants_sampled`.
3. **Outbreak Indicator ($Y=1$):**
   $$Y = \mathbb{I}\left( \max_{t \in [T+1, T+7]} \text{Incidence}_t \ge \text{ETL}_{\text{stage}} \lor \text{ConsecutiveTraps}_t \ge \text{ETL}_{\text{trap}} \right)$$
4. **Verified Non-Outbreak Indicator ($Y=0$):**
   Active scouting occurred within $[T+1, T+7]$, all measurements are sub-ETL, and zero spray applications masked natural population trends.

---

## 4. Commercial-Field Forecasting vs Research Station Micro-Plot Distinction

A foundational scientific distinction must be maintained when evaluating institutional data access:

| Characteristic | CROPSAP Historical Data | ICAR-CICR Historical Data | Analytical Utility & Risk |
|:---|:---|:---|:---|
| **Farm Operational Context** | Real-world working farms managed by smallholders. | Rigorously controlled research farm station. | CROPSAP reflects true smallholder commercial domain; CICR reflects agronomic potential under controlled conditions. |
| **Chemical Application Bias** | High: Farmers spray upon seeing first moths, causing sudden artificial collapses in pest incidence ($Y \rightarrow 0$). | Zero in untreated control checks (T7); fully documented in experimental treatments. | CICR untreated plots allow pure biophysical modeling without chemical distortion; CROPSAP data requires spray confounding adjustments. |
| **Spatial Autocorrelation** | Dispersed across talukas (spatial independence across villages). | Clustered on contiguous experimental station plots ($25–50\text{ m}^2$). | CROPSAP supports spatial cross-validation; CICR requires leave-plot/season-out splits to avoid spatial leakage. |
| **Model Role in AgriAdapt AI** | **Primary Target Domain:** Direct training/testing of commercial smallholder early warning. | **Mechanistic Validation:** Calibrating biological growth degree models and threshold transitions. | **DO NOT POOL INTO A SINGLE HOMOGENEOUS TRAINING SET.** |

---

## 5. Feasibility Verdict and Next Steps

1. **Both institutions hold scientifically invaluable records** that could unblock supervised machine learning if formally accessed.
2. **Zero records have been received or promised** to date.
3. Access requests will remain strictly aligned with the dual-pathway governance model: research station data for biological calibration, commercial surveillance for field validation.

