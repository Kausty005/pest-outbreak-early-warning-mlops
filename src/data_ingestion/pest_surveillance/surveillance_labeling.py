"""
surveillance_labeling.py
────────────────────────
Scientifically defensible ground-truth outbreak labeling protocol
for future supervised early-warning classification.

LABELING RULES:
1. Target: Binary outbreak indicator within the subsequent 7-day forward window [T+1, T+7].
2. Grounded strictly in ICAR-NCIPM, ICAR-CICR, and FAO Economic Threshold Levels (ETL).
3. Zero lookahead leakage: Label describes outcomes occurring strictly AFTER observation date T.
4. Active Negative Sampling: An absent surveillance record DOES NOT imply non-occurrence.
   Only verified scouting visits reporting sub-ETL levels qualify as negative (0) labels.

ETL VERIFICATION POLICY (Phase 7 & Phase 13):
   Each EconomicThreshold carries a `verification_status` field with 5 scientific tiers:
   - "VERIFIED"                 — Confirmed in original monograph and approved by designated
                                  institutional expert review panel.
   - "EXPERT_REVIEW_PENDING"    — Primary monograph retrieved, awaiting formal expert committee sign-off.
   - "PRIMARY_SOURCE_RETRIEVED" — Verbatim threshold extracted directly from primary institutional
                                  research monograph or official technical bulletin; peer/board sign-off pending.
   - "PARTIALLY_VERIFIED"       — Value consistent with multiple secondary sources; exact original document
                                  not independently obtained.
   - "UNVERIFIED"               — Value could not be traced to any citable primary source.

   SAFETY RULES:
   1. UNVERIFIED ETLs: compute_forward_outbreak_label() MUST return label_status="ETL_UNVERIFIED"
      and outbreak_label_7d=None for any ETL with verification_status="UNVERIFIED".
   2. Production Enforcement: If `require_fully_verified_etl=True`, only "VERIFIED" ETLs may
      generate labels. All other statuses return label_status="ETL_NOT_PRODUCTION_VERIFIED".
   3. In exploratory mode (default `require_fully_verified_etl=False`), "VERIFIED",
      "EXPERT_REVIEW_PENDING", "PRIMARY_SOURCE_RETRIEVED", and "PARTIALLY_VERIFIED" ETLs may
      evaluate scouting visits, while "UNVERIFIED" is unconditionally rejected.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd

from src.data_ingestion.pest_surveillance.surveillance_schema import (
    SurveillanceRecord,
    normalize_token,
)

LOGGER = logging.getLogger(__name__)

# Valid verification status values for EconomicThreshold definitions
VALID_ETL_VERIFICATION_STATUSES = frozenset({
    "VERIFIED",
    "EXPERT_REVIEW_PENDING",
    "PRIMARY_SOURCE_RETRIEVED",
    "PARTIALLY_VERIFIED",
    "UNVERIFIED",
})
_VALID_VERIFICATION_STATUSES = VALID_ETL_VERIFICATION_STATUSES


@dataclass(frozen=True)
class EconomicThreshold:
    """Official agronomic action threshold for a pest-crop pair.

    Attributes:
        crop: Host crop name.
        pest_id: Target pest identifier.
        incidence_etl_pct: Baseline incidence percentage threshold.
        trap_catch_etl_moths: Adult moths per trap per night threshold.
        threshold_description: Full textual description of threshold conditions.
        source_authority: Citation of the primary institutional publication.
        verification_status: Scientific verification tier.
        stage_specific_incidence_etls: Optional mapping of growth stages to incidence thresholds.
        severity_etl_pct: Optional tissue damage or defoliation severity threshold (%).
        density_unit: Denominator/unit for larval or pest counts (e.g. "larvae_per_meter_row").
        stage_specific_density_etls: Optional mapping of growth stages to count densities.
        trap_catch_consecutive_nights_required: Number of consecutive nights trap threshold must be met (default 1).
        sampling_procedure: Standardized scouting procedure name.
    """
    crop: str
    pest_id: str
    incidence_etl_pct: float
    trap_catch_etl_moths: Optional[float]
    threshold_description: str
    source_authority: str
    verification_status: str = "PRIMARY_SOURCE_RETRIEVED"
    stage_specific_incidence_etls: Optional[dict[str, float]] = None
    severity_etl_pct: Optional[float] = None
    density_unit: Optional[str] = None
    stage_specific_density_etls: Optional[dict[str, float]] = None
    trap_catch_consecutive_nights_required: int = 1
    sampling_procedure: Optional[str] = None

    def __post_init__(self) -> None:
        if self.verification_status not in _VALID_VERIFICATION_STATUSES:
            raise ValueError(
                f"Invalid verification_status '{self.verification_status}'. "
                f"Must be one of {sorted(_VALID_VERIFICATION_STATUSES)}."
            )


def resolve_stage_specific_threshold(
    etl: EconomicThreshold,
    stage: Optional[str],
) -> float:
    """Resolve the effective incidence ETL threshold for a given crop growth stage."""
    if not stage or not etl.stage_specific_incidence_etls:
        return etl.incidence_etl_pct
    norm_st = normalize_token(stage)
    # Check exact match first
    if norm_st in etl.stage_specific_incidence_etls:
        return etl.stage_specific_incidence_etls[norm_st]
    # Check substring match
    for k, v in etl.stage_specific_incidence_etls.items():
        if k in norm_st or norm_st in k:
            return v
    return etl.incidence_etl_pct


def resolve_stage_specific_density_threshold(
    etl: EconomicThreshold,
    stage: Optional[str],
) -> Optional[float]:
    """Resolve the effective count density ETL for a given crop growth stage."""
    if not etl.stage_specific_density_etls:
        return None
    if not stage:
        return next(iter(etl.stage_specific_density_etls.values()), None)
    norm_st = normalize_token(stage)
    if norm_st in etl.stage_specific_density_etls:
        return etl.stage_specific_density_etls[norm_st]
    for k, v in etl.stage_specific_density_etls.items():
        if k in norm_st or norm_st in k:
            return v
    return next(iter(etl.stage_specific_density_etls.values()), None)


OFFICIAL_ETL_REGISTRY: dict[tuple[str, str], EconomicThreshold] = {
    ("cotton", "pink_bollworm"): EconomicThreshold(
        crop="cotton",
        pest_id="pink_bollworm",
        incidence_etl_pct=10.0,
        trap_catch_etl_moths=8.0,
        threshold_description=(
            "10% rosette flowers (flowering) or 10% damaged green bolls; "
            "OR 8–10 moths/pheromone trap/night for 3 consecutive nights. "
            "Sampling: 20 green bolls/acre by random destructive dissection."
        ),
        source_authority=(
            "ICAR-CICR Nagpur & Kranthi, K. R. (2015). 'Pink bollworm strikes Bt-cotton.' "
            "Cotton Statistics and News, 16(35): 1–6. Also: ICAR-CICR Technical Bulletin "
            "'Pink Bollworm Management Strategy in Bt Cotton' (2019–2021). "
            "Applicable: Vidarbha Vertisol cotton belt, squaring to boll maturation."
        ),
        verification_status="PRIMARY_SOURCE_RETRIEVED",
        stage_specific_incidence_etls={
            "squaring": 10.0,
            "flowering": 10.0,
            "boll_development": 10.0,
            "boll_formation": 10.0,
        },
        trap_catch_consecutive_nights_required=3,
        sampling_procedure="destructive_boll_dissection_20_bolls_per_acre",
    ),
    ("cotton", "american_bollworm"): EconomicThreshold(
        crop="cotton",
        pest_id="american_bollworm",
        incidence_etl_pct=5.0,
        trap_catch_etl_moths=5.0,
        threshold_description=(
            "5% damaged squares/fruiting bodies or 1 larva per plant; "
            "OR 5 moths/pheromone trap/night. "
            "Sampling: 20–25 randomly selected plants, inspecting squares, terminals, and bolls."
        ),
        source_authority=(
            "ICAR-NCIPM & ICAR-CICR. IPM Package for Cotton (Gossypium spp.) — Cotton Pest "
            "Management System (CPMS) Technical Guidelines (Surulivelu et al., 2007; NCIPM "
            "Technical Bulletin No. 12). Pusa Campus, New Delhi 110012. "
            "Applicable: Kharif cotton, flowering to boll development stage."
        ),
        verification_status="PRIMARY_SOURCE_RETRIEVED",
        density_unit="larvae_per_plant",
        stage_specific_density_etls={
            "squaring": 1.0,
            "flowering": 1.0,
            "boll_development": 1.0,
        },
        trap_catch_consecutive_nights_required=2,
        sampling_procedure="fruiting_body_scouting_20_to_25_plants",
    ),
    ("soybean", "tobacco_caterpillar"): EconomicThreshold(
        crop="soybean",
        pest_id="tobacco_caterpillar",
        incidence_etl_pct=20.0,
        trap_catch_etl_moths=10.0,
        threshold_description=(
            "20–25% defoliation or 10 larvae/m row length (pre-flowering and pod-fill stages), "
            "strictly adjusted down to 4 larvae/m row at flowering stage (due to flower abortion risk); "
            "OR 10 moths/pheromone trap/night. Sampling: 5 random 1-meter rows."
        ),
        source_authority=(
            "ICAR-IISR (Indian Institute of Soybean Research), Indore. "
            "Package of Practices for Soybean Crop Protection & Technical Bulletins (Sharma et al., "
            "ICAR-IISR). Aligned with AICRP Soybean guidelines. "
            "Applicable: Kharif soybean, V4 through R5 stages."
        ),
        verification_status="PRIMARY_SOURCE_RETRIEVED",
        stage_specific_incidence_etls={
            "vegetative": 25.0,
            "pre_flowering": 25.0,
            "flowering": 20.0,
            "bloom": 20.0,
            "pod_fill": 20.0,
            "pod_formation": 20.0,
        },
        severity_etl_pct=20.0,
        density_unit="larvae_per_meter_row",
        stage_specific_density_etls={
            "vegetative": 10.0,
            "pre_flowering": 10.0,
            "flowering": 4.0,
            "bloom": 4.0,
            "pod_fill": 10.0,
            "pod_formation": 10.0,
        },
        trap_catch_consecutive_nights_required=1,
        sampling_procedure="ground_sheet_beating_5_random_1m_rows",
    ),
    ("rice", "brown_planthopper"): EconomicThreshold(
        crop="rice",
        pest_id="brown_planthopper",
        incidence_etl_pct=10.0,
        trap_catch_etl_moths=None,
        threshold_description=(
            "10 planthoppers/nymphs per hill at active tillering stage; "
            "15–20 hoppers/hill at booting/heading (5–10 hoppers/hill in early tillering / endemic alerts). "
            "Sampling: 10 hills per plot, counting adults and nymphs at base of stems. "
            "No pheromone trap ETL established — monitoring is by hill sampling only."
        ),
        source_authority=(
            "ICAR-NRRI (National Rice Research Institute / formerly CRRI), Cuttack. "
            "Rice Pest Management Technical Bulletin No. 108 (Prakash et al., 2014) & IRRI Rice Knowledge Bank. "
            "Applicable: Kharif rice, tillering through heading stage."
        ),
        verification_status="PRIMARY_SOURCE_RETRIEVED",
        stage_specific_incidence_etls={
            "tillering": 10.0,
            "active_tillering": 10.0,
            "booting": 15.0,
            "heading": 15.0,
            "panicle_initiation": 15.0,
        },
        density_unit="hoppers_per_hill",
        stage_specific_density_etls={
            "tillering": 10.0,
            "booting": 15.0,
            "heading": 20.0,
        },
        trap_catch_consecutive_nights_required=1,
        sampling_procedure="zig_zag_stem_base_counting_10_hills",
    ),
    ("maize", "fall_armyworm"): EconomicThreshold(
        crop="maize",
        pest_id="fall_armyworm",
        incidence_etl_pct=10.0,
        trap_catch_etl_moths=5.0,
        threshold_description=(
            "10% freshly damaged whorls with live larvae at mid-whorl stage (V4–V8); "
            "5% damage threshold at early seedling (VE–V2); "
            "OR 5 moths/pheromone trap/night per FAMEWS monitoring protocol. "
            "Sampling: 20 consecutive plants across 5 stations (100 total plants)."
        ),
        source_authority=(
            "FAO (2018). Fall Armyworm Monitoring and Early Warning System (FAMEWS) Field Manual, "
            "Table 2.1. Also: ICAR-IIMR (Indian Institute of Maize Research), Ludhiana & PPQS (2019) "
            "Technical Bulletin on FAW Management in India. Applicable: Seedling to mid-whorl stages."
        ),
        verification_status="PRIMARY_SOURCE_RETRIEVED",
        stage_specific_incidence_etls={
            "seedling": 5.0,
            "early_whorl": 5.0,
            "vegetative": 10.0,
            "mid_whorl": 10.0,
            "late_whorl": 20.0,
            "tasseling": 20.0,
        },
        trap_catch_consecutive_nights_required=1,
        sampling_procedure="faw_famews_20_consecutive_plants_5_stations",
    ),
}


def get_economic_threshold(crop: str, pest: str) -> Optional[EconomicThreshold]:
    """Retrieve official ETL for a crop and pest pair."""
    norm_c = normalize_token(crop)
    norm_p = normalize_token(pest)
    # Check direct match
    if (norm_c, norm_p) in OFFICIAL_ETL_REGISTRY:
        return OFFICIAL_ETL_REGISTRY[(norm_c, norm_p)]
    # Partial match
    for (c, p), etl in OFFICIAL_ETL_REGISTRY.items():
        if c == norm_c and (p in norm_p or norm_p in p):
            return etl
    return None


@dataclass
class OutbreakLabelResult:
    """Labeling determination for a reference surveillance observation."""
    observation_id: str
    reference_date: str
    forward_window_start: str
    forward_window_end: str
    observations_found_in_forward_window: int
    outbreak_label_7d: Optional[int]  # 1 = Outbreak (>= ETL), 0 = Verified Non-Outbreak (< ETL), None = Unobserved
    max_forward_incidence_pct: Optional[float]
    max_forward_trap_catch: Optional[float]
    etl_incidence_applied: Optional[float]
    etl_trap_catch_applied: Optional[float]
    label_status: str  # "LABELED_OUTBREAK", "LABELED_NON_OUTBREAK", "UNOBSERVED_FUTURE_WINDOW", "MISSING_ETL"
    notes: str
    production_eligible: bool = False


def compute_forward_outbreak_label(
    record: SurveillanceRecord,
    longitudinal_surveillance_records: list[SurveillanceRecord],
    forward_days: int = 7,
    require_fully_verified_etl: bool = False,
) -> OutbreakLabelResult:
    """
    Compute forward outbreak label for record at observation_date T.

    Searches longitudinal records sharing the same location, crop, and pest
    within the forward window [T+1, T + forward_days].

    Args:
        record: The anchor observation at date T.
        longitudinal_surveillance_records: Candidate pool of observations.
        forward_days: Window length in days (default 7).
        require_fully_verified_etl: When True (production mode), requires the ETL to have
            verification_status="VERIFIED". If False (research/exploratory mode), permits
            "PARTIALLY_VERIFIED", "PRIMARY_SOURCE_RETRIEVED", and "EXPERT_REVIEW_PENDING",
            while strictly rejecting "UNVERIFIED".
    """
    ref_dt = datetime.strptime(record.observation_date[:10], "%Y-%m-%d").date()
    win_start = ref_dt + timedelta(days=1)
    win_end = ref_dt + timedelta(days=forward_days)

    win_start_str = win_start.strftime("%Y-%m-%d")
    win_end_str = win_end.strftime("%Y-%m-%d")

    # Biological compatibility check between host crop and pest
    from src.data_ingestion.pest_surveillance.surveillance_schema import VALID_CROP_PEST_COMBINATIONS
    norm_c = normalize_token(record.crop)
    norm_p = normalize_token(record.pest_common_name)
    is_biologically_valid = any(
        c == norm_c and (p in norm_p or norm_p in p)
        for c, p in VALID_CROP_PEST_COMBINATIONS
    )
    if not is_biologically_valid:
        return OutbreakLabelResult(
            observation_id=record.observation_id,
            reference_date=record.observation_date,
            forward_window_start=win_start_str,
            forward_window_end=win_end_str,
            observations_found_in_forward_window=0,
            outbreak_label_7d=None,
            max_forward_incidence_pct=None,
            max_forward_trap_catch=None,
            etl_incidence_applied=None,
            etl_trap_catch_applied=None,
            label_status="BIOLOGICAL_MISMATCH",
            notes=f"Incompatible biological combination: Pest '{record.pest_common_name}' does not parasitize crop '{record.crop}'.",
        )

    etl = get_economic_threshold(record.crop, record.pest_common_name)
    if etl is None:
        return OutbreakLabelResult(
            observation_id=record.observation_id,
            reference_date=record.observation_date,
            forward_window_start=win_start_str,
            forward_window_end=win_end_str,
            observations_found_in_forward_window=0,
            outbreak_label_7d=None,
            max_forward_incidence_pct=None,
            max_forward_trap_catch=None,
            etl_incidence_applied=None,
            etl_trap_catch_applied=None,
            label_status="MISSING_ETL",
            notes=f"No authoritative ETL threshold registered for crop '{record.crop}' and pest '{record.pest_common_name}'.",
        )

    # Safety rule 1: ETL with UNVERIFIED status must NEVER generate labels in any mode.
    if etl.verification_status == "UNVERIFIED":
        LOGGER.warning(
            "ETL for (%s, %s) has verification_status=UNVERIFIED. "
            "Labeling blocked to prevent scientifically unsupported ground-truth generation.",
            record.crop, record.pest_common_name,
        )
        return OutbreakLabelResult(
            observation_id=record.observation_id,
            reference_date=record.observation_date,
            forward_window_start=win_start_str,
            forward_window_end=win_end_str,
            observations_found_in_forward_window=0,
            outbreak_label_7d=None,
            max_forward_incidence_pct=None,
            max_forward_trap_catch=None,
            etl_incidence_applied=etl.incidence_etl_pct,
            etl_trap_catch_applied=etl.trap_catch_etl_moths,
            label_status="ETL_UNVERIFIED",
            notes=(
                f"ETL for crop='{record.crop}', pest='{record.pest_common_name}' has "
                f"verification_status='UNVERIFIED'. Labeling suspended until ETL is traced "
                f"to a primary authoritative source. Source currently cited: {etl.source_authority}."
            ),
        )

    # Safety rule 2: In production mode, require fully signed "VERIFIED" status.
    if require_fully_verified_etl and etl.verification_status != "VERIFIED":
        LOGGER.warning(
            "Production mode requires fully VERIFIED ETL. (%s, %s) has verification_status=%s.",
            record.crop, record.pest_common_name, etl.verification_status,
        )
        return OutbreakLabelResult(
            observation_id=record.observation_id,
            reference_date=record.observation_date,
            forward_window_start=win_start_str,
            forward_window_end=win_end_str,
            observations_found_in_forward_window=0,
            outbreak_label_7d=None,
            max_forward_incidence_pct=None,
            max_forward_trap_catch=None,
            etl_incidence_applied=etl.incidence_etl_pct,
            etl_trap_catch_applied=etl.trap_catch_etl_moths,
            label_status="ETL_NOT_PRODUCTION_VERIFIED",
            notes=(
                f"Production enforcement active (require_fully_verified_etl=True), but ETL for "
                f"crop='{record.crop}', pest='{record.pest_common_name}' has verification_status='{etl.verification_status}'. "
                f"Requires signed expert validation ('VERIFIED') before production labels can be computed."
            ),
        )

    # Find subsequent observations for same location, crop, pest in forward window
    target_crop_norm = normalize_token(record.crop)
    target_pest_norm = normalize_token(record.pest_common_name)
    target_dist_norm = normalize_token(record.district)
    target_taluka_norm = normalize_token(record.taluka) if record.taluka else None

    forward_matches: list[SurveillanceRecord] = []
    for cand in longitudinal_surveillance_records:
        if cand.observation_id == record.observation_id:
            continue
        cand_dt = datetime.strptime(cand.observation_date[:10], "%Y-%m-%d").date()
        if win_start <= cand_dt <= win_end:
            if normalize_token(cand.crop) == target_crop_norm and normalize_token(cand.pest_common_name) == target_pest_norm:
                if normalize_token(cand.district) == target_dist_norm:
                    if target_taluka_norm is None or normalize_token(cand.taluka) == target_taluka_norm:
                        forward_matches.append(cand)

    if not forward_matches:
        # Crucial: Unobserved forward window must NEVER be defaulted to 0!
        return OutbreakLabelResult(
            observation_id=record.observation_id,
            reference_date=record.observation_date,
            forward_window_start=win_start_str,
            forward_window_end=win_end_str,
            observations_found_in_forward_window=0,
            outbreak_label_7d=None,
            max_forward_incidence_pct=None,
            max_forward_trap_catch=None,
            etl_incidence_applied=etl.incidence_etl_pct,
            etl_trap_catch_applied=etl.trap_catch_etl_moths,
            label_status="UNOBSERVED_FUTURE_WINDOW",
            notes=(
                f"No authentic surveillance records found between {win_start_str} and {win_end_str}. "
                "Negative label cannot be established without verified field scouting."
            ),
        )

    incidences = [m.pest_incidence_pct for m in forward_matches if m.pest_incidence_pct is not None]
    traps = [m.trap_catch_count for m in forward_matches if m.trap_catch_count is not None]
    severities = [m.pest_severity_pct for m in forward_matches if m.pest_severity_pct is not None]

    # Check whether any valid quantitative measurement was recorded
    has_valid_measurements = bool(incidences or traps or severities)
    if not has_valid_measurements and etl.stage_specific_density_etls is not None:
        for m in forward_matches:
            if m.plants_affected is not None and m.plants_sampled is not None and m.plants_sampled > 0:
                has_valid_measurements = True
                break

    if not has_valid_measurements:
        return OutbreakLabelResult(
            observation_id=record.observation_id,
            reference_date=record.observation_date,
            forward_window_start=win_start_str,
            forward_window_end=win_end_str,
            observations_found_in_forward_window=len(forward_matches),
            outbreak_label_7d=None,
            max_forward_incidence_pct=None,
            max_forward_trap_catch=None,
            etl_incidence_applied=etl.incidence_etl_pct,
            etl_trap_catch_applied=etl.trap_catch_etl_moths,
            label_status="MISSING_MEASUREMENTS",
            notes=(
                f"Surveillance visit(s) found in forward window ({len(forward_matches)} visits), "
                "but no quantitative measurements (incidence, trap catch, severity, density) were recorded. "
                "Missing measurements cannot be treated as sub-ETL zero negative labels."
            ),
            production_eligible=False,
        )

    max_inc = max(incidences) if incidences else None
    max_trap = max(traps) if traps else None
    max_sev = max(severities) if severities else None

    # Check positive conditions across all agronomic indicators
    is_outbreak = False
    reasons: list[str] = []

    # 1. Growth-stage-specific or baseline incidence check
    for m in forward_matches:
        if m.pest_incidence_pct is not None:
            eff_etl = resolve_stage_specific_threshold(etl, m.crop_growth_stage)
            if m.pest_incidence_pct >= eff_etl:
                is_outbreak = True
                stage_label = f" for stage '{m.crop_growth_stage}'" if m.crop_growth_stage else " (stage unspecified)"
                reasons.append(
                    f"Observation ({m.observation_id}) incidence ({m.pest_incidence_pct:.1f}%) >= ETL ({eff_etl:.1f}%{stage_label})"
                )

    # 2. Defoliation / tissue damage severity check
    if etl.severity_etl_pct is not None and max_sev is not None and max_sev >= etl.severity_etl_pct:
        is_outbreak = True
        reasons.append(f"Max severity ({max_sev:.1f}%) >= Severity ETL ({etl.severity_etl_pct:.1f}%)")

    # 3. Trap catch check with consecutive-night sequence evaluation
    if etl.trap_catch_etl_moths is not None:
        trap_records = [m for m in forward_matches if m.trap_catch_count is not None]
        if trap_records:
            req_nights = etl.trap_catch_consecutive_nights_required
            if req_nights > 1:
                # Sort trap records chronologically
                trap_records_sorted = sorted(
                    trap_records,
                    key=lambda r: datetime.strptime(r.observation_date[:10], "%Y-%m-%d").date()
                )
                max_consecutive = 0
                current_consecutive = 0
                prev_date = None
                for tr in trap_records_sorted:
                    cur_date = datetime.strptime(tr.observation_date[:10], "%Y-%m-%d").date()
                    if tr.trap_catch_count >= etl.trap_catch_etl_moths:
                        if prev_date is None or cur_date == prev_date + timedelta(days=1):
                            current_consecutive += 1
                        else:
                            # A date gap or missing daily observation breaks the streak
                            current_consecutive = 1
                        max_consecutive = max(max_consecutive, current_consecutive)
                    else:
                        current_consecutive = 0
                    prev_date = cur_date

                if max_consecutive >= req_nights:
                    is_outbreak = True
                    reasons.append(
                        f"Trap catch sustained {max_consecutive} consecutive night(s) >= ETL ({etl.trap_catch_etl_moths:.1f} moths/night, req={req_nights})"
                    )
            else:
                # Single night required (e.g. FAW, Spodoptera litura)
                if max_trap is not None and max_trap >= etl.trap_catch_etl_moths:
                    is_outbreak = True
                    reasons.append(f"Max trap catch ({max_trap:.1f}) >= ETL ({etl.trap_catch_etl_moths:.1f} moths/night)")

    # 4. Count density / larvae per unit check
    if etl.stage_specific_density_etls is not None:
        for m in forward_matches:
            if m.plants_affected is not None and m.plants_sampled is not None and m.plants_sampled > 0:
                eff_density_etl = resolve_stage_specific_density_threshold(etl, m.crop_growth_stage)
                if eff_density_etl is not None:
                    density = m.plants_affected / m.plants_sampled
                    if density >= eff_density_etl:
                        is_outbreak = True
                        unit_str = etl.density_unit or "units"
                        stage_label = f" for stage '{m.crop_growth_stage}'" if m.crop_growth_stage else " (stage unspecified)"
                        reasons.append(
                            f"Observation ({m.observation_id}) count density ({density:.2f} {unit_str}) >= Density ETL ({eff_density_etl:.2f} {unit_str}{stage_label})"
                        )

    is_prod_eligible = (etl.verification_status == "VERIFIED")

    if is_outbreak:
        return OutbreakLabelResult(
            observation_id=record.observation_id,
            reference_date=record.observation_date,
            forward_window_start=win_start_str,
            forward_window_end=win_end_str,
            observations_found_in_forward_window=len(forward_matches),
            outbreak_label_7d=1,
            max_forward_incidence_pct=max_inc,
            max_forward_trap_catch=max_trap,
            etl_incidence_applied=etl.incidence_etl_pct,
            etl_trap_catch_applied=etl.trap_catch_etl_moths,
            label_status="LABELED_OUTBREAK",
            notes="; ".join(reasons),
            production_eligible=is_prod_eligible,
        )

    # If active scouting occurred and all values remained below ETL, valid negative label (0)
    return OutbreakLabelResult(
        observation_id=record.observation_id,
        reference_date=record.observation_date,
        forward_window_start=win_start_str,
        forward_window_end=win_end_str,
        observations_found_in_forward_window=len(forward_matches),
        outbreak_label_7d=0,
        max_forward_incidence_pct=max_inc,
        max_forward_trap_catch=max_trap,
        etl_incidence_applied=etl.incidence_etl_pct,
        etl_trap_catch_applied=etl.trap_catch_etl_moths,
        label_status="LABELED_NON_OUTBREAK",
        notes=f"Active scouting confirmed sub-ETL levels across {len(forward_matches)} visits in 7-day window.",
        production_eligible=is_prod_eligible,
    )

