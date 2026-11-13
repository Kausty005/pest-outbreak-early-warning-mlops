# AgriAdapt AI — Prioritized Institutional Submission Packages & Checklists

**Document ID:** `AGRI-INST-SUB-2027-V1`  
**Version:** 1.0.0  
**Target Submission Packages:** CROPSAP Maharashtra & ICAR-CICR Nagpur (Priority Tier 1)  
**Secondary Institutions:** Dr. PDKV Akola, VNMKV Parbhani, KVK Nagpur, KVK Yavatmal  
**Governance Status:** DRAFT ONLY — NOT SUBMITTED  
**Legal Precaution:** Access to research data is strictly distinguished from permission to redistribute or incorporate into a production application. **Zero emails, uploads, or formal applications have been dispatched.**

---

## 1. Submission Package 1: CROPSAP Maharashtra

### 1.1 Target Authority & Verified Official Contact
- **Target Organization:** Crop Pest Surveillance and Advisory Project (CROPSAP), Department of Agriculture, Government of Maharashtra.
- **Recipient Designation:** The Commissioner of Agriculture / Director (Plant Protection & Extension).
- **Physical Office Address:** Commissionerate of Agriculture, Central Building, Shivaji Nagar, Pune, Maharashtra 411001.
- **Official Institutional Portals:** `krishi.maharashtra.gov.in` / `cropsap.maharashtra.gov.in`.
- **Institutional Role:** State custodian of agricultural pest surveillance, weekly advisory releases, and district-level pest severity tracking.

---

### 1.2 Administrative & Academic Prerequisites Checklist
| Check | Administrative Requirement | Responsible Party | Current Status |
|:---:|:---|:---|:---:|
| [ ] | **Official University Letterhead:** Formal letter printed on accredited university/institute stationary. | Lead Student Researcher & Registrar | `PENDING ACADEMIC SIGN-OFF` |
| [ ] | **Student Investigator Introduction:** Academic bio, degree enrolled (e.g. M.Tech / B.Tech / M.Sc.), enrollment number, department. | Student Researcher (`[STUDENT_NAME_PLACEHOLDER]`) | `DRAFT READY` |
| [ ] | **Academic Supervisor Endorsement:** Formal declaration, signature, and institutional email of supervising faculty. | Faculty Supervisor (`[SUPERVISOR_NAME_PLACEHOLDER]`) | `PENDING SUPERVISOR REVIEW` |
| [ ] | **Dean / Head of Department (HOD) Seal:** Departmental rubber stamp and executive counter-signature. | Head of Department (`[HOD_NAME_PLACEHOLDER]`) | `PENDING SUBMISSION` |
| [ ] | **Data-Use Agreement (DUA) Undertaking:** Enclosed university legal declaration of non-commercial academic research use. | University Legal Officer / Registrar | `DRAFT ATTACHED` |
| [ ] | **Identity Documentation:** Verified copies of institutional ID cards and bonafide student certificates. | Student Investigator | `PREPARED` |

---

### 1.3 Technical Proposal Dossier

#### Project Title & Description
**AgriAdapt AI: Climate-Resilient Agricultural Intelligence for Maharashtra**  
An academic, non-commercial machine learning research initiative developing environmental favorability and early-warning algorithms for cotton, soybean, rice, and maize pest complexes in Maharashtra.

#### Research Objectives
1. Quantify the empirical correlation between microclimate parameters (temperature, relative humidity, cumulative rainfall) and weekly pest incidence spikes.
2. Formulate biostatistically sound, multi-day forward forecasting models ($[T+1, T+7]$) grounded in verified State Economic Threshold Levels (ETLs).
3. Validate regional pest outbreak lead times to inform timely, non-chemical and biorational IPM interventions.

#### Exact Historical Data Requirements
- **Target Crops:** Cotton (*Gossypium hirsutum*), Soybean (*Glycine max*), Rice (*Oryza sativa*), Maize (*Zea mays*).
- **Target Pests:** Pink Bollworm (*Pectinophora gossypiella*), American Bollworm (*Helicoverpa armigera*), Tobacco Caterpillar (*Spodoptera litura*), Brown Planthopper (*Nilaparvata lugens*), Fall Armyworm (*Spodoptera frugiperda*).
- **Desired Granularity:** Weekly aggregated taluka/district pest severity ratings (Pest Severity Index: Low, Medium, High) and raw scouting summary reports.
- **Temporal Span:** Kharif 2018 through Kharif 2024 (minimum 5 continuous seasons).
- **Spatial Coverage:** Vidarbha and Marathwada divisions (specifically Nagpur, Amravati, Yavatmal, Akola, Wardha, Parbhani, Jalgaon).

#### Farmer Privacy & Data Protection Safeguards
- **Zero PII Requirement:** AgriAdapt AI explicitly requests that CROPSAP **strip all personally identifiable information (PII)** prior to data transfer, including farmer names, contact phone numbers, survey plot numbers (7/12 land records), and exact cadastral coordinates.
- **Spatial Aggregation:** Any spatial presentation of model outputs is jittered or aggregated to the taluka / sub-district centroid (accuracy buffer $\ge 3.0\text{ km}$).

#### Data Retention, Access Controls & Production Boundary
- **Air-Gapped Academic Storage:** Acquired raw records will be stored on an encrypted institutional server accessible only by accredited project investigators.
- **Scope Restriction:**
  - **Permitted Scope:** Academic analysis, algorithmic benchmarking, dissertation publication, and retrospective error validation.
  - **Strictly Prohibited Scope:** Commercial sale, proprietary redistribution, public GitHub raw data hosting, or deployment within a commercial SaaS API without separate bilateral commercial licensing.

