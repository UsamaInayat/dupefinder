"""
Side-by-side comparison: ResNet50 vs FashionCLIP

Runs both models on the same test images and generates one HTML report
showing both sets of results side-by-side so you can compare quality.

Usage (run AFTER downloading FashionCLIP indices from Vast.ai):
    cd ml-engine
    python fashionclip/scripts/quick_eval.py

Prerequisites:
    - backend/app/ml/faiss_indices/       (ResNet50 indices — already exist)
    - backend/app/ml/fashionclip_indices/ (FashionCLIP indices — download from Vast.ai)
    - ml-engine/evaluation/test_images/   (4 test images)

Output:
    ml-engine/evaluation/comparison_results.html
"""

import sys
import pickle
import base64
from io import BytesIO
from pathlib import Path

import numpy as np
import faiss
import requests
from PIL import Image
from pymongo import MongoClient

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent
FC_ROOT     = SCRIPT_DIR.parent
ML_ROOT     = FC_ROOT.parent                          # ml-engine/
BACKEND_ML  = ML_ROOT.parent / "backend" / "app" / "ml"

RESNET_FAISS  = BACKEND_ML / "faiss_indices"
RESNET_MAPS   = BACKEND_ML / "id_maps"
FC_FAISS      = BACKEND_ML / "fashionclip_indices"
FC_MAPS       = BACKEND_ML / "fashionclip_id_maps"
TEST_DIR      = ML_ROOT / "evaluation" / "test_images"
OUT_HTML      = ML_ROOT / "evaluation" / "comparison_results.html"

sys.path.insert(0, str(ML_ROOT))

MONGO_URI = "mongodb+srv://ussamainayat:ussamainayat@dupefinder.u30xrsm.mongodb.net/"
MONGO_DB  = "dupefinder"
MONGO_COL = "products"

TOP_K = 5

QUERIES = [
    {"file": "1 (1).jpg", "category_slug": "women_kurta",       "label": "Women Kurta"},
    {"file": "2.png",     "category_slug": "women_kurta",       "label": "Women Kurta"},
    {"file": "3.png",     "category_slug": "women_kurta",       "label": "Women Kurta"},
    {"file": "5.jpg",     "category_slug": "men_standard_suit", "label": "Men Standard Suit"},
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def img_to_b64(img: Image.Image) -> str:
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=75)
    return base64.b64encode(buf.getvalue()).decode()


def fetch_img(url: str) -> Image.Image | None:
    try:
        r = requests.get(url, timeout=6)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGB")
    except Exception:
        return None


def load_index_set(faiss_dir: Path, maps_dir: Path) -> tuple[dict, dict]:
    """Load all .index files and matching .pkl id_maps from a directory."""
    indices, id_maps = {}, {}
    for f in faiss_dir.glob("*.index"):
        m = maps_dir / f"{f.stem}.pkl"
        if not m.exists():
            continue
        indices[f.stem] = faiss.read_index(str(f))
        with open(m, "rb") as fp:
            id_maps[f.stem] = pickle.load(fp)
    return indices, id_maps


def coerce_pid(pid):
    try:
        return int(pid)
    except (ValueError, TypeError):
        return str(pid)


def search_index(indices, id_maps, cat_slug, q_vec, top_k):
    """Query a single FAISS index. Returns list of {product_id, score}."""
    if cat_slug not in indices:
        return []
    scores, fids = indices[cat_slug].search(q_vec, top_k)
    hits = []
    for fid, score in zip(fids[0], scores[0]):
        if fid >= 0:
            pid = id_maps[cat_slug].get(int(fid))
            if pid is not None:
                hits.append({"product_id": str(pid), "score": float(score)})
    return hits


def fetch_docs(collection, hits):
    pids  = [coerce_pid(h["product_id"]) for h in hits]
    score_map = {h["product_id"]: h["score"] for h in hits}
    docs  = {
        str(d.get("product_id", "")): d
        for d in collection.find({"product_id": {"$in": pids}})
    }
    return docs, score_map


