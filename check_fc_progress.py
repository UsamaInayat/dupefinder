"""
Check FashionCLIP generation progress on Vast.ai.
Upload once and run anytime to get current status.
"""
import os, subprocess

log_file   = "/root/fashionclip_generate.log"
output_dir = "/root/fashionclip_output"

# Process status
ps = subprocess.run(["ps", "aux"], capture_output=True, text=True).stdout
running = any("generate_embeddings" in l and "grep" not in l for l in ps.splitlines())
print(f"generate_embeddings.py running: {running}")

# Index count
if os.path.exists(f"{output_dir}/faiss_indices"):
    indices = [f for f in os.listdir(f"{output_dir}/faiss_indices") if f.endswith(".index")]
    print(f"FAISS indices built so far: {len(indices)}")
    for i in sorted(indices):
        size = os.path.getsize(f"{output_dir}/faiss_indices/{i}") // 1024
        print(f"  {i}  ({size} KB)")
else:
    print("FAISS indices dir not created yet")

# Last log lines
if os.path.exists(log_file):
    with open(log_file) as f:
        lines = f.readlines()
    print(f"\nLast 10 log lines:")
    for l in lines[-10:]:
        print(f"  {l.rstrip()}")
else:
    print(f"\nLog file not found: {log_file}")
