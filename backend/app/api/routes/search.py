"""
Image search API endpoints — FashionCLIP-powered similarity search.

Flow:
  1. User uploads an image
  2. FashionCLIP extracts a 512-dim embedding (L2-normalised)
  3. Query the FAISS index for the selected category (or all categories)
  4. Fetch matching product docs from MongoDB by product_id field
  5. Re-rank using combined score: visual similarity + price affordability + attribute match
  6. Return ranked results
"""

import sys
import time
import pickle
import threading
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Optional

import faiss
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from pydantic import BaseModel

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
ML_ENGINE    = PROJECT_ROOT / "ml-engine"
ML_DIR       = Path(__file__).parent.parent.parent / "ml"
FAISS_DIR    = ML_DIR / "fashionclip_indices"
ID_MAPS_DIR  = ML_DIR / "fashionclip_id_maps"
UPLOAD_DIR   = PROJECT_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

sys.path.insert(0, str(ML_ENGINE))

from app.core.database import get_products_collection

router = APIRouter()


# ── Response models ───────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    product_id:       str
    name:             str
    brand:            Optional[str]   = None
    price:            Optional[float] = None
    image_url:        Optional[str]   = None
    product_url:      Optional[str]   = None
    display_category: Optional[str]   = None
    similarity_score: float
    final_score:      float           # combined ranking score (sim + price + attr)

class SearchResponse(BaseModel):
    query_image:       str
    results:           List[SearchResult]
    search_time_ms:    float
    total_results:     int
    category_searched: Optional[str] = None


# ── Singleton resources (loaded once at startup) ───────────────────────────────

_extractor  = None
_indices:   dict = {}   # slug → faiss.Index
_id_maps:   dict = {}   # slug → {faiss_int_id: product_id}

# Protects all reads and writes to _indices/_id_maps so hot-reloads
# during a running search request never cause inconsistent state.
_index_lock = threading.Lock()


def get_extractor():
    global _extractor
    if _extractor is None:
        print("[INFO] Loading FashionCLIP extractor...")
        from fashionclip.extractor import FashionCLIPExtractor
        _extractor = FashionCLIPExtractor(device="cpu")
        print("[OK] FashionCLIP loaded")
    return _extractor


def _slug(category: str) -> str:
    return category.lower().replace(" ", "_").replace("/", "-")


def _load_indices():
    """Load all FashionCLIP FAISS indices and id_maps from disk."""
    if not FAISS_DIR.exists():
        print(f"[WARNING] FashionCLIP indices directory not found: {FAISS_DIR}")
        return

    count = 0
    new_indices = {}
    new_id_maps = {}
    for idx_file in FAISS_DIR.glob("*.index"):
        slug     = idx_file.stem
        map_file = ID_MAPS_DIR / f"{slug}.pkl"
        if not map_file.exists():
            print(f"[WARNING] id_map missing for {slug}, skipping")
            continue
        try:
            new_indices[slug] = faiss.read_index(str(idx_file))
            with open(map_file, "rb") as f:
                new_id_maps[slug] = pickle.load(f)
            count += 1
        except Exception as e:
            print(f"[WARNING] Failed to load index {slug}: {e}")

    with _index_lock:
        _indices.clear()
        _indices.update(new_indices)
        _id_maps.clear()
        _id_maps.update(new_id_maps)

    print(f"[OK] Loaded {count} FashionCLIP FAISS indices: {sorted(_indices.keys())}")


def hot_reload_indices(updated_slugs: list):
    """
    Replace in-memory indices for the given slugs by re-reading from disk.
    Called automatically after the reindex background task completes.
    Thread-safe: uses _index_lock so live search requests are not interrupted.
    """
    reloaded = []
    with _index_lock:
        for slug in updated_slugs:
            idx_file = FAISS_DIR / f"{slug}.index"
            map_file = ID_MAPS_DIR / f"{slug}.pkl"
            if idx_file.exists() and map_file.exists():
                try:
                    _indices[slug] = faiss.read_index(str(idx_file))
                    with open(map_file, "rb") as f:
                        _id_maps[slug] = pickle.load(f)
                    reloaded.append(slug)
                except Exception as e:
                    print(f"[WARNING] hot_reload failed for {slug}: {e}")
    if reloaded:
        print(f"[OK] Hot-reloaded {len(reloaded)} indices: {reloaded}")
    return reloaded


def _coerce_pid(pid):
    """product_id values are stored as int in MongoDB."""
    try:
        return int(pid)
    except (ValueError, TypeError):
        return str(pid)


# ── Multi-signal ranking ───────────────────────────────────────────────────────

