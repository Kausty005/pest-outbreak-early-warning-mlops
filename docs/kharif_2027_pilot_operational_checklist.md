# AgriAdapt AI — Kharif 2027 Field Surveillance Pilot Operational Readiness Checklist

**Document ID:** `AGRI-PILOT-CHK-2027-V1`  
**Version:** 1.0.0  
**Status:** DRAFT / OPERATIONAL SPECIFICATION  
**Scope:** Prospective Sentinel Plot Surveillance Pilot across 4 Maharashtra Districts (Nagpur, Amravati, Yavatmal, Jalgaon)  
**Target Season:** Kharif 2027 (June 2027 – October 2027, Standard Meteorological Weeks 24–39)  
**Total Target Sites:** 20 Sentinel Plots (5 plots per district)  
**Current Operational Status:** **STANDBY / NOT ACTIVATED. Zero sentinel plots currently recruited. Zero field observations collected.**

---

## 1. Executive Summary & Operational Boundary

The prospective Kharif 2027 sentinel pilot is designed to acquire the first authentic, prospective, longitudinal pest surveillance dataset for the AgriAdapt AI early-warning system. The pilot targets five smallholder farm plots across each of four agro-climatically distinct cotton-soybean-maize producing districts in Maharashtra: Nagpur, Amravati, Yavatmal, and Jalgaon.

To ensure scientific rigor, biometric reproducibility, and ethical compliance, field operations cannot proceed on an ad-hoc basis. This document formalizes the **16-Point Operational Readiness Checklist**. Every criterion must be systematically verified and signed off before the deployment of scouts or traps.

> [!IMPORTANT]
> **Operational Restriction:** This checklist is an operational planning and verification document. **No actual farm recruitment, scout deployment, trap installation, or field sampling has been initiated.** The platform remains in controlled pre-pilot standby.

---

## 2. The 16-Point Pilot Operational Readiness Checklist

### Category A: Field Site Selection & Governance (Points 1–3)

#### [ ] Point 1: Sentinel Field Recruitment & Farmer Onboarding
- **Requirement:** 20 willing smallholder farmers (plot size 1.0–2.5 acres) identified across Nagpur (5), Amravati (5), Yavatmal (5), and Jalgaon (5).
- **Verification Criteria:**
  - Written informed consent signed in Marathi/English explaining data collection, scouting frequency, and confidentiality.
  - Farmer briefed that early-warning alerts are experimental and do not replace local State Agricultural Extension advisories.
  - Baseline survey conducted: previous crop history, soil type, irrigation status (rainfed vs drip), and Bt hybrid cultivar name.
- **Verification Responsibility:** Field Pilot Coordinator & KVK Extension Liaison.
- **Current Status:** `PENDING / NOT STARTED`.

#### [ ] Point 2: Field Identifiers & GPS Polygon Boundary Verification
- **Requirement:** Precise spatial demarcation of each sentinel plot.
- **Verification Criteria:**
  - Plot corner coordinates recorded via dual-frequency GNSS/GPS (minimum 4 vertices, accuracy $\le 3.0$ meters).
  - Plot polygon digitized in GeoJSON format and verified against Bhuvan / Google Earth satellite imagery.
  - Unique hierarchical ID assigned: `MAH-{DISTRICT_CODE}-{TALUKA_CODE}-{PLOT_SERIAL}` (e.g., `MAH-NGP-KAT-001`).
- **Verification Responsibility:** GIS & Geospatial Data Specialist.
- **Current Status:** `PENDING / NOT STARTED`.

#### [ ] Point 3: Land Access Agreements & Institutional Indemnity
- **Requirement:** Formal institutional agreement safeguarding farmer rights and institutional property.
- **Verification Criteria:**
  - Land access MoU executed between academic research institution (e.g., Dr. PDKV / ICAR-CICR) and participating farmers.
  - Explicit indemnification clause protecting participating farmers against crop loss liability arising from observational scouting.
  - Stipulation confirming compensation for destructive sampling (e.g., green boll and whorl removal compensation).
