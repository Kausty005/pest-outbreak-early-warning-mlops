# AgriAdapt AI — Research-to-Commercial Domain Comparison Framework

**Module:** Pest Outbreak Early Warning MLOps  
**Version:** 1.0 (Phase 15 Domain Divergence & Transfer Architecture)  
**Date:** November 2026  
**Status:** Approved Methodological Framework  
**Author:** Entomological Machine Learning & Agro-Ecosystems Modeling Team  

---

## 1. Rationale & Core Problem Statement

A fundamental hazard in agricultural machine learning is **domain shift**: models trained or calibrated on controlled agricultural university research station plots fail catastrophically when deployed across commercial smallholder farmer fields.

Research station trials and commercial farming landscapes represent two fundamentally distinct ecological and agronomic domains:
1. **Source Domain ($\mathcal{D}_S$):** Research station experimental plots (e.g. Dr. PDKV Akola Central Research Station). Highly controlled micro-plots, uniform plant spacing, artificial buffer rows, and adjacent untreated/treated blocks.
2. **Target Domain ($\mathcal{D}_T$):** Smallholder rainfed commercial farms across Maharashtra (Nagpur, Amravati, Yavatmal, Jalgaon). Highly heterogeneous field sizes ($1\text{ to }5\text{ ha}$), variable soil depth, irregular sowing windows, mixed agrochemical spray practices, and surrounding wild host patches.

> [!CAUTION]
> **Governing Rule:** Historical research trial observations MUST NOT automatically become commercial-field training records. Unvalidated domain adaptation, transfer learning, or covariate shift correction without sufficient independent target-domain ground truth ($\ge 500$ verified commercial field observations) is strictly prohibited.

---

## 2. Systematic 11-Dimension Domain Divergence Taxonomy

