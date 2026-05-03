"""
FashionCLIP Incremental Re-indexing Script

Finds products in MongoDB that are NOT yet in the FAISS indices
(those without fashionclip_indexed=True), downloads their images,
extracts FashionCLIP embeddings, and appends them to the existing
category indices — WITHOUT rebuilding from scratch.

This script can be:
  1. Run manually after a scraping session:
       python ml-engine/scripts/reindex_new_products.py
  2. Run automatically from the backend after scraping completes
     (via run_reindex_task in admin_new.py).

Usage:
  python reindex_new_products.py [options]

  --limit N             Only process first N unindexed products (testing)
  --category "Women Kurta"  Only reindex a single category
  --dry-run             Show what would change, write nothing
  --migrate-existing    Mark all current products as fashionclip_indexed=True
                        (one-time setup after initial Vast.ai indexing)
"""

import sys
import os
import argparse
import gc
import pickle
import tempfile
import time
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import requests
import yaml
import faiss
from pymongo import MongoClient, UpdateOne
from PIL import Image

# ── Resolve paths ─────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
ML_ROOT      = SCRIPT_DIR.parent
PROJECT_ROOT = ML_ROOT.parent
def _path_from_env(name: str, default):
    raw = os.getenv(name, "").strip()
    return Path(raw) if raw else default


# Allow Railway volume mounts by pointing directly at dirs, or override the whole backend ML root.
BACKEND_ML = _path_from_env("BACKEND_APP_ML_DIR", PROJECT_ROOT / "backend" / "app" / "ml")
FAISS_DIR = _path_from_env("FAISS_INDEX_DIR", BACKEND_ML / "fashionclip_indices")
ID_MAPS_DIR = _path_from_env("FAISS_ID_MAP_DIR", BACKEND_ML / "fashionclip_id_maps")

sys.path.insert(0, str(ML_ROOT))

CONFIG_PATH = ML_ROOT / "config.yaml"
with open(CONFIG_PATH) as f:
    CFG = yaml.safe_load(f)

# Prefer environment variables (Railway / production), fall back to ml-engine/config.yaml (local dev).
# This avoids requiring committed secrets in config.yaml for deployed environments.
MONGO_URI = (
    os.getenv("MONGO_URI")
    or os.getenv("MONGODB_URI")
    or os.getenv("MONGODB_URL")
    or CFG.get("mongodb", {}).get("uri")
)
MONGO_DB = (
    os.getenv("MONGO_DB_NAME")
    or os.getenv("MONGODB_DATABASE")
    or os.getenv("DATABASE_NAME")
    or CFG.get("mongodb", {}).get("database")
)
MONGO_COL = os.getenv("MONGO_COLLECTION") or CFG.get("mongodb", {}).get("collection")

if not MONGO_URI:
    raise RuntimeError(
        "Mongo URI not configured. Set MONGO_URI (or MONGODB_URI) in the environment, "
        "or set mongodb.uri in ml-engine/config.yaml for local runs."
    )
if not MONGO_DB:
    raise RuntimeError(
        "Mongo database name not configured. Set MONGO_DB_NAME (or MONGODB_DATABASE), "
        "or set mongodb.database in ml-engine/config.yaml for local runs."
    )
if not MONGO_COL:
    raise RuntimeError(
        "Mongo collection not configured. Set MONGO_COLLECTION, "
        "or set mongodb.collection in ml-engine/config.yaml for local runs."
    )

DOWNLOAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        v = int(raw)
        return v if v > 0 else default
    except ValueError:
        return default


def _fashionclip_extract_batch_size() -> int:
    """
    Inference micro-batch for FashionCLIP. Large values (e.g. 32) often trigger
    OOM ('Killed') on small Railway containers; override with FASHIONCLIP_EXTRACT_BATCH.
    """
    raw = os.getenv("FASHIONCLIP_EXTRACT_BATCH", "").strip()
    if raw:
        try:
            return max(1, min(128, int(raw)))
        except ValueError:
            pass
    # Railway sets RAILWAY_ENVIRONMENT (~512MB–1GB hobby tiers): default small batch.
    if os.getenv("RAILWAY_ENVIRONMENT", "").strip():
        return 2
    return 32


