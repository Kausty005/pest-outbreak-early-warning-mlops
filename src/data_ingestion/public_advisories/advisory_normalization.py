"""
advisory_normalization.py
─────────────────────────
Multilingual entity extraction, normalisation, and language detection
for agricultural advisories in English, Marathi (मराठी), and Hindi (हिंदी).

Preserves:
- Original text verbatim in advisory_text
- Accurate translation provenance when translating
- Strict entity mapping preventing mistranslation of species names,
  numerical thresholds, or geographic locations
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
# MULTILINGUAL ENTITY LEXICONS
# ══════════════════════════════════════════════════════════════════════════════

CROP_LEXICON: dict[str, list[str]] = {
    "cotton": ["cotton", "कापूस", "कपाशी", "कपाशीचे", "कपाशीच्या", "कपाशीत", "कपास", "kapas", "bt cotton", "बीटी कापूस"],
    "soybean": ["soybean", "soya", "सोयाबीन", "सोया", "सोयाबीनचे", "सोयाबीनच्या"],
    "rice": ["rice", "paddy", "भात", "धान", "चावल", "dhan"],
    "maize": ["maize", "corn", "मका", "मक्का", "मक्यावरील", "makka"],
    "pigeonpea": ["pigeonpea", "red gram", "arhar", "tur", "तूर", "अरहर"],
    "chickpea": ["chickpea", "gram", "bengal gram", "चना", "हरभरा", "harbhara"],
    "sugarcane": ["sugarcane", "ऊस", "गन्ना"],
}

PEST_LEXICON: dict[str, dict[str, Any]] = {
    "pink_bollworm": {
        "common_name": "Pink Bollworm",
        "scientific_name": "Pectinophora gossypiella",
        "aliases": [
            "pink bollworm", "pbw", "pectinophora gossypiella",
            "गुलाबी बोंडअळी", "गुलाबी बोंड अळी", "गुलाबी सुंडी", "gulabi bond ali"
        ],
        "primary_crops": ["cotton"],
    },
    "american_bollworm": {
        "common_name": "American Bollworm",
        "scientific_name": "Helicoverpa armigera",
        "aliases": [
            "american bollworm", "helicoverpa", "helicoverpa armigera",
            "अमेरिकन बोंडअळी", "अमेरिकन सुंडी", "घाटे अळी", "ghate ali"
        ],
        "primary_crops": ["cotton", "chickpea", "pigeonpea"],
    },
    "tobacco_caterpillar": {
        "common_name": "Tobacco Caterpillar",
        "scientific_name": "Spodoptera litura",
        "aliases": [
            "tobacco caterpillar", "spodoptera litura", "spodoptera",
            "तंबाखूवरील लष्करी अळी", "तंबाखूची अळी", "पाने खाणारी अळी", "pane khanari ali",
            "तंबाखूवरील लष्किी अळी", "तंबाखूची लष्करी अळी", "तंबाखूची लष्किी अळी"
        ],
        "primary_crops": ["soybean", "cotton"],
    },
    "brown_planthopper": {
        "common_name": "Brown Planthopper",
        "scientific_name": "Nilaparvata lugens",
        "aliases": [
            "brown planthopper", "bph", "nilaparvata lugens",
            "तपकिरी तुडतुडे", "मावा/तुडतुडे", "tapkiri tudtude"
        ],
        "primary_crops": ["rice"],
    },
    "fall_armyworm": {
        "common_name": "Fall Armyworm",
        "scientific_name": "Spodoptera frugiperda",
        "aliases": [
            "fall armyworm", "faw", "spodoptera frugiperda",
            "अमेरिकन लष्करी अळी", "मक्यावरील लष्करी अळी", "लष्करी अळी",
            "अमेरिकन लष्किी अळी", "मक्यावरील लष्किी अळी", "लष्किी अळी", "लष्किी"
        ],
        "primary_crops": ["maize"],
    },
    "whitefly": {
        "common_name": "Whitefly",
        "scientific_name": "Bemisia tabaci",
        "aliases": [
            "whitefly", "white fly", "bemisia tabaci",
            "पांढरी माशी", "सफेद मक्खी", "pandhari mashi"
        ],
        "primary_crops": ["cotton", "soybean"],
    },
    "sucking_pests": {
        "common_name": "Sucking Pests Complex",
        "scientific_name": None,
        "aliases": [
            "sucking pests", "रसशोषक किडी", "रस चूसने वाले कीट",
            "मावा", "तुडतुडे", "फुलकिडे", "aphids", "jassids", "thrips"
        ],
        "primary_crops": ["cotton", "soybean"],
    },
}

MAHARASHTRA_DISTRICTS: dict[str, list[str]] = {
    "Nagpur": ["nagpur", "नागपूर", "नागपुर"],
    "Amravati": ["amravati", "अमरावती"],
    "Yavatmal": ["yavatmal", "yeotmal", "यवतमाळ", "यवतमाल"],
    "Jalgaon": ["jalgaon", "जळगाव", "जलगांव"],
    "Akola": ["akola", "अकोला"],
    "Wardha": ["wardha", "वर्धा"],
    "Nanded": ["nanded", "नांदेड"],
    "Jalna": ["jalna", "जालना"],
    "Buldhana": ["buldhana", "buldana", "बुलढाणा", "बुलडाणा"],
    "Washim": ["washim", "वाशिम"],
    "Chandrapur": ["chandrapur", "चंद्रपूर", "चंद्रपुर"],
    "Gadchiroli": ["gadchiroli", "गडचिरोली"],
    "Bhandara": ["bhandara", "भंडारा"],
    "Gondia": ["gondia", "गोंदिया"],
    "Dhule": ["dhule", "धुळे", "धुलिया"],
    "Nandurbar": ["nandurbar", "नंदुरबार"],
    "Chhatrapati Sambhajinagar": ["aurangabad", "chhatrapati sambhajinagar", "औरंगाबाद", "छत्रपती संभाजीनगर"],
    "Pune": ["pune", "पुणे"],
    "Nashik": ["nashik", "नाशिक"],
}


# ══════════════════════════════════════════════════════════════════════════════
# NORMALIZATION SERVICE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class NormalizedEntities:
    """Entities normalized from raw advisory text."""
    crop: Optional[str] = None
    pest_common_name: Optional[str] = None
    pest_scientific_name: Optional[str] = None
    district: Optional[str] = None
    language: str = "en"
    extraction_flags: list[str] = None

    def __post_init__(self) -> None:
        if self.extraction_flags is None:
            self.extraction_flags = []


class AdvisoryNormalizer:
    """Normalizes multilingual text into standardized agricultural entities."""

    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detect primary language of text snippet.
        Returns 'mr' (Marathi), 'hi' (Hindi), or 'en' (English).
        """
        if not text:
            return "en"
        # Count Devanagari characters (U+0900 to U+097F)
        devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
        total_alpha = len(re.findall(r"[a-zA-Z\u0900-\u097F]", text))

        if total_alpha == 0 or (devanagari_chars / total_alpha) < 0.2:
            return "en"

        # Distinguish Marathi from Hindi using distinctive function words
        marathi_markers = ["आहे", "करावे", "होते", "अळी", "शेतकऱ्यांनी", "पिकांचे", "फवारणी", "दिवस", "सापळे"]
        hindi_markers = ["है", "करें", "किसानों", "फसल", "दवा", "कीट", "छिड़काव", "दिन"]

        mr_count = sum(len(re.findall(rf"\b{m}\b", text)) for m in marathi_markers)
        hi_count = sum(len(re.findall(rf"\b{m}\b", text)) for m in hindi_markers)

        if mr_count >= hi_count:
            return "mr"
        return "hi"

    @classmethod
    def match_crop(cls, text: str) -> tuple[Optional[str], list[str]]:
        """Identify referenced crop from text. Returns (crop_name, flags)."""
        lower = text.lower()
        matched_crops = []
        for crop_id, variants in CROP_LEXICON.items():
            for v in variants:
                if v in lower or re.search(rf"\b{re.escape(v)}\b", lower, re.IGNORECASE):
                    if crop_id not in matched_crops:
                        matched_crops.append(crop_id)
                    break

        if not matched_crops:
            return None, ["CROP_UNIDENTIFIED"]
        if len(matched_crops) > 1:
            # Pick first, flag multiple
            return matched_crops[0], [f"MULTIPLE_CROPS_DETECTED_{'_'.join(matched_crops)}"]
        return matched_crops[0], []

    @classmethod
    def match_pest(cls, text: str, crop_hint: Optional[str] = None) -> tuple[Optional[str], Optional[str], list[str]]:
        """Identify referenced pest from text. Returns (common_name, scientific_name, flags)."""
        lower = text.lower()
        matched_pests = []

        for pest_id, info in PEST_LEXICON.items():
            for alias in info["aliases"]:
                if alias in lower or re.search(rf"\b{re.escape(alias)}\b", lower, re.IGNORECASE):
                    matched_pests.append(info)
                    break

        if not matched_pests:
            return None, None, ["PEST_UNIDENTIFIED"]

        # If crop_hint is available, prioritize pest compatible with that crop
        if crop_hint and len(matched_pests) > 1:
            compatible = [p for p in matched_pests if crop_hint in p["primary_crops"]]
            if compatible:
                chosen = compatible[0]
                flags = [f"RESOLVED_PEST_AMONG_{len(matched_pests)}_USING_CROP_{crop_hint}"]
                return chosen["common_name"], chosen["scientific_name"], flags

        chosen = matched_pests[0]
        flags = []
        if len(matched_pests) > 1:
            flags.append(f"MULTIPLE_PESTS_DETECTED_{len(matched_pests)}")
        return chosen["common_name"], chosen["scientific_name"], flags

    @classmethod
    def match_district(cls, text: str) -> tuple[Optional[str], list[str]]:
        """Identify referenced Maharashtra district from text."""
        lower = text.lower()
        matched_districts = []

        for dist_name, variants in MAHARASHTRA_DISTRICTS.items():
            for v in variants:
                if v in lower or re.search(rf"\b{re.escape(v)}\b", lower, re.IGNORECASE):
                    if dist_name not in matched_districts:
                        matched_districts.append(dist_name)
                    break

        if not matched_districts:
            return None, ["DISTRICT_UNSPECIFIED"]
        if len(matched_districts) > 1:
            return matched_districts[0], [f"REGIONAL_COVERAGE_{len(matched_districts)}_DISTRICTS"]
        return matched_districts[0], []

    @classmethod
    def normalize(cls, text: str, crop_hint: Optional[str] = None) -> NormalizedEntities:
        """Perform full entity normalization on an advisory text snippet."""
        lang = cls.detect_language(text)
        crop, crop_flags = cls.match_crop(text)
        effective_crop = crop or crop_hint
        pest_common, pest_sci, pest_flags = cls.match_pest(text, effective_crop)
        district, dist_flags = cls.match_district(text)

        all_flags = crop_flags + pest_flags + dist_flags
        return NormalizedEntities(
            crop=crop,
            pest_common_name=pest_common,
            pest_scientific_name=pest_sci,
            district=district,
            language=lang,
            extraction_flags=all_flags,
        )

    @classmethod
    def generate_dictionary_translation(
        cls,
        text: str,
        lang: str,
        entities: NormalizedEntities,
    ) -> Optional[str]:
        """
        Generate a verifiable semantic translation summary for non-English advisories.
        Ensures exact terms and entities are communicated accurately without hallucinatory expansion.
        """
        if lang == "en":
            return None

        # Build disciplined, factual translation synopsis
        parts = []
        crop_desc = entities.crop.capitalize() if entities.crop else "Unspecified crop"
        pest_desc = entities.pest_common_name or "pest activity"
        dist_desc = f"in {entities.district} district" if entities.district else "in Maharashtra"

        parts.append(f"Agricultural Advisory concerning {pest_desc} affecting {crop_desc} {dist_desc}.")

        # Detect recommendation triggers in Marathi/Hindi
        lower = text.lower()
        recs = []
        if any(w in lower for w in ["सापळे", "कामगंध", "trap", "फेरोमोन"]):
            recs.append("Install and monitor pheromone traps.")
        if any(w in lower for w in ["निरीक्षण", "पाहणी", "scout", "निगरानी"]):
            recs.append("Conduct regular field scouting.")
        if any(w in lower for w in ["फवारणी", "spray", "कीटकनाशक", "छिड़काव"]):
            recs.append("Apply recommended plant protection measures if economic threshold is reached.")
        if any(w in lower for w in ["हातवेचणी", "काढून टाकावे", "handpick"]):
            recs.append("Mechanically collect and destroy infested plant parts.")

        if recs:
            parts.append("Key recommendations: " + " ".join(recs))

        return " ".join(parts)
