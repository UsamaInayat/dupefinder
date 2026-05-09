"""
Fill fabric, material, features, and feature_keywords from existing description text.

Uses rule-based extract_features_from_description (no HTTP). By default only processes
products that have **no** feature extraction yet (all of fabric, material, features,
feature_keywords empty). Never overwrites non-empty fields.

Optional: ``--fill-partial`` also includes rows missing any one of those fields and
fills only the empty slots (still never overwrites existing values).

  cd backend
  python scripts/backfill_features_from_descriptions.py --limit 50000
  python scripts/backfill_features_from_descriptions.py --dry-run --limit 1000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from pymongo import MongoClient, UpdateOne
from pymongo.errors import AutoReconnect, NetworkTimeout, ServerSelectionTimeoutError

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.services.feature_extraction_service import feature_set_doc_from_product

_MONGO_KWARGS = {
    "serverSelectionTimeoutMS": 90_000,
    "connectTimeoutMS": 45_000,
    "socketTimeoutMS": 180_000,
    "maxPoolSize": 50,
}


def _has_nonempty_description() -> dict[str, Any]:
    return {
        "$expr": {
            "$and": [
                {"$eq": [{"$type": "$description"}, "string"]},
                {"$gt": [{"$strLenCP": {"$trim": {"input": "$description"}}}, 0]},
            ]
        }
    }


def _string_field_empty(field: str) -> dict[str, Any]:
    return {
        "$or": [
            {field: {"$exists": False}},
            {field: None},
            {"$expr": {"$ne": [{"$type": f"${field}"}, "string"]}},
            {
                "$expr": {
                    "$lte": [{"$strLenCP": {"$trim": {"input": {"$ifNull": [f"${field}", ""]}}}}, 0]
                }
            },
        ]
    }


def _keywords_empty() -> dict[str, Any]:
    return {
        "$or": [
            {"feature_keywords": {"$exists": False}},
            {"feature_keywords": None},
            {"$expr": {"$lte": [{"$size": {"$ifNull": ["$feature_keywords", []]}}, 0]}},
        ]
    }


def _needs_any_feature_fill() -> dict[str, Any]:
    return {
        "$or": [
            _string_field_empty("fabric"),
            _string_field_empty("material"),
            _string_field_empty("features"),
            _keywords_empty(),
        ]
    }


def _needs_all_feature_fields_empty() -> dict[str, Any]:
    """No extracted features yet (same cohort as description-only products)."""
    return {
        "$and": [
            _string_field_empty("fabric"),
            _string_field_empty("material"),
            _string_field_empty("features"),
            _keywords_empty(),
        ]
    }


def _query_backfill(*, fill_partial: bool) -> dict[str, Any]:
    need = _needs_any_feature_fill() if fill_partial else _needs_all_feature_fields_empty()
    return {"$and": [_has_nonempty_description(), need]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill feature fields from description text")
    parser.add_argument("--limit", type=int, default=50_000, help="Max documents to scan")
    parser.add_argument("--batch", type=int, default=500, help="Mongo bulk_write batch size")
    parser.add_argument("--dry-run", action="store_true", help="Do not write")
    parser.add_argument(
        "--fill-partial",
        action="store_true",
        help="Also process rows that already have some feature fields: only empty fields are filled.",
    )
    args = parser.parse_args()

    limit = max(1, args.limit)
    batch = max(50, min(args.batch, 2000))

    client = MongoClient(settings.MONGO_URI, **_MONGO_KWARGS)
    products = client[settings.MONGO_DB_NAME]["products"]

    query = _query_backfill(fill_partial=bool(args.fill_partial))
    total_match = products.count_documents(query)

    mode = "fill_partial" if args.fill_partial else "no_features_yet"
    print(
        f"[INFO] mode={mode} matching_documents~{total_match} will_scan<={limit} "
        f"dry_run={args.dry_run}"
    )

    cursor = products.find(
        query,
        {
            "_id": 1,
            "name": 1,
            "description": 1,
            "fabric": 1,
            "material": 1,
            "features": 1,
            "feature_keywords": 1,
        },
    ).limit(limit)

    pending: list[UpdateOne] = []
    scanned = 0
    would_write = 0
    modified = 0

    def flush() -> None:
        nonlocal pending, modified
        if args.dry_run or not pending:
            pending = []
            return
        delay = 2.0
        last_exc: Exception | None = None
        for attempt in range(10):
            try:
                r = products.bulk_write(pending, ordered=False)
                modified += r.modified_count + getattr(r, "upserted_count", 0)
                pending = []
                return
            except (ServerSelectionTimeoutError, AutoReconnect, NetworkTimeout) as exc:
                last_exc = exc
                print(f"[WARN] bulk_write retry {attempt + 1}/10: {exc!r}")
                import time

                time.sleep(min(delay, 60.0))
                delay = min(delay * 1.6, 60.0)
        if last_exc:
            raise last_exc

    for doc in cursor:
        scanned += 1
        set_doc = feature_set_doc_from_product(doc, overwrite=False)
        if not set_doc:
            continue
        would_write += 1
        if not args.dry_run:
            pending.append(UpdateOne({"_id": doc["_id"]}, {"$set": set_doc}))
            if len(pending) >= batch:
                flush()

    flush()
    client.close()

    print(
        f"[DONE] scanned={scanned} updates_built={would_write} "
        f"db_modified={modified} dry_run={args.dry_run}"
    )


if __name__ == "__main__":
    main()
