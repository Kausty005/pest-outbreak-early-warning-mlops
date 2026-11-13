# AgriAdapt AI — Independent Entomologist Review Tracking Register

**Document ID:** `AGRI-ETL-REG-2027-V1`  
**Version:** 1.0.0  
**Current Governance Status:** **NO REVIEWS COMPLETED. ZERO EXPERT APPROVALS OBTAINED.**  
**Target Registry:** Formal tracking log for independent external reviews of the five priority Economic Threshold Levels (ETLs).  
**Requirement:** Every transition from `PRIMARY_SOURCE_RETRIEVED` to `VERIFIED` requires a complete, signed, and institutionally verified entry in this register.

---

## 1. Governance Rules & Verification Standard

In strict accordance with the AgriAdapt AI scientific integrity policy:

1. **No Self-Certification:** Project developers, machine learning engineers, and student authors cannot act as the certifying entomologist.
2. **Accredited Reviewer Standard:** The reviewing expert must hold a postgraduate or doctorate degree (M.Sc. / Ph.D.) in Agricultural Entomology, Plant Protection, or Applied Zoology, with an active or emeritus faculty/scientist appointment at an accredited agricultural university (ICAR, SAU, or international CGIAR institute).
3. **Documentary Evidence Mandatory:** An entry cannot be marked `APPROVED` without physical or cryptographically verifiable documentary evidence (e.g., signed PDF review form with institutional seal, or formal institutional email from an `@icar.gov.in` / `@pdkv.ac.in` domain).
4. **No Fabricated Records:** Fabricating reviewer names, affiliations, or approval dates is strictly barred.

---

## 2. Master Review Tracking Log

| Log ID | Target Crop & Pest Combination | Proposed Expert Reviewer Name | Reviewer Institution & Designation | Expertise Domain | Review Dossier Dispatched Date | Review Completed Date | Formal Determination | Documentary Evidence Identifier | Operational Promotion Status |
|:---:|:---|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|
| `REV-2027-01` | **Cotton — Pink Bollworm**<br>(*Pectinophora gossypiella*) | *[PENDING IDENTIFICATION]* | ICAR-CICR Nagpur / Dr. PDKV Akola | Cotton Entomology & Bollworm Resistance | *Not Dispatched* | *Pending* | **PENDING** | *None* | `PRIMARY_SOURCE_RETRIEVED` (Unchanged) |
| `REV-2027-02` | **Cotton — American Bollworm**<br>(*Helicoverpa armigera*) | *[PENDING IDENTIFICATION]* | ICAR-NCIPM / Dr. PDKV Akola | IPM in Commercial Cotton | *Not Dispatched* | *Pending* | **PENDING** | *None* | `PRIMARY_SOURCE_RETRIEVED` (Unchanged) |
| `REV-2027-03` | **Soybean — Tobacco Caterpillar**<br>(*Spodoptera litura*) | *[PENDING IDENTIFICATION]* | ICAR-IISR Indore / VNMKV Parbhani | Legume Entomology & Defoliator IPM | *Not Dispatched* | *Pending* | **PENDING** | *None* | `PRIMARY_SOURCE_RETRIEVED` (Unchanged) |
| `REV-2027-04` | **Rice — Brown Planthopper**<br>(*Nilaparvata lugens*) | *[PENDING IDENTIFICATION]* | ICAR-NRRI Cuttack / ICAR-IIRR Hyderabad | Rice Entomology & Sap-Feeding Vector IPM | *Not Dispatched* | *Pending* | **PENDING** | *None* | `PRIMARY_SOURCE_RETRIEVED` (Unchanged) |
| `REV-2027-05` | **Maize — Fall Armyworm**<br>(*Spodoptera frugiperda*) | *[PENDING IDENTIFICATION]* | ICAR-IIMR Ludhiana / ICAR-NBAIR Bengaluru | Invasive Spodoptera & Whorl Damage IPM | *Not Dispatched* | *Pending* | **PENDING** | *None* | `PRIMARY_SOURCE_RETRIEVED` (Unchanged) |

---

## 3. Standardized Reviewer Record Dossier Structure

When an accredited external expert conducts an evaluation, the detailed audit record below must be completed and archived in `docs/reviews/`:

```markdown
================================================================================
AGRIADAPT AI — INDEPENDENT ENTOMOLOGIST AUDIT DOSSIER
================================================================================

1. REVIEWER CREDENTIALS & INTEGRITY ATTESTATION
- Full Name:                       [EXPERT_NAME]
- Academic / Professional Title:   [e.g. Principal Scientist / Professor]
- Institutional Affiliation:       [e.g. Division of Crop Protection, ICAR-CICR]
- Official Email:                  [user@institution.ac.in]
- Phone / Contact:                 [Official landline / office extension]
- Professional Profile / ORCID:    [0000-xxxx-xxxx-xxxx]
- Conflict of Interest Disclosure: "I declare no financial, commercial, or personal
                                    interest in the AgriAdapt AI early warning system."

2. THRESHOLD SPECIFICATION AUDITED
- Crop:                            [cotton / soybean / rice / maize]
- Pest:                            [Common name & Latin binomen]
- Source Monograph Cited:          [Author, Year, Title, Bulletin No., Page/Table]
- Implemented Baseline Threshold:  [% incidence / % defoliation / count / trap]
- Stage-Specific Conditions:       [e.g. vegetative vs flowering vs boll/panicle]
- Sampling Unit & Denominator:     [e.g. 20 plants/acre, 20 green bolls, 1m row]
- Consecutive Night Rules:         [e.g. 3 consecutive nights >= 8 moths/night]

3. CRITICAL EVALUATION & TECHNICAL ASSESSMENT
- Agronomic validity for Maharashtra agro-ecological conditions (1–5): [ ]
- Smallholder field scout feasibility (1–5):                           [ ]
- Stage-specific sensitivity and threshold accuracy (1–5):             [ ]
- Clarity of mathematical trigger logic (1–5):                         [ ]

4. REVIEWER COMMENTS, RESERVATIONS & MANDATED ADJUSTMENTS
[Detailed technical commentary, regional calibration recommendations, or
required modifications to numerical thresholds or sampling procedures]

5. FORMAL DETERMINATION
[ ] APPROVED AS SUBMITTED — Authorizes promotion to VERIFIED status.
[ ] CONDITIONALLY APPROVED — Requires specific code/threshold modifications.
[ ] REJECTED — Inappropriate or unsupported by empirical regional evidence.

6. DOCUMENTARY EVIDENCE ARCHIVE
- Document Type:    [Signed PDF Form / Scanned Letter / Official Institutional Email]
- File Path:        docs/reviews/evidence/[LOG_ID]_signed_review.[pdf|eml]
- SHA-256 Hash:     [Cryptographic hash of evidence document]
- Date Registered:  [YYYY-MM-DD]
================================================================================
```

---

## 4. Current Register Summary

- **Total Target Thresholds:** 5
- **Reviews Completed:** 0
- **Reviews in Progress:** 0
- **Expert Approvals Documented:** 0
- **Governing Status:** All five crop-pest thresholds remain strictly at **`PRIMARY_SOURCE_RETRIEVED`**.
- **Label Generation Guard:** As verified in Phase 16 unit tests, `production_eligible` is strictly `False` for all five thresholds, blocking unapproved thresholds from generating production labels.