def _reindex_download_workers() -> int:
    """Parallel image downloads during reindex; lower on small RAM hosts."""
    raw = os.getenv("REINDEX_DOWNLOAD_WORKERS", "").strip()
    if raw:
        return max(1, min(16, _env_int("REINDEX_DOWNLOAD_WORKERS", 4)))
    if os.getenv("RAILWAY_ENVIRONMENT", "").strip():
        return 3
    return 8


# ── Helpers ───────────────────────────────────────────────────────────────────

def _slug(cat: str) -> str:
    return cat.lower().replace(" ", "_").replace("/", "-")


def _coerce_pid(pid):
    try:
        return int(pid)
    except (ValueError, TypeError):
        return str(pid)


def _download_image(product_id, image_url: str, dest_dir: Path) -> Path | None:
    """Download image_url to dest_dir/{product_id}.jpg. Returns path or None."""
    if not image_url or not image_url.startswith("http"):
        return None
    dest = dest_dir / f"{product_id}.jpg"
    if dest.exists():
        return dest
    try:
        resp = requests.get(image_url, headers=DOWNLOAD_HEADERS, timeout=15, stream=True)
        if resp.status_code != 200:
            return None
        content_type = resp.headers.get("Content-Type", "")
        if "image" not in content_type and "octet-stream" not in content_type:
            return None
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return dest
    except Exception:
        return None


# ── One-time migration ────────────────────────────────────────────────────────

def migrate_existing(col, dry_run: bool = False):
    """
    Mark all products that don't have fashionclip_indexed set as True.
    Run this once after the initial Vast.ai indexing job to prevent
    re-processing the 23,056 already-indexed products.
    """
    query = {"fashionclip_indexed": {"$exists": False}}
    count = col.count_documents(query)
    print(f"[INFO] Found {count} products without fashionclip_indexed field")

    if count == 0:
        print("[OK] Nothing to migrate — all products already have the flag")
        return

    if dry_run:
        print(f"[DRY-RUN] Would mark {count} products as fashionclip_indexed=True")
        return

    result = col.update_many(query, {"$set": {"fashionclip_indexed": True}})
    print(f"[OK] Marked {result.modified_count} products as fashionclip_indexed=True")


# ── Core reindex logic ────────────────────────────────────────────────────────