The matrix below defines the eleven primary dimensions along which research station plots and commercial smallholder fields diverge, complete with the observable statistical shifts and biometric implications:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        RESEARCH STATION vs COMMERCIAL SMALLHOLDER DOMAIN MATRIX                        │
├──────┬─────────────────────────┬──────────────────────────────┬────────────────────────────────────────┤
│ #    │ Agronomic Dimension     │ Source Domain: Research Plot │ Target Domain: Commercial Smallholder  │
├──────┼─────────────────────────┼──────────────────────────────┼────────────────────────────────────────┤
│ 1    │ Plot Area               │ 20–50 m² micro-plots         │ 10,000–50,000 m² (1–5 hectares)        │
│ 2    │ Crop Cultivar / Variety │ Single pureline / hybrid     │ Mixed commercial Bt hybrids / local cv │
│ 3    │ Sowing Synchrony        │ Exact single calendar date   │ Staggered across 3–5 weeks by rainfall │
│ 4    │ Agrochemical Inputs     │ Zero spray (Untreated check) │ Variable, often unrecorded chemical mix│
│ 5    │ Scouting Rigor          │ Research entomologist, weekly│ Farmer / extension scout, variable     │
│ 6    │ Pest Inoculum Pressure  │ Artificially concentrated    │ Spatially patchy, landscape dispersal  │
│ 7    │ Trap Micro-Environment  │ Standard height, clear radius│ Placed near tree lines, dusty foliage  │
│ 8    │ Phenological Uniformity │ Highly uniform canopy height │ Uneven stand density, gap filling      │
│ 9    │ Surrounding Land Cover  │ Adjacent research trial plots│ Diverse crop mosaic (paddy, soybean)   │
│ 10   │ Edaphic & Hydrology     │ Engineered drainage / slopes │ Natural Vertisol flood / cracking      │
│ 11   │ Sampling Denominators   │ Exactly 20 bolls / 5 m rows  │ Pragmatic / variable plant inspection  │
└──────┴─────────────────────────┴──────────────────────────────┴────────────────────────────────────────┘
```

---

### Detailed Analysis of the 11 Divergence Dimensions

### 1. Plot Area & Boundary Dynamics
* **Research Station:** Micro-plots ($5.4\text{ m} \times 4.8\text{ m} \approx 25.92\text{ m}^2$) have a massive perimeter-to-area ratio. Edge effects dominate, and adult insect movement between plots takes seconds.
* **Commercial Farm:** Expansive holdings ($10,000\text{ to }50,000\text{ m}^2$) where interior microclimates differ substantially from field edges, and pest colonization follows directional wind and hedgerow gradients.

### 2. Crop Cultivar & Resistance Profile
* **Research Station:** Often uses specific historical cultivars (e.g. PKV-Rajat in Lande 2005) or pure lines for genetic control.
* **Commercial Farm:** Predominantly cultivated with modern multi-gene Bt-transgenic hybrids (Bollgard-II: Cry1Ac + Cry2Ab), with varying refuge non-Bt border compliance and field-evolved Cry-toxin resistance.

### 3. Sowing Date Synchrony & Crop Age
* **Research Station:** All experimental plots are seeded within a 4-hour window on a single day upon soil preparation.
* **Commercial Farm:** Sowing dates are dictated by localized pre-monsoon shower arrival, bullock/tractor availability, and seed credit access, resulting in a 30-day staggered sowing window across adjacent villages.

### 4. Agrochemical & Pesticide Intervention Regimes
* **Research Station Untreated Check:** Strict zero-spray policy throughout the season, allowing uninterrupted exponential pest population growth.
* **Commercial Farm:** Farmers typically apply 3 to 7 insecticide sprays of varying classes (organophosphates, synthetic pyrethroids, diamides), often triggered prematurely or late, creating artificial population crashes and resurgence cycles.

### 5. Scouting Consistency & Observer Bias
* **Research Station:** Conducted by trained graduate entomologists or ICAR technical officers using precision destructive dissection and calibrated magnification.
* **Commercial Farm:** Dependent on community pest monitors or mobile app submissions with varying diagnostic skill, lighting conditions, and inspection speeds.

### 6. Pest Population Density & Inoculum Pool
* **Research Station:** Maintained research farms frequently harbor high endemic pest populations year-round due to continuous host availability and adjacent unsprayed germplasm blocks.
* **Commercial Farm:** Initial early-season infestation is highly dependent on landscape-scale diapause survival, ginning mill proximity, and regional crop rotation history.

### 7. Pheromone Trap Placement & Plume Dynamics
* **Research Station:** Installed exactly 30 cm above crop canopy, unobstructed, with fresh septa replaced strictly every 21 days.
* **Commercial Farm:** Traps may be hung from field perimeter fence posts, tilted by monsoon winds, coated with agricultural dust, or left with expired lures.

### 8. Canopy Architecture & Phenological Microclimate
* **Research Station:** Optimized seed spacing, zero missing hills, and regular manual weeding create an open, uniform canopy.
* **Commercial Farm:** Patchy germination, weed competition, and variable intercropping (cotton + pigeonpea; soybean + maize) create dense microclimatic humidity pockets that accelerate fungal entomopathogens or sucking pest reproduction.

### 9. Surrounding Landscape Matrix
* **Research Station:** Surrounded by agricultural university research farms, orchards, and trial plots.
* **Commercial Farm:** Embedded in an agro-ecological mosaic of fallow wasteland, roadside alternate host weeds (*Abutilon indicum*, *Malvastrum coromandelianum*), and watercourses.

### 10. Edaphic Profile, Water Retention & Topography
* **Research Station:** High-input land preparation with graded bunding, artificial sub-surface drainage, and leveling.
* **Commercial Farm:** Heavy deep black cotton soils (Vertisols) subject to rapid waterlogging during heavy downpours, followed by severe moisture deficit and cracking during 10-day dry spells.

### 11. Observation Denominators & Measurement Paths
* **Research Station:** Standardized destructive sampling of exactly 20 bolls across 4 replications ($N=80$) or counting along 5 exact 1-meter ground rows.
* **Commercial Farm:** Pragmatic diagonal walk ("W" pattern) where scout counts affected plants per unit time or per 20 random steps.

---

## 3. Quantitative Domain Divergence Metrics

When prospective commercial field observations become available (Kharif 2027 sentinel pilot), the domain shift will be quantified using four statistical metrics:

### 3.1 Maximum Mean Discrepancy (MMD)
To measure the distribution distance between research plot covariates $X_S$ and commercial field covariates $X_T$:
$$\text{MMD}^2(\mathcal{D}_S, \mathcal{D}_T) = \frac{1}{n^2} \sum_{i=1}^n \sum_{j=1}^n k(x_i^S, x_j^S) - \frac{2}{nm} \sum_{i=1}^n \sum_{j=1}^m k(x_i^S, x_j^T) + \frac{1}{m^2} \sum_{i=1}^m \sum_{j=1}^m k(x_i^T, x_j^T)$$
where $k(\cdot, \cdot)$ is a Radial Basis Function (RBF) kernel parameterized on normalized weather and soil moisture features.

### 3.2 Wasserstein Distance / Earth Mover's Distance (EMD)
For univariate feature marginals (e.g. daily rainfall, relative humidity, maximum temperature, topsoil moisture):
$$\mathcal{W}_1(P_S, P_T) = \int_{-\infty}^{\infty} |F_S(u) - F_T(u)| \, du$$
quantifying the physical shift in environmental distributions between university stations and rural farm clusters.

### 3.3 Label Density Disparity ($\Delta Y$)
Comparing the marginal outbreak rate under identical climatic conditions:
$$\Delta Y = |P(Y=1 \mid \text{Station Plot}) - P(Y=1 \mid \text{Commercial Field})|$$
quantifying how much artificial research plot pressure inflates the apparent outbreak probability relative to commercial farming realities.

### 3.4 Population Stability Index (PSI)
Tracking covariate distribution drift across bi-weekly temporal slices:
$$\text{PSI} = \sum_{k=1}^K (P_{T,k} - P_{S,k}) \times \ln\left(\frac{P_{T,k}}{P_{S,k}}\right)$$
where $\text{PSI} > 0.25$ indicates severe domain shift requiring complete model recalibration.

---

## 4. Operational Transfer Governance Rules

1. **Strict Dataset Segregation:** Quarantined historical research trial data must remain in `data/raw/pest_surveillance/historical_transcriptions/` with tag `dataset_classification="HISTORICAL_RESEARCH_TRIAL"`. It must NEVER be co-mingled with prospective commercial data in `data/processed/pest_surveillance/`.
2. **No Unvalidated Transfer Learning:** No pre-trained weights, embeddings, or heuristic decision thresholds derived exclusively from research station micro-plots may be directly used for operational commercial decision-making without independent target-domain validation.
3. **Domain Comparison Milestone:** When the first 200 prospective sentinel field observations from the Kharif 2027 pilot are received, a formal **Domain Divergence Audit** will be computed using MMD and PSI before any combined descriptive analysis is permitted.