- **Verification Responsibility:** Institutional Registrar / Legal Counsel & Principal Investigator.
- **Current Status:** `PENDING / NOT STARTED`.

---

### Category B: Personnel Training, Kits & Equipment (Points 4–6)

#### [ ] Point 4: Scout Onboarding, Training & Accreditation
- **Requirement:** 8 field scouts (2 per district) and 4 district supervisors trained in standardized entomological sampling.
- **Verification Criteria:**
  - Completion of a 3-day practical training workshop on pest identification (eggs, larvae, nymphs, damage symptoms).
  - Demonstration of competence on destructive boll dissection and whorl damage scoring.
  - Passing score ($\ge 85\%$) on a standardized practical identification assessment.
  - Issued official AgriAdapt AI Field Scout ID badges and authorization letters.
- **Verification Responsibility:** Senior Entomologist (Dr. PDKV / CICR).
- **Current Status:** `PENDING / NOT STARTED`.

#### [ ] Point 5: Standardized Field Scouting Kits & PPE
- **Requirement:** Standardized, calibrated equipment delivered to all 8 field scouts.
- **Verification Criteria:**
  - Heavy-duty field backpack containing: 10x illuminated hand lens, stainless steel dissection knife, steel measuring tape (30 m), white scouting drop sheet ($1 \times 1\text{ m}$), tally counter, waterproof clipboards, sampling vials with 70% ethanol, and permanent field markers.
  - Personal Protective Equipment (PPE): UV-protective wide-brim field hat, nitrile sampling gloves, rubber gumboots for wet clay soils, and portable first-aid kit.
- **Verification Responsibility:** Field Operations Logistics Manager.
- **Current Status:** `PENDING / NOT STARTED`.

#### [ ] Point 6: Pheromone Trap Procurement, Calibration & GPS Placement
- **Requirement:** Certified delta / sleeve pheromone traps with species-specific lures installed at each sentinel plot.
- **Verification Criteria:**
  - Traps procured from ICAR-certified or PCI-approved vendors with batch purity certificates.
  - Lures: *P. gossypiella* (Gossyplure), *H. armigera* (Helilure), *S. litura* (Spodolure), *S. frugiperda* (FAW-lure).
  - Trap placement verified: 1 trap per target pest per acre, installed at canopy height (30 cm above top canopy), positioned away from field borders ($>15$ m inward) and windbreaks.
  - GPS coordinates of each trap recorded with unique Trap ID (`TRP-{PLOT_ID}-{PEST_CODE}`).
- **Verification Responsibility:** District Scouting Supervisors.
- **Current Status:** `PENDING / NOT STARTED`.

---

### Category C: Field Sampling Protocols & SOPs (Points 7–9)

#### [ ] Point 7: Trap Servicing, Lure Replacement & Daily/Weekly Catch Counting
- **Requirement:** Systematic trap inspection and scheduled lure replenishment.
- **Verification Criteria:**
  - Trap catches recorded daily during peak adult emergence periods or weekly during baseline scouting.
  - Lures replaced every 21 calendar days (or immediately following extreme heat $>42^\circ\text{C}$ or heavy monsoon storms).
  - Dead insects removed and sticky liners replaced when dust or moth wings saturate surface area ($>50\%$).
- **Verification Responsibility:** Field Scouts & District Supervisors.
- **Current Status:** `PENDING / NOT STARTED`.

#### [ ] Point 8: Standardized Diagonal "W" Scouting Transects
- **Requirement:** Rigorous representative sampling path avoiding edge bias.
- **Verification Criteria:**
  - Scouts follow a predefined "W"-shaped walking path across the 1-acre plot, sampling at 5 fixed stations (one at each vertex/point of the W).
  - Minimum distance of 10 meters maintained from plot boundaries and irrigation channels.
  - 4 consecutive plants sampled at each of the 5 stations (20 plants total per plot).
