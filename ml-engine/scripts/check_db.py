from pymongo import MongoClient
import yaml

with open('config.yaml') as f:
    cfg = yaml.safe_load(f)

client = MongoClient(cfg['mongodb']['uri'])
col = client[cfg['mongodb']['database']][cfg['mongodb']['collection']]

total = col.count_documents({})

pipeline = [
    {"$group": {"_id": "$display_category", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
]
results = list(col.aggregate(pipeline))

print(f"Total products: {total}")
print()
print("Products per display_category:")
for r in results:
    cat = r["_id"] or "(empty/none)"
    print(f"  {r['count']:>6}  {cat}")