def _rerank(
    hits:    list,
    docs:    dict,
    w_sim:   float = 0.7,
    w_price: float = 0.2,
    w_attr:  float = 0.1,
) -> list:
    """
    Re-rank FAISS hits using:
      final_score = w_sim * sim + w_price * price_score + w_attr * attr_score

    price_score: cheaper relative to most expensive result = higher score.
                 Missing price → neutral 0.5.
    attr_score:  1.0 if gender field is present and consistent, 0.5 otherwise.
                 (Category is already enforced at the FAISS index level.)

    Returns hits list with 'final_score' added, sorted descending.
    """
    prices = [
        docs[h["product_id"]].get("price")
        for h in hits
        if h["product_id"] in docs and docs[h["product_id"]].get("price") is not None
    ]
    max_price = max(prices) if prices else 1.0
    if max_price == 0:
        max_price = 1.0

    for hit in hits:
        doc   = docs.get(hit["product_id"], {})
        sim   = hit["score"]

        price = doc.get("price")
        if price is not None and max_price > 0:
            price_score = 1.0 - (price / max_price)
        else:
            price_score = 0.5

        # attr_score: reward products that have a gender field (indicates richer data)
        attr_score = 1.0 if doc.get("gender") else 0.5

        hit["final_score"] = round(
            (w_sim * sim) + (w_price * price_score) + (w_attr * attr_score), 6
        )

    hits.sort(key=lambda x: x["final_score"], reverse=True)
    return hits


# ── Search helpers ─────────────────────────────────────────────────────────────

def _faiss_search(query_vec: np.ndarray, category_slug: str, top_k: int) -> list:
    """Search a single FAISS index. Returns list of {product_id, score}."""
    with _index_lock:
        index  = _indices[category_slug]
        id_map = _id_maps[category_slug]
        scores, faiss_ids = index.search(query_vec, top_k)

    hits = []
    for fid, score in zip(faiss_ids[0], scores[0]):
        if fid < 0:
            continue
        pid = id_map.get(int(fid))
        if pid is not None:
            hits.append({"product_id": str(pid), "score": float(score)})
    return hits


def _search_all_categories(query_vec: np.ndarray, top_k: int) -> list:
    """Search all category indices, merge, and return global top-k."""
    with _index_lock:
        slugs = list(_indices.keys())

    all_hits = []
    for slug in slugs:
        all_hits.extend(_faiss_search(query_vec, slug, top_k))
    all_hits.sort(key=lambda x: x["score"], reverse=True)
    return all_hits[:top_k]


# ── Startup init ──────────────────────────────────────────────────────────────

def init_search_resources():
    """Called from main.py lifespan to eagerly load everything."""
    _load_indices()
    if _indices:
        get_extractor()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/similar", response_model=SearchResponse)