- **Verification Responsibility:** Field Scouts.
- **Current Status:** `PENDING / NOT STARTED`.

#### [ ] Point 9: Destructive Green Boll Sampling & Whorl Dissection
- **Requirement:** Objective internal infestation quantification.
- **Verification Criteria:**
  - Cotton: 20 medium-sized green bolls (firm, 20–25 days old) collected per plot (4 per station), dissected longitudinally with knife, inspected for internal locule damage, boll tunneling, and live larvae.
  - Maize: 20 whorls inspected visually for pinholes/frass; suspected plants destructively unrolled to inspect growing point for FAW larvae.
  - Soybean: 5 linear meter-row shake sheet counts performed along the transect.
- **Verification Responsibility:** Field Scouts.
- **Current Status:** `PENDING / NOT STARTED`.

---

### Category D: Environmental Disruption & Rescheduling SOPs (Point 10)

#### [ ] Point 10: Weather Disruption, Storm Waterlogging & Rescheduling SOPs
- **Requirement:** Standardized rules for missed or delayed scouting due to monsoon events.
- **Verification Criteria:**
  - Mandatory 48-hour rescheduling window: if scheduled visit day (Wednesday) is disrupted by heavy rain ($>50\text{ mm}$) or field waterlogging, visit rescheduled to Thursday or Friday.
  - If field remains inaccessible past Friday ($>48$ hours), observation marked strictly as `MISSING_WEATHER_DISRUPTION`. **Zero-imputation strictly forbidden.**
  - Waterlogged soil status and rainfall depth logged in weather disruption log.
- **Verification Responsibility:** District Scouting Supervisors.
- **Current Status:** `PENDING / NOT STARTED`.

---

### Category E: Digital Capture, Provenance & Ingestion (Points 11–13)

#### [ ] Point 11: Geotagged Photograph Evidence & Cryptographic Hashing
- **Requirement:** Verifiable visual proof of symptoms and trap catches.
- **Verification Criteria:**
  - Mobile scouting app captures high-resolution photograph of: (a) trap liner catch, (b) dissected damaged bolls/whorls, (c) field overview.
  - EXIF metadata verified: timestamp, GPS coordinates, camera model.
  - SHA-256 cryptographic hash calculated immediately upon capture and stored in metadata block.
- **Verification Responsibility:** Mobile App Software & Ingestion Pipeline.
- **Current Status:** `PENDING / NOT STARTED`.

#### [ ] Point 12: Mobile Data Synchronization & Offline Storage
- **Requirement:** Robust data retention in remote rural areas with intermittent connectivity.
- **Verification Criteria:**
  - SQLite local encrypted database stores records on device until network handshake.
  - Automatic JSON synchronization upon 4G/WiFi reconnection with retry backoff and checksum verification.
  - Conflict resolution protocol: server-side idempotency based on `observation_id` UUID.
- **Verification Responsibility:** AgriAdapt Mobile & Cloud Infrastructure Team.
- **Current Status:** `PENDING / NOT STARTED`.

#### [ ] Point 13: Offline CSV Batch Ingestion & Physical Bounds Validation
- **Requirement:** Automated fallback ingestion pipeline for physical field paper sheets.
- **Verification Criteria:**
  - Dual-operator independent transcription verified for all physical logsheets.
  - Strict ingestion validation using `src/data_ingestion/pest_surveillance/surveillance_validation.py`.
  - Rejection of out-of-range dates, coordinates, or biological incompatibilities.
- **Verification Responsibility:** MLOps Data Engineer.
- **Current Status:** `OPERATIONAL IN TEST ENVIRONMENT; NO PILOT DATA SUBMITTED`.

---

### Category F: Quality Assurance, Privacy & Outbreak Escalation (Points 14–16)

#### [ ] Point 14: Entomological Expert Review & Human Audit Trails
- **Requirement:** Weekly expert verification of surveillance data before pipeline admission.
- **Verification Criteria:**
  - Regional entomologist reviews weekly data batches via the Surveillance Audit Dashboard.
  - Visual verification of geotagged insect photographs.
  - Audit status assigned: `APPROVED`, `FLAGGED_FOR_RESAMPLING`, or `REJECTED`.