def run_reindex(
    category_filter: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
) -> dict:
    """
    Find unindexed products, extract FashionCLIP embeddings, append to FAISS indices.
    Returns summary dict: {category: n_added, ...}
    """
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=15000)
    col    = client[MONGO_DB][MONGO_COL]
    client.admin.command("ping")
    print("[OK] Connected to MongoDB")

    # ── Find unindexed products ───────────────────────────────────────────────
    query = {"fashionclip_indexed": {"$ne": True}}
    if category_filter:
        query["display_category"] = category_filter

    cursor = col.find(query, {
        "product_id": 1, "image_url": 1, "display_category": 1, "name": 1
    })
    if limit:
        cursor = cursor.limit(limit)

    products = list(cursor)
    print(f"[INFO] Found {len(products)} unindexed products")

    if not products:
        print("[INFO] Nothing to reindex")
        client.close()
        return {}

    if dry_run:
        cats = defaultdict(int)
        for p in products:
            cats[p.get("display_category", "unknown")] += 1
        print("[DRY-RUN] Would add:")
        for cat, n in sorted(cats.items()):
            print(f"  {n:>5}  {cat}")
        client.close()
        return dict(cats)

    # ── Download images to temp directory ────────────────────────────────────
    with tempfile.TemporaryDirectory(prefix="dupefinder_reindex_") as tmp_str:
        tmp_dir = Path(tmp_str)
        dl_workers = _reindex_download_workers()
        print(f"[INFO] Downloading images to {tmp_dir} (workers={dl_workers}) ...")

        valid_products = []
        t0 = time.time()

        def _dl(p):
            pid   = str(p.get("product_id", ""))
            url   = p.get("image_url", "")
            path  = _download_image(pid, url, tmp_dir)
            return p, path

        with ThreadPoolExecutor(max_workers=dl_workers) as executor:
            futures = {executor.submit(_dl, p): p for p in products}
            done = 0
            for fut in as_completed(futures):
                p, path = fut.result()
                if path:
                    p["_local_image"] = str(path)
                    valid_products.append(p)
                done += 1
                if done % 50 == 0:
                    print(f"  {done}/{len(products)} downloaded ...")

        elapsed = time.time() - t0
        print(f"[OK] Downloaded {len(valid_products)}/{len(products)} images in {elapsed:.1f}s")

        if not valid_products:
            print("[WARNING] No images could be downloaded — nothing to index")
            client.close()
            return {}

        # ── Load FashionCLIP extractor ────────────────────────────────────────
        print("[INFO] Loading FashionCLIP extractor ...")
        from fashionclip.extractor import FashionCLIPExtractor
        extractor = FashionCLIPExtractor(device="auto")

        # ── Extract embeddings ────────────────────────────────────────────────
        image_paths = [p["_local_image"] for p in valid_products]
        infer_bs = _fashionclip_extract_batch_size()
        # Optional: cap how many paths we pass per extract_batch call (frees PIL RAM between chunks).
        path_chunk = _env_int("REINDEX_EXTRACT_PATH_CHUNK", 0)
        if path_chunk <= 0:
            path_chunk = len(image_paths)
        print(
            f"[INFO] Extracting embeddings for {len(image_paths)} images "
            f"(infer_batch={infer_bs}, path_chunk={path_chunk}) ..."
        )
        t0 = time.time()
        emb_parts: list[np.ndarray] = []
        for off in range(0, len(image_paths), path_chunk):
            sub = image_paths[off : off + path_chunk]
            show_pb = len(image_paths) <= path_chunk or off == 0
            emb_parts.append(
                extractor.extract_batch(
                    sub,
                    batch_size=infer_bs,
                    show_progress=show_pb and len(sub) > infer_bs,
                )
            )
            gc.collect()
        embeddings = np.vstack(emb_parts) if len(emb_parts) > 1 else emb_parts[0]
        print(f"[OK] Embeddings extracted in {time.time()-t0:.1f}s  shape={embeddings.shape}")

        # ── Group by category ─────────────────────────────────────────────────
        by_cat = defaultdict(list)   # cat → [(embedding, product_id), ...]
        for i, p in enumerate(valid_products):
            cat = p.get("display_category") or "unknown"
            by_cat[cat].append((embeddings[i], str(p.get("product_id", ""))))

        # ── Append to FAISS indices ───────────────────────────────────────────
        summary = {}
        indexed_pids = []

        for cat, pairs in by_cat.items():
            s = _slug(cat)
            idx_path = FAISS_DIR / f"{s}.index"
            map_path = ID_MAPS_DIR / f"{s}.pkl"

            if idx_path.exists() and map_path.exists():
                # Load existing index — skip product_ids already present (safe resume / no dupes)
                index = faiss.read_index(str(idx_path))
                with open(map_path, "rb") as f:
                    id_map = pickle.load(f)
                existing = {str(v) for v in id_map.values()}
                to_add = [(v, pid) for v, pid in pairs if str(pid) not in existing]
                for v, pid in pairs:
                    if str(pid) in existing:
                        indexed_pids.append(str(pid))
                if len(to_add) < len(pairs):
                    print(f"[INFO] '{cat}': skip {len(pairs) - len(to_add)} already in index")
                if not to_add:
                    print(f"[SKIP] '{cat}': nothing new to append")
                    continue

                vecs    = np.stack([v for v, _ in to_add]).astype("float32")
                new_ids = [pid for _, pid in to_add]
                start_pos = index.ntotal
                index.add(vecs)
                for i, pid in enumerate(new_ids):
                    id_map[start_pos + i] = pid
                print(f"[OK] '{cat}': appended {len(new_ids)} vectors  "
                      f"(index now has {index.ntotal})")
            else:
                # No existing index — create new one for this category
                vecs    = np.stack([v for v, _ in pairs]).astype("float32")
                new_ids = [pid for _, pid in pairs]
                dim     = vecs.shape[1]   # 512
                index   = faiss.IndexFlatIP(dim)
                index.add(vecs)
                id_map  = {i: pid for i, pid in enumerate(new_ids)}
                print(f"[NEW] '{cat}': created index with {len(new_ids)} vectors")

            # Save updated index + id_map to disk atomically (write to .tmp first)
            FAISS_DIR.mkdir(parents=True, exist_ok=True)
            ID_MAPS_DIR.mkdir(parents=True, exist_ok=True)

            tmp_idx = idx_path.with_suffix(".index.tmp")
            tmp_map = map_path.with_suffix(".pkl.tmp")
            faiss.write_index(index, str(tmp_idx))
            with open(tmp_map, "wb") as f:
                pickle.dump(id_map, f)
            tmp_idx.replace(idx_path)
            tmp_map.replace(map_path)

            summary[cat] = len(new_ids)
            indexed_pids.extend(new_ids)

        # ── Mark products as indexed in MongoDB ───────────────────────────────
        print(f"[INFO] Marking {len(indexed_pids)} products as fashionclip_indexed=True ...")
        ops = [
            UpdateOne(
                {"product_id": _coerce_pid(pid)},
                {"$set": {"fashionclip_indexed": True}}
            )
            for pid in indexed_pids
        ]
        if ops:
            result = col.bulk_write(ops, ordered=False)
            print(f"[OK] MongoDB updated: {result.modified_count} products marked")

    client.close()

    # ── Print summary ─────────────────────────────────────────────────────────
    total = sum(summary.values())
    print("\n" + "=" * 55)
    print("REINDEX COMPLETE")
    print("=" * 55)
    for cat, n in sorted(summary.items()):
        print(f"  {n:>5}  {cat}")
    print(f"  {'-' * 40}")
    print(f"  {total:>5}  TOTAL")
    print("=" * 55)

    return summary


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="FashionCLIP incremental re-indexing for new scraped products"
    )
    parser.add_argument("--limit",     type=int,  default=None,  help="Max products to process")
    parser.add_argument("--category",  type=str,  default=None,  help="Only reindex this category")
    parser.add_argument("--dry-run",   action="store_true",       help="Preview without writing")
    parser.add_argument("--migrate-existing", action="store_true",
                        help="Mark existing 23k products as fashionclip_indexed=True (run once)")
    parser.add_argument("--reset-indexed", action="store_true",
                        help="Unset fashionclip_indexed on all products so next reindex run will rebuild indices + id_maps")
    args = parser.parse_args()

    if args.migrate_existing:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=15000)
        col    = client[MONGO_DB][MONGO_COL]
        migrate_existing(col, dry_run=args.dry_run)
        client.close()
        return

    if args.reset_indexed:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=15000)
        col    = client[MONGO_DB][MONGO_COL]
        result = col.update_many({}, {"$unset": {"fashionclip_indexed": 1}})
        print(f"[OK] Cleared fashionclip_indexed from {result.modified_count} products. Run reindex (no flags) to rebuild indices.")
        client.close()
        return

    run_reindex(
        category_filter = args.category,
        limit           = args.limit,
        dry_run         = args.dry_run,
    )


if __name__ == "__main__":
    main()
