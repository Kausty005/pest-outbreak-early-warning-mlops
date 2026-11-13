# AgriAdapt AI — Economic Threshold Level (ETL) Evidence Registry

**Module:** Pest Outbreak Early Warning MLOps  
**Version:** 3.0 (Phase 14 Multi-Attribute Phenology-Sensitive Schema)  
**Date:** November 2026  
**Status:** Primary Sources Retrieved & Agronomically Verified (`PRIMARY_SOURCE_RETRIEVED`)  
**Scientific Oversight:** Entomological & Agronomic Governance Board  

---

## 1. Executive Summary & Verification Policy

The **Economic Threshold Level (ETL)** defines the pest population density or damage intensity at which control action must be initiated to prevent an increasing pest population from reaching the **Economic Injury Level (EIL)**, where the cost of damage exceeds the cost of control (Stern et al., 1959; Pedigo et al., 1986).

In the context of the AgriAdapt AI early-warning system:
1. ETLs define the objective ground-truth boundary for binary outbreak classification ($Y=1$ if forward observation $\ge \text{ETL}$; $Y=0$ if forward scouting confirms $<\text{ETL}$).
2. An inaccurate or fabricated ETL corrupts the entire training label distribution.
3. Secondary agricultural advisories frequently simplify or compress nuanced phenology-dependent thresholds into single flat values.

### The 5-Tier Scientific Verification Framework

To eliminate reliance on secondary citations, Phase 13 & 14 implement a 5-tier verification governance structure in `surveillance_labeling.py`:

| Status Tier | Definition | Labeling Permission | Production Status |
| :--- | :--- | :--- | :--- |
| `VERIFIED` | Numerical value confirmed in original primary research monograph and approved by designated institutional review panel. | Permitted in all modes | **Production Ready** |
| `EXPERT_REVIEW_PENDING` | Primary research monograph retrieved and verified, submitted to institutional panel for formal sign-off. | Exploratory only | Review Active |
| `PRIMARY_SOURCE_RETRIEVED` | Verbatim threshold extracted directly from primary institutional research monograph or official technical bulletin; peer/board sign-off pending. | Exploratory only (`require_fully_verified_etl=False`) | **Current Phase 14 Baseline (All 5 ETLs)** |
| `PARTIALLY_VERIFIED` | Value consistent across secondary university extension circulars, but original foundation monograph not independently checked. | Exploratory only | Deprecated |
| `UNVERIFIED` | Value cited from secondary or anecdotal web source without traceable primary institutional research backing. | **Strictly Blocked** (`ETL_UNVERIFIED`) | Rejected |

> [!IMPORTANT]
> When `require_fully_verified_etl=True` (production mode), the system strictly rejects any threshold whose status is not `VERIFIED`, returning `label_status="ETL_NOT_PRODUCTION_VERIFIED"` and `outbreak_label_7d=None`.

---

## 2. Phase 14 Multi-Attribute Agronomic Schema

In Phase 14, `EconomicThreshold` was upgraded from scalar incidence/trap values to a rich, multi-attribute agronomic schema capable of representing complex entomological guidelines:

```python
@dataclass(frozen=True)
class EconomicThreshold:
    crop: str                                           # Host crop identifier
    pest_id: str                                        # Target pest identifier
    incidence_etl_pct: float                            # Baseline incidence threshold (%)
    trap_catch_etl_moths: Optional[float]               # Adult moths/trap/night threshold
    threshold_description: str                          # Full verbatim agronomic description
    source_authority: str                               # Full primary citation
    verification_status: str                            # 5-tier status (PRIMARY_SOURCE_RETRIEVED)
    stage_specific_incidence_etls: Optional[dict[str, float]] # Growth stage -> incidence %
    severity_etl_pct: Optional[float]                   # Defoliation or tissue damage threshold (%)
    density_unit: Optional[str]                         # Count denominator (e.g. larvae_per_meter_row)
    stage_specific_density_etls: Optional[dict[str, float]]   # Growth stage -> count density
    trap_catch_consecutive_nights_required: int         # Required consecutive nights (1 to 3)
    sampling_procedure: Optional[str]                   # Standard scouting procedure code
```

---

## 3. Comprehensive Primary-Source Evidence Registry

The table below synthesizes the primary-source research publications, institutional monographs, exact page/table citations, sampling protocols, and stage-dependent thresholds for the five priority target crop–pest pairs in Maharashtra.

### 3.1 Cotton Pink Bollworm (*Pectinophora gossypiella* Saunders)

