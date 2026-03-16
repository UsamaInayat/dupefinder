"""
FashionCLIP — Generate embeddings and build FAISS indices on Vast.ai GPU.

Key improvement over the old approach:
    Uses PyTorch DataLoader with num_workers=4 so images are loaded in
    parallel background threads while the GPU processes the current batch.
    Expected speed: ~1-2s/batch (vs ~20s/batch before) → 23k images in ~10min.

Run ON the Vast.ai instance:
    cd /root
    python ml-engine/fashionclip/scripts/generate_embeddings.py

Optional flags:
    --batch-size 64        GPU batch size (default: 64)
    --workers    4         DataLoader worker threads (default: 4)
    --category "Women Kurta"   Process one category only (for smoke test)
    --skip-mongo-push          Skip writing embeddings back to MongoDB

Output (on Vast.ai):
    /root/fashionclip_output/faiss_indices/{slug}.index
    /root/fashionclip_output/id_maps/{slug}.pkl

After job completes, download with download_fashionclip_indices.py
and place in backend/app/ml/fashionclip_indices/ + fashionclip_id_maps/
"""

import os
import sys
import csv
import pickle
import argparse
from pathlib import Path
from collections import defaultdict

import numpy as np
import yaml
import faiss
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from tqdm import tqdm
from transformers import CLIPModel, CLIPProcessor

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent
FC_ROOT     = SCRIPT_DIR.parent          # ml-engine/fashionclip/
ML_ROOT     = FC_ROOT.parent             # ml-engine/

CONFIG_PATH  = FC_ROOT / "config.yaml"
OUTPUT_DIR   = Path("/root/fashionclip_output")
FAISS_DIR    = OUTPUT_DIR / "faiss_indices"
ID_MAPS_DIR  = OUTPUT_DIR / "id_maps"

FAISS_DIR.mkdir(parents=True, exist_ok=True)
ID_MAPS_DIR.mkdir(parents=True, exist_ok=True)

with open(CONFIG_PATH) as f:
    CFG = yaml.safe_load(f)

MANIFEST_CSV = Path(CFG["paths"]["manifest_csv"])
MODEL_ID     = CFG["model"]["id"]
EMBED_DIM    = CFG["model"]["embedding_dimension"]  # 512

MONGO_URI = CFG["mongodb"]["uri"]
MONGO_DB  = CFG["mongodb"]["database"]
MONGO_COL = CFG["mongodb"]["collection"]


# ── Dataset (enables DataLoader parallel prefetch) ────────────────────────────

class CatalogueDataset(Dataset):
    """
    Wraps the manifest rows so DataLoader can load images in parallel
    background threads (num_workers > 0) while GPU processes current batch.
    """
    def __init__(self, rows: list, processor: CLIPProcessor):
        self.rows      = rows
        self.processor = processor

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        row = self.rows[idx]
        try:
            img = Image.open(row["local_image_path"]).convert("RGB")
        except Exception:
            img = Image.new("RGB", (224, 224))   # blank fallback

        pixel_values = self.processor(
            images=img, return_tensors="pt", padding=True
        )["pixel_values"].squeeze(0)             # (3, 224, 224)

        return pixel_values, str(row["product_id"]), str(row["display_category"] or "unknown")


def collate_fn(batch):
    pixel_values = torch.stack([b[0] for b in batch])
    product_ids  = [b[1] for b in batch]
    categories   = [b[2] for b in batch]
    return pixel_values, product_ids, categories


# ── Helpers ───────────────────────────────────────────────────────────────────

def slug(cat: str) -> str:
    return cat.lower().replace(" ", "_").replace("/", "-")