def make_cards(hits, docs, score_map):
    cards = ""
    for rank, hit in enumerate(hits, 1):
        pid   = hit["product_id"]
        score = hit["score"]
        doc   = docs.get(pid, {})
        name  = str(doc.get("name", "Unknown"))[:50]
        price = doc.get("price", "N/A")
        url   = doc.get("product_url", "#")
        img_url = doc.get("image_url", "")

        img = fetch_img(img_url) if img_url else None
        if img:
            img_tag = (
                f'<img src="data:image/jpeg;base64,{img_to_b64(img)}" '
                f'style="width:130px;height:165px;object-fit:cover;border-radius:5px">'
            )
        else:
            img_tag = (
                '<div style="width:130px;height:165px;background:#e0e0e0;'
                'border-radius:5px;display:flex;align-items:center;'
                'justify-content:center;color:#999;font-size:11px">No image</div>'
            )

        color = "#27ae60" if score > 0.6 else "#e67e22" if score > 0.4 else "#e74c3c"
        cards += f"""
        <div style="text-align:center;flex:0 0 145px">
          {img_tag}
          <div style="font-size:11px;font-weight:bold;color:{color};margin-top:4px">
            #{rank} &nbsp; {score:.3f}</div>
          <div style="font-size:10px;color:#333;margin-top:2px">{name}</div>
          <div style="font-size:11px;color:#c0392b;margin-top:1px">Rs {price}</div>
          <a href="{url}" target="_blank"
             style="font-size:10px;color:#2980b9">view</a>
        </div>"""
    return cards


# ── Main ──────────────────────────────────────────────────────────────────────

print("[1/5] Connecting to MongoDB...")
client     = MongoClient(MONGO_URI)
collection = client[MONGO_DB][MONGO_COL]

print("[2/5] Loading ResNet50 indices...")
if not RESNET_FAISS.exists():
    print(f"[ERROR] ResNet50 indices not found at {RESNET_FAISS}")
    sys.exit(1)
rn_indices, rn_maps = load_index_set(RESNET_FAISS, RESNET_MAPS)
print(f"       Loaded {len(rn_indices)} ResNet50 indices")

print("[3/5] Loading FashionCLIP indices...")
if not FC_FAISS.exists():
    print(f"[ERROR] FashionCLIP indices not found at {FC_FAISS}")
    print("       Run generate_embeddings.py on Vast.ai first, then download.")
    sys.exit(1)
fc_indices, fc_maps = load_index_set(FC_FAISS, FC_MAPS)
print(f"       Loaded {len(fc_indices)} FashionCLIP indices")

print("[4/5] Loading FashionCLIP extractor (CPU)...")
from fashionclip.extractor import FashionCLIPExtractor
fc_extractor = FashionCLIPExtractor(device="cpu")

print("[5/5] Loading ResNet50 extractor (CPU)...")
from embeddings.feature_extractor import FeatureExtractor
rn_extractor = FeatureExtractor(device="cpu")

# ── Run queries ───────────────────────────────────────────────────────────────

