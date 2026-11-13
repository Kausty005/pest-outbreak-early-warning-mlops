# AgriAdapt AI — Kharif 2027 Data Quality Assurance & Outbreak Escalation Protocol

**Document ID:** `AGRI-SOP-QA-ESCALATION-2027-V1`  
**Version:** 1.0.0  
**Phase:** 17  
**Scope:** Multi-Tier Quality Assurance and Emergency Outbreak Escalation for the Prospective Kharif 2027 Sentinel Pilot  
**Target Coverage:** 20 Sentinel Plots across 4 Maharashtra Districts (Nagpur, Amravati, Yavatmal, Jalgaon)  
**Governance Invariant:** Zero-imputation of missing data is strictly prohibited. Outbreak alerts are governed by verified agronomic thresholds.

---

## 1. Executive Summary & Regulatory Purpose

The integrity of an early-warning machine learning system depends entirely on the veracity of its observational labels. In agricultural surveillance, false negative labels (e.g. treating an unobserved or flooded plot as sub-ETL zero) blind the model to emerging pest dynamics, while false positive labels trigger unjustified chemical pesticide applications.

This Standard Operating Procedure (SOP) defines:
1. **The 4-Tier Data Quality Assurance Hierarchy:** Systematic gatekeeping from mobile edge validation to expert entomological audit.
2. **The Severe Outbreak Escalation Protocol ($2.0 \times \text{ETL}$):** Humanitarian and extension notification workflow triggered when pest pressure threatens catastrophic crop loss.
3. **The Data Correction & Audit Trail Standard:** Strict rules for modifying historical scouting entries without compromising provenance.
4. **The Monsoon Disruption & Missing Observation Protocol:** Enforcing strict zero-imputation rules during severe weather.

---

## 2. The 4-Tier Data Quality Assurance Hierarchy

```
[ LEVEL 1: Mobile Client Edge Validation ]
  │  • Physical bounds checking (e.g. incidence [0–100]%, non-negative counts).
  │  • Geographic bounding box validation (Maharashtra bounds: lat 15.6–22.1, lon 72.6–80.9).
  │  • Biological compatibility lookup (e.g. rejects Rice pests on Cotton).
  │  • Camera photo EXIF timestamp and GPS alignment check.
  ▼
[ LEVEL 2: Server Ingestion & Cryptographic Provenance ]
  │  • SHA-256 checksum calculation and storage in immutable raw file archive.
  │  • Business duplicate detection (rejects same date/location/crop/pest under HTTP 409).
  │  • Late submission warning flag (triggered if observation date > 3 days prior to sync).
  │  • Initial status locked at `UNVERIFIED` (never auto-verified).
  ▼
[ LEVEL 3: Entomological Human Expert Review ]
  │  • Weekly batch review by designated institutional entomologist (Dr. PDKV / CICR / KVK).
  │  • Visual examination of geotagged macro damage and trap liner photographs.
  │  • Action determination: `APPROVE` (`KVK_EXPERT_VALIDATED`), `REJECT` (`REJECTED`), `CORRECT_FIELDS`.
  │  • Append-only audit record generated in `surveillance_audit_log.json`.
  ▼
[ LEVEL 4: Biostatistical Longitudinal Consistency Checks ]
  │  • Multi-week time series trajectory analysis (flags sudden unbiological population collapses without spray).
  │  • Degree-day growth accumulation consistency (verifies developmental instar timing).
  │  • Regional peer-plot cross-validation (detects spatial anomalies against adjacent district plots).
```

---

## 3. Severe Outbreak Escalation Protocol ($2.0 \times \text{ETL}$)

When pest pressure reaches twice the verified Economic Threshold Level ($2.0 \times \text{ETL}$), the situation ceases to be purely observational and requires an immediate agricultural extension intervention to protect the farmer's livelihood.

### 3.1 Quantitative Emergency Escalation Triggers

