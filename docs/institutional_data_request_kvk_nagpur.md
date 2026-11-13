# Formal Collaboration & Data Access Request — Krishi Vigyan Kendra (KVK), Nagpur

> [!IMPORTANT]
> **SUBMISSION-READY DRAFT DOCUMENT** — This document is a formal collaboration request template prepared for AgriAdapt AI academic research. All bracketed placeholders (`[INSERT ...]`) must be completed by the student researcher and countersigned by their academic supervisor before institutional submission. **No communication has been sent; do not dispatch without institutional authorization.**

---

**Date:** [INSERT DATE]

**To:**  
The Senior Scientist & Head  
Krishi Vigyan Kendra (KVK), Nagpur  
ICAR - Central Institute for Cotton Research (CICR) Campus  
Post Bag No. 2, Shankarnagar P.O., Nagpur 440 010  
Maharashtra, India  

**Institutional Email:** `kvknagpur@gmail.com` / `nagpurkvk@yahoo.com`  
*(Verified active contact; verify before formal dispatch at [kvknagpur.org.in](https://kvknagpur.org.in/))*  

---

**Subject:** Request for Research Collaboration and Field Pest Surveillance Data Sharing — Academic Machine Learning Early-Warning Research (Vidarbha Kharif Sentinel Plots)

---

### 1. Applicant & Academic Affiliation

| Field | Applicant / Supervisor Details |
| :--- | :--- |
| **Principal Student Researcher** | [INSERT STUDENT FULL NAME] |
| **Degree & Programme** | [INSERT DEGREE, e.g. B.Tech / M.Tech in Computer Engineering / Data Science] |
| **Department** | [INSERT DEPARTMENT NAME] |
| **Academic Institution** | [INSERT UNIVERSITY / INSTITUTE NAME, e.g. Vishwakarma Institute of Technology, Pune] |
| **Faculty Research Supervisor** | [INSERT SUPERVISOR FULL NAME & DESIGNATION] |
| **Supervisor Institutional Email** | [INSERT SUPERVISOR OFFICIAL EMAIL] |
| **Student Institutional Email** | [INSERT STUDENT OFFICIAL EMAIL] |
| **Department Contact Phone** | [INSERT DEPARTMENT TELEPHONE NUMBER] |

---

### 2. Research Background & Public Interest Purpose

Under the **AgriAdapt AI** open-source research initiative, we are developing an explainable, data-driven pest outbreak early-warning system tailored to smallholder farmers in the Vidarbha region of Maharashtra. 

The early-warning architecture combines:
1. **Tier 1 (Automated Environmental Favorability):** Utilizing daily gridded temperature, relative humidity, growing degree days (GDD), and topsoil moisture (Copernicus ERA5-Land) across Nagpur district.
2. **Tier 2 (Longitudinal Field Surveillance Ground Truth):** Calibrating advance 7-day outbreak alerts against verified field scouting observations and pheromone trap records.

**Purely Non-Commercial Academic Research:** This work is conducted strictly for non-commercial undergraduate/postgraduate research and publication in open-access scientific venues. No proprietary algorithms or commercial monetization are involved.

---

### 3. Specific Data & Field Collaboration Requested

We respectfully request access to existing On-Farm Trial (OFT) and Front-Line Demonstration (FLD) pest monitoring logs, or collaboration on prospective sentinel plot scouting in Nagpur district:

1. **Target Crops:** Cotton (*Gossypium hirsutum*, Bt BG-II and non-Bt) and Soybean (*Glycine max*, e.g. JS-335).
2. **Target Pests:**
   - Cotton Pink Bollworm (*Pectinophora gossypiella*): Green boll dissection damage %, rosette flower incidence %, pheromone trap catches.
   - Sucking Pests Complex: Aphids, Jassids, Thrips, Whiteflies per leaf.
   - Soybean Defoliators: Tobacco Caterpillar (*Spodoptera litura*), Semilooper.
3. **Temporal Horizon:**
   - Historical: Kharif seasons 2021, 2022, 2023, and 2024 (weekly or fortnightly scouting visits).
   - Prospective: Participation as sentinel monitoring partners for the **Kharif 2027 Field Pilot** (July–October 2027).
4. **Requested Variables:** Observation date, taluka/village, crop growth stage, sampling method, total plants/bolls sampled, affected count, incidence %, damage severity %, trap type, and moth counts.

---

### 4. Data Security, Privacy & Farmer Safeguards

We formally commit to the following data governance principles:
- **Farmer Anonymization:** Landowner names, phone numbers, and survey numbers are stripped prior to ingestion. Observations use pseudonymous IDs (e.g. `SENTINEL-NAG-001`).
- **GPS Obfuscation (Coordinate Fuzzing):** Raw GPS coordinates are strictly fuzzed by $\pm 1.0\text{ km}$ in any public view to protect farmer privacy and prevent speculative land targeting.
- **DVC / Git Isolation:** Raw CSV exports are tracked locally via DVC and excluded from public Git repositories via `.gitignore`.
- **Institutional Attribution:** Full attribution and co-authorship on any resultant peer-reviewed publications.

---

### 5. Institutional Endorsement

__________________________________________  
**[INSERT STUDENT FULL NAME]**  
Student Researcher, Department of [INSERT DEPARTMENT]  

__________________________________________  
**[INSERT SUPERVISOR FULL NAME & DESIGNATION]**  
Faculty Supervisor & Head of Department, [INSERT INSTITUTION]  
*(Official Departmental Seal)*  

