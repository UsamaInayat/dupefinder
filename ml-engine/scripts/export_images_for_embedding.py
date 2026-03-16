"""
Phase 1 — Export product images from MongoDB for embedding generation.

Run this LOCALLY before uploading to Vast.ai.

What it does:
  1. Connects to MongoDB Atlas
  2. Queries all products with a valid image_url and broken_link=False
  3. Downloads each image to data/catalogue_images/{product_id}.jpg
  4. Writes data/manifest.csv with columns:
       product_id, local_image_path, display_category, gender,
       name, brand, price, product_url

Usage:
  cd ml-engine
  python scripts/export_images_for_embedding.py

  Optional flags:
    --limit 500          Only export first 500 products (for testing)
    --category "Women Kurta"  Only export one category
    --workers 8          Parallel download workers (default: 4)
"""

import os
import sys
import csv
import time
import argparse
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import yaml
from pymongo import MongoClient
from tqdm import tqdm


# ── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
ML_ROOT      = SCRIPT_DIR.parent
CONFIG_PATH  = ML_ROOT / "config.yaml"
IMAGES_DIR   = ML_ROOT / "data" / "catalogue_images"
MANIFEST_CSV = ML_ROOT / "data" / "manifest.csv"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)


# ── Config ───────────────────────────────────────────────────────────────────
with open(CONFIG_PATH, "r") as f:
    CONFIG = yaml.safe_load(f)

MONGO_URI    = CONFIG["mongodb"]["uri"]
MONGO_DB     = CONFIG["mongodb"]["database"]
MONGO_COL    = CONFIG["mongodb"]["collection"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}


# ── Helpers ──────────────────────────────────────────────────────────────────
def safe_product_id(product) -> str:
    """Return a filesystem-safe string ID for this product document."""
    pid = product.get("product_id")
    if pid:
        return str(pid)
    # Fallback: MD5 of product_url
    url = product.get("product_url", "")
    return hashlib.md5(url.encode()).hexdigest()[:16]


def download_image(product_id: str, image_url: str) -> str | None:
    """
    Download image_url and save to IMAGES_DIR/{product_id}.jpg.
    Returns local path string on success, None on failure.
    """
    if not image_url or not image_url.startswith("http"):
        return None

    dest = IMAGES_DIR / f"{product_id}.jpg"
    if dest.exists():
        return str(dest)           # Already downloaded

    try:
        resp = requests.get(image_url, headers=HEADERS, timeout=15, stream=True)
        if resp.status_code != 200:
            return None

        content_type = resp.headers.get("Content-Type", "")
        if "image" not in content_type and "octet-stream" not in content_type:
            return None

        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        return str(dest)

    except Exception:
        return None


def fetch_products(collection, category_filter: str | None, limit: int | None):
    """Query MongoDB for exportable products."""
    query = {
        "image_url": {"$exists": True, "$ne": "", "$ne": None},
        "broken_link": {"$ne": True},
    }
    if category_filter:
        query["display_category"] = category_filter

    cursor = collection.find(query, {
        "product_id": 1,
        "image_url": 1,
        "display_category": 1,
        "gender": 1,
        "name": 1,
        "brand": 1,
        "price": 1,
        "product_url": 1,
    })

    if limit:
        cursor = cursor.limit(limit)

    return list(cursor)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Export product images from MongoDB for embedding generation")
    parser.add_argument("--limit",    type=int,   default=None, help="Max products to export (default: all)")
    parser.add_argument("--category", type=str,   default=None, help="Export only this display_category")
    parser.add_argument("--workers",  type=int,   default=4,    help="Parallel download workers (default: 4)")
    args = parser.parse_args()

    print("[INFO] Connecting to MongoDB Atlas...")
    client     = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    db         = client[MONGO_DB]
    collection = db[MONGO_COL]

    # Verify connection
    client.admin.command("ping")
    print("[OK]  Connected to MongoDB Atlas")

    print("[INFO] Fetching product list...")
    products = fetch_products(collection, args.category, args.limit)
    print(f"[INFO] Found {len(products)} products to process")

    if not products:
        print("[WARN] No products found. Check your MongoDB data and filters.")
        return

    # ── Download images in parallel ───────────────────────────────────────
    print(f"\n[INFO] Downloading images with {args.workers} workers...")
    results = []          # (product_id, local_path, product_doc)
    failed  = []

    def _task(product):
        pid       = safe_product_id(product)
        image_url = product.get("image_url", "")
        local     = download_image(pid, image_url)
        return pid, local, product

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(_task, p): p for p in products}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Downloading"):
            pid, local_path, product = future.result()
            if local_path:
                results.append((pid, local_path, product))
            else:
                failed.append(product.get("product_url", "?"))

    print(f"\n[INFO] Download complete:")
    print(f"       Success : {len(results)}")
    print(f"       Failed  : {len(failed)}")

    if failed:
        fail_log = ML_ROOT / "data" / "failed_downloads.txt"
        with open(fail_log, "w", encoding="utf-8") as f:
            f.write("\n".join(failed))
        print(f"[INFO] Failed URLs logged to {fail_log}")

    # ── Write manifest.csv ────────────────────────────────────────────────
    print(f"\n[INFO] Writing manifest to {MANIFEST_CSV}...")
    with open(MANIFEST_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "product_id", "local_image_path", "display_category",
            "gender", "name", "brand", "price", "product_url"
        ])
        for pid, local_path, product in results:
            writer.writerow([
                pid,
                local_path,
                product.get("display_category", ""),
                product.get("gender", ""),
                product.get("name", ""),
                product.get("brand", ""),
                product.get("price", 0),
                product.get("product_url", ""),
            ])

    print(f"[OK]  manifest.csv written with {len(results)} rows")

    # ── Category summary ──────────────────────────────────────────────────
    from collections import Counter
    cats = Counter(p.get("display_category", "unknown") for _, _, p in results)
    print("\n[INFO] Products per category:")
    for cat, count in sorted(cats.items()):
        print(f"       {count:>5}  {cat}")

    print("\n[DONE] Export complete. Upload ml-engine/ to your Vast.ai instance.")
    print(f"       Total images saved : {len(results)}")
    print(f"       Manifest location  : {MANIFEST_CSV}")


if __name__ == "__main__":
    main()