def load_manifest(category_filter: str | None) -> list:
    if not MANIFEST_CSV.exists():
        raise FileNotFoundError(
            f"manifest.csv not found at {MANIFEST_CSV}. "
            "Run export_images_for_embedding.py first."
        )
    rows = []
    with open(MANIFEST_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if category_filter and row["display_category"] != category_filter:
                continue
            if Path(row["local_image_path"]).exists():
                rows.append(row)
            else:
                print(f"[WARN] Missing image, skipping: {row['local_image_path']}")
    print(f"[INFO] Manifest: {len(rows)} valid rows loaded")
    return rows


def _coerce_pid(pid: str):
    try:
        return int(pid)
    except (ValueError, TypeError):
        return str(pid)


# ── Embedding extraction with DataLoader ──────────────────────────────────────

def extract_all(rows: list, batch_size: int, num_workers: int, device: torch.device):
    """
    Extract FashionCLIP embeddings for all rows using DataLoader.
    Returns: { display_category: (np.ndarray[N,512], [product_id, ...]) }
    """
    processor = CLIPProcessor.from_pretrained(MODEL_ID)
    model     = CLIPModel.from_pretrained(MODEL_ID).to(device)
    model.eval()
    print(f"[OK]  FashionCLIP loaded on {device}")

    dataset = CatalogueDataset(rows, processor)
    loader  = DataLoader(
        dataset,
        batch_size  = batch_size,
        num_workers = num_workers,
        pin_memory  = (device.type == "cuda"),
        collate_fn  = collate_fn,
        prefetch_factor = 2 if num_workers > 0 else None,
    )

    # Collect all embeddings + metadata
    all_vecs: list[np.ndarray] = []
    all_pids: list[str]        = []
    all_cats: list[str]        = []

    with tqdm(total=len(rows), desc="FashionCLIP embeddings") as pbar:
        for pixel_values, product_ids, categories in loader:
            pixel_values = pixel_values.to(device)
            with torch.no_grad():
                vision_out = model.vision_model(pixel_values=pixel_values)
                pooled     = vision_out.pooler_output
                vecs       = model.visual_projection(pooled)

            vecs = vecs / vecs.norm(dim=-1, keepdim=True)
            all_vecs.append(vecs.cpu().float().numpy())
            all_pids.extend(product_ids)
            all_cats.extend(categories)
            pbar.update(len(product_ids))

    all_vecs_np = np.vstack(all_vecs)   # (total_N, 512)

    # Group by category
    by_cat: dict[str, tuple] = defaultdict(lambda: ([], []))
    for vec, pid, cat in zip(all_vecs_np, all_pids, all_cats):
        by_cat[cat][0].append(vec)
        by_cat[cat][1].append(pid)

    return {
        cat: (np.stack(vecs_list).astype("float32"), pids)
        for cat, (vecs_list, pids) in by_cat.items()
    }


# ── FAISS index building ───────────────────────────────────────────────────────

def build_indices(category_data: dict):
    for cat, (embeddings, product_ids) in category_data.items():
        n    = embeddings.shape[0]
        s    = slug(cat)

        print(f"[INFO] Building index for '{cat}'  ({n} vectors, dim={EMBED_DIM})")
        index = faiss.IndexFlatIP(EMBED_DIM)
        index.add(embeddings)

        faiss.write_index(index, str(FAISS_DIR / f"{s}.index"))
        id_map = {i: pid for i, pid in enumerate(product_ids)}
        with open(ID_MAPS_DIR / f"{s}.pkl", "wb") as f:
            pickle.dump(id_map, f)
        print(f"[OK]  {s}.index  +  {s}.pkl")


# ── MongoDB push (optional) ────────────────────────────────────────────────────

def push_to_mongo(category_data: dict):
    try:
        from pymongo import MongoClient, UpdateOne
    except ImportError:
        print("[WARN] pymongo not installed — skipping MongoDB push")
        return

    print("\n[INFO] Pushing embeddings to MongoDB...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    col    = client[MONGO_DB][MONGO_COL]
    total  = 0

    for cat, (embeddings, product_ids) in category_data.items():
        ops = [
            UpdateOne(
                {"product_id": _coerce_pid(pid)},
                {"$set": {"fashionclip_embedding": vec.tolist()}},
            )
            for pid, vec in zip(product_ids, embeddings)
        ]
        if ops:
            r = col.bulk_write(ops, ordered=False)
            total += r.modified_count
            print(f"[OK]  {cat}: updated {r.modified_count} docs")

    print(f"[OK]  Total updated: {total}")
    client.close()


# ── Summary ────────────────────────────────────────────────────────────────────

def print_summary(category_data: dict):
    print("\n" + "=" * 60)
    print("FASHIONCLIP EMBEDDING GENERATION COMPLETE")
    print("=" * 60)
    total = 0
    for cat, (emb, _) in sorted(category_data.items()):
        n     = emb.shape[0]
        total += n
        print(f"  {n:>5}  {cat:<35} -> {slug(cat)}.index")
    print("-" * 60)
    print(f"  {total:>5}  TOTAL")
    print(f"\n  FAISS indices : {FAISS_DIR}")
    print(f"  ID maps       : {ID_MAPS_DIR}")
    print("=" * 60)
    print("\nNext step: run download_fashionclip_indices.py on your local machine")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size",      type=int, default=64)
    parser.add_argument("--workers",         type=int, default=4)
    parser.add_argument("--category",        type=str, default=None)
    parser.add_argument("--skip-mongo-push", action="store_true")
    args = parser.parse_args()

    print("[INFO] DupeFinder — FashionCLIP Embedding Generation")
    print(f"[INFO] FAISS version : {faiss.__version__}")

    # Device
    if torch.cuda.is_available():
        n_gpu = torch.cuda.device_count()
        print(f"[INFO] CUDA GPUs: {n_gpu}")
        for i in range(n_gpu):
            print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        device = torch.device("cuda")
    else:
        print("[INFO] No GPU — running on CPU (slow!)")
        device = torch.device("cpu")

    rows = load_manifest(args.category)
    if not rows:
        print("[ERROR] No rows to process.")
        return

    category_data = extract_all(rows, args.batch_size, args.workers, device)
    build_indices(category_data)

    if not args.skip_mongo_push:
        push_to_mongo(category_data)
    else:
        print("[INFO] Skipping MongoDB push")

    print_summary(category_data)


if __name__ == "__main__":
    main()
