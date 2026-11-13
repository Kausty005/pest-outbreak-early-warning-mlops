# AgriAdapt AI — Pseudonymization, Coordinate Privacy & Re-Identification Risk Audit

**Document ID:** `AGRI-SEC-PRIVACY-AUDIT-2027-V1`  
**Version:** 1.0.0  
**Phase:** 18  
**Scope:** Cryptographic, Information-Theoretic, and Spatial Privacy Architecture Audit  
**Classification:** TECHNICAL AUDIT REPORT  
**Compliance Target:** ISO/IEC 27701 Privacy Information Management & DPDP Act 2023 Technical Guardrails

---

## 1. Executive Summary

Field agricultural surveillance inevitably collects sensitive information regarding identifiable farmers, land survey parcels, and geographic plot locations. If farm coordinates or identities leak, farmers face serious real-world risks:
- Commercial exploitation by aggressive agrochemical salespeople targeting high-infestation farms.
- Financial or credit penalties from informal money lenders or crop insurers inferring crop failure from pest alerts.
- Stigmatization within village communities if an outbreak is perceived as poor farm sanitation.

This document conducts an independent technical audit of the privacy mechanisms introduced in Phase 17 and hardened in Phase 18:
1. **Transition from Naive Salted Hashes to Keyed HMAC-SHA-256 (48-bit Entropy).**
2. **Deterministic Spatial Displacement (1.5–3.0 km) Defeating Law of Large Numbers (LLN) Averaging Attacks.**
3. **Quasi-Identifier Linkage Vulnerabilities and Mitigation (Village Name Suppression).**
4. **Air-Gapped Identity Vault Architecture and Collision Resolution.**

---

## 2. Farmer Identity Pseudonymization: Mathematical & Entropy Analysis

### 2.1 The Vulnerability of 24-Bit Naive Salted Hashes (Phase 17)
Phase 17 initially proposed generating farmer identifiers by taking the first 6 hexadecimal characters of a salted SHA-256 hash:
$$\text{ID} = \text{SHA256}(\text{salt} \parallel \text{farmer\_name})[0:6]$$

#### Entropy and Birthday Collision Analysis:
- 6 hexadecimal characters represent $b = 24\text{ bits}$ of entropy:
  $$N_{\text{space}} = 16^6 = 2^{24} = 16,777,216\text{ possible states}$$
- Under the Birthday Paradox, the collision probability for $n$ registered entities is approximated by:
  $$P(\text{collision}) \approx 1 - \exp\left(-\frac{n(n-1)}{2 N_{\text{space}}}\right) \approx 1 - \exp\left(-\frac{n^2}{2 \times 1.67 \times 10^7}\right)$$
- For a regional scaling target of $n = 5,000$ farmers across Maharashtra:
  $$P(\text{collision}) \approx 1 - \exp\left(-\frac{25 \times 10^6}{3.35 \times 10^7}\right) \approx 1 - \exp(-0.745) \approx 52.5\%$$
A 52.5% probability of identity collision across 5,000 farmers is unacceptably high for production systems. Furthermore, a simple static salt is vulnerable to pre-computation or offline dictionary attacks if the salt leaks.

---

### 2.2 Hardened Architecture: Keyed HMAC-SHA-256 (48-bit Entropy)
In Phase 18 (`surveillance_pseudonymization.py`), the pseudonymization engine was completely re-architected:

```
[ Input: Legal Name + Land Survey No + District ]
                      │
                      ▼
            [ Secret Key K (HMAC) ]
                      │
                      ▼
         [ HMAC-SHA256(K, Payload) ]
                      │
                      ▼
        [ Truncate to 12 Hex Chars (48 Bits) ]
                      │
                      ▼
         FMR-{DIST}-{12_HEX_HMAC}
```

#### Entropy and Collision Probability:
- 12 hexadecimal characters represent $b = 48\text{ bits}$ of entropy:
  $$N_{\text{space}} = 16^{12} = 2^{48} \approx 2.8147 \times 10^{14}\text{ possible states}$$
- For $n = 10,000$ registered farmers:
  $$P(\text{collision}) \approx \frac{(10^4)^2}{2 \times 2.8147 \times 10^{14}} = \frac{10^8}{5.63 \times 10^{14}} \approx 1.776 \times 10^{-7}$$
