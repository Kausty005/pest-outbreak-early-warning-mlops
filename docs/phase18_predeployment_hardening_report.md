# AgriAdapt AI — Phase 18: Pre-Deployment Hardening, Privacy Validation and Scientific Governance Audit Report

**Document ID:** `AGRI-REPORT-PHASE18-HARDENING-2027-V1`  
**Version:** 1.0.0  
**Phase:** 18  
**Scope:** Comprehensive Technical, Privacy, Biostatistical, and Agronomic Audit of the Pest Surveillance Module  
**Execution Date:** November 2026  
**Final Physical Deployment Decision:** **`NO-GO (PHYSICAL DEPLOYMENT BLOCKED)`**  
**ML Model Training Status:** **`BLOCKED (ZERO AUTHENTIC GROUND TRUTH OBSERVATIONS)`**

---

## 1. Executive Summary & Context

Phase 17 successfully architected the prospective operational workflow for the Kharif 2027 Maharashtra Sentinel Pilot. However, before deploying software to field personnel or engaging farmers, rigorous engineering ethics mandate an independent adversarial audit of all technical claims, privacy mechanisms, calendar calculations, and regulatory assumptions.

Phase 18 was executed to conduct this pre-deployment hardening and scientific governance audit. The key findings and technical achievements include:
1. **Kharif 2027 Calendar Validation:** Reconciled the 20-week schedule (SMW 24–43: June 15 – October 31, 2027). Flagged two major discrepancies: (a) Cycle 7's premature truncation at season close, and (b) the agronomic error of deploying cotton pink bollworm pheromone traps over bare soil at sowing rather than at 45 DAS (squaring/flowering).
2. **Scientific Review of Emergency Escalation:** Re-evaluated the $2.0 \times \text{ETL}$ trigger and 4-hour response target. Identified extreme binomial noise in small samples ($N=5 \rightarrow 1\text{ damaged} = 20\%$) and proved the 4-hour SLA is impossible in rural Vidarbha during monsoon floods. Formally reclassified the protocol as **`PROVISIONAL — EXPERT APPROVAL REQUIRED`** and established a strict separation preventing operational alerts from corrupting ML training labels.
3. **Cryptographic Pseudonymization Hardening:** Replaced naive 24-bit salted SHA-256 (which had a $52.5\%$ collision probability across 5,000 farmers) with **Keyed HMAC-SHA-256 with 48 bits entropy** (collision probability $< 1.78 \times 10^{-7}$ for 10,000 farmers), integrated with an air-gapped `IdentityVault` featuring automatic collision resolution.
4. **Deterministic Spatial Displacement (LLN Immunity):** Proved that independent random coordinate fuzzing is completely defeated by Law of Large Numbers (LLN) averaging attacks ($\bar{x} \to x_{\text{true}}$). Implemented deterministic keyed polar displacement (1.5–3.0 km) per `field_id`, guaranteeing $100\%$ repeat query consistency, coupled with village name suppression (`[SUPPRESSED_FOR_PRIVACY]`) to eliminate quasi-identifier linkage.
5. **API Security & Cryptographic Audit Chaining:** Hardened `backend/app/api/pest_surveillance.py` with a 5 MB CSV payload size limit (HTTP 413), CSV formula injection (CWE-1236) neutralization, tamper-evident SHA-256 audit-log hash chaining with verification endpoint (`GET /pest-surveillance/audit-log/verify`), and role-based access restrictions for unmasked coordinates.
6. **DPDP Act Reality Check:** Replaced legally overstated claims of "100% certified DPDP compliance" with factual, legally accurate positioning acknowledging that MeitY subordinate rules remain unnotified, delineating statutory roles, and establishing a University Legal Counsel checklist.
7. **Comprehensive 12-Gate Go/No-Go Decision:** Formulated a formal 12-gate checklist. Gates 1–11 are NO-GO (Standby), while Gate 12 (Software Infrastructure) is GO. The composite project decision is **`NO-GO / PHYSICAL FIELD DEPLOYMENT IS STRICTLY BLOCKED`**.

---

## 2. Kharif 2027 Calendar Validation & Agronomic Audit