| Target Pest Complex | Stage / Condition | Baseline ETL | Severe Escalation Trigger ($2.0 \times \text{ETL}$) | Sampling Verification Mandate |
|:---|:---|:---:|:---:|:---|
| **Cotton Pink Bollworm** (*P. gossypiella*) | Boll Formation to Bursting | 10.0% green boll damage | **$\ge 20.0\%$ damaged green bolls** with live larvae | Destructive dissection of 20 bolls; cross-checked by District Supervisor. |
| **Cotton Pink Bollworm Trap** | Adult Moth Flight | 8.0 moths/night (3 nights) | **$\ge 16.0$ moths/night for 3 consecutive nights** | Verified trap liner count + photo evidence. |
| **Cotton American Bollworm** (*H. armigera*) | Squaring to Peak Boll | 1 larva / plant OR 5% damage | **$\ge 2.0$ larvae / plant OR $\ge 20.0\%$ square flare** | Diagonal 'W' count across 25 plants. |
| **Soybean Tobacco Caterpillar** (*S. litura*) | Vegetative Stage (V3–V6) | 20.0% defoliation | **$\ge 40.0\%$ canopy defoliation** | 5 linear meter shake sheet beat count. |
| **Soybean Tobacco Caterpillar** | Flowering to Pod Fill | 4.0 larvae / meter row | **$\ge 10.0$ larvae / meter row** | Verified ground cloth beat count. |
| **Rice Brown Planthopper** (*N. lugens*) | Active Tillering to Booting | 10 hoppers / hill | **$\ge 20.0$ planthoppers / hill** | Base of culms count across 20 hills. |
| **Maize Fall Armyworm** (*S. frugiperda*) | Mid-Whorl Stage (V4–V8) | 10.0% whorl damage | **$\ge 20.0\%$ whorls with fresh frass & larvae** | 100 consecutive plants across 5 stations. |

---

### 3.2 The 4-Hour Emergency Escalation Workflow

```
[ Step 1: Automated Detection (T = 0 Hours) ]
  │  Scout submits observation meeting $2.0 \times \text{ETL}$ criteria.
  │  Server validation engine flags observation as `EMERGENCY_ESCALATION_TRIGGERED`.
  ▼
[ Step 2: District Supervisor Field Verification (T + 1 Hour) ]
  │  District Supervisor receives high-priority mobile alert.
  │  Supervisor calls scout, reviews macro photo, and verifies sampling count validity.
  ▼
[ Step 3: Institutional Authority Notification (T + 2 Hours) ]
  │  Automated notification dispatched via encrypted SMS and priority email to:
  │  1. Senior Scientist & Head, local District Krishi Vigyan Kendra (KVK).
  │  2. District Agriculture Officer (DAO), Dept. of Agriculture, Govt. of Maharashtra.
  │  3. Lead Institutional Entomologist (Dr. PDKV Akola / ICAR-CICR Nagpur).
  ▼
[ Step 4: Farmer Advisory Delivery (T + 4 Hours) ]
  │  District Supervisor and KVK Extension Officer visit the host farmer.
  │  Deliver official ICAR/SAU recommended emergency IPM package (e.g. bio-rational biopesticides,
  │  entomopathogenic fungi, or certified chemical control depending on instar stage).
```

---

## 4. Data Correction & Dispute Resolution Protocol

Any modification to a recorded observation after initial ingestion must follow strict audit logging rules:

1. **Immutable Raw Ingestion:** The original raw submission string and file hash are permanently preserved in `data/raw/pest_surveillance/` and are never overwritten.
2. **Permitted Correction Triggers:**
   - Field scout clerical transcription slip (e.g. entered 150 sampled plants instead of 20).
   - Expert re-identification of photographed specimen after microscopic examination.
   - GPS coordinate correction following differential GNSS post-processing.
3. **Mandatory Audit Logging:** Every correction requires an API payload to `POST /pest-surveillance/review` with `action="CORRECT_FIELDS"` supplying:
   - `observation_id`: Target observation identifier.
   - `reviewer_id`: Identity of certifying expert entomologist.
   - `justification`: Detailed scientific or clerical rationale.
   - `field_corrections`: Key-value pairs of corrected fields.
4. **Audit Trail Schema:** Logged append-only to `surveillance_audit_log.json` containing `audit_id`, `old_status`, `new_status`, `timestamp`, and SHA-256 hash.

---

## 5. Weather Disruption & Missing Observation Protocols

Monsoon weather in Vidarbha and Marathwada routinely disrupts scheduled scouting. The following protocol governs disruption handling:

1. **Mandatory 48-Hour Rescheduling Window:** If scheduled Wednesday scouting is prevented by heavy rain ($>50\text{ mm}$) or field waterlogging, scouting must be attempted on Thursday or Friday.
2. **Cutoff Rule:** If the plot remains inaccessible through Friday 18:00 IST, the visit for that SMW is recorded as:
   `observation_date = NULL`, `label_status = "MISSED_VISIT_WATERLOGGING"`.
3. **No Retrospective Imputation:** Under no circumstances may an observer visit on Sunday or the following week and record the observation under the missed SMW.
4. **Strict Zero-Imputation Prohibition:** A missed observation is **NEVER** backfilled or imputed as $0.0\%$ pest incidence. In early-warning modeling, missing data represents unobserved uncertainty; assigning zero creates dangerous artificial non-outbreak training labels.