- Even at $n = 1,000,000$ farmers:
  $$P(\text{collision}) \approx \frac{(10^6)^2}{5.63 \times 10^{14}} = \frac{10^{12}}{5.63 \times 10^{14}} \approx 0.177\%$$
At under $2 \times 10^{-7}$ for the pilot cohort, birthday collisions are statistically negligible.

#### Cryptographic Advantages of HMAC over Hash Prepending:
1. **Keyed Security:** Unlike unkeyed SHA-256, HMAC ($H(K \oplus \text{opad} \parallel H(K \oplus \text{ipad} \parallel M))$) guarantees unforgeability and prevents length-extension attacks.
2. **Dictionary Attack Resistance:** An attacker possessing the public farmer list cannot verify guesses without possessing the private key $K$.
3. **Key Rotation Support:** By versioning secret keys ($K_1, K_2$), identity mappings can be rotated across multi-year surveillance cohorts.

---

## 3. Coordinate Privacy & Law of Large Numbers (LLN) Averaging Attacks

### 3.1 The Vulnerability of Dynamic Random Fuzzing
A common privacy failure mode in geospatial systems is applying independent uniform or Gaussian noise on every API request:
$$\tilde{x}_t = x_{\text{true}} + \epsilon_t, \quad \epsilon_t \sim \mathcal{U}(-R, R)$$

#### Mathematical Proof of Vulnerability (Averaging Attack):
Suppose an adversary queries the public surveillance API $M$ times for a specific target plot over the season:
$$\bar{x}_M = \frac{1}{M}\sum_{t=1}^M \tilde{x}_t = x_{\text{true}} + \frac{1}{M}\sum_{t=1}^M \epsilon_t$$
By the Central Limit Theorem and the Weak Law of Large Numbers (WLLN):
$$\lim_{M \to \infty} \frac{1}{M}\sum_{t=1}^M \epsilon_t = \mathbb{E}[\epsilon] = 0$$
The standard error of the attacker's estimate decreases as $O(1/\sqrt{M})$:
$$\text{Var}(\bar{x}_M) = \frac{\sigma_\epsilon^2}{M}$$
For $R = 2.0\text{ km}$ ($\sigma \approx 1.15\text{ km}$), after $M = 100$ queries:
$$\text{SE}(\bar{x}_{100}) \approx \frac{1.15}{10} \approx 115\text{ meters}$$
After $M = 10,000$ automated queries, the precision reaches $\approx 11\text{ meters}$, pinpointing the exact field boundary and defeating the entire privacy budget.

---

### 3.2 The Phase 18 Solution: Deterministic Keyed Spatial Displacement
To completely eliminate LLN averaging attacks, the displacement vector must be **strictly deterministic for each field**:

$$\theta = 2\pi \cdot \frac{\text{HMAC}(K, \text{"ANGLE"} \parallel \text{field\_id}) \pmod{2^{32}}}{2^{32}}$$
$$r = R_{\min} + (R_{\max} - R_{\min}) \cdot \frac{\text{HMAC}(K, \text{"RADIUS"} \parallel \text{field\_id}) \pmod{2^{32}}}{2^{32}}$$
$$\Delta \text{lat} = \frac{r \sin\theta}{111.0}, \quad \Delta \text{lon} = \frac{r \cos\theta}{104.3}$$
$$\tilde{x} = x_{\text{true}} + \Delta \text{lat}, \quad \tilde{y} = y_{\text{true}} + \Delta \text{lon}$$

#### Properties Established:
1. **$100\%$ Query Reproducibility:** Querying the public API 10,000 times for `MAH-NGP-KAT-001` returns the exact same coordinates $(\tilde{x}, \tilde{y})$.
   $$\bar{x}_M = \tilde{x} \ne x_{\text{true}} \quad \forall M$$
   The attacker's sample mean is identical to any single sample; zero information is gained from repeated querying.
2. **Bounded Distance:** The displacement distance $r$ is guaranteed to lie within $[1.5, 3.0]\text{ km}$, protecting farm privacy while preserving regional agro-climatic validity.
3. **Field Isolation:** Two sentinel fields located in the same village receive independent displacement vectors derived from their distinct field IDs, preventing cluster analysis from reconstructing original relative spacing.

---

