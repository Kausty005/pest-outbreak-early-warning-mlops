# Formal Data-Sharing Request — CROPSAP Maharashtra

> [!IMPORTANT]
> **DRAFT DOCUMENT** — This letter is a template. All bracketed fields must be completed by the student researcher or their institutional supervisor before dispatch. Do not send without supervisor review and institutional approval.

---

**Date:** [INSERT DATE]

**To:**

The Director of Agriculture (Extension & Training) / State Nodal Officer, CROPSAP  
Commissionerate of Agriculture  
Government of Maharashtra  
Central Building, Pune 411 001  
Maharashtra, India

**Reference Email:** cropsap.maha@gov.in / commagri.pune@gov.in  
*(Verify current contact details at [cropsap.maharashtra.gov.in](https://cropsap.maharashtra.gov.in/) before dispatch)*

---

**Subject:** Formal Request for Access to Historical CROPSAP Pest Surveillance Records for Academic Research on Machine Learning–Based Early Warning Systems — Kharif 2021, 2022, and 2023

---

Dear Sir/Madam,

I am writing to formally request access to historical pest surveillance data collected under the **Crop Pest Surveillance and Advisory Project (CROPSAP)** by the Department of Agriculture, Government of Maharashtra, for the purpose of academic research on machine learning–based pest outbreak early warning systems.

## 1. Applicant Information

| Field | Details |
|---|---|
| **Applicant Name** | [INSERT STUDENT FULL NAME] |
| **Programme** | [INSERT DEGREE, e.g., B.Tech. / M.Tech. / M.Sc. in Computer Science / Agricultural Informatics] |
| **Institution** | [INSERT INSTITUTION NAME AND ADDRESS] |
| **Department** | [INSERT DEPARTMENT NAME] |
| **Supervisor / Guide** | [INSERT SUPERVISOR NAME AND DESIGNATION] |
| **Supervisor Email** | [INSERT SUPERVISOR EMAIL] |
| **Institutional Email** | [INSERT STUDENT INSTITUTIONAL EMAIL] |
| **Contact Phone** | [INSERT PHONE NUMBER] |

---

## 2. Research Context and Objectives

We are developing **AgriAdapt AI**, an open-source machine learning–based agricultural advisory system targeting smallholder farmers in the Vidarbha and Khandesh regions of Maharashtra.

The pest outbreak early warning module is designed to:

1. Predict the **likelihood of a pest outbreak within a seven-day forecasting horizon** using environmental and agronomic features.
2. Issue **location-specific, crop-specific alerts** to enable timely and targeted farmer interventions.
3. Function as an experimental tool to assist agricultural extension workers and Krishi Vigyan Kendra (KVK) advisors.

**We are not commercialising this system.** The research is conducted purely for academic purposes as part of a postgraduate / undergraduate final-year project.

---

## 3. Requested Data

We specifically request field-level pest surveillance records collected by CROPSAP scouting teams (Krishi Sahayak / TAO / DSAO) for the following parameters:

### 3.1 Spatial Coverage

| Region | Districts Prioritised |
|---|---|
| **Vidarbha** | Nagpur, Amravati, Yavatmal, Wardha, Akola |
| **Khandesh** | Jalgaon, Dhule |

### 3.2 Temporal Coverage

| Kharif Season | Preferred SMW Range |
|---|---|
| Kharif 2021 | SMW 23–44 (June–October 2021) |
| Kharif 2022 | SMW 23–44 (June–October 2022) |
| Kharif 2023 | SMW 23–44 (June–October 2023) |

### 3.3 Target Crops and Pests

| Crop | Pest | Priority |
|---|---|---|
| Cotton | Pink Bollworm (*Pectinophora gossypiella*) | HIGH |
| Cotton | American Bollworm (*Helicoverpa armigera*) | HIGH |
| Soybean | Tobacco Caterpillar (*Spodoptera litura*) | HIGH |
| Rice | Brown Planthopper (*Nilaparvata lugens*) | MEDIUM |
| Maize | Fall Armyworm (*Spodoptera frugiperda*) | MEDIUM |

### 3.4 Requested Data Fields

The following fields correspond to our validated data schema (28-column surveillance schema):

| # | Field Name | Description |
|---|---|---|
| 1 | `observation_id` | Unique record identifier |
| 2 | `observation_date` | ISO 8601 date of field observation (YYYY-MM-DD) |
| 3 | `district` | Administrative district |
| 4 | `taluka` | Administrative taluka (sub-district) |
| 5 | `village` | Village or gram panchayat name |
| 6 | `latitude` | GPS latitude (WGS84, decimal degrees) |
| 7 | `longitude` | GPS longitude (WGS84, decimal degrees) |
| 8 | `crop` | Crop name (standardised) |
| 9 | `crop_variety` | Cultivar or hybrid (e.g., Bt Cotton BG-II) |
| 10 | `pest_common_name` | Common pest name |
| 11 | `pest_scientific_name` | Binomial scientific nomenclature |
| 12 | `pest_incidence_pct` | Percentage of infested plants or organs [0–100%] |
| 13 | `pest_severity_pct` | Severity / defoliation percentage [0–100%] |
| 14 | `trap_type` | Type of pheromone or physical trap |
| 15 | `trap_catch_count` | Moth catch count per trap per night |
| 16 | `plants_sampled` | Number of plants inspected per plot |
| 17 | `plants_affected` | Number of plants showing pest symptoms |
| 18 | `sampling_method` | Fixed plot / roving survey / trap monitoring |
| 19 | `observation_frequency` | Weekly / semi-weekly |
| 20 | `sowing_date` | Date of crop sowing (YYYY-MM-DD) |
| 21 | `crop_growth_stage` | Phenological stage at observation time |
| 22 | `days_since_sowing` | Integer days from sowing to observation |
| 23 | `source_organization` | Reporting organisation (CROPSAP) |
| 24 | `scout_id` | Anonymised field scout identifier |
| 25 | `plot_id` | Fixed or roving plot identifier |
| 26 | `verification_status` | Whether record was validated by supervisor |
| 27 | `data_license` | GOVERNMENT_RESTRICTED or equivalent |
| 28 | `notes` | Any additional field remarks |

> **We understand that GPS coordinates of individual farmers' fields may be commercially sensitive. We are fully willing to accept spatial aggregation to village or taluka centroid level if the Department requires this.**

---

## 4. Data Governance and Security Commitments

We formally undertake the following:

1. **Non-Commercial Use Only.** The requested data will be used exclusively for academic research and educational demonstration. No commercial exploitation or redistribution will occur.

2. **Confidentiality.** Individual farmer identities and exact field GPS coordinates will not be disclosed in any publication, presentation, or public repository. Data will be reported only in aggregated or anonymised form.

3. **Secure Storage.** The data will be stored on a password-protected encrypted local drive. It will NOT be committed to any public version-control repository (GitHub, GitLab, etc.). Access will be restricted to the principal researcher and their institutional supervisor.

4. **Signed NDA.** We are willing to sign a Non-Disclosure Agreement as required by the Commissionerate of Agriculture.

5. **Attribution.** Any paper, poster, report, or public presentation derived from this research will explicitly acknowledge CROPSAP and the Department of Agriculture, Government of Maharashtra.

6. **Deletion.** At the conclusion of the research project, all received raw records will be securely deleted or returned as directed by the Department.

---

## 5. Institutional Authorization

This request is made with the knowledge and approval of the undersigned supervisor/guide at [INSERT INSTITUTION NAME].

| | |
|---|---|
| **Student Signature** | ______________________________ |
| **Date** | [INSERT DATE] |
| **Supervisor Signature** | ______________________________ |
| **Supervisor Name & Designation** | [INSERT SUPERVISOR NAME AND DESIGNATION] |
| **Institutional Stamp / Letterhead** | *(Please submit on official department letterhead)* |

---

## 6. Enclosures

Please find the following enclosed with this letter:

1. Institutional affiliation letter signed by the Head of Department / Dean of Faculty.
2. Project synopsis (2–3 pages) describing the AgriAdapt AI pest early warning research.
3. Draft Non-Disclosure Agreement (or the Department's preferred NDA format).
4. Data schema (28-column CSV header template).

---

We are grateful for the work CROPSAP has done in systematically monitoring agricultural pest pressure across Maharashtra. We believe this collaboration will produce a valuable scientific validation of machine learning–based early warning tools in support of Maharashtra's agricultural extension objectives.

We sincerely hope the Department will consider this request favourably and would welcome the opportunity to discuss the research further at your convenience.

Yours faithfully,

**[INSERT STUDENT FULL NAME]**  
[INSERT PROGRAMME AND YEAR]  
[INSERT INSTITUTION, DEPARTMENT]  
[INSERT INSTITUTIONAL EMAIL]  
[INSERT PHONE NUMBER]

**Countersigned:**  
**[INSERT SUPERVISOR NAME]**  
[INSERT DESIGNATION AND DEPARTMENT]  
[INSERT INSTITUTION]

---

> [!NOTE]
> **Submission Guidance**
> - Submit on official institution letterhead.
> - Send by registered post and simultaneously by email to both `cropsap.maha@gov.in` and `commagri.pune@gov.in`.
> - Verify current contact details at [cropsap.maharashtra.gov.in](https://cropsap.maharashtra.gov.in/) before dispatch.
> - Expect a response time of 4–8 weeks; a follow-up call to the CROPSAP Nodal Officer is recommended after 3 weeks.
> - If a formal MoU template is provided by the Department, execute it in preference to this letter.

