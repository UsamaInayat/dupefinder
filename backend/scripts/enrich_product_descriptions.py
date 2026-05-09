"""
Backfill product descriptions and extracted feature fields from existing product URLs.

Resume (default): only rows missing description OR marked failed by a previous run — no full restart.
  Pass 1 defaults to the **newest** backlog rows: ``--last 20000`` (sort ``--sort-key`` descending). Use ``--last 0`` for oldest-first.

  cd backend
  python scripts/enrich_product_descriptions.py --limit 32013 --concurrency 64 \\
    --mongo-batch 250 --chunk-size 600 --quiet --max-passes 8

After N products in **resume** order (missing/failed only) — if nothing runs, your backlog may be < N; use catalog scope:
  python scripts/enrich_product_descriptions.py --skip 12000 --limit 20000 ...

Skip N in **all products with URL** order, then take up to `--limit`, then only rows still missing/failed (typical “I already did 12k”):
  python scripts/enrich_product_descriptions.py --skip-scope catalog --skip 12000 --limit 20000 \\
    --concurrency 80 --mongo-batch 300 --chunk-size 800 --quiet --max-passes 8

Full re-scrape pass 1, then retry failures only on later passes:
  python scripts/enrich_product_descriptions.py --all --overwrite --limit 32013 \\
    --concurrency 64 --mongo-batch 250 --chunk-size 600 --quiet --max-passes 8

Mongo fields used for resume (safe, small):
  description_enrich_status: "ok" | "failed"
  description_enrich_last_error: short string
  description_enrich_last_attempt: UTC datetime
  description_enrich_attempts: int (incremented on scrape failure)
"""

from __future__ import annotations

import argparse
import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, Literal

import httpx
from bs4 import BeautifulSoup
from pymongo import MongoClient, UpdateOne
from pymongo.errors import AutoReconnect, NetworkTimeout, ServerSelectionTimeoutError

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.services.feature_extraction_service import extract_features_from_description
from app.services.scraper_service import ProductScraper

# Longer timeouts + retried writes reduce crashes when DNS / Atlas blips (Errno 11001).
_MONGO_KWARGS = {
    "serverSelectionTimeoutMS": 90_000,
    "connectTimeoutMS": 45_000,
    "socketTimeoutMS": 180_000,
    "maxPoolSize": 50,
}


def _has_url() -> dict[str, Any]:
    return {"product_url": {"$exists": True, "$type": "string", "$ne": ""}}


def _missing_or_failed_description() -> dict[str, Any]:
    """Rows that still need a description scrape (resume / retry cycles)."""
    return {
        "$or": [
            {"description": {"$exists": False}},
            {"description": None},
            {"description": ""},
            {"description_enrich_status": "failed"},
            {"description_enrich_status": "failed_retryable"},
        ]
    }


def _permanent_failure_statuses() -> list[str]:
    return [
        "invalid_url_scheme",
        "http_404",
        "http_410",
        "no_description",
    ]


def _is_retryable_error(err: str) -> bool:
    if not err:
        return True
    if err in _permanent_failure_statuses():
        return False
    if err.startswith("http_"):
        # Retry only transient HTTP codes.
        return err in {"http_408", "http_425", "http_429", "http_500", "http_502", "http_503", "http_504"}
    return True


def _missing_description_only() -> dict[str, Any]:
    return {
        "$and": [
            {
                "$or": [
                    {"description": {"$exists": False}},
                    {"description": None},
                    {"description": ""},
                ]
            },
            {
                # Do not keep reprocessing rows previously marked failed.
                "$or": [
                    {"description_enrich_status": {"$exists": False}},
                    {"description_enrich_status": None},
                    {"description_enrich_status": ""},
                    {"description_enrich_status": "ok"},
                ]
            },
        ]
    }


def _missing_or_retryable_failed_description() -> dict[str, Any]:
    """Rows that should be retried on later passes."""
    return {
        "$or": [
            {"description": {"$exists": False}},
            {"description": None},
            {"description": ""},
            {"description_enrich_status": "failed"},
            {"description_enrich_status": "failed_retryable"},
        ]
    }


def _query_resume(*, include_failed: bool) -> dict[str, Any]:
    needs_desc = _missing_or_retryable_failed_description() if include_failed else _missing_description_only()
    return {"$and": [_has_url(), needs_desc]}


