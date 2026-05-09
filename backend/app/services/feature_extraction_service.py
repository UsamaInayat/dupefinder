"""
Extract comparison-friendly product features from description text.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Optional


_FABRIC_PATTERNS = {
    "khaddar": [r"\bkhaddar\b"],
    "karandi": [r"\bkarandi\b"],
    "cambric": [r"\bcambric\b"],
    "lawn": [r"\blawn\b"],
    "linen": [r"\blinen\b", r"\barabic linen\b"],
    "corduroy": [r"\bcorduroy\b"],
    "pashmina": [r"\bpashmina\b", r"\bpashmina blend\b"],
    "jacquard": [r"\bjacquard\b", r"\breverse jacquard\b"],
    "crepe": [r"\bcrepe\b", r"\bdobby crepe\b"],
    "dobby": [r"\bdobby\b"],
    "slub cotton": [r"\bslub cotton\b"],
    "cotton": [r"\bcotton\b"],
    "silk": [r"\bsilk\b", r"\bsilk[- ]?touch\b"],
    "chiffon": [r"\bchiffon\b"],
    "velvet": [r"\bvelvet\b"],
    "denim": [r"\bdenim\b"],
    "georgette": [r"\bgeorgette\b"],
    "viscose": [r"\bviscose\b"],
    "organza": [r"\borganza\b"],
    "net": [r"\bnet\b"],
}

_MATERIAL_PATTERNS = {
    "pu leather": [r"\bpu leather\b"],
    "faux leather": [r"\bfaux leather\b"],
    "leather": [r"\bleather\b"],
    "stainless steel": [r"\bstainless steel\b"],
    "zinc alloy": [r"\bzinc alloy\b"],
    "brass": [r"\bbrass\b"],
    "synthetic": [r"\bsynthetic\b"],
    "rubber": [r"\brubber\b"],
    "silicone": [r"\bsilicone\b"],
}

_FEATURE_PATTERNS = [
    r"\bwaterproof\b",
    r"\bwater resistant\b",
    r"\bstretchable\b",
    r"\bbreathable\b",
    r"\bembroidered\b",
    r"\bprinted\b",
    r"\bhandmade\b",
    r"\blightweight\b",
    r"\banti[- ]?slip\b",
    r"\bdual time\b",
    r"\bchronograph\b",
    r"\balarm\b",
    r"\bstitched\b",
    r"\bunstitched\b",
    r"\b2[ -]?piece\b",
    r"\b3[ -]?piece\b",
]

_TOKEN_STOPWORDS = frozenset(
    {
        "that",
        "this",
        "with",
        "from",
        "your",
        "have",
        "been",
        "will",
        "were",
        "their",
        "there",
        "these",
        "those",
        "about",
        "which",
        "would",
        "could",
        "should",
        "product",
        "products",
        "details",
        "description",
        "available",
        "shipping",
        "delivery",
        "please",
        "contact",
        "visit",
        "website",
        "color",
        "colors",
        "sizes",
        "size",
        "inch",
        "inches",
        "machine",
        "wash",
        "washing",
        "care",
        "instructions",
        "made",
        "using",
        "high",
        "best",
        "great",
        "good",
        "very",
        "more",
        "most",
        "some",
        "such",
        "also",
        "only",
        "just",
        "like",
        "each",
        "other",
        "into",
        "than",
        "then",
        "them",
        "when",
        "where",
        "while",
        "after",
        "before",
        "between",
        "through",
        "during",
        "without",
        "within",
        "across",
        "price",
        "offer",
        "stock",
    }
)


def _fallback_keywords(text: str, existing: set[str], *, max_tokens: int = 10) -> list[str]:
    """
    When pattern lists find nothing, pull distinctive lowercase tokens from the text
    (length >= 4, not stopwords) in first-seen order for search/compare use.
    """
    out: list[str] = []
    for m in re.finditer(r"\b[a-z]{4,}\b", text.lower()):
        w = m.group(0)
        if w in _TOKEN_STOPWORDS or w in existing:
            continue
        if w not in out:
            out.append(w)
        if len(out) >= max_tokens:
            break
    return out


_FABRIC_SPECIFICITY = {
    "khaddar": 100,
    "karandi": 95,
    "cambric": 92,
    "corduroy": 90,
    "pashmina": 90,
    "jacquard": 88,
    "crepe": 86,
    "dobby": 84,
    "slub cotton": 82,
    "lawn": 80,
    "linen": 78,
    "silk": 75,
    "chiffon": 74,
    "velvet": 73,
    "denim": 72,
    "georgette": 71,
    "viscose": 70,
    "organza": 69,
    "net": 68,
    "cotton": 40,
}


def _clean(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text or "").strip()
    return collapsed[:2000]


def _canonical_matches(text: str, mapping: dict[str, list[str]]) -> list[str]:
    """
    Returns canonical labels sorted by first occurrence in text.
    """
    found_positions: list[tuple[int, str]] = []
    for label, patterns in mapping.items():
        first_pos: Optional[int] = None
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                pos = match.start()
                if first_pos is None or pos < first_pos:
                    first_pos = pos
        if first_pos is not None:
            found_positions.append((first_pos, label))
    found_positions.sort(key=lambda item: item[0])
    return [label for _, label in found_positions]


def _all_matches(text: str, patterns: list[str]) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            token = match.group(0).strip().lower()
            if token not in found:
                found.append(token)
    return found


def _primary_fabric(candidates: list[str]) -> Optional[str]:
    if not candidates:
        return None
    return max(candidates, key=lambda c: _FABRIC_SPECIFICITY.get(c, 50))


def extract_features_from_description(description: str, name_text: str = "") -> dict:
    """
    Returns normalized feature fields for DB upsert.
    """
    text = _clean(f"{name_text} {description}".strip())
    if not text:
        return {
            "fabric": None,
            "material": None,
            "feature_keywords": [],
            "features": "",
        }

    fabric_matches = _canonical_matches(text, _FABRIC_PATTERNS)
    material_matches = _canonical_matches(text, _MATERIAL_PATTERNS)
    fabric = _primary_fabric(fabric_matches)
    material = material_matches[0] if material_matches else None
    feature_keywords = _all_matches(text, _FEATURE_PATTERNS)
    for f in fabric_matches[:2]:
        if f not in feature_keywords:
            feature_keywords.append(f)
    for m in material_matches[:2]:
        if m not in feature_keywords:
            feature_keywords.append(m)

    if not feature_keywords:
        existing = {k.lower() for k in feature_keywords}
        existing.update(fabric_matches)
        existing.update(material_matches)
        for w in _fallback_keywords(text, existing, max_tokens=10):
            feature_keywords.append(w)

    features_summary = ", ".join(feature_keywords[:6])

    return {
        "fabric": fabric,
        "material": material,
        "feature_keywords": feature_keywords,
        "features": features_summary,
    }


def should_merge_feature_field(current: object, overwrite: bool) -> bool:
    """Whether an extracted value may replace the current DB field."""
    if overwrite:
        return True
    if current is None:
        return True
    if isinstance(current, str):
        return current.strip() == ""
    if isinstance(current, list):
        return len(current) == 0
    return False


def feature_set_doc_from_product(doc: Mapping[str, Any], *, overwrite: bool) -> Optional[dict[str, Any]]:
    """
    Build a $set payload from name + description using extract_features_from_description.
    Only includes keys where the extractor produced a value and merge rules allow write.
    """
    desc = doc.get("description")
    if not isinstance(desc, str) or not desc.strip():
        return None
    extracted = extract_features_from_description(desc, str(doc.get("name") or ""))
    set_doc: dict[str, Any] = {}
    if extracted.get("fabric") and should_merge_feature_field(doc.get("fabric"), overwrite):
        set_doc["fabric"] = extracted["fabric"]
    if extracted.get("material") and should_merge_feature_field(doc.get("material"), overwrite):
        set_doc["material"] = extracted["material"]
    if extracted.get("feature_keywords") and should_merge_feature_field(
        doc.get("feature_keywords"), overwrite
    ):
        set_doc["feature_keywords"] = extracted["feature_keywords"]
    if extracted.get("features") and should_merge_feature_field(doc.get("features"), overwrite):
        set_doc["features"] = extracted["features"]
    return set_doc or None