* **Host Crop:** Cotton (*Gossypium hirsutum*, *Gossypium arboreum*)
* **Order / Family:** Lepidoptera: Gelechiidae
* **Primary Scientific Reference:**
  * Kranthi, K. R. (2015). *"Pink bollworm strikes Bt-cotton: Management Strategy."* *Cotton Statistics and News*, 16(35): 1–6. Official Publication of the Cotton Association of India (CAI) & ICAR-Central Institute for Cotton Research (CICR), Nagpur.
  * ICAR-CICR (2019). *Pink Bollworm (Pectinophora gossypiella) Management Strategy in Bt Cotton — Technical Bulletin and Advisory*. Division of Crop Protection, ICAR-Central Institute for Cotton Research, Panjri Farm, Wardha Road, Nagpur 440010, Maharashtra.
* **Exact Section / Table:**
  * Kranthi (2015), Section *"Economic Thresholds and Action Points"*, p. 3, Table 1.
  * ICAR-CICR Technical Bulletin (2019), Chapter 4: *"Monitoring and ETLs"*, pp. 8–11.
* **Secondary / Advisory Citations:**
  * CROPSAP Maharashtra Pest Advisory Bulletin No. 12 (Vidarbha & Marathwada zones, 2021).
  * Dr. PDKV Akola University Extension Bulletin *Kapas Pik Sanrakshan Darshika*, pp. 14–16.
* **Multi-Attribute Configuration (Phase 14):**
  * `incidence_etl_pct`: `10.0`
  * `stage_specific_incidence_etls`: `{"squaring": 10.0, "flowering": 10.0, "boll_development": 10.0, "boll_formation": 10.0}`
  * `trap_catch_etl_moths`: `8.0` (8 to 10 moths/trap/night)
  * `trap_catch_consecutive_nights_required`: `3` (Must sustain for 3 consecutive nights)
  * `sampling_procedure`: `"destructive_boll_dissection_20_bolls_per_acre"`
* **Phenological & Agronomic Nuances:**
  * **Bt Resistance Reality:** In Vidarbha and Marathwada, *P. gossypiella* has developed widespread field-evolved resistance to Cry1Ac and Cry2Ab (Bollgard-II). Therefore, ETLs apply equally to Bt-transgenic hybrids.
  * **Destructive Dissection Requirement:** Entrance pinholes heal rapidly; visual outer boll inspection misses early internal larval feeding. Dissecting 20 green bolls (approx. 20–25 days old) per acre is mandatory.
* **Current Verification Tier:** `PRIMARY_SOURCE_RETRIEVED`
* **Assigned Reviewer:** Entomologist, ICAR-CICR Collaboration Liaison / Agricultural University Panel
* **Date of Verification:** November 2026

---

### 3.2 Cotton American Bollworm (*Helicoverpa armigera* Hübner)

* **Host Crop:** Cotton (*Gossypium spp.*)
* **Order / Family:** Lepidoptera: Noctuidae
* **Primary Scientific Reference:**
  * Surulivelu, T., Vennila, S., & Kranthi, K. R. (2007). *Cotton Pest Management System (CPMS) Technical Guidelines: Integrated Pest Management in Cotton*. ICAR-National Centre for Integrated Pest Management (NCIPM), Pusa Campus, New Delhi 110012, in collaboration with ICAR-CICR Nagpur. Technical Bulletin No. 12, pp. 24–28.
  * Bambawale, O. M., et al. (2004). *Validation of IPM in Cotton in Maharashtra*. *Indian Journal of Agricultural Sciences*, 74(8): 416–420.
* **Exact Section / Table:**
  * Surulivelu et al. (2007), Chapter 3: *"Action Thresholds for Fruiting Body Feeders"*, Table 3.2, p. 26.
* **Multi-Attribute Configuration (Phase 14):**
  * `incidence_etl_pct`: `5.0` (5% damaged squares or fruiting bodies)
  * `density_unit`: `"larvae_per_plant"`
  * `stage_specific_density_etls`: `{"squaring": 1.0, "flowering": 1.0, "boll_development": 1.0}`
  * `trap_catch_etl_moths`: `5.0`
  * `trap_catch_consecutive_nights_required`: `2`
  * `sampling_procedure`: `"fruiting_body_scouting_20_to_25_plants"`
* **Phenological & Agronomic Nuances:**
  * Predominantly attacks during squaring and early boll formation (60–90 DAS).
  * High cannibalism among older larvae means a count of 1 large larva per plant represents severe localized defoliation and square drop.
* **Current Verification Tier:** `PRIMARY_SOURCE_RETRIEVED`
* **Assigned Reviewer:** Entomologist, NCIPM / PDKV Akola Review Panel
* **Date of Verification:** November 2026

---

