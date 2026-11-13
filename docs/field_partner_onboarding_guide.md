# AgriAdapt AI — Field Partner Onboarding & Surveillance Guide

**Component:** Maharashtra Field Pest Surveillance Pilot (Vidarbha & Khandesh)  
**Target Audience:** Krishi Vigyan Kendra (KVK) Scientists, University Field Researchers, and Agricultural Scouts  
**Applicable Districts:** Nagpur, Amravati, Yavatmal, Jalgaon  
**Target Cropping Season:** Kharif 2027 (Preparatory Pilot)  
**Version:** 1.0 (Operational Field Manual)  

---

## Welcome & Purpose

Welcome to the **AgriAdapt AI Field Surveillance Pilot**. This project is an open-source academic research initiative developing a seven-day pest outbreak early-warning system for smallholder agriculture in Maharashtra. 

Machine learning models require **authentic, weekly, plot-level field scouting data**. Your observations form the scientific ground truth against which early-warning alerts are validated. This manual explains how to conduct field scouting, record insect pest counts, submit data, and maintain farmer privacy.

---

## 1. Field Scouting Schedule & Sentinel Plots

- **Sentinel Field Continuity:** The same 20 selected farm plots (5 per district) will be monitored throughout the cropping season. Do not change plots mid-season.
- **Weekly Frequency:** Scouting occurs **every 7 days ($\pm 1$ day)**, ideally on the same day each week (e.g. every Tuesday morning).
- **Time of Day:** Conduct scouting between **7:00 AM – 10:30 AM** or **4:30 PM – 6:30 PM** when temperatures are moderate, insects are active, and foliage is dry.
- **Missed Visits Protocol:** If extreme weather or flooding prevents access on scheduled day, scout within the next 2 days. If a visit cannot take place, **leave the record blank**. *Never invent or estimate pest counts for an unvisited week.*

---

## 2. Species-Specific Scouting Protocols

### 2.1 Cotton Pink Bollworm (*Pectinophora gossypiella*)
1. **Flowering Stage (45–70 Days After Sowing - DAS):**
   - Walk a **'W'-pattern** across the 1-acre plot.
   - Inspect 20 randomly selected open flowers.
   - Count the number of **rosette flowers** (petals twisted/webbed together enclosing young larvae).
   - *Incidence % = (Rosette Flowers / 20) $\times$ 100*.
2. **Boll Development Stage (70–130 DAS):**
   - Randomly collect **20 green bolls** (approx. marble-sized to lemon-sized, 20–25 days old) across 20 distinct plants.
   - Dissect each boll cleanly in half using a penknife.
   - Inspect locules for internal burrowing, lint discoloration, or pink larvae.
   - *Damage % = (Damaged Bolls / 20) $\times$ 100*. (Economic Threshold: $\ge 10\%$).
3. **Pheromone Delta Traps:**
   - Install 2 Delta or Sleeve traps per acre with **Gossyplure** septa at canopy height.
   - Inspect moth catches twice weekly (e.g. Monday and Thursday mornings).
   - Record total moths per trap. Clean the sticky liner; replace lure septa every 21 days.
   - *ETL: 8–10 moths per trap per night for 3 consecutive nights*.

---

### 2.2 Cotton American Bollworm (*Helicoverpa armigera*)
- Walk a zigzag transect inspecting **20 consecutive plants**.
- Examine terminal shoots, tender squares, and small bolls.
- Look for flared squares (flared bracteoles), circular boreholes with fresh frass, or green/brown larvae.
- *ETL: 1 larva per plant OR 5% damaged fruiting bodies*.

---

### 2.3 Soybean Tobacco Caterpillar (*Spodoptera litura*) & Defoliators
- Select **5 random spots** per acre along a diagonal transect.
- At each spot, place a 1-meter white cloth or plastic sheet between rows.
- Shake the plants vigorously over the sheet; count dislodged larvae per 1-meter row length.
- Visually estimate leaf defoliation percentage across the sampled canopy.
- *ETL: 20–25% defoliation during flowering/pod-fill OR 10 larvae per meter row*.

---