def _query_full_catalog() -> dict[str, Any]:
    return _has_url()


_ENRICH_PROJECTION: dict[str, int] = {
    "_id": 1,
    "name": 1,
    "product_url": 1,
    "description": 1,
    "fabric": 1,
    "material": 1,
    "features": 1,
    "feature_keywords": 1,
}


def _catalog_slice_pipeline(
    *,
    skip: int,
    cap: int,
    sort_key: str,
    full_first_pass: bool,
    sort_desc: bool,
    include_failed: bool,
) -> list[dict[str, Any]]:
    """Skip/limit over all URL products, then optionally keep only resume rows."""
    direction = -1 if sort_desc else 1
    pipeline: list[dict[str, Any]] = [
        {"$match": _query_full_catalog()},
        {"$sort": {sort_key: direction}},
    ]
    if skip > 0:
        pipeline.append({"$skip": skip})
    pipeline.append({"$limit": cap})
    if not full_first_pass:
        if include_failed:
            pipeline.append({"$match": _missing_or_retryable_failed_description()})
        else:
            pipeline.append({"$match": _missing_description_only()})
    pipeline.append({"$project": _ENRICH_PROJECTION})
    return pipeline


def _should_set(current: object, overwrite: bool) -> bool:
    if overwrite:
        return True
    if current is None:
        return True
    if isinstance(current, str):
        return current.strip() == ""
    if isinstance(current, list):
        return len(current) == 0
    return False


def _make_fast_client(concurrency: int) -> httpx.AsyncClient:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }
    n = max(32, min(concurrency * 2, 200))
    return httpx.AsyncClient(
        timeout=httpx.Timeout(45.0, connect=15.0),
        follow_redirects=True,
        headers=headers,
        limits=httpx.Limits(max_keepalive_connections=n, max_connections=n),
    )


def _bulk_write_retry(collection: Any, ops: list[UpdateOne], *, quiet: bool) -> Any:
    if not ops:
        return None
    delay = 2.0
    last_exc: Exception | None = None
    for attempt in range(10):
        try:
            return collection.bulk_write(ops, ordered=False)
        except (ServerSelectionTimeoutError, AutoReconnect, NetworkTimeout) as exc:
            last_exc = exc
            if not quiet:
                print(f"[WARN] Mongo bulk_write retry {attempt + 1}/10 after: {exc!r}")
            time.sleep(min(delay, 60.0))
            delay = min(delay * 1.6, 60.0)
    if last_exc:
        raise last_exc
    raise RuntimeError("bulk_write failed without exception")


async def _fetch_description(
    client: httpx.AsyncClient,
    scraper: ProductScraper,
    product_url: str,
) -> tuple[str | None, int | None]:
    lowered = (product_url or "").strip().lower()
    if not (lowered.startswith("http://") or lowered.startswith("https://")):
        # Skip non-web schemes (mailto:, tel:, javascript:, etc.).
        return None, -1

    for attempt in range(2):
        try:
            response = await client.get(product_url)
            if response.status_code == 429 and attempt == 0:
                await asyncio.sleep(2.5)
                continue
            if response.status_code != 200:
                return None, response.status_code
            soup = BeautifulSoup(response.text, "html.parser")
            description = scraper._extract_description(soup)
            return (description or None), 200
        except Exception:
            if attempt == 0:
                await asyncio.sleep(1.0)
                continue
            return None, None
    return None, None


def _build_success_set_doc(doc: dict[str, Any], description: str, overwrite: bool) -> dict[str, Any] | None:
    extracted = extract_features_from_description(
        description,
        name_text=str(doc.get("name") or ""),
    )
    now = datetime.now(timezone.utc)
    set_doc: dict[str, Any] = {
        "description_updated_at": now,
        "description_enrich_status": "ok",
        "description_enrich_last_attempt": now,
        "description_enrich_last_error": None,
    }

    if _should_set(doc.get("description"), overwrite):
        set_doc["description"] = description
    if extracted["fabric"] and _should_set(doc.get("fabric"), overwrite):
        set_doc["fabric"] = extracted["fabric"]
    if extracted["material"] and _should_set(doc.get("material"), overwrite):
        set_doc["material"] = extracted["material"]
    if extracted["features"] and _should_set(doc.get("features"), overwrite):
        set_doc["features"] = extracted["features"]
    if extracted["feature_keywords"] and _should_set(doc.get("feature_keywords"), overwrite):
        set_doc["feature_keywords"] = extracted["feature_keywords"]

    return set_doc


