"""
One-time backfill: sets display_category on all existing MongoDB products.

This is identical logic to POST /api/admin/categories/backfill-display
but runs directly against MongoDB — no backend or auth token needed.

Usage:
  cd ml-engine
  python scripts/backfill_display_category.py
"""

import re
import yaml
from pymongo import MongoClient

# ── Load config ───────────────────────────────────────────────────────────────
with open("config.yaml") as f:
    cfg = yaml.safe_load(f)

client = MongoClient(cfg["mongodb"]["uri"])
col    = client[cfg["mongodb"]["database"]][cfg["mongodb"]["collection"]]

# ── Endpoint sets (copied from backend/app/api/routes/admin_new.py) ───────────
WOMEN_KURTA_ENDPOINTS         = frozenset({"2-piece-essential-summer-pret-kt","charizma-vasal-vol-02-2026","eid-collection","essential-summer-pret","florence-summer-edit-26","luxe-2025","luxury-pret","new-arrival-summer-26","new-arrivals","pret","ready-to-wear","satori-2026","women"})
WOMEN_LAWN_ENDPOINTS          = frozenset({"eid-lawn-2026","lawn-in-stock","ramadan-festive-sale-lawn-khaddar-stiched-cords","ramadan-festive-sale-lawn-khaddar-stitched-cords"})
WOMEN_LUXE_ENDPOINTS          = frozenset({"bridal-in-stock","festive-in-stock","wedding-unstitched-2025"})
WOMEN_SHORT_KURTI_ENDPOINTS   = frozenset({"ss-wesst","ss-west","short-kurti"})
WOMEN_ACCESSORIES_ENDPOINTS   = frozenset({"accessories"})
WOMEN_ANARKALI_FROCK_ENDPOINTS= frozenset({"anarkali-frock"})
WOMEN_BOTTOMS_ENDPOINTS       = frozenset({"bottoms"})
WOMEN_BAGS_ENDPOINTS          = frozenset({"cross-body-bags"})
WOMEN_JEWELRY_ENDPOINTS       = frozenset({"jewelry"})
WOMEN_TOPS_ENDPOINTS          = frozenset({"tops"})
WOMEN_UNSTITCHED_ENDPOINTS    = frozenset({"unstitched","unstitched-fabric"})
WOMEN_WESTERN_ENDPOINTS       = frozenset({"western"})
WOMEN_WINTER_PANTS_ENDPOINTS  = frozenset({"winter-pants"})

MEN_STANDARD_SUIT_ENDPOINTS   = frozenset({"all"})
MEN_TRADITIONAL_SUIT_ENDPOINTS= frozenset({"men","men-main","men-ready-to-wear","new-arrival"})
MEN_CASUAL_WEAR_ENDPOINTS     = frozenset({"men-products"})
MEN_FOOTWEAR_ENDPOINTS        = frozenset({"men-footwear"})
MEN_SHOES_ENDPOINTS           = frozenset({"men-shoes-shoes"})
MEN_SWEATER_ENDPOINTS         = frozenset({"men-sweater"})
MEN_WRIST_WATCHES_ENDPOINTS   = frozenset({"mens-wrist-watches","men-wrist-watches"})


