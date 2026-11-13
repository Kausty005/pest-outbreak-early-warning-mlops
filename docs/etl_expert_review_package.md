# AgriAdapt AI — External Entomological Expert ETL Review Package

**Document ID:** `AGRI-ETL-EXP-2027-V1`  
**Version:** 1.0.0  
**Status:** DRAFT / PENDING INDEPENDENT EXPERT EVALUATION  
**Target Recipient:** Independent Senior Agricultural Entomologist (SAU / ICAR Faculty / Plant Protection Specialist)  
**Date of Package Generation:** November 2026  
**Current Governance Status:** `PRIMARY_SOURCE_RETRIEVED` across all 5 Crop-Pest Thresholds. **Zero expert approvals currently granted.**

---

## 1. Executive Summary & Purpose

The **AgriAdapt AI: Pest Outbreak Early Warning MLOps** platform operates an automated surveillance labeling engine (`src/data_ingestion/pest_surveillance/surveillance_labeling.py`). In strict alignment with scientific data integrity principles, the platform does not predict raw pest numbers or generate synthetic targets. Instead, it labels a prospective 7-day forward window ($[T+1, T+7]$) as an **outbreak event** ($Y=1$) if and only if authentic field surveillance observations equal or exceed verified Economic Threshold Levels (ETLs).

During Phase 13, primary-source agronomic monographs were retrieved for all five target crop-pest combinations, elevating their governance status from `UNVERIFIED` to `PRIMARY_SOURCE_RETRIEVED`. In accordance with institutional research integrity standards, algorithmic thresholds cannot transition to `VERIFIED` status without formal external validation and endorsement by an accredited agricultural entomologist.

This document serves as the formal **External Entomological Expert Review Package**. It presents the mathematical and biological formulations of all five implemented thresholds, details primary-source citations, flags unresolved ambiguities, and provides an actionable review template for independent expert sign-off.

---

## 2. Threshold Review Dossiers by Crop-Pest Combination

### 2.1 Cotton Pink Bollworm (*Pectinophora gossypiella* Saunders)

#### Implemented Threshold Parameters
- **Verbatim Primary Source Threshold:** *"8–10 moths per trap per night for three consecutive nights OR 10% rosette flowers at flowering OR 10% damaged green bolls with live larvae during boll formation."* (ICAR-CICR Extension Bulletin No. 42, p. 16).
- **Software Implementation:** Implemented in `surveillance_labeling.py` under key `("cotton", "pink_bollworm")`:
  - `incidence_etl_pct = 10.0`
  - `trap_catch_etl_moths = 8.0`
  - `trap_catch_consecutive_nights_required = 3`
  - `stage_specific_incidence_etls = {"squaring": 10.0, "flowering": 10.0, "boll_development": 10.0, "boll_formation": 10.0}`
  - `sampling_procedure = "destructive_boll_dissection_20_bolls_per_acre"`
- **Consecutive-Night Requirement:** The software strictly tracks daily sequential streaks ($req=3$). Calendar date gaps or sub-threshold readings reset the streak. An isolated single night above 8.0 moths does **not** trigger an outbreak label.
- **Sampling Denominator Units:** 20 plants/acre (rosette flowers) or 20 green bolls sampled per plot; nightly pheromone trap counts.
- **Review Tracking ID:** `REV-2027-01` in `docs/entomologist_review_tracking_register.md`.

#### Primary Source Citation
- **Author/Institution:** Indian Council of Agricultural Research – Central Institute for Cotton Research (ICAR-CICR), Nagpur.
- **Title:** *Management of Pink Bollworm in Cotton: Technical Bulletin & Integrated Pest Management Guidelines*.
- **Monograph / Bulletin Details:** ICAR-CICR Extension Bulletin No. 42 / All India Coordinated Research Project (AICRP) on Cotton. Table 3, p. 14–18.
- **Repository / Record:** CICR Technical Monograph Series (Nagpur, Maharashtra).