def _failure_update(doc_id: Any, err: str) -> UpdateOne:
    now = datetime.now(timezone.utc)
    msg = (err or "unknown")[:400]
    retryable = _is_retryable_error(msg)
    return UpdateOne(
        {"_id": doc_id},
        {
            "$set": {
                "description_enrich_status": "failed_retryable" if retryable else "failed_permanent",
                "description_enrich_last_error": msg,
                "description_enrich_last_attempt": now,
            },
            "$inc": {"description_enrich_attempts": 1 if retryable else 0},
        },
    )


def _always_log(msg: str) -> None:
    """Printed even with --quiet so empty runs are diagnosable."""
    print(msg)


async def run(
    limit: int,
    overwrite: bool,
    dry_run: bool,
    full_first_pass: bool,
    concurrency: int,
    mongo_batch: int,
    chunk_size: int,
    quiet: bool,
    max_passes: int,
    skip: int,
    sort_key: str,
    skip_scope: Literal["resume", "catalog"],
    last_n: int,
    reverse_order: bool,
    include_failed: bool,
) -> None:
    mongo_client = MongoClient(settings.MONGO_URI, **_MONGO_KWARGS)
    products = mongo_client[settings.MONGO_DB_NAME]["products"]

    scraper = ProductScraper()
    old_client = scraper.client
    scraper.client = _make_fast_client(concurrency)
    await old_client.aclose()

    total_db_modified = 0
    total_scrape_fail = 0
    total_dry = 0
    total_noop_url = 0

    try:
        for pass_num in range(1, max(1, max_passes) + 1):
            if pass_num == 1 and full_first_pass:
                query = _query_full_catalog()
            else:
                query = _query_resume(include_failed=include_failed)

            try:
                remaining = products.count_documents(query)
            except Exception as exc:
                if not quiet:
                    print(f"[ERROR] Mongo count_documents failed: {exc!r}")
                raise

            if remaining == 0:
                _always_log(
                    f"[ABORT] pass={pass_num} reason=no_matching_documents "
                    f"(pass1 full catalog has no URLs, or resume has nothing missing/failed)"
                )
                break

            use_catalog_slice = pass_num == 1 and skip_scope == "catalog"
            use_resume_skip = pass_num == 1 and skip > 0 and skip_scope == "resume"
            use_last = pass_num == 1 and last_n > 0
            sort_dir = -1 if reverse_order else 1
            tail = max(0, remaining - skip) if use_resume_skip else remaining
            if use_resume_skip and tail == 0:
                _always_log(
                    f"[ABORT] pass={pass_num} reason=skip_larger_than_resume_backlog "
                    f"remaining_in_resume={remaining} skip={skip} "
                    f"(use --skip-scope catalog to skip by full URL list order, or lower --skip)"
                )
                break

            if use_catalog_slice:
                # Slice width after skip: bounded by --last and --limit when both used.
                cap = min(last_n, limit) if use_last else limit
            elif use_last:
                if use_resume_skip:
                    cap = min(last_n, limit, tail)
                else:
                    cap = min(last_n, limit, remaining)
            elif use_resume_skip:
                cap = min(limit, tail)
            else:
                cap = min(limit, remaining)
            if not quiet:
                print(
                    f"[INFO] Pass {pass_num}/{max_passes}: remaining~{remaining} "
                    f"skip_scope={skip_scope} skip_pass1={skip if pass_num == 1 else 0} "
                    f"tail~{tail if use_resume_skip else remaining} "
                    f"last_n={last_n if pass_num == 1 else 0} sort_dir={sort_dir if pass_num == 1 else 1} "
                    f"will_process<={cap} | full_first_pass={full_first_pass and pass_num == 1}"
                )
            elif pass_num == 1:
                _always_log(
                    f"[RUN] pass={pass_num}/{max_passes} skip_scope={skip_scope} "
                    f"resume_backlog~{remaining} skip={skip if pass_num == 1 else 0} "
                    f"last_n={last_n} sort_dir={sort_dir} cap<={cap} "
                    f"full_first_pass={full_first_pass and pass_num == 1}"
                )

            if use_catalog_slice:
                pipeline = _catalog_slice_pipeline(
                    skip=skip,
                    cap=cap,
                    sort_key=sort_key,
                    full_first_pass=full_first_pass and pass_num == 1,
                    sort_desc=sort_dir == -1,
                    include_failed=include_failed,
                )
                docs = await asyncio.to_thread(lambda: list(products.aggregate(pipeline, allowDiskUse=True)))
            else:
                cursor = products.find(query, _ENRICH_PROJECTION).sort(sort_key, sort_dir)
                if use_resume_skip:
                    cursor = cursor.skip(skip)
                cursor = cursor.limit(cap)
                docs = list(cursor)

            matched = len(docs)
            if matched == 0:
                _always_log(
                    f"[ABORT] pass={pass_num} reason=no_docs_after_query "
                    f"(skip_scope={skip_scope} skip={skip} cap={cap}; "
                    f"catalog slice may have no missing/failed rows in that window)"
                )
                break

            semaphore = asyncio.Semaphore(concurrency)
            pending_success: list[UpdateOne] = []
            pending_fail: list[UpdateOne] = []

            async def process_doc_write(doc: dict[str, Any], idx: int, total: int) -> tuple[str, UpdateOne | None]:
                product_url = str(doc.get("product_url") or "").strip()
                if not product_url:
                    return ("noop_url", None)

                async with semaphore:
                    description, status = await _fetch_description(scraper.client, scraper, product_url)
                    if not description:
                        if not quiet:
                            if status is None:
                                print(f"[ERROR] {idx}/{total} failed url={product_url}")
                            elif status == -1:
                                print(f"[WARN] {idx}/{total} skip invalid_url_scheme url={product_url}")
                            elif status != 200:
                                print(f"[WARN] {idx}/{total} skip status={status} url={product_url}")
                            elif status == 200:
                                print(f"[WARN] {idx}/{total} no description url={product_url}")
                            else:
                                print(f"[WARN] {idx}/{total} skip status={status} url={product_url}")
                        if status == -1:
                            err = "invalid_url_scheme"
                        elif status == 200:
                            err = "no_description"
                        elif status is not None:
                            err = f"http_{status}"
                        else:
                            err = "network_or_parse"
                        if dry_run:
                            return ("dry_fail", None)
                        return ("fail", _failure_update(doc["_id"], err))

                    set_doc = _build_success_set_doc(doc, description, overwrite)

                    if dry_run:
                        if not quiet:
                            print(
                                f"[DRY RUN] {idx}/{total} would update name={doc.get('name', 'Unknown')} "
                                f"fields={list(set_doc.keys())}"
                            )
                        return ("dry_ok", None)

                    return ("write", UpdateOne({"_id": doc["_id"]}, {"$set": set_doc}))

            pass_db_modified = 0
            pass_fail = 0
            pass_dry_ok = 0
            pass_dry_fail = 0
            pass_noop_url = 0

            async def flush_split() -> None:
                nonlocal pass_db_modified, pending_success, pending_fail
                if dry_run:
                    pending_success.clear()
                    pending_fail.clear()
                    return
                if pending_success:
                    r = await asyncio.to_thread(_bulk_write_retry, products, list(pending_success), quiet=quiet)
                    if r:
                        pass_db_modified += r.modified_count + getattr(r, "upserted_count", 0)
                    pending_success.clear()
                if pending_fail:
                    r2 = await asyncio.to_thread(_bulk_write_retry, products, list(pending_fail), quiet=quiet)
                    if r2:
                        pass_db_modified += r2.modified_count + getattr(r2, "upserted_count", 0)
                    pending_fail.clear()

            for start in range(0, matched, chunk_size):
                chunk = docs[start : start + chunk_size]
                tasks = [process_doc_write(d, start + i + 1, matched) for i, d in enumerate(chunk)]
                results = await asyncio.gather(*tasks)

                for outcome, op in results:
                    if outcome == "write" and op is not None:
                        pending_success.append(op)
                        if len(pending_success) >= mongo_batch:
                            await flush_split()
                    elif outcome == "fail" and op is not None:
                        pending_fail.append(op)
                        pass_fail += 1
                        if len(pending_fail) >= mongo_batch:
                            await flush_split()
                    elif outcome == "dry_ok":
                        pass_dry_ok += 1
                    elif outcome == "dry_fail":
                        pass_dry_fail += 1
                    elif outcome == "noop_url":
                        pass_noop_url += 1

                await flush_split()

                if quiet:
                    done = min(start + len(chunk), matched)
                    print(
                        f"[PROGRESS] pass={pass_num} {done}/{matched} | "
                        f"pass_db_modified~{pass_db_modified} | pass_fail={pass_fail}"
                    )

            await flush_split()

            total_db_modified += pass_db_modified
            total_scrape_fail += pass_fail
            total_dry += pass_dry_ok + pass_dry_fail
            total_noop_url += pass_noop_url

            if not quiet:
                print(
                    f"[INFO] Pass {pass_num} done: db_bulk_modified~{pass_db_modified} "
                    f"scrape_fail_markers={pass_fail} dry_ok={pass_dry_ok} dry_fail={pass_dry_fail}"
                )

    finally:
        await scraper.close()
        mongo_client.close()

    print(
        "[DONE] all_passes | db_bulk_modified_total=%s scrape_fail_events=%s | "
        "dry_events=%s noop_url=%s dry_run=%s"
        % (total_db_modified, total_scrape_fail, total_dry, total_noop_url, dry_run)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill descriptions/features from product URLs")
    parser.add_argument(
        "--limit",
        type=int,
        default=20_000,
        help="Max products per pass; also caps --last (default 20000 to match --last).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="When set with --all, overwrite existing description/feature fields where allowed",
    )
    parser.add_argument("--dry-run", action="store_true", help="Do not write DB updates")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Pass 1: every product with a URL. Later passes only retry missing/failed.",
    )
    parser.add_argument(
        "--max-passes",
        type=int,
        default=8,
        help="Retry cycles for rows still missing description or status=failed (default 8).",
    )
    parser.add_argument("--concurrency", type=int, default=56, help="Parallel HTTP requests")
    parser.add_argument("--mongo-batch", type=int, default=250, help="Mongo bulk_write batch size")
    parser.add_argument("--chunk-size", type=int, default=500, help="asyncio.gather chunk size")
    parser.add_argument("--quiet", action="store_true", help="Less console output")
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Pass 1 only: skip N after sort (--sort-key). With --skip-scope resume, N is within the missing/failed set only. "
        "Pass 2+ ignores skip. See --skip-scope catalog for skipping by full URL list.",
    )
    parser.add_argument(
        "--sort-key",
        type=str,
        default="_id",
        help="Field to sort before --skip (default _id). Use product_id only if indexed / present.",
    )
    parser.add_argument(
        "--skip-scope",
        choices=("resume", "catalog"),
        default="resume",
        help="resume: skip counts only rows missing/failed (default). "
        "catalog: pass 1 only -- skip/limit over ALL products with URL, then keep rows to enrich "
        "(use when --skip is larger than the resume backlog).",
    )
    parser.add_argument(
        "--last",
        type=int,
        default=20_000,
        metavar="N",
        help="Pass 1: process up to N rows with largest --sort-key (newest ObjectIds when _id). "
        "Caps at backlog size. Use 0 for oldest-first (ignore --last). Default 20000.",
    )
    parser.add_argument(
        "--reverse-order",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Sort scraping order by --sort-key descending (default true). "
        "Use --no-reverse-order for ascending order.",
    )
    parser.add_argument(
        "--include-failed",
        action="store_true",
        help="Include failed URLs in resume retries. Default is off (ignore failed URLs and scrape missing descriptions only).",
    )
    args = parser.parse_args()

    try:
        asyncio.run(
            run(
                limit=max(1, args.limit),
                overwrite=bool(args.overwrite),
                dry_run=args.dry_run,
                full_first_pass=bool(args.all),
                concurrency=max(1, min(args.concurrency, 150)),
                mongo_batch=max(50, min(args.mongo_batch, 1000)),
                chunk_size=max(100, min(args.chunk_size, 3000)),
                quiet=args.quiet,
                max_passes=max(1, min(args.max_passes, 50)),
                skip=max(0, args.skip),
                sort_key=(args.sort_key or "_id").strip() or "_id",
                skip_scope=args.skip_scope,
                last_n=max(0, args.last),
                reverse_order=bool(args.reverse_order),
                include_failed=bool(args.include_failed),
            )
        )
    except KeyboardInterrupt:
        print("[ABORT] interrupted_by_user (Ctrl+C).")


if __name__ == "__main__":
    main()
