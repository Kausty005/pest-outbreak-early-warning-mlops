# Authentic Pest Surveillance Data Collection & Ingestion Guide

**Project:** AgriAdapt AI / Pest Outbreak Early Warning MLOps  
**Component:** Ground-Truth Surveillance Data Acquisition & Ingestion Pipeline  
**Target Region:** Maharashtra, India  
**Target Crops:** Cotton (*Gossypium hirsutum*), Soybean (*Glycine max*), Rice (*Oryza sativa*), Maize (*Zea mays*)  
**Version:** 1.0 (November 2026)

---

## 1. Purpose & Guiding Principles

This guide outlines the protocol for acquiring, formatting, validating, and ingesting authentic agricultural pest surveillance data into AgriAdapt AI. 

> [!IMPORTANT]
> **STRICT SCIENTIFIC INVARIANTS:**
> 1. **Zero Data Fabrication:** No synthetic, simulated, or rule-generated surrogate surveillance records may be introduced into this pipeline.
> 2. **Preserve Missing Values:** If a measurement was not recorded in the field (e.g. pheromone trap catches on a visual scouting plot, or topsoil moisture on a roving survey), the field **must remain completely blank (empty)**. Under NO circumstances should missing fields be filled with zeros (`0`) or imputed averages.
> 3. **Non-Inference of Non-Occurrence:** An unmonitored farm or missing date must never be interpreted as "zero pest incidence" or "no outbreak". Negative training labels require active, documented scouting confirming sub-ETL levels.

---

## 2. Authoritative Data Sources in Maharashtra

Surveillance records must originate from recognized, accredited agricultural research or government institutions:

1. **CROPSAP Maharashtra (Crop Pest Surveillance and Advisory Project):**
   - *Authority:* Commissionerate of Agriculture, Government of Maharashtra (Pune).
   - *Data Assets:* Weekly fixed-plot (Monday) and roving-plot (Thursday) scouting across ~350 talukas.
   - *Access Procedure:* Formal submission of an institutional research proposal and Non-Disclosure Agreement (NDA) to the Director of Agriculture (Extension & Training), Central Building, Pune 411001 (`cropsap.maha@gov.in`).
2. **ICAR-NCIPM (National Research Centre for Integrated Pest Management):**
   - *Authority:* Indian Council of Agricultural Research, New Delhi.
   - *Data Assets:* National Cotton Pest Management System (CPMS) and multi-state pest tracking.
   - *Access Procedure:* Formal research data-sharing request via the Director, ICAR-NCIPM, Pusa Campus, New Delhi 110012 (`director.ncipm@icar.gov.in`).
3. **ICAR-CICR (Central Institute for Cotton Research, Nagpur):**
   - *Authority:* Division of Crop Protection, ICAR-CICR Nagpur.
   - *Data Assets:* Weekly pheromone trap catches (moths/trap/night) and green boll destructive dissection data from Vidarbha Vertisol tracts.
   - *Access Procedure:* Collaborative Research Project (CRP) agreement with ICAR-CICR (`cicrnagpur@gmail.com`).
4. **State Agricultural Universities (SAUs) & Research Stations:**
   - *Dr. PDKV Akola:* RARS Amravati, ARS Yavatmal, Cotton Research Station Akola.
   - *VNMKV Parbhani:* Cotton and Soybean Entomology Research Plots.
   - *MPKV Rahuri:* Oilseeds and Cereals Research Stations (Jalgaon, Pune).
   - *Access Procedure:* Research data access request to the Director of Research of the respective university.

---

## 3. Standardized Surveillance Schema & Field Dictionary

All submissions must conform to the standard template located at:  
`data/raw/pest_surveillance/surveillance_data_template.csv`

