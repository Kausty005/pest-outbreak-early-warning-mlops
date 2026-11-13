# AgriAdapt AI — Kharif 2027 Privacy, Farmer Rights & Data Governance Audit

**Document ID:** `AGRI-AUD-GOV-PRIVACY-2027-V1`  
**Version:** 1.0.0  
**Phase:** 17  
**Scope:** Privacy Impact Assessment, Farmer Data Protection, and Governance Architecture for Kharif 2027 Sentinel Pilot  
**Statutory Framework:** Digital Personal Data Protection (DPDP) Act, 2023 (India) & ICAR Data Sharing Guidelines  
**Governance Invariant:** No farmer Personally Identifiable Information (PII) enters analytical or machine learning datasets.

---

## 1. Executive Summary & Statutory Framework

Agricultural data collected from rural smallholders contains sensitive personal and operational information. In rural Maharashtra, disclosing exact farm locations, cadastral survey numbers, or individual crop infestation severities can result in social stigmatization, pesticide seller exploitation, or predatory contract farming practices.

Furthermore, the enactment of the **Digital Personal Data Protection (DPDP) Act, 2023 (India)** establishes strict statutory obligations regarding notice, purpose limitation, data minimization, consent management, and the right to erasure.

This document details the **Privacy and Data Governance Architecture** for the Kharif 2027 pilot, auditing pseudonymization, coordinate fuzzing, role-based access control, raw-data retention, and farmer rights protocols.

---

## 2. Farmer Consent & Withdrawal Framework

### 2.1 Bilingual Informed Consent Protocol
Prior to any sentinel field enrollment, host farmers must be provided with a physical printed information sheet and consent form in both **Marathi** and **English**:
1. **Notice of Purpose:** Explicitly states that data is collected for non-commercial academic research on pest forecasting.
2. **Voluntary Participation:** Confirms that participation is voluntary and refusal does not affect the farmer's access to public agricultural extension or KVK advisories.
3. **Scouting Frequency:** Details that scouts will visit once weekly (Wednesday) and install one or more pheromone traps.
4. **Compensation Agreement:** Stipulates fair compensation for destructively sampled green bolls (20 bolls/acre/week) and maize whorls.
5. **No PII Disclosure:** Guarantees that farmer names, phone numbers, and land parcel numbers will never be published or shared with third parties.

---

### 2.2 Consent Withdrawal Protocol (Right to Erasure)
Under Section 6(4) of the DPDP Act 2023, a data principal has the unconditional right to withdraw consent at any time:
1. **Withdrawal Notification:** The farmer may inform the field scout, district supervisor, or local KVK in writing or verbally.
2. **Immediate Field Halt:** Pheromone traps are removed within 48 hours, and all future scouting visits are terminated.
3. **Data Quarantine:** The field identifier is flagged as `STATUS = "CONSENT_WITHDRAWN"`.
4. **Historical Data Handling:**
   - Raw records containing field metadata are excised from active modeling queues.
   - Retrospective aggregated data already anonymized and published in research theses cannot be retroactively retracted, but no further analytical use occurs.
   - Proof of withdrawal is logged in the University Ethics Compliance Registry.

---

## 3. Cryptographic Pseudonymization Architecture

```
[ Rural Smallholder Farmer ]
  │
  ├─► Legal Name: "Ramrao Patil"
  ├─► Contact Phone: "+91 98xxxxxxxx"
  ├─► 7/12 Survey No: "Gut No. 142/2"
  ├─► Exact GPS Centroid: [21.274812, 78.583190]
  ▼
[ Air-Gapped University Registrar Vault (Encrypted SQLite / AES-256) ]
  │  Stores: True Identity <──► Salted Key Lookup Table
  ▼
[ AgriAdapt AI Public Analytical & Modeling Pipeline ]
  │  • Farmer Identifier: `FMR-NGP-9E2A8F`
  │  • Sentinel Field ID: `MAH-NGP-KAT-001`
  │  • Public Fuzzed GPS: [21.2891, 78.5684] (Jittered 2.1 km)
  │  • Taluka / District: "Katol / Nagpur"
  │  • NO PERSONAL IDENTIFIERS PERMITTED IN REPOSITORY OR API
```

