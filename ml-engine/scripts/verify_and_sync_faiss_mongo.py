"""
After a crash during reindex: verify FAISS + id_maps are consistent, optionally
sync MongoDB fashionclip_indexed from id_maps (vectors on disk but flags not set).

Then run: python ml-engine/scripts/reindex_new_products.py
"""
import pickle
import sys
from pathlib import Path
from collections import defaultdict

import faiss
import yaml
from pymongo import MongoClient

SCRIPT_DIR = Path(__file__).resolve().parent
ML_ROOT = SCRIPT_DIR.parent
BACKEND_ML = ML_ROOT.parent / "backend" / "app" / "ml"
FAISS_DIR = BACKEND_ML / "fashionclip_indices"
ID_MAPS_DIR = BACKEND_ML / "fashionclip_id_maps"

with open(ML_ROOT / "config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
m = cfg["mongodb"]


def main():
    errors = []
    all_pids: set[str] = set()
    dup_by_slug: dict[str, list] = defaultdict(list)

    for idx_path in sorted(FAISS_DIR.glob("*.index")):
        slug = idx_path.stem
        map_path = ID_MAPS_DIR / f"{slug}.pkl"
        if not map_path.exists():
            errors.append(f"MISSING_MAP {slug}: no {map_path.name}")
            continue

        # Stale tmp from crashed replace — safe to remove if main index loads
        tmp_idx = idx_path.with_suffix(".index.tmp")
        tmp_map = map_path.with_suffix(".pkl.tmp")
        try:
            index = faiss.read_index(str(idx_path))
        except Exception as e:
            errors.append(f"CORRUPT_INDEX {slug}: {e}")
            continue

        try:
            with open(map_path, "rb") as f:
                id_map = pickle.load(f)
        except Exception as e:
            errors.append(f"CORRUPT_MAP {slug}: {e}")
            continue

        nvec = index.ntotal
        nmap = len(id_map)
        if nvec != nmap:
            errors.append(f"MISMATCH {slug}: index.ntotal={nvec} id_map len={nmap}")
            continue

        seen = {}
        for k, pid in id_map.items():
            sp = str(pid)
            all_pids.add(sp)
            if sp in seen:
                dup_by_slug[slug].append((sp, seen[sp], k))
            else:
                seen[sp] = k

    print("=== FAISS / id_map verification ===")
    if errors:
        print(f"[FAIL] {len(errors)} problem(s):")
        for e in errors:
            print(" ", e)
        sys.exit(1)

    print(f"[OK] All {len(list(FAISS_DIR.glob('*.index')))} index files + maps consistent")

    if dup_by_slug:
        print("[WARN] Duplicate product_id in same category map (search may return dupes):")
        for slug, dups in dup_by_slug.items():
            if dups:
                print(f"  {slug}: {len(dups)} duplicate(s), e.g. {dups[:3]}")
    else:
        print("[OK] No duplicate product_ids within a category map")

    print(f"[INFO] Unique product_ids across all maps: {len(all_pids)}")

    # Sync Mongo: mark indexed=True for every pid present in FAISS maps
    client = MongoClient(m["uri"], serverSelectionTimeoutMS=25000)
    client.admin.command("ping")
    col = client[m["database"]][m["collection"]]

    def coerce(pid: str):
        try:
            return int(pid)
        except ValueError:
            return pid

    plist = [coerce(p) for p in sorted(all_pids)]
    batch = 2000
    total_mod = 0
    for i in range(0, len(plist), batch):
        chunk = plist[i : i + batch]
        r = col.update_many(
            {"product_id": {"$in": chunk}},
            {"$set": {"fashionclip_indexed": True}},
        )
        total_mod += r.modified_count
    print(f"[OK] MongoDB sync: update_many in batches, modified_count={total_mod}")
    print("     (only docs that were missing/false changed)")

    not_idx = col.count_documents({"fashionclip_indexed": {"$ne": True}})
    total = col.count_documents({})
    print(f"[INFO] After sync — total products: {total}, still NOT indexed: {not_idx}")

    client.close()
    print("\nNext: python ml-engine/scripts/reindex_new_products.py")
    print("      (processes only products still missing from FAISS + Mongo)")


if __name__ == "__main__":
    main()
