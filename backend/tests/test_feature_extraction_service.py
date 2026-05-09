from app.services.feature_extraction_service import (
    extract_features_from_description,
    feature_set_doc_from_product,
)


def test_extract_features_from_description_with_common_terms():
    desc = (
        "Premium cotton lawn kurta, breathable and lightweight, "
        "with embroidered front and water resistant finish."
    )
    out = extract_features_from_description(desc)

    assert out["fabric"] in {"cotton", "lawn"}
    assert out["material"] is None
    assert "breathable" in out["feature_keywords"]
    assert "lightweight" in out["feature_keywords"]
    assert "embroidered" in out["feature_keywords"]
    assert isinstance(out["features"], str)
    assert out["features"] != ""


def test_extract_features_from_empty_description():
    out = extract_features_from_description("")
    assert out["fabric"] is None
    assert out["material"] is None
    assert out["feature_keywords"] == []
    assert out["features"] == ""


def test_extract_features_from_name_when_description_missing():
    out = extract_features_from_description(
        "",
        name_text="Printed Warm Khaddar Stitched 2 Piece",
    )
    assert out["fabric"] == "khaddar"


def test_feature_set_doc_from_product_fills_empty_only():
    doc = {
        "name": "Shirt",
        "description": "Soft silk shirt, breathable and lightweight.",
        "fabric": "",
        "material": None,
        "features": "",
        "feature_keywords": [],
    }
    patch = feature_set_doc_from_product(doc, overwrite=False)
    assert patch is not None
    assert patch["fabric"] == "silk"
    assert "breathable" in patch["feature_keywords"]
    assert patch["features"]


def test_feature_set_doc_from_product_respects_nonempty():
    doc = {
        "name": "X",
        "description": "Cotton lawn piece.",
        "fabric": "lawn",
        "material": None,
        "features": "existing",
        "feature_keywords": ["cotton"],
    }
    patch = feature_set_doc_from_product(doc, overwrite=False)
    assert patch is None or "fabric" not in patch


def test_extract_features_fallback_keywords_without_patterns():
    desc = (
        "Premium elegant garment tailored for daily comfort and refined appearance "
        "with subtle texture throughout."
    )
    out = extract_features_from_description(desc)
    assert out["fabric"] is None
    assert out["material"] is None
    assert len(out["feature_keywords"]) >= 3
    assert "elegant" in out["feature_keywords"] or "garment" in out["feature_keywords"]
    assert out["features"]


def test_feature_set_doc_from_product_overwrite():
    doc = {
        "name": "X",
        "description": "Cotton lawn piece.",
        "fabric": "lawn",
        "material": None,
        "features": "old",
        "feature_keywords": ["cotton"],
    }
    patch = feature_set_doc_from_product(doc, overwrite=True)
    assert patch is not None
    assert "fabric" in patch

