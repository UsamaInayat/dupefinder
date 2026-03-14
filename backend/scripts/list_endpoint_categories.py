"""
One-off script: list all endpoint_category values in the products collection
with counts, so we can match exact DB values to WOMEN_LUXE / WOMEN_SHORT_KURTI.
Run from backend: python -m scripts.list_endpoint_categories
"""
import os
import sys
from pathlib import Path

# backend/scripts/ -> backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.chdir(Path(__file__).resolve().parent.parent)

from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient

# Same as app config
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://ussamainayat:ussamainayat@dupefinder.u30xrsm.mongodb.net/")
MONGO_DB = os.getenv("MONGO_DB_NAME", "dupefinder")
COLLECTION = "products"

# What we expect in code (for comparison)
WOMEN_LUXE = {"bridal-in-stock", "festive-in-stock", "wedding-unstitched-2025"}
WOMEN_SHORT_KURTI = {"ss-wesst", "ss-west", "short-kurti"}


def main():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    db = client[MONGO_DB]
    products = db[COLLECTION]
    total = products.count_documents({})
    print(f"Total products: {total}\n")
    print("All endpoint_category values in DB (repr = exact string):")
    print("-" * 60)
    slugs = products.distinct("endpoint_category")
    if not slugs:
        print("(none or field missing)")
        return
    for s in sorted(slugs, key=lambda x: (x or "").lower()):
        count = products.count_documents({"endpoint_category": s})
        # Show exact value so we see spaces, typos, unicode
        in_luxe = (s or "").strip().lower().replace(" ", "-").replace("_", "-") in {x.lower() for x in WOMEN_LUXE}
        in_short = (s or "").strip().lower().replace(" ", "-").replace("_", "-") in {x.lower() for x in WOMEN_SHORT_KURTI}
        tag = ""
        if in_luxe:
            tag = "  -> Women Luxe"
        elif in_short:
            tag = "  -> Women Short Kurti"
        else:
            norm = (s or "").strip().lower().replace(" ", "-").replace("_", "-")
            if any(norm == x for x in WOMEN_LUXE) or any(norm == x for x in WOMEN_SHORT_KURTI):
                tag = "  (normalized matches)"
        print(f"  count={count:5d}  endpoint_category={repr(s)}{tag}")
    print("-" * 60)
    print("\nExpected in code:")
    print("  WOMEN_LUXE:", sorted(WOMEN_LUXE))
    print("  WOMEN_SHORT_KURTI:", sorted(WOMEN_SHORT_KURTI))


def test_product_filter():
    """Run the same filter as GET /products for Women Short Kurti and Women Luxe."""
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    db = client[MONGO_DB]
    products = db[COLLECTION]
    # Import the actual filter from the app
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from app.api.routes.admin_new import _category_filter_for_products
    for cat in ["Women Short Kurti", "Women Luxe"]:
        cf = _category_filter_for_products(cat)
        n = products.count_documents({"$and": [cf]})
        print(f"  Filter '{cat}' -> count = {n}")


def check_gender():
    """Check gender field for Women Short Kurti and Women Luxe products."""
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    db = client[MONGO_DB]
    products = db[COLLECTION]
    for label, slug_list in [("Women Short Kurti", list(WOMEN_SHORT_KURTI)), ("Women Luxe", list(WOMEN_LUXE))]:
        pipeline = [
            {"$match": {"endpoint_category": {"$in": slug_list}}},
            {"$group": {"_id": "$gender", "count": {"$sum": 1}}}
        ]
        out = list(products.aggregate(pipeline))
        print(f"  {label} - gender breakdown: {out}")


if __name__ == "__main__":
    main()
    print("\nSame filter as GET /products (no gender):")
    test_product_filter()
    print("\nGender in DB for Short kurti / Luxe products:")
    check_gender()
