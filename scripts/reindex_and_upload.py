#!/usr/bin/env python3
"""
Run FashionCLIP reindex locally (same Mongo as production), pack indices + id_maps
into a .tar.gz, and POST them to the Railway API for atomic install + hot-reload.

Prereqs (from repo root, with ml-engine deps installed):
  pip install -r ml-engine/requirements.txt
  pip install httpx

Env (same as ml-engine/scripts/reindex_new_products.py for Mongo):
  MONGO_URI / MONGODB_URI, MONGO_DB_NAME, MONGO_COLLECTION

Railway API:
  Set REINDEX_ON_SERVER=false on the service so scrape does not OOM during reindex.
  Increase upload limit if needed: REINDEX_REMOTE_UPLOAD_MAX_BYTES (default 900000000).

Usage:
  python scripts/reindex_and_upload.py --api-base https://YOUR.railway.app/api \\
      --token YOUR_ADMIN_JWT

  python scripts/reindex_and_upload.py --api-base https://.../api --token $TOKEN --skip-reindex
      # only pack + upload existing backend/app/ml indices
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _default_ml_dir() -> Path:
    raw = (os.environ.get("BACKEND_APP_ML_DIR") or "").strip()
    return Path(raw) if raw else ROOT / "backend" / "app" / "ml"


def _run_local_reindex() -> None:
    script = ROOT / "ml-engine" / "scripts" / "reindex_new_products.py"
    if not script.is_file():
        raise SystemExit(f"Missing {script}")
    env = os.environ.copy()
    print("[INFO] Running local reindex (writes under BACKEND_APP_ML_DIR / FAISS_INDEX_DIR)...", flush=True)
    subprocess.check_call([sys.executable, str(script)], cwd=str(ROOT), env=env)


def _build_tarball(ml_dir: Path) -> Path:
    idx = Path(os.environ.get("FAISS_INDEX_DIR", str(ml_dir / "fashionclip_indices")))
    maps = Path(os.environ.get("FAISS_ID_MAP_DIR", str(ml_dir / "fashionclip_id_maps")))
    if not idx.is_dir() or not maps.is_dir():
        raise SystemExit(f"Missing indices dirs:\n  {idx}\n  {maps}")
    staging = Path(tempfile.mkdtemp(prefix="faiss_tar_stage_"))
    try:
        shutil.copytree(idx, staging / "fashionclip_indices")
        shutil.copytree(maps, staging / "fashionclip_id_maps")
        arc_base = staging.parent / f"{staging.name}_bundle"
        arc = shutil.make_archive(
            str(arc_base),
            "gztar",
            root_dir=str(staging),
            base_dir=".",
        )
        return Path(arc)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _upload(api_base: str, token: str, tar_path: Path) -> None:
    try:
        import httpx
    except ImportError as e:
        raise SystemExit("pip install httpx") from e

    base = api_base.rstrip("/")
    url = f"{base}/admin/reindex-remote/upload"
    print(f"[INFO] POST {url} ({tar_path.stat().st_size} bytes) ...", flush=True)
    with open(tar_path, "rb") as f:
        files = {"file": ("faiss_bundle.tar.gz", f, "application/gzip")}
        headers = {"Authorization": f"Bearer {token}"}
        with httpx.Client(timeout=httpx.Timeout(600.0)) as client:
            r = client.post(url, headers=headers, files=files)
    if r.status_code >= 400:
        raise SystemExit(f"Upload failed HTTP {r.status_code}: {r.text[:2000]}")
    print("[OK]", r.json(), flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description="Local reindex + upload FAISS bundle to DupeFinder API")
    p.add_argument(
        "--api-base",
        required=True,
        help="API root including /api, e.g. https://dupefinder-api.up.railway.app/api",
    )
    p.add_argument(
        "--token",
        default=os.environ.get("DUPFINDER_ADMIN_TOKEN", ""),
        help="Admin JWT (or set DUPFINDER_ADMIN_TOKEN)",
    )
    p.add_argument(
        "--skip-reindex",
        action="store_true",
        help="Only pack + upload existing local index directories",
    )
    args = p.parse_args()
    if not args.token.strip():
        raise SystemExit("Missing --token or DUPFINDER_ADMIN_TOKEN")

    ml_dir = _default_ml_dir()
    if not args.skip_reindex:
        _run_local_reindex()
    tar = _build_tarball(ml_dir)
    try:
        _upload(args.api_base, args.token.strip(), tar)
    finally:
        tar.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