### 2.4 Maize Fall Armyworm (*Spodoptera frugiperda*)
- Inspect **5 groups of 20 consecutive plants** across the field (100 plants total).
- Examine central whorls from top to bottom for:
  - Pin-holes and windowing on young leaves.
  - Moist, sawdust-like frass deep inside the whorl.
  - Live larvae hidden within whorls or ear tips.
- *ETL: 10% freshly damaged whorls with live larvae during mid-whorl stage (V4–V8)*.

---

### 2.5 Sucking Pests Complex (Aphids, Jassids, Thrips, Whiteflies)
- Randomly select **20 plants** across the plot.
- On each plant, count insects on **3 leaves**: 1 from top canopy, 1 from middle, 1 from bottom.
- *ETL for Jassids: 2 nymphs/leaf (yellowing/hopperburn along leaf margins)*.
- *ETL for Whitefly: 6–8 adults or nymphs/leaf*.

---

## 3. How to Submit Field Observations

Scouts and field researchers can submit observations through two methods:

### Method A: Web / Mobile Form Data Entry
1. Open the AgriAdapt AI dashboard on your phone or laptop.
2. Navigate to the **🔍 Field Surveillance** tab $\rightarrow$ **📝 Data Entry**.
3. Select District, Taluka, Village, and enter field coordinates.
4. Select Crop, Crop Variety, and Target Pest.
5. Enter quantitative measurements:
   - Plants Sampled (e.g. 20 bolls dissected).
   - Plants Affected (e.g. 2 bolls damaged).
   - Measured Incidence % (e.g. 10.0%).
   - Trap Catch (if trap inspected).
6. Enter your Observer ID (e.g. `SCOUT-NAG-01`).
7. Click **📤 Submit for Verification**. (Your record will immediately enter the review queue with status `UNVERIFIED`).

### Method B: Weekly Batch CSV Upload
If you record field visits on an offline spreadsheet, export it as a standard `.csv` file:
1. Ensure columns follow the template:
   `observation_date,district,taluka,village,latitude,longitude,crop,pest_common_name,pest_incidence_pct,plants_sampled,plants_affected,sampling_method,observer_id`
2. Navigate to **🔍 Field Surveillance** $\rightarrow$ **📤 Batch CSV Upload**.
3. Select your CSV file and click **Validate & Ingest CSV**.
4. The system validates all rows, checks Maharashtra bounds, detects duplicate rows, and provides a summary report.

---

## 4. Photographic Evidence & Quality Control

- **Mandatory Photo Threshold:** If you observe pest incidence or damage approaching or exceeding Economic Threshold Level ($\ge 80\%$ of ETL), you **must photograph the symptom**.
- **Photo Guidelines:**
  - Clear close-up of the dissected boll, whorl, or defoliated leaf with symptom visible.
  - Include a reference object (e.g. coin, pen, or finger) for scale.
  - Enable GPS location tagging on your camera smartphone if possible.
- **Supervisor Quality Audit:** 10% of sentinel fields will undergo random double-scouting by senior KVK entomologists within 24 hours to verify observation repeatability.

---

## 5. Farmer Privacy & Land Protection

As field researchers, protecting farmer trust is our highest ethical obligation:
- **Never Record Sensitive Personal Data:** Do not enter the farmer's full name, phone number, Aadhaar number, or 7/12 land parcel numbers in public fields.
- **Coordinate Fuzzing:** The system automatically obfuscates farm coordinates by adding random noise within a 1.0 km radius in any public-facing report or dashboard. The farmer's private boundaries are never published.
- **Informed Consent:** Ensure the participating farmer signs the standard one-page academic consent form explaining that crop health data will be studied for research early-warning models.

---

## 6. Escalation Protocol for Severe Pest Outbreaks

If you encounter an emergency pest flaring:
- e.g. $> 25\%$ Pink Bollworm boll damage, severe Fall Armyworm defoliation, or massive trap catches ($> 20\text{ moths/night}$):
1. **Immediate Notification:** Call your supervising KVK Senior Scientist or the District Agricultural Officer (DAO) within 24 hours.
2. **Advisory Formulation:** Guide the farmer to official university recommendations (e.g. ICAR-CICR or Dr. PDKV spray schedules). *Do not recommend unapproved or banned chemical mixtures.*
3. **Record Flagging:** Check the "Critical Outbreak" box on the data entry form and upload photos immediately for expedited verification.