### 2.1 The 20-Week Weekly Visit Schedule
The Kharif 2027 pilot spans **Standard Meteorological Weeks (SMW) 24 through 43** (June 15 to October 31, 2027), consisting of 4 baseline weeks followed by 16 intensive weekly surveillance visits on Wednesdays (with a $\pm 48\text{ hour}$ weather contingency window):

| Week | Phase | SMW | Exact Wednesday Date | Crop Phenology | Target Pest Surveillance Focus | Lure Cycle (21-Day) |
|:---:|:---|:---:|:---:|:---|:---|:---:|
| 1 | Baseline 1 | 24 | Jun 16, 2027 | Land Prep / Sowing | Baseline cutworms, soil pests | Lure Cycle 1 (Provisional) |
| 2 | Baseline 2 | 25 | Jun 23, 2027 | Emergence | Early vegetative checks, sucking pests | Baseline reading |
| 3 | Baseline 3 | 26 | Jun 30, 2027 | Vegetative (V2–V4) | Soybean defoliation index, FAW whorls | Routine reading |
| 4 | Baseline 4 | 27 | Jul 07, 2027 | Mid Vegetative | *S. litura* egg masses, BPH lower culms | **Lure Cycle 2 Replace** |
| 5 | Intensive 1 | 28 | Jul 14, 2027 | Squaring Start | Cotton American bollworm square entry | Routine reading |
| 6 | Intensive 2 | 29 | Jul 21, 2027 | Squaring / Bloom | Pink Bollworm rosette flowers | Routine reading |
| 7 | Intensive 3 | 30 | Jul 28, 2027 | Flowering (R1) | PBW rosette flower counts, defoliation | **Lure Cycle 3 Replace** |
| 8 | Intensive 4 | 31 | Aug 04, 2027 | Peak Flowering | *H. armigera* young larvae, FAW plugs | Routine reading |
| 9 | Intensive 5 | 32 | Aug 11, 2027 | Early Boll (R3) | Destructive 20-boll dissection start | Routine reading |
| 10 | Intensive 6 | 33 | Aug 18, 2027 | Mid Boll Formation | PBW internal locule entry, BPH burn | **Lure Cycle 4 Replace** |
| 11 | Intensive 7 | 34 | Aug 25, 2027 | Peak Boll Fill | Destructive 20-boll sampling, BPH | Routine reading |
| 12 | Intensive 8 | 35 | Sep 01, 2027 | Boll Maturation | *P. gossypiella* exit holes, FAW ear | Routine reading |
| 13 | Intensive 9 | 36 | Sep 08, 2027 | Early Boll Burst | Destructive 20-boll sampling | **Lure Cycle 5 Replace** |
| 14 | Intensive 10 | 37 | Sep 15, 2027 | Boll Bursting | PBW late-season diapausing larvae | Routine reading |
| 15 | Intensive 11 | 38 | Sep 22, 2027 | Peak Boll Burst | Stained lint damage, final soybean | Routine reading |
| 16 | Intensive 12 | 39 | Sep 29, 2027 | Cotton First Picking| Destructive 20-boll dissection | **Lure Cycle 6 Replace** |
| 17 | Intensive 13 | 40 | Oct 06, 2027 | Second Picking | PBW locule damage in green bolls | Routine reading |
| 18 | Intensive 14 | 41 | Oct 13, 2027 | Third Flush | Diapause checks in green bolls | Routine reading |
| 19 | Intensive 15 | 42 | Oct 20, 2027 | Late Flush / Senescence| Final destructive boll dissection | **Lure Cycle 7 Replace** |
| 20 | Intensive 16 | 43 | Oct 27, 2027 | Harvest Completion | Cumulative damage tally | Final catch count |
| — | Close | 44 | Nov 03, 2027 | Post-Harvest Stalks | Trap decommissioning & residue audit | Trap Decommission |

### 2.2 Agronomic Calendar Discrepancies Flagged
1. **Lure Cycle 7 Truncation:** Pheromone lures have a chemical active life of 21 days. Installing Cycle 7 on Week 19 (October 20) for a pilot that concludes on Week 20 (October 27) means the lure is in service for only 7–11 days before decommissioning. Claiming "7 complete replacement cycles" is technically inaccurate; Cycle 7 is truncated mid-lifespan.
2. **Cotton Trap Sowing Timing Conflict:** Deploying Pink Bollworm pheromone lures at Week 1 (June 16) over bare soil violates standard ICAR-CICR guidelines. Standard ICAR recommendations dictate trap placement starting at **45 DAS** (squaring/flowering initiation, around mid-July). Sowing-time deployment in Vidarbha exposes pheromone septa to $>40^\circ\text{C}$ pre-monsoon heat, degrading the synthetic gossyplure chemical before moths are active or squares exist to host eggs. The pilot protocol must be amended before field deployment to initiate PBW pheromone monitoring at Week 5 (SMW 28).