---

## 2. Submission Package 2: ICAR-CICR Nagpur

### 2.1 Target Authority & Verified Official Contact
- **Target Organization:** ICAR – Central Institute for Cotton Research (ICAR-CICR).
- **Recipient Designation:** The Director, ICAR-CICR, Nagpur / Head, Division of Crop Protection.
- **Physical Office Address:** Near Hindustan Petroleum Depot, Panjri Farm, Wardha Road, Nagpur, Maharashtra 440010.
- **Official Institutional Portal:** `cicr.icar.gov.in`.
- **Institutional Role:** National premier research institute for cotton entomology, Pink Bollworm insecticide resistance monitoring, and AICRP on Cotton coordination.

---

### 2.2 Administrative & Academic Prerequisites Checklist
| Check | Administrative Requirement | Responsible Party | Current Status |
|:---:|:---|:---|:---:|
| [ ] | **Official University Collaboration Letter:** Addressed directly to Director, ICAR-CICR, requesting collaborative academic evaluation. | Principal Investigator / Dean | `DRAFT READY` |
| [ ] | **ICAR Material/Data Transfer Agreement (MTA/DTA):** Standard ICAR bilateral institutional agreement form. | University Registrar & ICAR PME Cell | `PENDING MTA FORM` |
| [ ] | **Academic Co-Investigators:** Named entomology faculty and machine learning research supervisors. | Academic Faculty Advisor (`[SUPERVISOR_NAME_PLACEHOLDER]`) | `PENDING CO-SIGNATURE` |
| [ ] | **Joint Authorship Undertaking:** Formal commitment guaranteeing co-authorship for ICAR entomologists in resulting peer-reviewed publications. | Research Project Lead | `INCORPORATED IN PROPOSAL` |
| [ ] | **Institutional Clearances:** University Ethics & Academic Board approvals. | University Academic Council | `PENDING REVIEW` |

---

### 2.3 Technical Proposal Dossier

#### Project Title & Focus
**Biostatistical Early Warning of Cotton Bollworm Complexes Using Weather Covariates & Verified Action Thresholds**

#### Research Objectives
1. Establish mathematical transition functions from adult male pheromone trap catch surges to larval green boll damage.
2. Empirically validate the 8–10 moths/trap/night (3 consecutive nights) action threshold under variable Vidarbha microclimates.
3. Compare research station micro-plot dynamics against smallholder sentinel farm behavior.

#### Exact Historical Data Requirements
- **Pheromone Trap Records:** Daily or weekly trap catch counts (adult male moths per trap) for *P. gossypiella* and *H. armigera* from CICR Nagpur experimental plots (2015–2025).
- **Destructive Boll Dissection Logs:** Weekly green boll sampling records (bolls sampled, bolls damaged, locule damage %, live larval count).
- **Phenology & Variety Attributes:** Cotton hybrid details (Bt vs Non-Bt, BG-II event, variety name, sowing date, flowering date, boll opening date).
- **Weather Observations:** High-resolution daily station agrometeorological readings (temperature min/max, relative humidity at 07:00 and 14:00 hrs, rainfall, sunshine hours).

#### Governance, Attribution & Intellectual Property
- **Non-Commercial Research License:** Data will be utilized exclusively for academic model development.
- **Scientific Attribution:** ICAR-CICR scientists will be formally credited as research collaborators and co-authors on all resulting publications.
- **Strict Software Boundary:** Raw ICAR-CICR station data will **never be redistributed** or integrated into open-source software distributions.

---

## 3. Submission Package 3 & 4: State Agricultural Universities (Dr. PDKV & VNMKV)

### 3.1 Dr. PDKV Akola
- **Recipient:** Director of Research / Head, Department of Agricultural Entomology, Dr. PDKV, Akola, Maharashtra 444104.
- **Focus:** Controlled digitization of historical postgraduate dissertation field trials (e.g. Lande, 2005; Gitte, 2010); entomological threshold advisory review.
- **Status:** Package compiled; pending university supervisor authorization.

### 3.2 VNMKV Parbhani
- **Recipient:** Director of Research / Head, Department of Entomology, VNMKV, Parbhani, Maharashtra 431402.
- **Focus:** Marathwada regional surveillance data; soybean defoliation and pest incidence logs.
- **Status:** Package compiled; pending institutional co-sign off.

---

## 4. Submission Package 5 & 6: Krishi Vigyan Kendras (KVK Nagpur & KVK Yavatmal)

### 4.1 KVK Nagpur (Selsura / Dr. PDKV)
- **Recipient:** Senior Scientist & Head, Krishi Vigyan Kendra, Nagpur.
- **Focus:** Frontline demonstration (FLD) pest logs; hosting and supervision of 5 Kharif 2027 cotton/soybean sentinel plots.
- **Status:** Operational blueprint ready; on-field execution on `STANDBY`.

### 4.2 KVK Yavatmal
- **Recipient:** Senior Scientist & Head, Krishi Vigyan Kendra, Yavatmal.
- **Focus:** High-endemic Pink Bollworm sentinel field hosting (5 plots); emergency escalation network integration.
- **Status:** Operational blueprint ready; on-field execution on `STANDBY`.

---

## 5. Formal Operational Declaration

All six packages documented above are **internal technical specifications**. In accordance with scientific governance rules, **NO institutional application, email, phone call, or form submission will be executed** without explicit, written authorization from the project user and academic supervisors.

