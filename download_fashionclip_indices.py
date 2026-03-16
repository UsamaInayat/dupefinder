"""
Download FashionCLIP FAISS indices from Vast.ai to backend/app/ml/

Run this AFTER generate_embeddings.py has completed on Vast.ai.
Update SSH_HOST and SSH_PORT to match your new Vast.ai instance.

Usage:
    python download_fashionclip_indices.py
"""
import subprocess, sys
from pathlib import Path

# ── UPDATE THESE when you get the new Vast.ai instance ───────────────────────
SSH_KEY  = r"C:\Users\US\Desktop\dupefinder\vastai_key.pem"
SSH_HOST = "root@86.127.245.129"
SSH_PORT = "22575"
# ─────────────────────────────────────────────────────────────────────────────

REMOTE_OUTPUT = "/root/fashionclip_output"
LOCAL_ML      = Path(r"C:\Users\US\Desktop\dupefinder\backend\app\ml")
FC_FAISS_DST  = LOCAL_ML / "fashionclip_indices"
FC_MAPS_DST   = LOCAL_ML / "fashionclip_id_maps"


def run(cmd, check=True):
    print(f"  > {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.stdout.strip(): print(r.stdout.strip())
    if r.stderr.strip(): print(r.stderr.strip())
    if check and r.returncode != 0:
        print(f"[ERROR] Command failed (exit {r.returncode})")
        sys.exit(1)
    return r


print("=" * 60)
print("DupeFinder — Download FashionCLIP Indices from Vast.ai")
print("=" * 60)

# Step 1: verify remote output exists
print("\n[1/4] Checking remote output...")
r = run(["ssh", "-o", "StrictHostKeyChecking=no", "-p", SSH_PORT,
         "-i", SSH_KEY, SSH_HOST,
         "ls /root/fashionclip_output/faiss_indices/*.index 2>/dev/null | wc -l"], check=False)
count = r.stdout.strip().split()[-1] if r.stdout.strip() else "0"
if count == "0":
    print("[ERROR] No .index files found — Vast.ai job may not have finished yet.")
    sys.exit(1)
print(f"[OK] Found {count} index files on Vast.ai")

# Step 2: clear any old FC indices locally
print("\n[2/4] Clearing existing local FashionCLIP indices...")
for f in FC_FAISS_DST.glob("*.index"):
    f.unlink(); print(f"  Deleted: {f.name}")
for f in FC_MAPS_DST.glob("*.pkl"):
    f.unlink(); print(f"  Deleted: {f.name}")

# Step 3: download indices
print("\n[3/4] Downloading fashionclip_indices/ ...")
run(["scp", "-o", "StrictHostKeyChecking=no", "-P", SSH_PORT, "-i", SSH_KEY, "-r",
     f"{SSH_HOST}:{REMOTE_OUTPUT}/faiss_indices/.", str(FC_FAISS_DST)])

# Step 4: download id_maps
print("\n[4/4] Downloading id_maps/ ...")
run(["scp", "-o", "StrictHostKeyChecking=no", "-P", SSH_PORT, "-i", SSH_KEY, "-r",
     f"{SSH_HOST}:{REMOTE_OUTPUT}/id_maps/.", str(FC_MAPS_DST)])

# Summary
indices = list(FC_FAISS_DST.glob("*.index"))
maps    = list(FC_MAPS_DST.glob("*.pkl"))
print(f"\n{'='*60}\nDOWNLOAD COMPLETE")
print(f"  FashionCLIP indices : {len(indices)}  -> {FC_FAISS_DST}")
print(f"  ID maps             : {len(maps)}  -> {FC_MAPS_DST}")
print("\nIndex files:")
for f in sorted(indices):
    print(f"  {f.name:<45} {f.stat().st_size//1024:>5} KB")
print("="*60)
print("\nNext steps:")
print("  1. Restart the backend")
print("  2. cd ml-engine && python fashionclip/scripts/quick_eval.py")
print("  3. Open ml-engine/evaluation/comparison_results.html")