## 4. Quasi-Identifier Linkage Risk & Public Sanitization

Even with cryptographically pseudonymous IDs and fuzzed coordinates, records can be re-identified through **Quasi-Identifier Linkage Attacks** (Latanya Sweeney, 2002).

### 4.1 Agronomic Quasi-Identifier Tuples
In rural Maharashtra, an agricultural observation contains several public or semi-public attributes:
$$Q = (\text{District}, \text{Taluka}, \text{Village}, \text{Crop}, \text{Variety}, \text{Sowing Date}, \text{Field Size})$$

#### Re-Identification Scenario:
- In village *Paradsinga* (Taluka Katol, District Nagpur), there may be only 30 cotton-growing farmers.
- Among those 30, only 2 farmers planted hybrid *RCH-659 BG-II* on the exact date *June 18, 2027*.
- If the public dataset exposes `(Paradsinga, Cotton, RCH-659, 2027-06-18)`, the candidate pool shrinks from thousands to **2 farmers**.
- An adversary knowing one of the two had a pest infestation can identify the farm with $>50\%$ certainty.

### 4.2 Sanitization Policy (`sanitize_public_surveillance_record`)
To enforce robust $k$-anonymity across the dataset, Phase 18 implements strict public export sanitization:
1. **Village Name Suppression:** The `village` attribute is unconditionally overwritten with `[SUPPRESSED_FOR_PRIVACY]`. Taluka and district are retained, ensuring the anonymity set size $k$ exceeds several thousand farms.
2. **Observer & Reviewer PII Removal:** Internal researcher IDs, scout phone numbers, and free-text notes containing personal references are completely stripped.
3. **Coordinate Masking:** Unauthenticated or public endpoints unconditionally displace coordinates by 1.5–3.0 km.
4. **Access Control Gate:** Retrieval of unmasked farm coordinates (`fuzz_coordinates=False`) is restricted to authorized researchers presenting a valid HMAC-authenticated `X-API-Key`.

---

## 5. Air-Gapped Identity Vault Architecture

To enforce strict separation of duties, identity mappings are isolated in the `IdentityVault` module:

```
┌───────────────────────────────────────┐      ┌──────────────────────────────────────┐
│       OPERATIONAL DATABASE            │      │        AIR-GAPPED IDENTITY VAULT     │
│   (data/processed/pest_surveillance/) │      │    (data/vault/surveillance_vault)   │
├───────────────────────────────────────┤      ├──────────────────────────────────────┤
│ • field_id: MAH-NGP-KAT-001           │      │ • field_id: MAH-NGP-KAT-001          │
│ • farmer_id: FMR-NAG-9E2A8F14BC01     │  X   │ • farmer_id: FMR-NAG-9E2A8F14BC01    │
│ • observation_date: 2027-07-14        │      │ • Legal Name: Ramesh B. Patil        │
│ • pest_incidence_pct: 12.5%           │      │ • Survey No: Gut No. 74/2A           │
│ • fuzzed_lat: 21.0621, lon: 78.9642   │      │ • Masked Phone: +91-XXXXX-3210       │
│ • verification_status: VALIDATED      │      │ • Signed DPDP Consent SHA-256        │
└───────────────────────────────────────┘      └──────────────────────────────────────┘
                     ▲                                            ▲
                     │                                            │
               Public / API                               Strict Admin Token
```

### 5.1 Collision Resolution in IdentityVault
While HMAC collision probability is $< 10^{-6}$, the vault includes explicit defensive handling:
- If a registration matches both name and survey number: returns existing ID (idempotency).
- If a hash collision occurs between two distinct legal entities: detects collision and automatically appends a collision counter suffix (`-C1`, `-C2`), logging an audit alert.

---

## 6. Audit Conclusion & Compliance Status

The Phase 18 privacy enhancements achieve state-of-the-art protection for prospective field surveillance data:
- **Entropy:** 48 bits (HMAC-SHA-256) renders collision attacks unfeasible.
- **Geospatial Privacy:** Deterministic spatial displacement renders Law of Large Numbers averaging attacks mathematically ineffective.
- **Quasi-Identifier Protection:** Village suppression and attribute sanitization eliminate micro-location linkage.
- **Role Isolation:** The identity vault prevents accidental leakage of farmer identities to modelers and public consumers.