### 3.1 Pseudonym Generation Mechanism
- Farmer pseudonyms are generated deterministically using salted SHA-256 hashes:
  $$\text{farmer\_id} = \text{"FMR-" } + \text{DistrictCode} + \text{"-" } + \text{SHA-256}(\text{PII} + \text{SecretSalt})[:6].\text{upper()}$$
- The secret salt is retained exclusively by the University Principal Investigator and Registrar. Developers, data engineers, and model trainers have zero access to the unhashed lookup table.

---

## 4. Coordinate Protection & Public Spatial Fuzzing

Exact cadastral GPS coordinates represent a high privacy vulnerability because satellite imagery combined with land registry (Bhuvan / Mahabhulekh) can easily identify the landholder.

### 4.1 Restricted Access vs Public Access Tiers

| Tier | Access Audience | Coordinate Representation | Access Control Policy |
|:---|:---|:---|:---|
| **Tier 1: Field Execution** | Field Scouts & District Supervisors | Exact GPS Coordinates ($\pm 3.0\text{ m}$) | On-device mobile app cache only; authenticated scout PIN required. |
| **Tier 2: Research Analysis** | Accredited University Researchers | Exact GPS Coordinates | Restricted institutional research server; encrypted at rest. |
| **Tier 3: Public Dashboard & API** | Public Web Dashboard / Extension | **Fuzzed GPS Coordinates** ($1.5–3.0\text{ km}$ jitter) | Publicly queryable; prevents individual farm triangulation. |
| **Tier 4: Research Publications** | Academic Papers & Monographs | District / Taluka Centroid Aggregation | Map markers display only taluka boundary polygons. |

### 4.2 Spatial Fuzzing Algorithm
For all public dashboard endpoints (`GET /pest-surveillance/records`, `GET /pest-surveillance/dashboard`), coordinates are fuzzed using a deterministic cryptographic offset:
$$\text{Lat}_{\text{public}} = \text{Lat}_{\text{exact}} + \delta_{\text{lat}}, \quad \text{Lon}_{\text{public}} = \text{Lon}_{\text{exact}} + \delta_{\text{lon}}$$
where $\delta_{\text{lat}}, \delta_{\text{lon}} \in [0.015^\circ, 0.030^\circ]$ ($\approx 1.6\text{–}3.2\text{ km}$), preserving regional microclimate context while rendering individual field identification impossible.

---

## 5. Role-Based Access Control (RBAC) Matrix

| User Role | View Drafts | Create Observation | Upload Batch CSV | Review & Approve | Reconcile Corrections | Export Analytical Data | Audit Log Access |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Field Scout** (`SCT-*`) | YES (Own) | YES | NO | NO | NO | NO | NO |
| **District Supervisor** | YES (District) | YES | YES | NO | NO | NO | Read Only |
| **Institutional Entomologist** | YES (All) | NO | NO | **YES** | **YES** | Read Only | Read Only |
| **MLOps Data Architect** | NO | NO | YES | NO | NO | **YES** | Read Only |
| **University Lead PI / DPO** | YES (All) | NO | NO | NO | NO | **YES** | **Admin / Audit** |

---

## 6. Retention, Cryptographic Hashing & Backup Controls

1. **Raw File Retention:** All raw uploaded CSVs and JSON streams are isolated in `data/raw/pest_surveillance/` with immutable write-once read-many (WORM) filesystem permissions.
2. **SHA-256 Cryptographic Checksums:** Calculated on every file ingestion and stored alongside records to detect silent bit rot or unauthorized tampering.
3. **Backup Schedule:**
   - **Daily Incremental Backup:** Automated snapshot of `field_surveillance_records.json` and `surveillance_audit_log.json` to encrypted cloud vault.
   - **Weekly Full Image:** Compressed and GPG-encrypted tarball archived with 7-year retention policy.
4. **Disaster Recovery:** In the event of primary database corruption, the state can be fully replayed from immutable raw files and the append-only audit log.

---

## 7. Compliance Verification & Legal Disclaimer

This data governance architecture aligns with established academic best practices under the DPDP Act 2023. **Legal compliance is an ongoing institutional duty.** Formal sign-off by the university legal counsel and Data Protection Officer (DPO) is required before commencing field data collection.

