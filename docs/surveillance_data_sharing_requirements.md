# Surveillance Data Sharing Requirements and Governance Plan

**Project:** AgriAdapt AI — Pest Outbreak Early Warning MLOps  
**Module:** Authentic Pest Surveillance Data Governance  
**Version:** DRAFT — Requires supervisor review and institutional legal approval  
**Date:** [INSERT DATE]

---

> [!CAUTION]
> This governance plan describes intended data handling protocols. It becomes binding only after execution of a formal MoU or NDA with the data-providing institution. No surveillance data has been received as of the time this document was prepared.

---

## 1. Purpose

This document defines the data governance obligations that the AgriAdapt AI research team commits to when receiving **authentic pest surveillance records** from institutional partners, specifically:

- **CROPSAP Maharashtra** (Commissionerate of Agriculture, Government of Maharashtra)
- **ICAR-CICR Nagpur** (ICAR–Central Institute for Cotton Research)
- **ICAR-NCIPM** (ICAR–National Research Centre for Integrated Pest Management)
- **State Agricultural Universities** (Dr. PDKV Akola, VNMKV Parbhani, MPKV Rahuri)

---

## 2. Data Ownership and Permitted Use

| Principle | Policy |
|---|---|
| **Ownership** | Surveillance records remain the intellectual property of the providing institution. This research team acquires a **non-exclusive, time-limited right to use** the data for academic research only. |
| **Permitted use** | Academic research; model training, validation, and reporting in peer-reviewed venues. |
| **Prohibited use** | Commercial exploitation; redistribution to third parties; use in products or services; sale or licensing of derivative datasets. |
| **Sublicensing** | Strictly prohibited. Data may not be shared with any third party without written consent of the original institution. |

---

## 3. Confidentiality Obligations

### 3.1 Farmer Privacy

- Individual farmer identities and farm names will **NOT** be recorded, stored, or published.
- GPS coordinates of individual farms will be **spatially aggregated** to village centroid or taluka centroid before storage.
- No coordinates more precise than village-level will appear in any publication, presentation, or public repository.

### 3.2 Scout Identity

- Field scout identifiers (scout_id) will be stored only as anonymised codes (e.g., SCOUT-001).
- No personal names of government field scouts will be published.

### 3.3 Non-Disclosure

- All team members (researcher, supervisor, collaborators) with access to raw surveillance data must be briefed on this governance plan and explicitly agree to its terms.

---

## 4. Data Storage and Security

| Requirement | Specification |
|---|---|
| **Storage medium** | Local encrypted hard drive (AES-256 or equivalent) on the researcher's designated institutional workstation. |
| **Cloud storage** | **Prohibited.** Surveillance data must NOT be synced to any cloud storage service (Google Drive, OneDrive, Dropbox, iCloud, etc.). |
| **Version control** | **Prohibited.** Raw surveillance CSV files must NOT be committed to any Git repository (public or private). See Section 5. |
| **Backup** | One encrypted backup copy is permitted on a physically separate drive stored securely at the institution. No network-attached backup to external services. |
| **Access control** | Only the named principal researcher and their direct supervisor may access raw files. |

---

## 5. Git Repository Exclusions (`.gitignore` Policy)

The AgriAdapt AI public GitHub repository enforces the following exclusion rules to prevent accidental publication of surveillance records:

```gitignore
# Authentic pest surveillance data — MUST NOT be committed.
# Records received under institutional MoU/NDA are confidential.
data/raw/pest_surveillance/*.csv
# Exception: the empty headers-only schema template is publicly committed
!data/raw/pest_surveillance/surveillance_data_template.csv
```

> [!WARNING]
> **Before any `git push`, confirm that no surveillance CSV files appear in `git status`.** If a file was accidentally staged, remove it immediately with `git rm --cached` and add the path to `.gitignore`. **Never force-push to remove committed sensitive data without also rotating all affiliated credentials.**

**The following file IS committed and is public (empty headers, zero rows):**

```
data/raw/pest_surveillance/surveillance_data_template.csv
```

This template contains only column headers and is used for schema documentation and partner communication. It contains no observation records.

---

## 6. Provenance and Integrity Verification

Every ingested surveillance file is processed through the `surveillance_loader.py` module, which:

1. Computes a **SHA-256 cryptographic hash** of the raw file at time of ingestion.
2. Stores the hash alongside the filename, institution, and ingestion timestamp in a provenance log.
3. Re-verifies the hash on every subsequent access to detect unintended file modification.

The provenance log (`data/raw/pest_surveillance/provenance_log.json`) is committed to the repository **without the data files themselves**, allowing reproducibility without data disclosure.

---

## 7. Retention and Deletion Protocol

| Phase | Action |
|---|---|
| **During active research** | Data stored on encrypted drive; provenance log maintained. |
| **Post submission of dissertation/paper** | Data retained for a minimum of **3 years** from submission, as required by most institutional research data management policies. |
| **Post retention period (or at partner's request)** | All raw surveillance CSV files are **securely deleted** (overwritten with DoD 5220.22-M standard or equivalent) from all storage media. Provenance log entries (hashes only, no data) are retained indefinitely. |
| **Early deletion on partner request** | If the partner institution requests early deletion, all copies will be deleted within 14 days of written notice, with written confirmation provided. |

---

## 8. Attribution and Publication Requirements

### 8.1 Mandatory Acknowledgement

All publications, conference papers, posters, presentations, and public repository READMEs derived from research using institutional surveillance data must include an explicit acknowledgement such as:

> "Pest surveillance ground-truth data were provided by [INSTITUTION NAME] under a formal academic data-sharing agreement. The authors gratefully acknowledge [INSTITUTION] and its field scouting teams for enabling this research."

### 8.2 Co-authorship

Where the partner institution's scientists have made substantive intellectual contributions (e.g., threshold validation, field methodology design, manuscript review), co-authorship will be offered in accordance with the International Committee of Medical Journal Editors (ICMJE) or equivalent authorship criteria.

### 8.3 Review Opportunity

Before any public disclosure of findings based on shared surveillance data, the partner institution will be offered a **30-day review period** to verify the accuracy and appropriateness of how their data has been represented.

---

## 9. Data Schema and Format Specification

Received surveillance records must conform to the 28-column schema defined in:

```
data/raw/pest_surveillance/surveillance_data_template.csv
src/data_ingestion/pest_surveillance/surveillance_schema.py
```

Fields that cannot be obtained from a partner must remain empty (`NaN` / blank in CSV). They must **never be filled with arbitrary zeroes or invented values**.

---

## 10. Incident Response

If a data breach, accidental public disclosure, or access control violation occurs:

1. Immediately notify the institutional supervisor.
2. Within **24 hours**, notify the partner institution in writing.
3. Assess the scope of disclosure and take immediate remediation steps.
4. Cooperate with the partner institution's preferred remediation protocol.
5. Document the incident in the provenance log.

---

## 11. Approval and Signatures

This governance plan must be reviewed and approved by the following before surveillance data is received:

| Role | Name | Signature | Date |
|---|---|---|---|
| Principal Researcher | [INSERT NAME] | _________________ | [DATE] |
| Academic Supervisor | [INSERT NAME] | _________________ | [DATE] |
| Head of Department | [INSERT NAME] | _________________ | [DATE] |
| Partner Institution Representative *(if applicable)* | [INSERT NAME] | _________________ | [DATE] |

---

> [!NOTE]
> This plan should be updated whenever new institutional partners or data types are added to the project. Version-control this document within the project repository.