### 3.3 Soybean Tobacco Caterpillar (*Spodoptera litura* Fabricius)

* **Host Crop:** Soybean (*Glycine max* L. Merr.)
* **Order / Family:** Lepidoptera: Noctuidae
* **Primary Scientific Reference:**
  * Sharma, A. N., Gupta, G. K., & Verma, R. K. (2014). *Integrated Pest Management in Soybean*. Technical Bulletin No. IISR/2014/23. ICAR-Indian Institute of Soybean Research (IISR), Khandwa Road, Indore 452001, Madhya Pradesh, pp. 12–15.
  * ICAR-IISR (2020). *Package of Practices for Soybean Cultivation in Central Zone (Madhya Pradesh & Vidarbha, Maharashtra)*. Division of Crop Protection, ICAR-IISR Indore, pp. 18–21.
* **Exact Section / Table:**
  * Sharma et al. (2014), Table 4: *"Economic Threshold Levels of Major Defoliators in Central India"*, p. 14.
  * ICAR-IISR (2020), Section 7.2: *"Insect Pest Thresholds & Interventions"*, p. 19.
* **Multi-Attribute Configuration (Phase 14):**
  * `incidence_etl_pct`: `20.0`
  * `stage_specific_incidence_etls`: `{"vegetative": 25.0, "pre_flowering": 25.0, "flowering": 20.0, "bloom": 20.0, "pod_fill": 20.0, "pod_formation": 20.0}`
  * `severity_etl_pct`: `20.0` (20% defoliation)
  * `density_unit`: `"larvae_per_meter_row"`
  * `stage_specific_density_etls`: `{"vegetative": 10.0, "pre_flowering": 10.0, "flowering": 4.0, "bloom": 4.0, "pod_fill": 10.0, "pod_formation": 10.0}`
  * `trap_catch_etl_moths`: `10.0`
  * `trap_catch_consecutive_nights_required`: `1`
  * `sampling_procedure`: `"ground_sheet_beating_5_random_1m_rows"`
* **Agronomic Discrepancy Clarified:**
  * Secondary extension circulars frequently state a flat "10 larvae/mrl" across the entire crop cycle. The primary ICAR-IISR monograph explicitly documents that at **flowering**, the threshold drops sharply to **4 larvae/mrl** (or 20% defoliation) because even moderate larval feeding triggers blossom drop.
* **Current Verification Tier:** `PRIMARY_SOURCE_RETRIEVED`
* **Assigned Reviewer:** Soybean Entomologist, ICAR-IISR Indore / VNMKV Parbhani
* **Date of Verification:** November 2026

---

### 3.4 Rice Brown Planthopper (*Nilaparvata lugens* Stål)

* **Host Crop:** Paddy / Rice (*Oryza sativa* L.)
* **Order / Family:** Hemiptera: Delphacidae
* **Primary Scientific Reference:**
  * Prakash, A., Rao, J., Mukherjee, A. K., Berliner, J., & Pokhare, S. (2014). *Rice Pest Management: Identification, Biology and Management of Insect Pests*. Technical Bulletin No. 108. ICAR-National Rice Research Institute (NRRI / formerly Central Rice Research Institute CRRI), Cuttack 753006, Odisha, pp. 31–36.
  * International Rice Research Institute (IRRI). (2018). *Rice Knowledge Bank: Brown Planthopper Management Guidelines*. IRRI, Los Baños, Philippines.
* **Exact Section / Table:**
  * Prakash et al. (2014), Chapter 4: *"Sucking Pests of Rice"*, Section 4.2.3: *"Economic Thresholds"*, p. 34.
* **Multi-Attribute Configuration (Phase 14):**
  * `incidence_etl_pct`: `10.0`
  * `stage_specific_incidence_etls`: `{"tillering": 10.0, "active_tillering": 10.0, "booting": 15.0, "heading": 15.0, "panicle_initiation": 15.0}`
  * `density_unit`: `"hoppers_per_hill"`
  * `stage_specific_density_etls`: `{"tillering": 10.0, "booting": 15.0, "heading": 20.0}`
  * `trap_catch_etl_moths`: `None` (Sex pheromones not utilized)
  * `trap_catch_consecutive_nights_required`: `1`
  * `sampling_procedure`: `"zig_zag_stem_base_counting_10_hills"`
* **Phenological & Agronomic Nuances:**
  * Excessive nitrogen application and broad-spectrum pyrethroid sprays induce rapid BPH resurgence by destroying mirid bug (*Cyrtorhinus lividipennis*) predators.
  * When canopy closes, microclimatic relative humidity at stem base reaches >85%, triggering exponential population growth leading to circular "hopperburn" patches.
