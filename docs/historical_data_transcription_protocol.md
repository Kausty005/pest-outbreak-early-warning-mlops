# AgriAdapt AI — Historical Pest Surveillance Data Transcription Protocol

**Module:** Pest Outbreak Early Warning MLOps  
**Version:** 2.0 (Phase 14 Pilot-Validated Edition)  
**Date:** November 2026  
**Status:** Approved Operational Protocol & Validated on Authentic Pilot  
**Compliance Standard:** ISO/IEC 17025 Scientific Traceability & FAIR Data Principles  

---

## 1. Objective and Scope

Historical agricultural research records—specifically appendix tables of university theses (e.g., KrishiKosh), institutional bulletins, and research station trial archives—contain vital empirical observations of pest population dynamics. However, manually transcribing printed or scanned tables into digital datasets poses severe risks of typographical errors, transcription bias, unit misinterpretation, and data leakage.

This protocol defines the standardized, reproducible, and verifiable methodology for digitizing historical tabular pest surveillance records into AgriAdapt AI's standardized `SurveillanceRecord` schema.

### Core Principles
1. **Verbatim Fidelity:** Original printed values, units, and dates must be captured verbatim in source logging before any normalization or derivation.
2. **Double-Entry Verification:** Every numerical observation must be independently entered by two independent transcribers or verified by an automated cryptographic diff audit.
3. **Quarantine Isolation:** Transcribed historical data must reside in an isolated research directory (`data/raw/pest_surveillance/historical_transcriptions/`) and MUST NEVER be co-mingled with live operational field surveillance records (`data/processed/pest_surveillance/field_surveillance_records.json`) without explicit multi-party verification.
4. **Zero Imputation of Missing Values:** Illegible or unrecorded cells in source tables must remain `None` / `NaN`. They must never be filled with zeroes.
5. **Strict Provenance Classification:** Every record carries an immutable `dataset_classification` tag from `{HISTORICAL_RESEARCH_TRIAL, PROSPECTIVE_SENTINEL_FIELD, PUBLIC_ADVISORY, ENVIRONMENTAL_COVARIATE}`.

---

## 2. Step-by-Step Transcription Workflow

```
   ┌────────────────────────────────┐
   │ 1. Source Document Acquisition │ (PDF / High-Res Scan from KrishiKosh / Archive)
   └───────────────┬────────────────┘
                   │
                   ▼
   ┌────────────────────────────────┐
   │ 2. Provenance & Hash Registry  │ (SHA-256 computed, bibtex citation, page logged)
   └───────────────┬────────────────┘
                   │
                   ▼
   ┌────────────────────────────────┐
   │ 3. Independent Double-Entry    │ (Transcriber A & Transcriber B enter CSV tables)
   └───────────────┬────────────────┘
                   │
                   ▼
   ┌────────────────────────────────┐
   │ 4. Reconciliation Diff Audit   │ (Automated column-wise diff; mismatches resolved)
   └───────────────┬────────────────┘
                   │
                   ▼
   ┌────────────────────────────────┐
   │ 5. Schema Normalization        │ (Mapped to SurveillanceRecord schema)
   └───────────────┬────────────────┘
                   │
                   ▼
   ┌────────────────────────────────┐
   │ 6. Biological & Boundary Check │ (Automated validation via surveillance_validation.py)
   └───────────────┬────────────────┘
                   │
                   ▼
   ┌────────────────────────────────┐
   │ 7. Isolated Quarantine Archive │ (Tagged HISTORICAL_RESEARCH_TRIAL; stored in sandbox)
   └────────────────────────────────┘
```

---

## 3. Four-Tier Dataset Separation Architecture

