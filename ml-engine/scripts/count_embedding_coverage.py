"""One-off: report how many products lack fashionclip_indexed=True."""
import sys
from pathlib import Path

import yaml
from pymongo import MongoClient

ML_ROOT = Path(__file__).resolve().parent.parent
with open(ML_ROOT / "config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

m = cfg["mongodb"]
client = MongoClient(m["uri"], serverSelectionTimeoutMS=25000)
client.admin.command("ping")
col = client[m["database"]][m["collection"]]

total = col.estimated_document_count()
indexed = col.count_documents({"fashionclip_indexed": True})
not_indexed = col.count_documents({"fashionclip_indexed": {"$ne": True}})
missing_field = col.count_documents({"fashionclip_indexed": {"$exists": False}})
explicit_false = col.count_documents({"fashionclip_indexed": False})

print("=== FashionCLIP embedding index status (MongoDB) ===")
print("Database:", m["database"])
print("Collection:", m["collection"])
print("Total products (estimated):", total)
print("Marked fashionclip_indexed=True:", indexed)
print("NOT indexed (missing OR not true):", not_indexed)
print("  - fashionclip_indexed field missing:", missing_field)
print("  - fashionclip_indexed explicitly false:", explicit_false)
print()
print("Products that still need embeddings (reindex target):", not_indexed)
client.close()
sys.exit(0)
