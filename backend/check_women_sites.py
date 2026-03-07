"""
Check each brand URL from local_brands_links_women.csv:
- If /collections/ in URL: try products.json (Shopify). If 200 + has products -> shopify_json
- Else: fetch HTML, check product markers -> generic
Updates ScraperType per row so scraping works correctly.
"""
import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import httpx
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "local_brands_links_women.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
}


async def check_shopify_json(url: str, client: httpx.AsyncClient) -> tuple[bool, int]:
    """Return (success, product_count)."""
    try:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        path = (parsed.path or "").rstrip("/")
        if "/collections/" not in path:
            return False, 0
        # Build collection JSON URL (path already has /collections/xxx)
        json_url = f"{base}{path}/products.json"
        r = await client.get(
            json_url,
            params={"limit": 5},
            headers={**HEADERS, "Referer": base + "/"},
            timeout=15.0,
        )
        if r.status_code != 200:
            return False, 0
        raw = r.content.decode("utf-8", errors="replace")
        data = json.loads(raw)
        products = data.get("products") or []
        return True, len(products)
    except Exception as e:
        return False, 0


def has_product_markers(html: str) -> tuple[bool, str]:
    """Check if HTML has product grid/selectors or Rs./price."""
    if not html or len(html) < 2000:
        return False, "small_html"
    soup = BeautifulSoup(html, "html.parser")
    selectors = [
        ".ftc-product", ".ftc-product-grid > *", "li.product", ".type-product",
        ".card-wrapper", ".product-card", ".product-item", "[class*='product-card']",
        "[class*='card-wrapper']", ".woocommerce-loop-product", "li[class*='grid__item']",
        "[class*='product-item']", ".grid-product", ".product-grid-item",
        "a[href*='/products/']", ".product-card__link",
    ]
    for sel in selectors:
        try:
            els = soup.select(sel)
            if len(els) >= 2:
                return True, f"selector:{sel[:35]}"
        except Exception:
            pass
    if re.search(r"[Rr][Ss]\.?\s*[\d,]+|[Pp][Kk][Rr]\s*[\d,]+", html):
        if re.search(r"/products/|/product/|data-product|Shopify\.", html) or soup.select_one("img[src*='cdn'], img[src*='shop'], img[src*='upload'], img[src*='cloudfront']"):
            return True, "price_and_product_markers"
    return False, "no_markers"


async def check_html(url: str, client: httpx.AsyncClient) -> tuple[int, bool, str]:
    """Fetch HTML, return (content_length, has_product_markers, note)."""
    try:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}/"
        r = await client.get(url, headers={**HEADERS, "Referer": origin}, timeout=15.0)
        if r.status_code != 200:
            return 0, False, f"status_{r.status_code}"
        raw = r.content.decode("utf-8", errors="replace")
        has_mark, note = has_product_markers(raw)
        return len(raw), has_mark, note
    except Exception as e:
        return 0, False, f"error:{type(e).__name__}"


async def main():
    import os
    max_rows = int(os.environ.get("CHECK_WOMEN_MAX_ROWS", "0"))  # 0 = all

    df = pd.read_csv(CSV_PATH)
    if "Brand" not in df.columns or "Website" not in df.columns:
        print("CSV must have Brand, Website")
        return
    if "ScraperType" not in df.columns:
        df["ScraperType"] = ""

    if max_rows > 0:
        df = df.head(max_rows).copy()
        print(f"Checking first {max_rows} rows only.", flush=True)

    results = []  # list of (recommended_type, note) per row index
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for idx, row in df.iterrows():
            brand = str(row.get("Brand", "")).strip()
            website = str(row.get("Website", "")).strip()
            first_url = (website.split("|")[0] or "").strip() if website else ""

            if not first_url or not first_url.startswith("http"):
                results.append(("generic", "no_url"))
                print(f"[{idx+2}] {brand}: skip (no url)")
                continue

            recommended = "generic"
            note = ""

            if "/collections/" in first_url:
                ok, count = await check_shopify_json(first_url, client)
                if ok and count > 0:
                    recommended = "shopify_json"
                    note = f"products.json ok, {count} products"
                else:
                    length, has_mark, mark_note = await check_html(first_url, client)
                    if has_mark:
                        recommended = "generic"
                        note = f"json_fail html_ok len={length} {mark_note}"
                    else:
                        note = f"json_fail html_note={mark_note}"
            else:
                length, has_mark, mark_note = await check_html(first_url, client)
                if has_mark:
                    recommended = "generic"
                    note = f"len={length} {mark_note}"
                else:
                    note = f"no_markers len={length} {mark_note}"

            results.append((recommended, note))
            print(f"[{idx+2}] {brand}: {recommended} | {note}", flush=True)
            await asyncio.sleep(0.5)

    for idx in range(len(results)):
        rec, _ = results[idx]
        df.at[df.index[idx], "ScraperType"] = rec if rec == "shopify_json" else "generic"

    if max_rows > 0:
        print("\n(Dry run: not saving CSV)", flush=True)
    else:
        df.to_csv(CSV_PATH, index=False)
    print("\nUpdated local_brands_links_women.csv with ScraperType.")
    shopify_count = sum(1 for r, _ in results if r == "shopify_json")
    print(f"Summary: shopify_json={shopify_count}, generic={len(results) - shopify_count}")


if __name__ == "__main__":
    import os
    os.environ["PYTHONUNBUFFERED"] = "1"
    asyncio.run(main())