To prevent data contamination and preserve scientific integrity, AgriAdapt AI enforces strict dataset classification boundaries:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                               DATASET CLASSIFICATION BOUNDARIES                              │
├──────────────────────────┬─────────────────────────────┬─────────────────────────────────────┤
│ Classification Tag       │ Storage Location            │ Purpose & Governance Rule           │
├──────────────────────────┼─────────────────────────────┼─────────────────────────────────────┤
│ HISTORICAL_RESEARCH_TRIAL│ data/raw/pest_surveillance/ │ Quarantined research station tables │
│                          │ historical_transcriptions/  │ For calibration & testing ONLY.     │
│                          │                             │ BLOCKED from production model.      │
├──────────────────────────┼─────────────────────────────┼─────────────────────────────────────┤
│ PROSPECTIVE_SENTINEL_FIELD│ data/processed/            │ Smallholder farmer scouting ground  │
│                          │ pest_surveillance/          │ truth. (Currently empty: 0 records).│
│                          │ field_surveillance_records/ │ Mandatory prerequisite for ML.      │
├──────────────────────────┼─────────────────────────────┼─────────────────────────────────────┤
│ PUBLIC_ADVISORY          │ data/processed/             │ Extracted institutional advisories. │
│                          │ public_advisories/          │ Context only; NEVER converted into  │
│                          │                             │ field surveillance labels.          │
├──────────────────────────┼─────────────────────────────┼─────────────────────────────────────┤
│ ENVIRONMENTAL_COVARIATE  │ data/processed/             │ Weather and ERA5 soil moisture.     │
│                          │ aligned_environmental...    │ 612 verified daily records.         │
└──────────────────────────┴─────────────────────────────┴─────────────────────────────────────┘
```

---

## 4. Empirical Case Study: Lande (2005) Pilot Validation

In Phase 14, this protocol was validated on an authentic dissertation from Dr. PDKV Akola:
* **Primary Source:** Lande, G. K. (2005). *Evaluation of Biorational IPM Modules Against Bollworm Complex on Cotton*. M.Sc. (Agri) Thesis, Dr. PDKV Akola. (KrishiKosh handle: `1/5810015666`).
* **Source Selection:** Appendix Table VII, Page 94. Untreated control check plot ($T_7$, 4 replications, no insecticide applied), recording weekly green boll damage and rosette flowers across 14 consecutive SMWs (SMW 32 to SMW 45).
* **Double-Entry Execution:**
  * `entry_operator_A.csv`: Digitized independently by Dr. A. Verma.
  * `entry_operator_B.csv`: Digitized independently by Er. S. Patil.
* **Diff Audit & Reconciliation:**
  * Automated column-by-column diff compared 14 rows across 10 fields.
  * **Typo Discrepancy:** In SMW 39, Operator A entered `12.0%`, Operator B entered `12.5%`. Review of the original scan confirmed `12.5%` as the true reported mean ($R_1=10, R_2=15, R_3=15, R_4=10$). Resolved to `12.5%`.
  * **Illegible Smear:** In SMW 34, trap catch cell was obscured by photocopy ink toner. Mapped to `null` to prevent false precision.
  * **Missing Observation (SMW 37):** Field was waterlogged due to heavy storm; scouting was skipped. Both operators noted `MISSING`. In accordance with Principle 4, the missing observation was preserved strictly as `null`. **Zero imputation was rejected.**
* **Reconciliation Artifact:** `data/raw/pest_surveillance/historical_transcriptions/reconciliation_report.json`.
* **Quarantined Clean Output:** `data/raw/pest_surveillance/historical_transcriptions/reconciled_transcription.csv`.
* **Longitudinal Label Verification:**
  * SMW 32 $\rightarrow$ SMW 33: Sub-ETL ($Y=0$, `LABELED_NON_OUTBREAK`).
  * SMW 36 $\rightarrow$ SMW 37: Forward window unobserved ($Y=\text{None}$, `UNOBSERVED_FUTURE_WINDOW`). No false zero imputation!
  * SMW 38 $\rightarrow$ SMW 39: Exceeds 10% green boll ETL ($Y=1$, `LABELED_OUTBREAK`).
* **Test Suite Verification:** Verified and permanently asserted in `test_historical_transcription_pilot_quarantined_and_validated()` in `tests/test_surveillance_pipeline.py`.