def _or_regex(endpoint_set):
    """Build a MongoDB $or list of case-insensitive exact-match regex queries."""
    return [{"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}}
            for s in endpoint_set]


def _display_category_from_endpoint(slug: str, gender: str) -> str:
    """Mirror of the backend helper — returns display name for a given slug."""
    slug = (slug or "").lower().strip()
    if gender in ("w", "women"):
        if slug in WOMEN_KURTA_ENDPOINTS:          return "Women Kurta"
        if slug in WOMEN_LAWN_ENDPOINTS:           return "Women Lawn"
        if slug in WOMEN_LUXE_ENDPOINTS:           return "Women Luxe"
        if slug in WOMEN_SHORT_KURTI_ENDPOINTS:    return "Women Short Kurti"
        if slug in WOMEN_ACCESSORIES_ENDPOINTS:    return "Women Accessories"
        if slug in WOMEN_ANARKALI_FROCK_ENDPOINTS: return "Women Anarkali Frock"
        if slug in WOMEN_BOTTOMS_ENDPOINTS:        return "Women Bottoms"
        if slug in WOMEN_BAGS_ENDPOINTS:           return "Women Bags"
        if slug in WOMEN_JEWELRY_ENDPOINTS:        return "Women Jewelry"
        if slug in WOMEN_TOPS_ENDPOINTS:           return "Women Tops"
        if slug in WOMEN_UNSTITCHED_ENDPOINTS:     return "Women Unstitched"
        if slug in WOMEN_WESTERN_ENDPOINTS:        return "Women Western"
        if slug in WOMEN_WINTER_PANTS_ENDPOINTS:   return "Women Winter Pants"
    if gender in ("m", "men"):
        if slug in MEN_STANDARD_SUIT_ENDPOINTS:    return "Men Standard Suit"
        if slug in MEN_TRADITIONAL_SUIT_ENDPOINTS: return "Men Traditional Suit"
        if slug in MEN_CASUAL_WEAR_ENDPOINTS:      return "Men Casual Wear"
        if slug in MEN_FOOTWEAR_ENDPOINTS:         return "Men Footwear"
        if slug in MEN_SHOES_ENDPOINTS:            return "Men Shoes"
        if slug in MEN_SWEATER_ENDPOINTS:          return "Men Sweater"
        if slug in MEN_WRIST_WATCHES_ENDPOINTS:    return "Men Wrist Watches"
    return slug or "Other"


# ── Run backfill ──────────────────────────────────────────────────────────────
print("[INFO] Starting display_category backfill...")
print(f"[INFO] Total products: {col.count_documents({})}")

totals = {}

def bulk(label, query, display_name):
    r = col.update_many(query, {"$set": {"display_category": display_name}})
    totals[label] = r.modified_count
    if r.modified_count:
        print(f"  {r.modified_count:>5}  {display_name}  ({label})")

# Women – endpoint-based
bulk("kurta_endpoint",      {"gender": "w", "endpoint_category": {"$in": list(WOMEN_KURTA_ENDPOINTS)}},       "Women Kurta")
bulk("lawn_endpoint",       {"gender": "w", "endpoint_category": {"$in": list(WOMEN_LAWN_ENDPOINTS)}},        "Women Lawn")
bulk("lawn_ramadan_regex",  {"gender": "w", "$and": [{"endpoint_category": {"$regex": "ramadan", "$options": "i"}}, {"endpoint_category": {"$regex": "lawn", "$options": "i"}}]}, "Women Lawn")
bulk("kurta_legacy",        {"gender": "w", "category": {"$regex": "women.*(stitched|western)", "$options": "i"}}, "Women Kurta")
bulk("lawn_legacy",         {"gender": "w", "category": {"$regex": "women.*unstitched", "$options": "i"}},    "Women Lawn")

# Women – endpoint-only (no gender filter)
bulk("luxe_endpoint",       {"$or": _or_regex(WOMEN_LUXE_ENDPOINTS)},           "Women Luxe")
bulk("short_kurti_endpoint",{"$or": _or_regex(WOMEN_SHORT_KURTI_ENDPOINTS)},    "Women Short Kurti")
bulk("accessories",         {"$or": _or_regex(WOMEN_ACCESSORIES_ENDPOINTS)},    "Women Accessories")
bulk("anarkali_frock",      {"$or": _or_regex(WOMEN_ANARKALI_FROCK_ENDPOINTS)}, "Women Anarkali Frock")
bulk("bottoms",             {"$or": _or_regex(WOMEN_BOTTOMS_ENDPOINTS)},        "Women Bottoms")
bulk("bags",                {"$or": _or_regex(WOMEN_BAGS_ENDPOINTS)},           "Women Bags")
bulk("jewelry",             {"$or": _or_regex(WOMEN_JEWELRY_ENDPOINTS)},        "Women Jewelry")
bulk("tops",                {"$or": _or_regex(WOMEN_TOPS_ENDPOINTS)},           "Women Tops")
bulk("unstitched",          {"$or": _or_regex(WOMEN_UNSTITCHED_ENDPOINTS)},     "Women Unstitched")
bulk("western",             {"$or": _or_regex(WOMEN_WESTERN_ENDPOINTS)},        "Women Western")
bulk("winter_pants",        {"$or": _or_regex(WOMEN_WINTER_PANTS_ENDPOINTS)},   "Women Winter Pants")

# Men – endpoint-based
bulk("men_standard_suit",   {"$or": _or_regex(MEN_STANDARD_SUIT_ENDPOINTS)},    "Men Standard Suit")
bulk("men_traditional_suit",{"$or": _or_regex(MEN_TRADITIONAL_SUIT_ENDPOINTS)}, "Men Traditional Suit")
bulk("men_casual_wear",     {"$or": _or_regex(MEN_CASUAL_WEAR_ENDPOINTS)},      "Men Casual Wear")
bulk("men_footwear",        {"$or": _or_regex(MEN_FOOTWEAR_ENDPOINTS)},         "Men Footwear")
bulk("men_shoes",           {"$or": _or_regex(MEN_SHOES_ENDPOINTS)},            "Men Shoes")
bulk("men_sweater",         {"$or": _or_regex(MEN_SWEATER_ENDPOINTS)},          "Men Sweater")
bulk("men_wrist_watches",   {"$or": _or_regex(MEN_WRIST_WATCHES_ENDPOINTS)},    "Men Wrist Watches")

# Fallback: any product still missing display_category — derive from endpoint or category field
print("\n[INFO] Running fallback for remaining products without display_category...")
fallback_count = 0
missing_query  = {"$or": [{"display_category": {"$exists": False}}, {"display_category": ""}]}
for doc in col.find(missing_query, {"_id": 1, "gender": 1, "endpoint_category": 1, "category": 1}):
    gender = (doc.get("gender") or "").lower().strip()
    slug   = (doc.get("endpoint_category") or "").strip()
    val    = _display_category_from_endpoint(slug, gender)
    if not val or val == "Other":
        val = (doc.get("category") or "Other").strip() or "Other"
    col.update_one({"_id": doc["_id"]}, {"$set": {"display_category": val}})
    fallback_count += 1

print(f"  {fallback_count:>5}  products updated via fallback")

# ── Final summary ──────────────────────────────────────────────────────────────
print("\n[INFO] Final product counts per display_category:")
pipeline = [{"$group": {"_id": "$display_category", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
for r in col.aggregate(pipeline):
    cat = r["_id"] or "(empty)"
    print(f"  {r['count']:>6}  {cat}")

still_empty = col.count_documents({"$or": [{"display_category": {"$exists": False}}, {"display_category": ""}]})
print(f"\n[{'OK' if still_empty == 0 else 'WARN'}]  Products still without display_category: {still_empty}")
print("[DONE] Backfill complete.")