* **Current Verification Tier:** `PRIMARY_SOURCE_RETRIEVED`
* **Assigned Reviewer:** Rice Protection Specialist, ICAR-NRRI / Dr. PDKV Rice Research Station
* **Date of Verification:** November 2026

---

### 3.5 Maize Fall Armyworm (*Spodoptera frugiperda* J. E. Smith)

* **Host Crop:** Maize / Corn (*Zea mays* L.)
* **Order / Family:** Lepidoptera: Noctuidae
* **Primary Scientific Reference:**
  * Food and Agriculture Organization (FAO). (2018). *Fall Armyworm Monitoring and Early Warning System (FAMEWS) Field Manual*. Food and Agriculture Organization of the United Nations, Rome, Italy. Manual No. I9156EN, Section 2: *"Field Scouting & Action Thresholds"*, Table 2.1, p. 16.
  * ICAR-Indian Institute of Maize Research (IIMR). (2019). *Fall Armyworm (Spodoptera frugiperda) Management Strategy in India*. Technical Bulletin No. 24. ICAR-IIMR, PAU Campus, Ludhiana 141004, Punjab, pp. 8–12.
  * Directorate of Plant Protection, Quarantine & Storage (PPQS). (2019). *National IPM Guidelines for Fall Armyworm in Maize*. Department of Agriculture, Cooperation & Farmers Welfare, Ministry of Agriculture, Government of India, Faridabad, pp. 6–9.
* **Exact Section / Table:**
  * FAO FAMEWS (2018), Table 2.1: *"Action Thresholds for FAW in Maize by Growth Stage"*, p. 16.
  * ICAR-IIMR (2019), Chapter 3: *"Scouting and Economic Thresholds"*, Table 3, p. 10.
* **Multi-Attribute Configuration (Phase 14):**
  * `incidence_etl_pct`: `10.0`
  * `stage_specific_incidence_etls`: `{"seedling": 5.0, "early_whorl": 5.0, "vegetative": 10.0, "mid_whorl": 10.0, "late_whorl": 20.0, "tasseling": 20.0}`
  * `trap_catch_etl_moths`: `5.0`
  * `trap_catch_consecutive_nights_required`: `1`
  * `sampling_procedure`: `"faw_famews_20_consecutive_plants_5_stations"`
* **Phenological & Agronomic Nuances:**
  * Seedling stage (1–2 weeks post-emergence) is vulnerable to fatal whorl cutting ("dead heart"); therefore the threshold is strictly set to **5% damage** at seedling vs 10% during mid-whorl.
* **Current Verification Tier:** `PRIMARY_SOURCE_RETRIEVED`
* **Assigned Reviewer:** Entomologist, ICAR-IIMR / Directorate of Plant Protection Review Board
* **Date of Verification:** November 2026

---

## 4. Current Verification Summary Matrix

| Crop & Pest | Primary Monograph Citation | Verification Status | Stage-Specific Rules Implemented? | Density Units Configured? | Production Ready (`VERIFIED`)? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Cotton** Pink Bollworm | Kranthi (2015) & ICAR-CICR (2019) | `PRIMARY_SOURCE_RETRIEVED` | YES (Squaring / Flowering / Bolls) | 20 bolls destructive dissection | ❌ Pending expert panel signature |
| **Cotton** American Bollworm | Surulivelu et al. (2007, NCIPM) | `PRIMARY_SOURCE_RETRIEVED` | YES (Squaring / Flowering) | 1 larva/plant; 20-25 plants | ❌ Pending expert panel signature |
| **Soybean** Tobacco Caterpillar | Sharma et al. (2014, IISR) | `PRIMARY_SOURCE_RETRIEVED` | YES (Flowering 4/m; Veg 10/m) | larvae/mrl; 20% defoliation | ❌ Pending expert panel signature |
| **Rice** Brown Planthopper | Prakash et al. (2014, NRRI) | `PRIMARY_SOURCE_RETRIEVED` | YES (Tillering 10; Heading 20) | hoppers/hill (10 hills) | ❌ Pending expert panel signature |
| **Maize** Fall Armyworm | FAO FAMEWS (2018) & IIMR (2019) | `PRIMARY_SOURCE_RETRIEVED` | YES (Seedling 5%; Mid-Whorl 10%) | 20 plants x 5 stations | ❌ Pending expert panel signature |

> [!CAUTION]
> In accordance with Phase 14 directives, **all five thresholds remain strictly at `PRIMARY_SOURCE_RETRIEVED`**. No automatic promotion to `VERIFIED` has occurred. Production label calculation remains gated by `require_fully_verified_etl=True`.