- **Verification Responsibility:** Institutional Entomologist.
- **Current Status:** `PENDING / NOT STARTED`.

#### [ ] Point 15: Farmer Privacy, Pseudonymous Farmer IDs & Location Obfuscation
- **Requirement:** Strict compliance with farmer data protection principles.
- **Verification Criteria:**
  - Farmer names, phone numbers, and Aadhaar numbers segregated from the analytical pipeline.
  - Pseudonymous identifiers (`FMR-{DISTRICT}-{HASH}`) utilized across all research tables.
  - Public visualizations jitter GPS coordinates by 1.5–3.0 km to prevent farm identification.
- **Verification Responsibility:** Platform Data Protection Officer.
- **Current Status:** `COMPLIANT BY DESIGN; ZERO PRODUCTION FARMER DATA COLLECTED`.

#### [ ] Point 16: Emergency Severe Outbreak Escalation & KVK Notification
- **Requirement:** Immediate humanitarian and agricultural extension alert protocol.
- **Verification Criteria:**
  - If field observation exceeds $2.0 \times \text{ETL}$ (e.g., $>20\%$ boll damage or $>20$ larvae/meter), an automated emergency alert triggers within 4 hours.
  - Direct alert dispatched to local KVK Senior Scientist (Plant Protection) and District Agriculture Officer (DAO).
  - Recommended ICAR-approved emergency remediation guidelines supplied to the host farmer.
- **Verification Responsibility:** AgriAdapt Automated Alert System & KVK Liaison.
- **Current Status:** `PENDING / NOT STARTED`.

---

## 3. Operational Sign-Off Protocol

The Kharif 2027 Sentinel Surveillance Pilot cannot transition from `STANDBY` to `ACTIVE` until all 16 points above are signed by the responsible project leaders:

```markdown
================================================================================
KHARIF 2027 SENTINEL PILOT DEPLOYMENT AUTHORIZATION
================================================================================

Lead Principal Investigator (Academic):   ____________________ Date: ___________
Chief Agricultural Entomologist:          ____________________ Date: ___________
Lead MLOps Data Architect:                ____________________ Date: ___________
Field Operations & Logistics Director:    ____________________ Date: ___________

Pilot Activation Status: [ ] APPROVED FOR DEPLOYMENT   [X] STANDBY / PRE-DEPLOYMENT
================================================================================
```

---

## 4. Field Partner & Scout Onboarding Operational Framework

### 4.1 Scout Onboarding Checklist
Every recruited scout must complete the following onboarding gates prior to field assignment:
1. [ ] **Identity & Accreditation:** Verification of educational background (diploma / degree in agriculture or allied biological sciences) and government ID.
2. [ ] **3-Day Practical Entomological Training:** Practical sessions on boll dissection, whorl unrolling, sweep-net / beat-sheet methods, and delta trap servicing.
3. [ ] **Mobile App & Offline Sync Training:** Hands-on test of mobile app data entry, handling GPS signal loss, offline caching, and JSON sync.
4. [ ] **Scout Kit Issuance & Calibration:** Hand lens (10x), dissection knife, steel tape (30 m), white drop sheet, tally counter, sampling vials with 70% ethanol, PPE kit, official ID card.
5. [ ] **Code of Conduct & Ethics Agreement:** Signed undertaking pledging scientific accuracy, zero fabrication, respectful interaction with host farmers, and privacy protection.

---

### 4.2 Researcher Responsibility Matrix (RACI)