| Column Name | Data Type | Requirement | Valid Range / Format | Unit / Standard | Description & Collection Rule |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `observation_id` | String | Mandatory | Alphanumeric (e.g. `CR-2023-NGP-001`) | Unique ID | Unique identifier for the individual scouting observation. |
| `observation_date` | Date | Mandatory | `YYYY-MM-DD` | ISO 8601 | Exact calendar date on which the field inspection occurred. |
| `district` | String | Mandatory | `Nagpur`, `Amravati`, `Yavatmal`, `Jalgaon`, etc. | Text | Administrative district in Maharashtra. |
| `taluka` | String | Optional | e.g. `Hingna`, `Katol`, `Chandur` | Text | Sub-district or administrative block. |
| `village` | String | Optional | e.g. `Kanhan`, `Wadgaon` | Text | Village or gram panchayat name. |
| `latitude` | Float | Mandatory | `15.6000` to `22.1000` | WGS84 Degrees | Decimal latitude. Must lie within Maharashtra geographical boundaries. |
| `longitude` | Float | Mandatory | `72.6000` to `80.9000` | WGS84 Degrees | Decimal longitude. Must lie within Maharashtra geographical boundaries. |
| `crop` | String | Mandatory | `cotton`, `soybean`, `rice`, `maize` | Lowercase Text | Target host crop. |
| `crop_variety` | String | Optional | e.g. `Bt BG-II`, `JS-335`, `PKV-Tara` | Text | Commercial hybrid, cultivar, or germplasm accession. |
| `pest_common_name` | String | Mandatory | e.g. `Pink Bollworm`, `Tobacco Caterpillar` | Text | Common agronomic name of the monitored pest. |
| `pest_scientific_name` | String | Optional | e.g. `Pectinophora gossypiella` | Binomial Latin | Scientific Latin nomenclature. |
| `pest_incidence_pct` | Float | Conditional* | `0.0` to `100.0` | Percentage (%) | Percentage of plants, leaves, or organs infested. **Leave blank if unmeasured.** |
| `pest_severity_pct` | Float | Conditional* | `0.0` to `100.0` | Percentage (%) | Degree of tissue loss or defoliation severity. **Leave blank if unmeasured.** |
| `trap_type` | String | Optional | `pheromone_delta`, `light_trap`, `none` | Category | Type of trap used for insect monitoring. |
| `trap_catch_count` | Float | Conditional* | $\ge 0.0$ | Insects / Trap | Cumulative count of trapped adult moths or insects. **Leave blank if unmeasured.** |
| `plants_sampled` | Integer | Optional | $\ge 1$ (e.g. `20`) | Count | Total plants inspected across field quadrants. |
| `plants_affected` | Integer | Optional | $\le \text{plants\_sampled}$ | Count | Number of sampled plants with live pests or damage. |
| `sampling_method` | String | Mandatory | `fixed_plot_scouting`, `roving_survey`, etc. | Category | Standard field sampling procedure. |
| `observation_frequency` | String | Mandatory | `daily`, `weekly`, `bi_weekly`, `irregular` | Category | Temporal cadence of monitoring visits. |
| `sowing_date` | Date | Optional | `YYYY-MM-DD` | ISO 8601 | Field planting date. Essential for phenology alignment. |
| `crop_growth_stage` | String | Optional | `squaring`, `flowering`, `boll_formation` | Category | Phenological growth stage observed during scouting. |
| `days_since_sowing` | Integer | Optional | $\ge 0$ | Days (DSS) | Elapsed days between sowing and observation date. |
| `source_organization` | String | Mandatory | e.g. `CROPSAP-Maharashtra`, `ICAR-CICR` | Text | Official originating institutional body. |
| `source_document` | String | Optional | e.g. `cropsap_kharif_2023_export.csv` | Text | Original file, bulletin, or trial registry reference. |
| `source_record_id` | String | Optional | e.g. `1048291` | Text | Primary key in originating database. |
| `collection_method` | String | Mandatory | `field_scouting_visual`, `destructive_dissection` | Category | Visual count, sweep net, trap inspection, or dissection. |
| `verification_status` | String | Mandatory | `UNVERIFIED`, `FIELD_SCOUT_VERIFIED`, etc. | Category | Quality assurance audit status. |
| `data_license` | String | Mandatory | `GOVERNMENT_RESTRICTED`, `CC_BY_4_0`, etc. | Legal Term | Usage licensing classification. |

*\*Conditional Rule:* Each row must contain at least one valid quantitative measurement: `pest_incidence_pct`, `pest_severity_pct`, `trap_catch_count`, or a valid `plants_affected` / `plants_sampled` pair.

---

## 4. Handling Missing Values vs Zeros

```
Case A: Field scout visited the plot and found 0 infested plants out of 20 sampled.
  ➜ pest_incidence_pct = 0.0
  ➜ plants_affected = 0
  ➜ plants_sampled = 20
  (Valid scouted zero. Confirms non-occurrence.)

Case B: Visual scouting was conducted, but NO pheromone trap was installed in this field.
  ➜ trap_catch_count = [LEAVE COMPLETELY BLANK]
  (DO NOT enter 0! Entering 0 falsely indicates that a trap was present and caught zero moths.)

Case C: Pheromone trap catch was recorded, but leaf defoliation percentage was not scored.
  ➜ trap_catch_count = 14.0
  ➜ pest_severity_pct = [LEAVE COMPLETELY BLANK]
```

---

## 5. Submitting and Ingesting Surveillance Data

Once an authorized CSV or Excel dataset is prepared:

1. Place the raw file in: `data/raw/pest_surveillance/<filename>.csv`
2. Run the ingestion, validation, and alignment pipeline:
   ```python
   from src.data_ingestion.pest_surveillance import (
       load_surveillance_file,
       validate_surveillance_records,
       match_observation_to_environmental_grid,
       extract_antecedent_environmental_features,
       compute_forward_outbreak_label,
   )

   # Step 1: Load with cryptographic SHA-256 provenance hashing
   load_res = load_surveillance_file("data/raw/pest_surveillance/<filename>.csv")

   # Step 2: Validate physical and biological bounds
   valid_recs, report = validate_surveillance_records(load_res.loaded_records)
   print(f"Validated {report.valid_records_count} records ({report.invalid_records_count} rejected).")
   ```
3. Inspect the generated validation report to ensure zero biological contradictions or spatial coordinate errors before proceeding to ML dataset generation.