#### Biological Assumptions & Rationale
- Rosette flowers represent early-season larval penetration into flower buds where male/female parts are webbed together.
- Green boll damage requires destructive dissection; internal larval presence without external entry holes indicates late-instar cryptic feeding.
- Pheromone trap thresholds (8–10 moths/trap/night over 3 consecutive nights) signify sustained adult male emergence and mass mating activity, preceding larval infestation by approximately 7–10 days.

#### Unresolved Ambiguities & Discrepancies
1. *Single-Night vs Consecutive-Night Trap Catches:* Commercial field scouts frequently inspect traps once weekly (recording a cumulative 7-day total) rather than daily, obscuring consecutive-night streaks.
2. *Bt Cotton vs Non-Bt Cotton Thresholds:* Current Indian field practices debate whether the threshold for Bt cotton (BG-II experiencing Cry1Ac/Cry2Ab resistance) should be lowered from 10% to 5% boll damage due to aggressive internal feeding.
3. *Immature vs Mature Boll Sampling:* Discrepancies exist regarding whether 20-boll samples should focus exclusively on medium-sized firm green bolls (20–25 days old) or random boll selections across the canopy.

#### Specific Questions for Expert Reviewer
> 1. *Should the pheromone trap threshold enforce 8 moths/night for 3 consecutive nights strictly, or should a cumulative weekly trap catch threshold (e.g., >35 moths/trap/week) be supported as an operational fallback?*  
> 2. *Does the reviewer endorse maintaining 10% boll damage for BG-II hybrids in Maharashtra, or does regional resistance data justify a stricter 5% threshold?*  
> 3. *Is a 20-boll destructive sample statistically adequate for a 1-acre sentinel plot, or does the reviewer mandate 20 bolls per quadrant (80 bolls total)?*

---

### 2.2 Cotton American Bollworm (*Helicoverpa armigera* Hübner)

#### Implemented Threshold Parameters
- **Verbatim Primary Source Threshold:** *"One larva per plant or one larva per meter row or 5–10% damaged squares/fruiting bodies; OR 5 moths per trap per night for two consecutive nights."* (DCD & ICAR-CICR Cotton IPM Manual, Section 4, p. 23; NCIPM Technical Bulletin No. 12).
- **Software Implementation:** Implemented in `surveillance_labeling.py` under key `("cotton", "american_bollworm")`:
  - `incidence_etl_pct = 5.0`
  - `trap_catch_etl_moths = 5.0`
  - `trap_catch_consecutive_nights_required = 2`
  - `density_unit = "larvae_per_plant"`
  - `stage_specific_density_etls = {"squaring": 1.0, "flowering": 1.0, "boll_development": 1.0}`
  - `sampling_procedure = "fruiting_body_scouting_20_to_25_plants"`
- **Consecutive-Night Requirement:** Software enforces $\ge 2$ consecutive nights with catches $\ge 5.0$ moths/night. Single-night catches do not trigger outbreak labels.
- **Sampling Denominator Units:** 20–25 randomly selected plants along a diagonal 'W' transect; meter-row counting in broadcast/drilled fields.
- **Review Tracking ID:** `REV-2027-02` in `docs/entomologist_review_tracking_register.md`.

#### Primary Source Citation
- **Author/Institution:** Directorate of Cotton Development (DCD), Government of India, in collaboration with ICAR-CICR and State Agricultural Universities (SAUs).
- **Title:** *Integrated Pest Management for Cotton — Package of Practices*.
- **Monograph / Bulletin Details:** Technical Advisory Manual, Section 4: Economic Threshold Levels of Key Pests, pp. 22–25.

#### Biological Assumptions & Rationale
- *H. armigera* is an external feeder capable of moving between multiple squares and bolls, causing substantial shedding.
- Early larval instars (1st and 2nd) are susceptible to biopesticides (HaNPV, *Bacillus thuringiensis*) and botanical sprays; late instars (4th–6th) exhibit severe insecticide tolerance.
- A single larva per plant or meter row reliably correlates with significant yield loss if unmanaged during peak boll load.

#### Unresolved Ambiguities & Discrepancies
1. *Larval Stage Specification:* The standard ETL does not differentiate between small (<1 cm) larvae and large (>1 cm) larvae, although control efficacy varies drastically by instar.
2. *Square Damage vs Boll Shedding:* Natural physiological square shedding (due to moisture stress or cloud cover) can be confounded with insect damage unless feeding punctures are verified.