| Operational Role | Lead PI (Academic) | Senior Entomologist | MLOps Data Engineer | District Supervisor | Field Scout | Host Farmer |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Sentinel Plot Recruitment & Consent** | **A** | C | I | **R** | I | C |
| **Pheromone Trap Installation & Servicing** | I | **A** | I | C | **R** | I |
| **Weekly In-Field Scouting & Dissection** | I | C | I | **A** | **R** | I |
| **Photograph Capture & SHA-256 Hashing** | I | I | **A** | C | **R** | I |
| **Mobile Synchronization & Validation** | I | I | **A** | C | **R** | I |
| **Weekly Entomological Batch Review** | I | **R / A** | C | C | I | I |
| **Severe Outbreak ($2\times\text{ETL}$) Escalation** | **A** | **R** | C | **R** | C | C |
| **Data Correction & Audit Log Revision** | **A** | **R** | **R** | C | I | I |

*Key: R = Responsible, A = Accountable, C = Consulted, I = Informed.*

---

### 4.3 Data Quality Escalation Workflow

```
[ Field Scout Data Submission ]
  │
  ▼
[ Automated Schema & Physical Bounds Validation ]
  ├─► [ REJECT: Physical bounds violated (e.g. >100% damage) ] ──► Return to Scout for Resampling
  ▼
[ Ingestion into Quarantined Raw Staging Area ]
  │
  ▼
[ Weekly Entomologist Expert Review Dashboard ]
  ├─► [ FLAGGED: Photographed pest does not match reported symptoms ]
  │     │
  │     ▼
  │   [ District Supervisor Field Re-Inspection within 48 Hours ]
  │
  ├─► [ APPROVED: Expert verifies diagnosis and symptom counts ]
  │     │
  │     ▼
  │   [ Admission to Validated Surveillance Staging ]
```

---

### 4.4 Weekly Submission & Missed-Visit Procedures

#### Weekly Submission Protocol
- **Scheduled Day:** Every Wednesday by 18:00 IST.
- **Sync Procedure:** Scout syncs records via the mobile app. If connectivity is unavailable in the village, synchronization must be completed within 24 hours from taluka headquarters.
- **Verification Notification:** Mobile app receives cryptographic acknowledgement from the server confirming SHA-256 batch integrity.

#### Missed-Visit Protocol
- **Heavy Rain / Waterlogging:** If Wednesday visit is blocked, visit within $\pm 48\text{ hours}$ (Thursday or Friday).
- **Unresolved Inaccessibility:** If field remains impassable past Friday, record is logged as:
  `observation_date = NULL`, `status = "MISSED_VISIT_WATERLOGGING"`.
- **Zero Imputation Prohibited:** Missing scouting visits must **NEVER** be backfilled, interpolated, or imputed as $0.0\%$.

---

### 4.5 Photo Evidence Requirements

Every scouting submission must attach at least two high-resolution photographs:
1. **Pest / Damage Close-Up:** Macro photograph of dissected boll locule, unrolled whorl with frass, or skeletonized leaf surface with millimeter scale visible.
2. **Trap Liner Catch Photograph:** Clear, top-down view of pheromone trap sticky insert showing individual moth specimens.
3. **EXIF & Hash Integrity:** Image metadata must contain valid GPS coordinates and timestamps matching the scouting log. SHA-256 checksum calculated on device upon capture.

---

### 4.6 Data Correction & Expert Audit Trail Protocol

- **Immutable Raw Log:** Raw mobile submissions are never overwritten or deleted.
- **Correction Mechanism:** Any data correction (e.g., re-identifying a moth species after laboratory examination) creates an append-only audit entry in `surveillance_audit_history`.
- **Mandatory Audit Attributes:** `corrected_field`, `old_value`, `new_value`, `reason_for_correction`, `correcting_expert_name`, `timestamp`.

---

### 4.7 Field Access & Farmer Consent Checklist

Before entering any farm plot:
- [ ] Signed bilingual informed consent form on file (Marathi and English).
- [ ] Host farmer contacted 24 hours prior to scheduled scouting visit.
- [ ] Compensation protocol established for destructive green boll / whorl sampling.
- [ ] Privacy terms reconfirmed: zero public disclosure of farm cadastral coordinates or personal names.
- [ ] Agreement that experimental model predictions are non-operational research insights.