html_blocks = []
for q in QUERIES:
    qpath = TEST_DIR / q["file"]
    if not qpath.exists():
        print(f"  [SKIP] {q['file']} not found in {TEST_DIR}")
        continue

    cat_slug = q["category_slug"]
    print(f"\n  Query: {q['file']}  ({q['label']})")

    # ResNet50 query vector (normalize before FAISS)
    rn_raw  = rn_extractor.extract_from_path(qpath).astype("float32")
    rn_norm = np.linalg.norm(rn_raw)
    rn_vec  = (rn_raw / (rn_norm if rn_norm > 0 else 1e-8)).reshape(1, -1)

    # FashionCLIP query vector (already L2-normalised by extractor)
    fc_vec = fc_extractor.extract_from_path(qpath).astype("float32").reshape(1, -1)

    # FAISS search
    rn_hits = search_index(rn_indices, rn_maps, cat_slug, rn_vec, TOP_K)
    fc_hits = search_index(fc_indices, fc_maps, cat_slug, fc_vec, TOP_K)

    # Fetch product docs
    all_hits = rn_hits + fc_hits
    all_docs, _ = fetch_docs(collection, all_hits)

    rn_docs, rn_score_map = fetch_docs(collection, rn_hits)
    fc_docs, fc_score_map = fetch_docs(collection, fc_hits)

    rn_cards = make_cards(rn_hits, rn_docs, rn_score_map)
    fc_cards = make_cards(fc_hits, fc_docs, fc_score_map)

    q_img = Image.open(qpath).convert("RGB")
    q_b64 = img_to_b64(q_img)

    query_card = f"""
        <div style="text-align:center;flex:0 0 145px">
          <img src="data:image/jpeg;base64,{q_b64}"
               style="width:130px;height:165px;object-fit:cover;border-radius:5px;
                      border:3px solid #2980b9">
          <div style="font-size:11px;color:#2980b9;font-weight:bold;margin-top:4px">
            QUERY</div>
          <div style="font-size:10px;color:#555">{q['file']}</div>
        </div>"""

    html_blocks.append(f"""
    <div style="border:1px solid #ddd;border-radius:10px;padding:20px;margin:28px 0;background:#fafafa">
      <h3 style="margin:0 0 14px;font-size:15px;color:#2c3e50">
        {q['file']} &rarr; <span style="color:#8e44ad">{q['label']}</span>
      </h3>

      <!-- ResNet50 row -->
      <div style="margin-bottom:18px">
        <div style="font-size:12px;font-weight:bold;color:#555;margin-bottom:8px;
                    background:#ecf0f1;padding:4px 10px;border-radius:4px;display:inline-block">
          ResNet50  (2048-dim)
        </div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-start">
          {query_card}
          {rn_cards}
        </div>
      </div>

      <!-- FashionCLIP row -->
      <div>
        <div style="font-size:12px;font-weight:bold;color:#555;margin-bottom:8px;
                    background:#fdebd0;padding:4px 10px;border-radius:4px;display:inline-block">
          FashionCLIP  (512-dim, fashion fine-tuned)
        </div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:flex-start">
          {query_card}
          {fc_cards}
        </div>
      </div>
    </div>""")

# ── Write HTML ────────────────────────────────────────────────────────────────

rn_total = sum(idx.ntotal for idx in rn_indices.values())
fc_total = sum(idx.ntotal for idx in fc_indices.values())

html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>ResNet50 vs FashionCLIP — DupeFinder Evaluation</title>
  <style>
    body  {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
             max-width: 1300px; margin: 30px auto; padding: 0 20px; color: #2c3e50 }}
    h1   {{ font-size: 22px; border-bottom: 3px solid #2980b9; padding-bottom: 8px }}
    .meta {{ background: #ecf0f1; padding: 12px 16px; border-radius: 8px;
             font-size: 13px; margin-bottom: 20px; display:flex; gap:30px }}
    .m   {{ text-align:center }}
    .m b {{ display:block; font-size:20px }}
  </style>
</head>
<body>
  <h1>ResNet50 vs FashionCLIP — Visual Similarity Comparison</h1>
  <div class="meta">
    <div class="m"><b style="color:#2980b9">ResNet50</b> 2048-dim · {len(rn_indices)} categories · {rn_total:,} vectors</div>
    <div class="m"><b style="color:#e67e22">FashionCLIP</b> 512-dim · {len(fc_indices)} categories · {fc_total:,} vectors</div>
    <div class="m"><b>{len(html_blocks)}</b> queries · top-{TOP_K} results each</div>
  </div>
  {''.join(html_blocks)}
</body>
</html>"""

OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
OUT_HTML.write_text(html, encoding="utf-8")
print(f"\n[DONE] Report written: {OUT_HTML}")
print("Open it in your browser to compare ResNet50 vs FashionCLIP results.")
