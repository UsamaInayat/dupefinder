"""
Vast.ai setup + launch script for FashionCLIP embedding generation.
Upload this file to the instance, then run it.

On Vast.ai (after scp upload):
    python3 /root/vastai_fashionclip_setup.py
"""
import subprocess, sys, os

def run(cmd, label=""):
    print(f"\n[RUN] {label or cmd}")
    r = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if r.stdout: print(r.stdout[-2000:])
    if r.stderr: print(r.stderr[-1000:])
    if r.returncode != 0:
        print(f"[ERROR] exit code {r.returncode}")
    return r.returncode == 0

print("=" * 60)
print("Vast.ai — FashionCLIP Pipeline Setup")
print("=" * 60)

# 1. Install dependencies
print("\n[STEP 1] Installing Python dependencies...")
run("pip install torch torchvision --quiet", "torch + torchvision")
run("pip install transformers>=4.35.0 --quiet", "transformers (FashionCLIP)")
run("pip install faiss-cpu pymongo dnspython Pillow tqdm pyyaml requests --quiet",
    "faiss + pymongo + utils")

# 2. Verify GPU
print("\n[STEP 2] Checking GPU...")
run("python3 -c \"import torch; print('CUDA:', torch.cuda.is_available()); "
    "[print(f'GPU {i}:', torch.cuda.get_device_name(i)) for i in range(torch.cuda.device_count())]\"",
    "GPU check")

# 3. Download images from MongoDB (runs synchronously so generate can start right after)
print("\n[STEP 3] Downloading catalogue images from MongoDB...")
images_dir = "/root/ml-engine/data/catalogue_images"
manifest   = "/root/ml-engine/data/manifest.csv"

existing_images = 0
if os.path.exists(images_dir):
    existing_images = len([f for f in os.listdir(images_dir) if not f.startswith(".")])

if existing_images > 20000 and os.path.exists(manifest):
    print(f"[OK] {existing_images} images already present — skipping download")
else:
    print(f"[INFO] Found {existing_images} images, running export_images_for_embedding.py ...")
    ok = run(
        "python3 /root/ml-engine/scripts/export_images_for_embedding.py --workers 16",
        "Downloading catalogue images"
    )
    if not ok:
        print("[ERROR] Image download failed — check MongoDB connection")
        sys.exit(1)

    if os.path.exists(manifest):
        with open(manifest) as f:
            lines = sum(1 for _ in f) - 1
        print(f"[OK] manifest.csv now has {lines} rows")
    else:
        print("[ERROR] manifest.csv was not created — aborting")
        sys.exit(1)

# 4. Launch generate_embeddings.py in background
print("\n[STEP 4] Launching FashionCLIP embedding generation...")
log_file = "/root/fashionclip_generate.log"
script   = "/root/ml-engine/fashionclip/scripts/generate_embeddings.py"

if not os.path.exists(script):
    print(f"[ERROR] Script not found: {script}")
    print("        Upload ml-engine/fashionclip/ folder first via SCP")
    sys.exit(1)

proc = subprocess.Popen(
    ["python3", script, "--skip-mongo-push", "--batch-size", "64", "--workers", "4"],
    cwd="/root/ml-engine",
    stdout=open(log_file, "w"),
    stderr=subprocess.STDOUT,
    start_new_session=True,
)

print(f"[OK] Process started — PID {proc.pid}")
print(f"[OK] Log file: {log_file}")
print(f"\nMonitor progress:")
print(f"  python3 /root/check_fc_progress.py")