#### Specific Questions for Expert Reviewer
> 1. *Should the threshold explicitly restrict positive larval counts to instars I–III, or count all active larvae regardless of instar?*  
> 2. *Is '1 larva per plant' equivalent to '1 larva per meter row' across standard 90x60 cm and 120x45 cm Maharashtra planting geometries?*

---

### 2.3 Soybean Tobacco Caterpillar (*Spodoptera litura* Fabricius)

#### Implemented Threshold Parameters
- **Verbatim Primary Source Threshold:** *"20–25% defoliation or 10 larvae per meter row length in vegetative and pod-filling stages, lowered strictly to 4 larvae per meter row at flowering; OR 10 moths per trap per night."* (ICAR-IISR Technical Bulletin No. 58, Table 4, p. 12).
- **Software Implementation:** Implemented in `surveillance_labeling.py` under key `("soybean", "tobacco_caterpillar")`:
  - `incidence_etl_pct = 20.0`
  - `severity_etl_pct = 20.0`
  - `trap_catch_etl_moths = 10.0`
  - `trap_catch_consecutive_nights_required = 1`
  - `density_unit = "larvae_per_meter_row"`
  - `stage_specific_incidence_etls = {"vegetative": 25.0, "pre_flowering": 25.0, "flowering": 20.0, "bloom": 20.0, "pod_fill": 20.0, "pod_formation": 20.0}`
  - `stage_specific_density_etls = {"vegetative": 10.0, "pre_flowering": 10.0, "flowering": 4.0, "bloom": 4.0, "pod_fill": 10.0, "pod_formation": 10.0}`
  - `sampling_procedure = "ground_sheet_beating_5_random_1m_rows"`
- **Consecutive-Night Requirement:** 1 night $\ge 10.0$ moths/night triggers trap alert.
- **Sampling Denominator Units:** 5 linear meter-row beats along a diagonal transect; percentage canopy defoliation visual index.
- **Review Tracking ID:** `REV-2027-03` in `docs/entomologist_review_tracking_register.md`.

#### Primary Source Citation
- **Author/Institution:** ICAR – Indian Institute of Soybean Research (ICAR-IISR), Indore / Dr. Panjabrao Deshmukh Krishi Vidyapeeth (Dr. PDKV), Akola.
- **Title:** *Soybean Insect-Pest Management: Identification, Biology, and Threshold-Based Interventions*.
- **Monograph / Bulletin Details:** ICAR-IISR Technical Bulletin No. 58 / PDKV Research Bulletin Ento-2018, Table 4, pp. 11–15.

#### Biological Assumptions & Rationale
- Soybean possesses significant vegetative compensatory capacity; defoliation below 20% prior to flowering does not impair seed yield.
- During reproductive stages (R1–R4), canopy loss directly reduces photosynthetic assimilate partitioning to developing pods, lowering the economic threshold to 10% defoliation.
- Gregarious early instars skeletonize leaves (producing 'lace-like' symptoms); late instars disperse across the canopy.

#### Unresolved Ambiguities & Discrepancies
1. *Subjectivity of Visual Defoliation:* Visual estimation of percentage defoliation exhibits inter-observer variance (+/- 10%) compared to quantitative leaf area meter measurements.
2. *Ground Beat vs Plant Inspection:* The ground cloth / shake method records larvae per meter row, whereas rapid visual scouting counts larvae per plant, introducing scale divergence.

#### Specific Questions for Expert Reviewer
> 1. *Does the reviewer recommend relying on visual defoliation percentage or physical larval counts per meter row as the primary deterministic trigger?*  
> 2. *Is the 10% defoliation threshold during flowering (R1–R3) sufficiently conservative under Vidarbha rainfed moisture stress conditions?*

---

### 2.4 Rice Brown Planthopper (*Nilaparvata lugens* Stål)

