"""
For each brand in local_brands_links_women.csv, find exact product listing URL
(same idea as men's CSV: /collections/..., /women, etc.) and update CSV.
"""
import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
import pandas as pd
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "local_brands_links_women.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
}

# Paths to try (product listing pages) - women's fashion
PATHS_TO_TRY = [
    "/collections/women",
    "/collections/all",
    "/collections/pret",
    "/collections/women-pret",
    "/collections/new-arrival",
    "/collections/lawn",
    "/collections/women-main",
    "/collections/collections",
    "/collections/shop",
    "/women",
    "/shop",
    "/collections",
    "/",  # base as fallback
]


async def check_shopify_products_json(base: str, path: str, client: httpx.AsyncClient) -> tuple[bool, int]:
    """Return (success, product_count) for Shopify products.json."""
    if "/collections/" not in path:
        return False, 0
    try:
        # path like /collections/women -> json_url /collections/women/products.json
        path_clean = path.rstrip("/")
        json_url = f"{base}{path_clean}/products.json?limit=3"
        r = await client.get(json_url, headers={**HEADERS, "Referer": base + "/"}, timeout=10)
        if r.status_code != 200:
            return False, 0
        raw = r.content.decode("utf-8", errors="replace")
        data = json.loads(raw)
        products = data.get("products") or []
        return True, len(products)
    except Exception:
        return False, 0


def has_products_in_html(html: str) -> bool:
    """True if HTML has product markers (selectors or Rs./price)."""
    if not html or len(html) < 1500:
        return False
    if re.search(r"[Rr][Ss]\.?\s*[\d,]+|[Pp][Kk][Rr]\s*[\d,]+", html):
        if "/products/" in html or "product" in html.lower() or "collection" in html.lower():
            return True
    soup = BeautifulSoup(html, "html.parser")
    for sel in [".product", ".card-wrapper", ".product-card", ".ftc-product", "[class*='product']", "li[class*='grid__item']"]:
        try:
            if len(soup.select(sel)) >= 2:
                return True
        except Exception:
            pass
    return False


async def find_best_url(base_url: str, client: httpx.AsyncClient) -> tuple[str, str]:
    """
    Try PATHS_TO_TRY and return (best_url, scraper_type).
    scraper_type: 'shopify_json' if Shopify collection with products.json, else '' (generic).
    """
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    origin = base + "/"
    for path in PATHS_TO_TRY:
        url = urljoin(base, path) if path != "/" else base + "/"
        try:
            # Prefer Shopify JSON if this is a collection path
            if "/collections/" in url:
                ok, count = await check_shopify_products_json(base, path, client)
                if ok and count > 0:
                    return url, "shopify_json"
            # Else check HTML
            r = await client.get(url, headers={**HEADERS, "Referer": origin}, timeout=12)
            if r.status_code != 200:
                continue
            raw = r.content.decode("utf-8", errors="replace")
            if has_products_in_html(raw):
                scraper = "shopify_json" if "/collections/" in url else ""
                return url, scraper
        except Exception:
            continue
    return base_url, ""


async def main():
    df = pd.read_csv(CSV_PATH)
    if "Brand" not in df.columns or "Website" not in df.columns:
        print("CSV must have Brand, Website")
        return
    rows = []
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for idx, row in df.iterrows():
            brand = str(row.get("Brand", "")).strip()
            current_url = str(row.get("Website", "")).strip()
            scraper_type = str(row.get("ScraperType", "")).strip()
            if not brand or not current_url or not current_url.startswith("http"):
                rows.append({"Brand": brand, "Website": current_url, "ScraperType": scraper_type})
                continue
            new_url, suggested_type = await find_best_url(current_url, client)
            st = suggested_type if suggested_type else scraper_type
            if st == "nan":
                st = ""
            rows.append({"Brand": brand, "Website": new_url, "ScraperType": st})
            print(f"{brand}: {new_url} ({st or 'generic'})")
            await asyncio.sleep(0.6)
    out = pd.DataFrame(rows)
    out.to_csv(CSV_PATH, index=False)
    print(f"\nUpdated {CSV_PATH} with {len(rows)} rows.")


if __name__ == "__main__":
    asyncio.run(main())