---

## 3. Scientific Review of Emergency Escalation Protocol

### 3.1 Binomial Variance and Sample Size Noise
As detailed in `docs/emergency_escalation_scientific_review.md`, evaluating the $2.0 \times \text{ETL}$ trigger against small samples exposes the system to high false alarm rates:
- At $N = 5$ sampled units, $k = 1$ damaged unit yields an apparent incidence of $20.0\%$, immediately breaching the escalation threshold.
- The standard error at $N=5$ for $p=0.10$ is $\pm 13.4\%$, with a 95% Wilson confidence interval spanning $[3.6\%, 62.4\%]$.
- **Mandatory Guardrail:** Sampling effort minimums are now required ($N \ge 20$ bolls for cotton PBW, $N \ge 25$ plants for ABW, $N \ge 100$ plants for FAW).

### 3.2 Operational Unfeasibility of 4-Hour Response in Rural Vidarbha
- Intermittent 2G/zero cellular connectivity in interior blocks (e.g. Yavatmal, Katol) prevents real-time alert sync.
- Heavy monsoon rains cause black cotton soil (Vertisols) to become impassable clay mud, halting physical travel for 24–48 hours.
- A 4-hour physical SLA is operationally unachievable and creates false expectations; standard response time is calibrated to **24 to 48 hours**.

### 3.3 Status Reclassification
The emergency escalation protocol is formally classified as:
$$\textbf{PROVISIONAL — EXPERT APPROVAL REQUIRED}$$
Operational emergency notifications are strictly isolated and **never generate machine learning training labels ($Y \ne 1$)**.

---

## 4. Cryptographic Pseudonymization & Coordinate Privacy Hardening

### 4.1 Pseudonymization: Salted SHA-256 vs. Keyed HMAC-SHA-256
| Parameter | Phase 17 Salted SHA-256 | Phase 18 Keyed HMAC-SHA-256 |
|:---|:---:|:---:|
| Truncated Length | 6 Hex Characters | **12 Hex Characters** |
| Entropy Space | 24 bits ($1.67 \times 10^7$) | **48 bits ($2.81 \times 10^{14}$)** |
| Collision Prob ($N=5,000$) | $52.5\%$ (High risk) | **$< 10^{-7}$ (Negligible)** |
| Offline Dictionary Attack | Vulnerable if salt leaks | **Resistant (Secret Keyed HMAC)** |
| Collision Resolution | None (Data overwritten) | **Air-gapped Vault with `-C1`, `-C2`** |

### 4.2 Defeating Law of Large Numbers (LLN) Averaging Attacks
- **Random Fuzzing Vulnerability:** Querying an API with independent random noise $\epsilon \sim \mathcal{U}(-R, R)$ allows an adversary to compute the mean of $M$ responses: $\lim_{M \to \infty} \frac{1}{M}\sum \tilde{x}_i = x_{\text{true}}$.
- **Deterministic Keyed Displacement:** Derived via $\text{HMAC}(K, \text{field\_id})$, returning the exact identical displaced coordinate on every query:
  $$\frac{1}{M}\sum_{i=1}^M \tilde{x}_i = \tilde{x} \ne x_{\text{true}} \quad \forall M$$
- **Quasi-Identifier Suppression:** The `village` attribute is unconditionally masked as `[SUPPRESSED_FOR_PRIVACY]` in public exports, preventing micro-location linkage attacks.

---

## 5. Deployment Security & Operational API Controls