@router.post("/upload",  response_model=SearchResponse)
async def search_by_image(
    file:      UploadFile         = File(..., description="Image file to search"),
    top_k:     int                = Query(5, ge=1, le=20),
    category:  Optional[str]      = Query(None, description="display_category to search in"),
    min_price: Optional[float]    = Query(None, ge=0),
    max_price: Optional[float]    = Query(None, ge=0),
    w_sim:     float              = Query(0.7,  ge=0.0, le=1.0, description="Weight for visual similarity (default 0.7)"),
    w_price:   float              = Query(0.2,  ge=0.0, le=1.0, description="Weight for price affordability (default 0.2)"),
    w_attr:    float              = Query(0.1,  ge=0.0, le=1.0, description="Weight for attribute match (default 0.1)"),
):
    """
    Upload an image and get back the most visually similar products,
    re-ranked by a combined score (visual similarity + price + attributes).

    - **category**: optional display_category filter (e.g. 'Women Kurta').
    - **w_sim / w_price / w_attr**: ranking weights (must not need to sum to 1).
    """
    start = time.time()

    # ── Validate file type ────────────────────────────────────────────────────
    allowed = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp"}
    if file.content_type not in allowed:
        raise HTTPException(400, f"Unsupported file type '{file.content_type}'. Use: {allowed}")

    # ── Save uploaded file ────────────────────────────────────────────────────
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved    = UPLOAD_DIR / f"search_{ts}_{file.filename}"
    contents = await file.read()
    saved.write_bytes(contents)
    print(f"[INFO] Saved upload: {saved}")

    # ── Check indices are loaded ──────────────────────────────────────────────
    with _index_lock:
        indices_ready = bool(_indices)
    if not indices_ready:
        _load_indices()
    with _index_lock:
        indices_ready = bool(_indices)
    if not indices_ready:
        raise HTTPException(503, "FashionCLIP indices not loaded. Run embedding generation first.")

    # ── Extract embedding (FashionCLIP returns L2-normalised 512-dim vectors) ─
    extractor = get_extractor()
    q_vec = extractor.extract_from_path(str(saved)).astype("float32").reshape(1, -1)
    print(f"[INFO] Embedding extracted  shape={q_vec.shape}")

    # ── FAISS search ──────────────────────────────────────────────────────────
    category_slug = _slug(category) if category else None

    if category_slug:
        with _index_lock:
            available = sorted(_indices.keys())
        if category_slug not in available:
            raise HTTPException(404, f"No index for category '{category}'. Available: {available}")
        hits = _faiss_search(q_vec, category_slug, top_k)
        searched_label = category
    else:
        hits = _search_all_categories(q_vec, top_k)
        searched_label = "all"

    if not hits:
        raise HTTPException(404, "No similar products found.")

    print(f"[INFO] FAISS returned {len(hits)} candidates")

    # ── Fetch product details from MongoDB ────────────────────────────────────
    collection = get_products_collection()
    pid_values = [_coerce_pid(h["product_id"]) for h in hits]

    docs = {
        str(d.get("product_id", "")): d
        for d in collection.find({"product_id": {"$in": pid_values}})
    }
    print(f"[INFO] MongoDB returned {len(docs)} product docs")

    # ── Apply optional price filter ───────────────────────────────────────────
    if min_price is not None or max_price is not None:
        filtered = []
        for hit in hits:
            price = docs.get(hit["product_id"], {}).get("price")
            if min_price is not None and (price is None or price < min_price):
                continue
            if max_price is not None and (price is None or price > max_price):
                continue
            filtered.append(hit)
        hits = filtered

    if not hits:
        raise HTTPException(404, "No products matched the price filter.")

    # ── Re-rank: combine similarity + price + attributes ─────────────────────
    hits = _rerank(hits, docs, w_sim=w_sim, w_price=w_price, w_attr=w_attr)

    # ── Build response ────────────────────────────────────────────────────────
    results: List[SearchResult] = []
    for hit in hits:
        doc = docs.get(hit["product_id"], {})
        results.append(SearchResult(
            product_id       = hit["product_id"],
            name             = str(doc.get("name", "Unknown Product")),
            brand            = doc.get("brand"),
            price            = doc.get("price"),
            image_url        = doc.get("image_url"),
            product_url      = doc.get("product_url"),
            display_category = doc.get("display_category"),
            similarity_score = hit["score"],
            final_score      = hit["final_score"],
        ))

    elapsed = (time.time() - start) * 1000
    print(f"[OK] Search done in {elapsed:.1f}ms  "
          f"weights=({w_sim}/{w_price}/{w_attr})  "
          f"top={results[0].name if results else 'none'}")

    return SearchResponse(
        query_image       = str(saved),
        results           = results,
        search_time_ms    = elapsed,
        total_results     = len(results),
        category_searched = searched_label,
    )


# ── Search history + stats ────────────────────────────────────────────────────

@router.get("/history")
async def get_search_history(limit: int = Query(10, ge=1, le=100)):
    """Get recent search history."""
    try:
        from app.core.database import get_search_history_collection
        collection = get_search_history_collection()
        cursor  = collection.find().sort("timestamp", -1).limit(limit)
        history = []
        for doc in cursor:
            doc.pop("embedding", None)
            doc["_id"] = str(doc["_id"])
            for r in doc.get("results", []):
                if "product_id" in r:
                    r["product_id"] = str(r["product_id"])
            history.append(doc)
        return {"history": history, "count": len(history)}
    except Exception as e:
        print(f"[ERROR] get_search_history: {e}")
        raise HTTPException(500, f"Failed to get history: {e}")


@router.get("/stats")
async def get_search_stats():
    """Get search statistics."""
    try:
        from app.core.database import get_search_history_collection
        col   = get_search_history_collection()
        total = col.count_documents({})
        stats = list(col.aggregate([{"$group": {"_id": None,
            "avg": {"$avg": "$search_time_ms"},
            "min": {"$min": "$search_time_ms"},
            "max": {"$max": "$search_time_ms"}}}]))
        if stats:
            s = stats[0]
            return {"total_searches": total,
                    "avg_search_time_ms": round(s.get("avg", 0), 2),
                    "min_search_time_ms": round(s.get("min", 0), 2),
                    "max_search_time_ms": round(s.get("max", 0), 2)}
        return {"total_searches": 0, "avg_search_time_ms": 0,
                "min_search_time_ms": 0, "max_search_time_ms": 0}
    except Exception as e:
        print(f"[ERROR] get_search_stats: {e}")
        raise HTTPException(500, f"Failed to get stats: {e}")