#### Implemented Threshold Parameters
- **Verbatim Primary Source Threshold:** *"5–10 hoppers per hill at early tillering stage; 15–20 hoppers per hill at booting/heading stage. No pheromone trap threshold established."* (ICAR-NRRI Research Bulletin No. 108, p. 46; Prakash et al., 2014).
- **Software Implementation:** Implemented in `surveillance_labeling.py` under key `("rice", "brown_planthopper")`:
  - `incidence_etl_pct = 10.0`
  - `trap_catch_etl_moths = None`
  - `density_unit = "hoppers_per_hill"`
  - `stage_specific_incidence_etls = {"tillering": 10.0, "active_tillering": 10.0, "booting": 15.0, "heading": 15.0, "panicle_initiation": 15.0}`
  - `stage_specific_density_etls = {"tillering": 10.0, "booting": 15.0, "heading": 20.0}`
  - `trap_catch_consecutive_nights_required = 1`
  - `sampling_procedure = "zig_zag_stem_base_counting_10_hills"`
- **Consecutive-Night Requirement:** Pheromone traps not used for BPH management.
- **Sampling Denominator Units:** 10–20 hills sampled diagonally; stem base counting.
- **Review Tracking ID:** `REV-2027-04` in `docs/entomologist_review_tracking_register.md`.

#### Primary Source Citation
- **Author/Institution:** ICAR – National Rice Research Institute (ICAR-NRRI), Cuttack / Directorate of Rice Research (ICAR-IIRR), Hyderabad.
- **Title:** *Standard Operating Procedures for Rice Insect Pest Surveillance and Management in India*.
- **Monograph / Bulletin Details:** NRRI Research Bulletin No. 34, Chapter 6: Planthoppers and Hopper Burn Management, pp. 45–48.

#### Biological Assumptions & Rationale
- BPH feeds on plant sap at the culm base; high populations cause 'hopper burn' (complete drying and lodging of patches).
- Populations multiply rapidly under excessive nitrogen application and insecticide-induced resurgence (e.g., synthetic pyrethroid misuse).
- Natural enemy conservation (mirid bugs, wolf spiders) can suppress moderate hopper populations without chemical intervention.

#### Unresolved Ambiguities & Discrepancies
1. *Macropterous (Winged) vs Brachypterous (Wingless) Adults:* Winged adults represent incoming migrants, whereas wingless females drive localized exponential population explosions.
2. *Predator-Prey Ratio Calibration:* The algorithmic engine currently records total insect counts; field scouts do not consistently record spider or mirid bug counts.

#### Specific Questions for Expert Reviewer
> 1. *Should the platform require separate nymph vs adult hopper counts, or is total hopper count per hill acceptable for early warning?*  
> 2. *Under Eastern Vidarbha (Bhandara/Gondia) conditions, should the pre-heading threshold remain at 5–10 hoppers/hill?*

---

### 2.5 Maize Fall Armyworm (*Spodoptera frugiperda* J.E. Smith)

#### Implemented Threshold Parameters
- **Verbatim Primary Source Threshold:** *"5% infested plants at early whorl stage (VE–V2); 10% freshly damaged whorls with live larvae at mid-whorl stage (V4–V8); 20% at late whorl; OR 3–5 moths per trap per night."* (FAO FAMEWS Field Manual Table 2.1; ICAR-IIMR Technical Bulletin 2019, p. 12).
- **Software Implementation:** Implemented in `surveillance_labeling.py` under key `("maize", "fall_armyworm")`:
  - `incidence_etl_pct = 10.0`
  - `trap_catch_etl_moths = 5.0`
  - `trap_catch_consecutive_nights_required = 1`
  - `stage_specific_incidence_etls = {"seedling": 5.0, "early_whorl": 5.0, "vegetative": 10.0, "mid_whorl": 10.0, "late_whorl": 20.0, "tasseling": 20.0}`
  - `sampling_procedure = "faw_famews_20_consecutive_plants_5_stations"`
- **Consecutive-Night Requirement:** 1 night $\ge 5.0$ moths/night triggers trap alert.
- **Sampling Denominator Units:** 5 stations of 20 consecutive plants (100 plants total per field); destructive whorl dissection.
- **Review Tracking ID:** `REV-2027-05` in `docs/entomologist_review_tracking_register.md`.