The following controls were implemented in `backend/app/api/pest_surveillance.py`:
1. **CSV Payload Size Restriction:** Enforced `MAX_CSV_SIZE_BYTES = 5 * 1024 * 1024` (5 MB). Files exceeding 5 MB are rejected with HTTP 413 (`REQUEST_ENTITY_TOO_LARGE`).
2. **Formula Injection Sanitization (CWE-1236):** All CSV text cells starting with `=`, `+`, `-`, `@`, `\t`, or `\r` are sanitized by prepending a single quote `'` unless the value is a valid numeric float/integer.
3. **Cryptographic Audit Log Hash Chaining:** Human review audit entries in `surveillance_audit_log.json` form a tamper-evident SHA-256 hash chain:
   $$\text{entry\_hash} = \text{SHA256}(\text{prev\_entry\_hash} \parallel \text{JSON}(\text{entry}))$$
4. **Audit Verification Endpoint:** `GET /pest-surveillance/audit-log/verify` validates the cryptographic integrity of the entire audit chain, reporting broken pointers or altered records.
5. **Coordinate Protection Gate:** `GET /pest-surveillance/records` defaults to `fuzz_coordinates=True`. Requesting unmasked coordinates (`fuzz_coordinates=False`) requires an authorized research API key in the `X-API-Key` header, returning HTTP 403 Forbidden for unauthorized requests.

---

## 6. Verification Test Results

```
┌────────────────────────────────────────────────────────────────────────┐
│                      VERIFICATION TEST SUMMARY                         │
├────────────────────────────────────────┬─────────┬──────────┬──────────┤
│ Test Suite                             │ Tests   │ Status   │ Time     │
├────────────────────────────────────────┼─────────┼──────────┼──────────┤
│ Security, Privacy & Cryptography Suite │ 12 / 12 │ PASSED   │ 2.57s    │
│ Field Pilot Simulation Suite           │ 14 / 14 │ PASSED   │ 2.11s    │
│ Field Surveillance Pipeline Suite      │ 32 / 32 │ PASSED   │ 4.89s    │
│ Full Backend Test Suite (21 Modules)   │ 170/170 │ PASSED   │ 55.50s   │
│ Frontend Unit Tests (Vitest)           │ 4 / 4   │ PASSED   │ 0.90s    │
│ Frontend Production Build (Vite)       │ 44 mod  │ PASSED   │ 0.90s    │
├────────────────────────────────────────┴─────────┴──────────┴──────────┤
│ Production Surveillance Store Records: 0 (Verified clean)              │
│ Supervised Outbreak ML Model Status: BLOCKED                           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. 12-Gate Go/No-Go Checklist Summary

As documented in `docs/physical_deployment_go_no_go_checklist.md`:
- **Gate 01 (University Ethics / IRB Clearance):** NO-GO (Not submitted).
- **Gate 02 (Institutional DUAs):** NO-GO (6 packages in pre-submission draft).
- **Gate 03 (KVK Partner Agreements):** NO-GO (Draft guides only).
- **Gate 04 (Field Scout Recruitment):** NO-GO (0 scouts hired).
- **Gate 05 (Farmer Informed Consent):** NO-GO (0 farmers enrolled).
- **Gate 06 (Sentinel Field Ground-Truthing):** NO-GO (0 plots surveyed).
- **Gate 07 (Hardware Procurement):** NO-GO (0 traps procured).
- **Gate 08 (Destructive Sampling Verification):** NO-GO (Pending expert sign-off).
- **Gate 09 (Entomological Review Panel):** NO-GO (Panel not yet formally seated).
- **Gate 10 (Legal Counsel DPDP Clearance):** NO-GO (Legal cell not engaged).
- **Gate 11 (Emergency Escalation Ratification):** NO-GO (Protocol PROVISIONAL).
- **Gate 12 (Software Infrastructure & Data Invariants):** **GO (100% OPERATIONAL)**.

### Composite Executive Determination:
$$\mathbf{PHYSICAL\ FIELD\ DEPLOYMENT\ IS\ STRICTLY\ BLOCKED}$$

---

## 8. Summary of Scientific Invariants Upheld

Throughout Phase 18, all foundational project commitments were rigorously maintained:
- **Zero synthetic observations created:** Production storage remains completely empty (0 records).
- **No external contacts made:** No institutions contacted, no emails sent, no scouts or farmers recruited.
- **No ML model trained:** Supervised pest outbreak model training remains strictly blocked.
- **ETL status preserved:** All 5 crop-pest ETLs remain at `PRIMARY_SOURCE_RETRIEVED`.
- **Existing modules untouched:** Fertilizer model, maize CNN, and unified advisory systems remain unchanged.

