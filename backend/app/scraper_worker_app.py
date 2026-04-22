"""
Minimal FastAPI app for the Railway scraper worker.

This service exists only to run Playwright-heavy scraping in a separate container
so the main API image can stay under Railway image size limits.

Security:
- Requires `X-Scraper-Token: <SCRAPER_SERVICE_TOKEN>` on every request.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from urllib.parse import urlparse


def _require_token(x_scraper_token: Optional[str] = Header(default=None)) -> None:
    expected = os.getenv("SCRAPER_SERVICE_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=500, detail="SCRAPER_SERVICE_TOKEN is not configured on scraper worker")
    if (x_scraper_token or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid scraper token")


app = FastAPI(title="DupeFinder Scraper Worker", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "scraper-worker"}


class RemoteScrapeRequest(BaseModel):
    brand_name: str
    urls: List[str] = Field(default_factory=list)
    category: str = ""
    gender: Optional[str] = None
    scraper_type: str = "generic"


@app.post("/scrape/brand")
async def scrape_brand(payload: RemoteScrapeRequest, _: None = Depends(_require_token)) -> Dict[str, Any]:
    # Import inside handler so module import stays light for tooling.
    from app.services.scraper_service import ProductScraper

    if not payload.urls:
        raise HTTPException(status_code=400, detail="No urls provided")

    scraper = ProductScraper()
    try:
        all_products: List[Dict[str, Any]] = []
        seen: set[str] = set()

        for brand_url in payload.urls:
            if not (brand_url or "").strip().startswith("http"):
                continue

            parsed = urlparse(brand_url or "")
            path = (parsed.path or "").strip("/")
            url_lower = (brand_url or "").lower()
            use_exact_listing = (
                len(path.split("/")) >= 1 and path != ""
                or ".html" in url_lower
                or "/collections/" in url_lower
                or "/product-category/" in url_lower
                or "/search" in url_lower
                or any(
                    x in url_lower
                    for x in ["/shirts", "/products", "/men", "/women", "/shop/", "/category/"]
                )
            )

            timeout_seconds = 300.0 if use_exact_listing else 60.0
            try:
                if use_exact_listing:
                    page_products = await asyncio.wait_for(
                        scraper.scrape_exact_listing_url(
                            brand_url,
                            payload.brand_name,
                            payload.category,
                            payload.gender,
                            None,
                            scraper_type=(payload.scraper_type or "generic").strip().lower() or "generic",
                        ),
                        timeout=timeout_seconds,
                    )
                else:
                    page_products = await asyncio.wait_for(
                        scraper.scrape_brand_website(
                            brand_url,
                            payload.brand_name,
                            payload.category,
                            payload.gender,
                        ),
                        timeout=timeout_seconds,
                    )
            except asyncio.TimeoutError:
                page_products = []

            for p in page_products:
                purl = (p.get("product_url") or "").strip()
                if purl and purl not in seen:
                    seen.add(purl)
                    all_products.append(p)

        return {"ok": True, "count": len(all_products), "products": all_products}
    finally:
        try:
            await scraper.close()
        except Exception:
            pass


class RemoteScrapeSingleUrlRequest(BaseModel):
    brand_name: str
    brand_url: str
    category: str = ""
    gender: Optional[str] = None
    scraper_type: str = "generic"


@app.post("/scrape/url")
async def scrape_single_url(payload: RemoteScrapeSingleUrlRequest, _: None = Depends(_require_token)) -> Dict[str, Any]:
    """
    Scrape a single brand URL with the same listing-vs-home heuristic used by admin scraping.
    """
    from app.services.scraper_service import ProductScraper

    brand_url = (payload.brand_url or "").strip()
    if not brand_url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid brand_url")

    parsed = urlparse(brand_url)
    path = (parsed.path or "").strip("/")
    url_lower = brand_url.lower()
    use_exact_listing = (
        len(path.split("/")) >= 1 and path != ""
        or ".html" in url_lower
        or "/collections/" in url_lower
        or "/product-category/" in url_lower
        or "/search" in url_lower
        or any(x in url_lower for x in ["/shirts", "/products", "/men", "/women", "/shop/", "/category/"])
    )

    scraper = ProductScraper()
    try:
        timeout_seconds = 300.0 if use_exact_listing else 60.0
        try:
            if use_exact_listing:
                page_products = await asyncio.wait_for(
                    scraper.scrape_exact_listing_url(
                        brand_url,
                        payload.brand_name,
                        payload.category,
                        payload.gender,
                        None,
                        scraper_type=(payload.scraper_type or "generic").strip().lower() or "generic",
                    ),
                    timeout=timeout_seconds,
                )
            else:
                page_products = await asyncio.wait_for(
                    scraper.scrape_brand_website(
                        brand_url,
                        payload.brand_name,
                        payload.category,
                        payload.gender,
                    ),
                    timeout=timeout_seconds,
                )
        except asyncio.TimeoutError:
            page_products = []

        return {
            "ok": True,
            "use_exact_listing": use_exact_listing,
            "count": len(page_products),
            "products": page_products,
        }
    finally:
        try:
            await scraper.close()
        except Exception:
            pass