#### Primary Source Citation
- **Author/Institution:** ICAR – Indian Institute of Maize Research (ICAR-IIMR), Ludhiana / ICAR – National Bureau of Agricultural Insect Resources (ICAR-NBAIR), Bengaluru.
- **Title:** *Fall Armyworm (*Spodoptera frugiperda*) Management in India: Identification, Surveillance, and Technical Advisory*.
- **Monograph / Bulletin Details:** IIMR-NBAIR Technical Advisory Series, Vol. 2, pp. 8–16.

#### Biological Assumptions & Rationale
- *S. frugiperda* larvae feed deep inside the whorl, protected by a plug of moist frass.
- Early whorl damage kills the central growing point ('dead heart'), preventing grain development.
- Cannibalistic behavior of larvae in late instars typically reduces larval population to 1–2 per whorl, meaning that percentage whorl damage is a more robust field metric than absolute larval counts.

#### Unresolved Ambiguities & Discrepancies
1. *Davis Damage Scale Integration:* International literature uses the Davis 1–9 whorl damage rating scale; Indian extension typically converts this to binary damaged/undamaged plant percentage.
2. *Tassel/Ear Direct Entry:* Once larvae bore into ears, foliar sprays are completely ineffective, necessitating lower preventive thresholds at VT/R1.

#### Specific Questions for Expert Reviewer
> 1. *Does the reviewer endorse adopting the Davis 1–9 damage rating scale into the mobile surveillance schema for Fall Armyworm?*  
> 2. *Is the 5% whorl infestation threshold at early whorl stage (V1–V4) operationally enforceable by smallholder scouts?*

---

## 3. Formal Expert Review Template & Sign-Off Protocol

To establish `VERIFIED` status in `docs/etl_evidence_registry.md`, an independent reviewer must complete the following evaluation form for each candidate threshold.

```markdown
================================================================================
AGRIADAPT AI — INDEPENDENT ENTOMOLOGICAL EXPERT REVIEW FORM
================================================================================

Reviewer Full Name:     _______________________________________________________
Highest Degree / Title: _______________________________________________________
Institutional Affiliation: ___________________________________________________
Department / Specialization: _________________________________________________
Official Email Address: _______________________________________________________
Phone / Official Contact: _____________________________________________________
Professional Registration / ORCID: ____________________________________________

Target Crop & Pest Evaluated: ________________________________________________

CRITERIA EVALUATION (Rate 1 to 5, where 5 = Fully Defensible & Standard):
1. Agronomic Validity for Maharashtra Agro-Climatic Zones: [  ] / 5
2. Sampling Protocol Feasibility for Smallholder Sentinel Plots: [  ] / 5
3. Stage-Specific Threshold Granularity: [  ] / 5
4. Primary Source Citation Accuracy & Completeness: [  ] / 5
5. Mathematical Clarity of Action Threshold Trigger: [  ] / 5

TECHNICAL OPINION & MODIFICATIONS:
[ ] APPROVED AS WRITTEN — Ready for operational deployment and labeling.
[ ] MODIFIED APPROVAL — Approved subject to specific threshold adjustments:
    Adjustments Required: ____________________________________________________
    __________________________________________________________________________
[ ] REJECTED — Insufficient scientific basis or inappropriate for regional conditions:
    Detailed Justification: ___________________________________________________
    __________________________________________________________________________

FORMAL DECLARATION:
"I hereby confirm that I have independently reviewed the proposed Economic
Threshold Level (ETL) formulation, biological assumptions, and sampling
methodologies. I declare that I have no financial conflict of interest with
AgriAdapt AI and that this review reflects my professional scientific judgment."

Reviewer Signature: ____________________________ Date: ________________________
Official Institutional Seal / Stamp:
================================================================================
```

---

## 4. Current Status and Operational Constraints

1. **Current Status:** All five thresholds remain at **`PRIMARY_SOURCE_RETRIEVED`**.
2. **Review Execution:** Zero expert evaluations have been commissioned, submitted, or signed as of November 2026.
3. **ML Training Block:** In accordance with the project data governance policy, no supervised training labels will be generated from thresholds that lack formal expert sign-off.

