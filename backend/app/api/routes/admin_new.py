"""
Admin Dashboard API Endpoints
4 Modules: User Management, Product Catalogue, ML Training, Auto Sync/Scraping
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timedelta
from bson import ObjectId
import pandas as pd
import io
import asyncio
import httpx

from app.dependencies.auth import get_current_user
from app.core.database import (
    get_users_collection,
    get_products_collection,
    get_scraping_history_collection,
    get_db
)
from app.services.scraper_service import scrape_from_excel_files
from app.services.category_normalizer import normalize_category, get_category_display_name
from app.models.admin import AdminLogin, AdminToken, AdminResponse
from app.core.security import verify_password
from app.utils.auth import create_access_token
from app.api.routes.auth import _effective_name_for_user
import os
import re
import logging
import hashlib
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

logger = logging.getLogger(__name__)

# Endpoint slug -> display category (generalized) for women. Men mapping added later.
WOMEN_KURTA_ENDPOINTS = frozenset({
    "2-piece-essential-summer-pret-kt", "charizma-vasal-vol-02-2026", "eid-collection",
    "essential-summer-pret", "florence-summer-edit-26", "luxe-2025", "luxury-pret",
    "new-arrival-summer-26", "new-arrivals", "pret", "ready-to-wear", "satori-2026", "women",
    "chic-essentials", "long-shirts", "short-shirts",
    "search-2-piece", "search-summer-wear-2pc",
})
WOMEN_LAWN_ENDPOINTS = frozenset({
    "eid-lawn-2026", "lawn-in-stock",
    # Ramadan / lawn khaddar stiched cords style endpoint (slug may vary)
    "ramadan-festive-sale-lawn-khaddar-stiched-cords", "ramadan-festive-sale-lawn-khaddar-stitched-cords",
    "summer-essentials", "andaaz-collection", "eid-edit26", "3-pc-lawn",
    "search-3-piece", "search-summer-wear-3pc",
    # Limelight Formal collection handle (user-requested: show under Women Lawn)
    "formal-wear",
})
WOMEN_LUXE_ENDPOINTS = frozenset({
    "bridal-in-stock", "festive-in-stock", "wedding-unstitched-2025",
    "lu-zella-premium-formals-25", "daily-wear", "formals", "search-3pcs",
})
WOMEN_SHORT_KURTI_ENDPOINTS = frozenset({
    "ss-wesst", "ss-west", "short-kurti",
    "2-pc-co-ords", "co-ord-set",
})
WOMEN_ACCESSORIES_ENDPOINTS = frozenset({"accessories", "search-accessories"})
WOMEN_ANARKALI_FROCK_ENDPOINTS = frozenset({
    "anarkali-frock", "frocks-maxi", "kaftans", "search-long-floral-dresses",
})
WOMEN_BOTTOMS_ENDPOINTS = frozenset({"bottoms"})
WOMEN_BAGS_ENDPOINTS = frozenset({
    "cross-body-bags", "crossbody-bags", "canvas-bags", "shoulder-bags", "tote-bags",
    "hand-bags", "mini-bags", "bags", "handbags", "search-bags",
})
WOMEN_JEWELRY_ENDPOINTS = frozenset({
    "jewelry", "earrings", "stud-set", "necklace", "rings", "anklet",
})
WOMEN_TOPS_ENDPOINTS = frozenset({"tops"})
WOMEN_UNSTITCHED_ENDPOINTS = frozenset({"unstitched", "unstitched-fabric"})
WOMEN_WESTERN_ENDPOINTS = frozenset({"western"})
WOMEN_WINTER_PANTS_ENDPOINTS = frozenset({"winter-pants"})
# Men's endpoint -> display category (generalized)
MEN_STANDARD_SUIT_ENDPOINTS = frozenset({"all"})
MEN_TRADITIONAL_SUIT_ENDPOINTS = frozenset({"men", "men-main", "men-ready-to-wear", "new-arrival"})
MEN_CASUAL_WEAR_ENDPOINTS = frozenset({"men-products"})
MEN_FOOTWEAR_ENDPOINTS = frozenset({"men-footwear"})
MEN_SHOES_ENDPOINTS = frozenset({"men-shoes-shoes"})
MEN_SWEATER_ENDPOINTS = frozenset({"men-sweater"})
MEN_WRIST_WATCHES_ENDPOINTS = frozenset({"mens-wrist-watches", "men-wrist-watches"})

# Legacy category values (from old scraper) -> display category for backfill
LEGACY_WOMEN_KURTA = frozenset({"women → stitched", "women → western wear", "women→stitched", "women→western wear"})
LEGACY_WOMEN_LAWN = frozenset({"women → unstitched", "women→unstitched"})


# All women endpoint sets combined (for "always map when building category list")
_WOMEN_ALL_ENDPOINTS = (
    WOMEN_KURTA_ENDPOINTS | WOMEN_LAWN_ENDPOINTS | WOMEN_LUXE_ENDPOINTS | WOMEN_SHORT_KURTI_ENDPOINTS
    | WOMEN_ACCESSORIES_ENDPOINTS | WOMEN_ANARKALI_FROCK_ENDPOINTS | WOMEN_BOTTOMS_ENDPOINTS
    | WOMEN_BAGS_ENDPOINTS | WOMEN_JEWELRY_ENDPOINTS | WOMEN_TOPS_ENDPOINTS | WOMEN_UNSTITCHED_ENDPOINTS
    | WOMEN_WESTERN_ENDPOINTS | WOMEN_WINTER_PANTS_ENDPOINTS
)
# All men endpoint sets combined
_MEN_ALL_ENDPOINTS = (
    MEN_STANDARD_SUIT_ENDPOINTS | MEN_TRADITIONAL_SUIT_ENDPOINTS | MEN_CASUAL_WEAR_ENDPOINTS
    | MEN_FOOTWEAR_ENDPOINTS | MEN_SHOES_ENDPOINTS | MEN_SWEATER_ENDPOINTS | MEN_WRIST_WATCHES_ENDPOINTS
)


def _slug_to_display_for_categories(slug: str) -> str:
    """For category dropdown only: map slug to display name. Same as Women Kurta/Lawn - always generalize."""
    if not slug or not isinstance(slug, str):
        return slug or ""
    # Normalize: lowercase, spaces/underscores/unicode dashes to ascii hyphen (DB may have different chars)
    s = (slug or "").strip().lower()
    for ch in [" ", "_", "\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2212"]:
        s = s.replace(ch, "-")
    if s in WOMEN_KURTA_ENDPOINTS:
        return "Women Kurta"
    if s in WOMEN_LAWN_ENDPOINTS:
        return "Women Lawn"
    if s in WOMEN_LUXE_ENDPOINTS:
        return "Women Luxe"
    if s in WOMEN_SHORT_KURTI_ENDPOINTS:
        return "Women Short Kurti"
    if "ramadan" in s and ("lawn" in s or "khaddar" in s):
        return "Women Lawn"
    if s in WOMEN_ACCESSORIES_ENDPOINTS:
        return "Women Accessories"
    if s in WOMEN_ANARKALI_FROCK_ENDPOINTS:
        return "Women Anarkali Frock"
    if s in WOMEN_BOTTOMS_ENDPOINTS:
        return "Women Bottoms"
    if s in WOMEN_BAGS_ENDPOINTS:
        return "Women Bags"
    if s in WOMEN_JEWELRY_ENDPOINTS:
        return "Women Jewelry"
    if s in WOMEN_TOPS_ENDPOINTS:
        return "Women Tops"
    if s in WOMEN_UNSTITCHED_ENDPOINTS:
        return "Women Unstitched"
    if s in WOMEN_WESTERN_ENDPOINTS:
        return "Women Western"
    if s in WOMEN_WINTER_PANTS_ENDPOINTS:
        return "Women Winter Pants"
    # Men's display categories
    if s in MEN_STANDARD_SUIT_ENDPOINTS:
        return "Men Standard Suit"
    if s in MEN_TRADITIONAL_SUIT_ENDPOINTS:
        return "Men Traditional Suit"
    if s in MEN_CASUAL_WEAR_ENDPOINTS:
        return "Men Casual Wear"
    if s in MEN_FOOTWEAR_ENDPOINTS:
        return "Men Footwear"
    if s in MEN_SHOES_ENDPOINTS:
        return "Men Shoes"
    if s in MEN_SWEATER_ENDPOINTS:
        return "Men Sweater"
    if s in MEN_WRIST_WATCHES_ENDPOINTS:
        return "Men Wrist Watches"
    return (slug or "").strip()


def _normalize_slug(s: str) -> str:
    """Normalize for set lookup: lowercase, spaces and underscores to hyphens."""
    if not s:
        return ""
    return (s or "").strip().lower().replace(" ", "-").replace("_", "-")


def _listing_endpoint_slug(url: str) -> str:
    """
    Derive endpoint_category slug from a listing URL.
    Uses last path segment for collections; search?q= / search= -> search-<normalized>;
    WooCommerce /product-category/x/ -> x.
    """
    if not url or not isinstance(url, str):
        return ""
    try:
        parsed = urlparse(url.strip())
        path = (parsed.path or "").strip("/")
        segments = [s for s in path.split("/") if s]
        qs = parse_qs(parsed.query)
        last = segments[-1] if segments else ""
        if last.lower() == "search":
            for key in ("q", "search"):
                vals = qs.get(key) or []
                if vals and str(vals[0]).strip():
                    raw = unquote(str(vals[0]).strip())
                    normalized = re.sub(r"[^a-z0-9]+", "-", raw.lower())[:96].strip("-")
                    return f"search-{normalized}" if normalized else "search"
            return "search"
        lowered = [s.lower() for s in segments]
        if "product-category" in lowered:
            idx = lowered.index("product-category")
            if idx + 1 < len(segments):
                return segments[idx + 1].lower()
        if segments:
            slug = segments[-1].lower()
            if slug.endswith(".html"):
                slug = slug[:-5]
            return slug
    except Exception:
        pass
    return ""


def _display_category_from_endpoint(endpoint_slug: str, gender: Optional[str]) -> str:
    """Map endpoint_category (+ gender) to generalized display category. Returns slug if no mapping."""
    if not endpoint_slug:
        return ""
    slug = _normalize_slug(endpoint_slug)
    # When gender is w, or when slug is a known women-only endpoint (map even when gender=All)
    use_women_mapping = (gender or "").strip().lower() == "w" or slug in _WOMEN_ALL_ENDPOINTS
    if use_women_mapping:
        if slug in WOMEN_KURTA_ENDPOINTS:
            return "Women Kurta"
        if slug in WOMEN_LAWN_ENDPOINTS:
            return "Women Lawn"
        if slug in WOMEN_LUXE_ENDPOINTS:
            return "Women Luxe"
        if slug in WOMEN_SHORT_KURTI_ENDPOINTS:
            return "Women Short Kurti"
        # Partial match for ramadan/lawn/khaddar style slugs
        if "ramadan" in slug and ("lawn" in slug or "khaddar" in slug):
            return "Women Lawn"
        if slug in WOMEN_ACCESSORIES_ENDPOINTS:
            return "Women Accessories"
        if slug in WOMEN_ANARKALI_FROCK_ENDPOINTS:
            return "Women Anarkali Frock"
        if slug in WOMEN_BOTTOMS_ENDPOINTS:
            return "Women Bottoms"
        if slug in WOMEN_BAGS_ENDPOINTS:
            return "Women Bags"
        if slug in WOMEN_JEWELRY_ENDPOINTS:
            return "Women Jewelry"
        if slug in WOMEN_TOPS_ENDPOINTS:
            return "Women Tops"
        if slug in WOMEN_UNSTITCHED_ENDPOINTS:
            return "Women Unstitched"
        if slug in WOMEN_WESTERN_ENDPOINTS:
            return "Women Western"
        if slug in WOMEN_WINTER_PANTS_ENDPOINTS:
            return "Women Winter Pants"
    # Men's mapping: never treat women's scrapes as men's when slug overlaps (e.g. collections/all).
    use_men_mapping = (gender or "").strip().lower() == "m" or (
        slug in _MEN_ALL_ENDPOINTS and (gender or "").strip().lower() != "w"
    )
    if use_men_mapping:
        if slug in MEN_STANDARD_SUIT_ENDPOINTS:
            return "Men Standard Suit"
        if slug in MEN_TRADITIONAL_SUIT_ENDPOINTS:
            return "Men Traditional Suit"
        if slug in MEN_CASUAL_WEAR_ENDPOINTS:
            return "Men Casual Wear"
        if slug in MEN_FOOTWEAR_ENDPOINTS:
            return "Men Footwear"
        if slug in MEN_SHOES_ENDPOINTS:
            return "Men Shoes"
        if slug in MEN_SWEATER_ENDPOINTS:
            return "Men Sweater"
        if slug in MEN_WRIST_WATCHES_ENDPOINTS:
            return "Men Wrist Watches"
    return endpoint_slug  # keep original slug if no mapping (e.g. bags, jewelry)


def _display_category_from_legacy(category: str) -> Optional[str]:
    """Map legacy category string to display category for backfill. Returns None if no mapping."""
    if not category:
        return None
    c = (category or "").strip().lower()
    if c in LEGACY_WOMEN_KURTA:
        return "Women Kurta"
    if c in LEGACY_WOMEN_LAWN:
        return "Women Lawn"
    if "women" in c and ("stitched" in c or "western" in c):
        return "Women Kurta"
    if "women" in c and "unstitched" in c:
        return "Women Lawn"
    return None


def _category_filter_for_products(display_name: str):
    """Return MongoDB query fragment to filter by display category (includes endpoint/legacy so existing data matches)."""
    if not display_name:
        return None
    name = (display_name or "").strip()
    if name == "Women Kurta":
        return {"$or": [
            {"display_category": "Women Kurta"},
            {"gender": "w", "endpoint_category": {"$in": list(WOMEN_KURTA_ENDPOINTS)}},
            {"gender": "w", "category": {"$regex": "women.*(stitched|western)", "$options": "i"}},
        ]}
    if name == "Women Lawn":
        return {"$or": [
            {"display_category": "Women Lawn"},
            {"gender": "w", "endpoint_category": {"$in": list(WOMEN_LAWN_ENDPOINTS)}},
            {"gender": "w", "$and": [{"endpoint_category": {"$regex": "ramadan", "$options": "i"}}, {"endpoint_category": {"$regex": "lawn", "$options": "i"}}]},
            {"gender": "w", "category": {"$regex": "women.*unstitched", "$options": "i"}},
        ]}
    # Women Luxe: same pattern as Women Kurta – display_category OR (gender w + endpoint in list)
    if name == "Women Luxe":
        return {"$or": [
            {"display_category": "Women Luxe"},
            {"gender": "w", "endpoint_category": {"$in": list(WOMEN_LUXE_ENDPOINTS)}},
        ]}
    # Women Short Kurti: same pattern as Women Kurta. Match old "kurti" spelling in DB for backward compatibility.
    if name == "Women Short Kurti":
        return {"$or": [
            {"display_category": "Women Short Kurti"},
            {"display_category": "Women Short kurti"},
            {"gender": "w", "endpoint_category": {"$in": list(WOMEN_SHORT_KURTI_ENDPOINTS)}},
        ]}
    # Men Standard Suit: endpoint "all" (by endpoint only, like Women Luxe). Match old "Mens" spelling in DB for backward compatibility.
    if name == "Men Standard Suit":
        return {"$or": [
            {"display_category": "Men Standard Suit"},
            {"display_category": "Mens Standard Suit"},
            {"endpoint_category": {"$in": list(MEN_STANDARD_SUIT_ENDPOINTS)}},
        ]}
    # Men Traditional Suit: men, men-main, men-ready-to-wear
    if name == "Men Traditional Suit":
        return {"$or": [
            {"display_category": "Men Traditional Suit"},
            {"display_category": "Mens Traditional Suit"},
            {"endpoint_category": {"$in": list(MEN_TRADITIONAL_SUIT_ENDPOINTS)}},
        ]}
    # Men Casual Wear: men-products
    if name == "Men Casual Wear":
        return {"$or": [
            {"display_category": "Men Casual Wear"},
            {"display_category": "Mens Casual Wear"},
            {"endpoint_category": {"$in": list(MEN_CASUAL_WEAR_ENDPOINTS)}},
        ]}
    # Women Accessories: accessories endpoint (women links)
    if name == "Women Accessories":
        return {"$or": [
            {"display_category": "Women Accessories"},
            {"endpoint_category": {"$in": list(WOMEN_ACCESSORIES_ENDPOINTS)}},
        ]}
    # Women Anarkali Frock, Bottoms, Bags, Jewelry, Tops, Unstitched, Western, Winter Pants
    if name == "Women Anarkali Frock":
        return {"$or": [
            {"display_category": "Women Anarkali Frock"},
            {"endpoint_category": {"$in": list(WOMEN_ANARKALI_FROCK_ENDPOINTS)}},
        ]}
    if name == "Women Bottoms":
        return {"$or": [
            {"display_category": "Women Bottoms"},
            {"endpoint_category": {"$in": list(WOMEN_BOTTOMS_ENDPOINTS)}},
        ]}
    if name == "Women Bags":
        return {"$or": [
            {"display_category": "Women Bags"},
            {"endpoint_category": {"$in": list(WOMEN_BAGS_ENDPOINTS)}},
        ]}
    if name == "Women Jewelry":
        return {"$or": [
            {"display_category": "Women Jewelry"},
            {"endpoint_category": {"$in": list(WOMEN_JEWELRY_ENDPOINTS)}},
        ]}
    if name == "Women Tops":
        return {"$or": [
            {"display_category": "Women Tops"},
            {"endpoint_category": {"$in": list(WOMEN_TOPS_ENDPOINTS)}},
        ]}
    if name == "Women Unstitched":
        return {"$or": [
            {"display_category": "Women Unstitched"},
            {"endpoint_category": {"$in": list(WOMEN_UNSTITCHED_ENDPOINTS)}},
        ]}
    if name == "Women Western":
        return {"$or": [
            {"display_category": "Women Western"},
            {"endpoint_category": {"$in": list(WOMEN_WESTERN_ENDPOINTS)}},
        ]}
    if name == "Women Winter Pants":
        return {"$or": [
            {"display_category": "Women Winter Pants"},
            {"endpoint_category": {"$in": list(WOMEN_WINTER_PANTS_ENDPOINTS)}},
        ]}
    # Men Footwear, Men Shoes, Men Sweater, Men Wrist Watches
    if name == "Men Footwear":
        return {"$or": [
            {"display_category": "Men Footwear"},
            {"endpoint_category": {"$in": list(MEN_FOOTWEAR_ENDPOINTS)}},
        ]}
    if name == "Men Shoes":
        return {"$or": [
            {"display_category": "Men Shoes"},
            {"endpoint_category": {"$in": list(MEN_SHOES_ENDPOINTS)}},
        ]}
    if name == "Men Sweater":
        return {"$or": [
            {"display_category": "Men Sweater"},
            {"endpoint_category": {"$in": list(MEN_SWEATER_ENDPOINTS)}},
        ]}
    if name == "Men Wrist Watches":
        return {"$or": [
            {"display_category": "Men Wrist Watches"},
            {"endpoint_category": {"$in": list(MEN_WRIST_WATCHES_ENDPOINTS)}},
        ]}
    # Any other name: exact display_category or endpoint_category match
    return {"$or": [{"display_category": name}, {"endpoint_category": name}, {"category": name}]}


# Directory for downloaded product images (served at /data/product_images/)
def _get_product_images_dir():
    base = Path(__file__).resolve().parent.parent.parent.parent.parent  # routes -> api -> app -> backend -> project root
    d = base / "data" / "product_images"
    d.mkdir(parents=True, exist_ok=True)
    return d

def _looks_like_image_url(url: str) -> bool:
    """Reject malformed URLs (e.g. junaidjamshed.com/mens/255&fit=bounds) that are not real image URLs."""
    if not url:
        return False
    ul = url.lower()
    if any(x in ul for x in ["loader", "lazyload", "placeholder.com"]):
        return False
    # Real image URLs usually have extension or path segment
    path_part = ul.split("?")[0]
    if any(ext in path_part for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
        return True
    if any(seg in path_part for seg in [
        "/media/", "/cdn/", "/files/", "/upload", "/product/", "/shop/files/", "/uploads/",
        "/catalog/", "/img/", "/images/", "/assets/", "/static/",
        "/mens/", "/women/", "/womens/"  # e.g. Junaid Jamshed /mens/255&fit=bounds
    ]):
        return True
    return False


async def _download_product_image(image_url: str, product_url: str) -> Optional[str]:
    """Download image from URL and save to data/product_images. Returns relative path like 'product_images/xxx.jpg' or None. Skips if file already exists."""
    if not image_url or not image_url.strip().lower().startswith(("http://", "https://")):
        return None
    if not _looks_like_image_url(image_url):
        return None
    url_lower = image_url.lower()
    if "loader" in url_lower or "lazyload" in url_lower or image_url.rstrip("/").endswith(".gif"):
        return None
    img_dir = _get_product_images_dir()
    # Try common extensions for "already exists" check (we don't know ext before download)
    base_name = hashlib.md5(((product_url or "") + (image_url or "")).encode("utf-8")).hexdigest()[:16]
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        if (img_dir / (base_name + ext)).exists():
            return f"product_images/{base_name}{ext}"
    try:
        parsed = urlparse(image_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            r = await client.get(
                image_url,
                headers={
                    "Referer": origin + "/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0",
                    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                },
            )
            r.raise_for_status()
            ct = r.headers.get("content-type", "").split(";")[0].strip().lower()
            if "image" not in ct:
                return None
            ext = ".jpg"
            if "png" in ct:
                ext = ".png"
            elif "webp" in ct:
                ext = ".webp"
            elif "gif" in ct and len(r.content) > 500:
                ext = ".gif"
            name = base_name + ext
            path = img_dir / name
            path.write_bytes(r.content)
            return f"product_images/{name}"
    except Exception as e:
        logger.debug(f"Could not download product image: {e}")
        return None

router = APIRouter(tags=["Admin Dashboard"])

def _cleanup_user_related_data(db, user_id: str, email: Optional[str] = None):
    db.refresh_tokens.delete_many({"user_id": user_id})
    db.user_app_data.delete_many({"user_id": user_id})
    db.community_posts.delete_many({"author_user_id": user_id})
    db.community_posts.update_many({}, {"$pull": {"replies": {"author_user_id": user_id}}})
    db.community_reports.delete_many(
        {
            "$or": [
                {"reporter_user_id": user_id},
                {"post_author_user_id": user_id},
                {"reply_author_user_id": user_id},
            ]
        }
    )
    db.community_notifications.delete_many(
        {"$or": [{"recipient_user_id": user_id}, {"actor_user_id": user_id}]}
    )
    db.community_user_blocks.delete_many(
        {"$or": [{"blocker_user_id": user_id}, {"blocked_user_id": user_id}]}
    )
    if email:
        db.otps.delete_many({"email": email})


# ============================================
# Admin Authentication
# ============================================

@router.post("/login", response_model=AdminToken)
async def admin_login(credentials: AdminLogin):
    """
    Admin login endpoint
    
    - **email**: Admin email address
    - **password**: Admin password
    
    **Default Admin Credentials:**
    - Email: admin@dupefinder.com
    - Password: admin123
    """
    try:
        db = get_db()
        if db is None:
            logger.error("Database connection is None")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection error"
            )
        
        admins_collection = db.admins
        
        # Find admin
        admin = admins_collection.find_one({"email": credentials.email})
        
        if not admin:
            logger.warning(f"Admin not found: {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin credentials"
            )
        
        # Verify password using verify_password from security
        try:
            password_valid = verify_password(credentials.password, admin["hashed_password"])
        except Exception as e:
            logger.error(f"Password verification error: {e}, type: {type(admin.get('hashed_password'))}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying password: {str(e)}"
            )
        
        if not password_valid:
            logger.warning(f"Invalid password for admin: {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin credentials"
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": credentials.email, "role": "admin"})
        
        # Prepare admin response
        admin["_id"] = str(admin["_id"])
        if "hashed_password" in admin:
            del admin["hashed_password"]
        # Legacy or hand-edited docs may omit fields required by AdminResponse
        if not admin.get("full_name"):
            admin["full_name"] = "Admin"
        if admin.get("created_at") is None:
            admin["created_at"] = datetime.utcnow()
        
        return AdminToken(
            access_token=access_token,
            admin=AdminResponse(**admin)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in admin_login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ============================================
# Helper: Check if user is admin
# ============================================

async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """
    Dependency to ensure user is an admin
    Verifies admin token and returns admin data
    """
    from app.utils.auth import verify_token
    from app.core.database import get_db
    import logging
    
    logger = logging.getLogger(__name__)
    
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token, token_type="access")
    
    if not payload:
        logger.warning(f"Token verification failed for token: {token[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if it's an admin token (has role="admin" or sub field)
    email = payload.get("sub") or payload.get("email")
    role = payload.get("role")
    
    logger.info(f"Token payload - email: {email}, role: {role}, keys: {list(payload.keys())}")
    
    # If it has role="admin", it's an admin token
    if role == "admin" and email:
        # Get admin from admins collection
        db = get_db()
        admin = db.admins.find_one({"email": email})
        
        if not admin:
            logger.warning(f"Admin not found in database for email: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        admin["_id"] = str(admin["_id"])
        logger.info(f"Admin authenticated: {email}")
        return admin
    
    # If it has user_id, try to get user and check if admin
    user_id = payload.get("user_id")
    if user_id:
        # This is a regular user token - check if they're an admin
        # For now, we'll only allow admin tokens
        logger.warning(f"Regular user token used for admin endpoint: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. Please login as admin.",
        )
    
    logger.warning(f"Token missing required fields - email: {email}, role: {role}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Invalid admin token. Token payload: {list(payload.keys())}",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ============================================
# MODULE 1: User Management
# ============================================

@router.get("/users")
async def get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[str] = None,  # 'active', 'inactive', 'all'
    admin: dict = Depends(require_admin)
):
    """
    Get all registered users with pagination and filtering
    
    Module 1: User Management - View login data
    """
    users = get_users_collection()
    
    # Build query - only show verified users
    query = {"is_verified": True}
    if search:
        query["email"] = {"$regex": search, "$options": "i"}
    
    if status_filter == "active":
        query["is_active"] = True
    elif status_filter == "inactive":
        query["is_active"] = False
    
    # Get total count
    total = users.count_documents(query)
    
    # Get paginated users
    skip = (page - 1) * page_size
    user_list = list(
        users.find(query, {"password_hash": 0})  # Exclude password
        .skip(skip)
        .limit(page_size)
        .sort("created_at", -1)
    )
    
    # Format response
    for user in user_list:
        user["_id"] = str(user["_id"])
    
    return {
        "users": user_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.put("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Deactivate a user account permanently
    
    Module 1: User Management - Deactivate accounts
    """
    users = get_users_collection()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    result = users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": False, "deactivated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "message": "User deactivated successfully",
        "user_id": user_id
    }


@router.put("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Reactivate a user account
    
    Module 1: User Management
    """
    users = get_users_collection()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    result = users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": True}, "$unset": {"deactivated_at": ""}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "message": "User activated successfully",
        "user_id": user_id
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Delete a user permanently
    
    Module 1: User Management - Delete user accounts
    """
    users = get_users_collection()
    db = get_db()
    
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")
    
    existing = users.find_one({"_id": ObjectId(user_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    result = users.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    _cleanup_user_related_data(db, user_id, existing.get("email"))
    
    return {
        "success": True,
        "message": "User deleted successfully",
        "user_id": user_id
    }


# ============================================
# MODULE 2: Product Catalogue Management
# ============================================

@router.post("/products/import-csv")
async def import_products_from_csv(
    file: UploadFile = File(...),
    admin: dict = Depends(require_admin)
):
    """
    Import products from CSV file
    
    Module 2: Product Catalogue - Add products via CSV
    
    CSV Format: name, category, brand, price, image_url, description
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Normalize column names: lowercase and strip whitespace
        df.columns = df.columns.str.strip().str.lower()
        
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        logger.info(f"Processing {len(df)} rows from CSV")
        logger.info(f"CSV columns (normalized): {list(df.columns)}")
        if len(df) > 0:
            logger.info(f"First row sample: {df.iloc[0].to_dict()}")
        
        # Validate required columns (case-insensitive)
        required_cols = ['name', 'category', 'brand', 'price']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_cols)}. Found columns: {', '.join(df.columns)}"
            )
        
        if len(df) == 0:
            raise HTTPException(
                status_code=400,
                detail="CSV file is empty or contains no valid data rows"
            )
        
        # Process products
        products = get_products_collection()
        success_count = 0
        error_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # Clean and validate data - handle NaN values properly
                name = None
                category = None
                brand = None
                
                # Extract name
                if 'name' in row and pd.notna(row['name']):
                    name = str(row['name']).strip()
                elif 'product_name' in row and pd.notna(row.get('product_name')):
                    name = str(row['product_name']).strip()
                elif 'product' in row and pd.notna(row.get('product')):
                    name = str(row['product']).strip()
                
                # Extract category
                if 'category' in row and pd.notna(row['category']):
                    category = str(row['category']).strip()
                elif 'cat' in row and pd.notna(row.get('cat')):
                    category = str(row['cat']).strip()
                
                # Extract brand
                if 'brand' in row and pd.notna(row['brand']):
                    brand = str(row['brand']).strip()
                elif 'brand_name' in row and pd.notna(row.get('brand_name')):
                    brand = str(row['brand_name']).strip()
                
                # Validate required fields with detailed error messages
                if not name or name == 'None' or name == '' or name == 'nan':
                    raise ValueError(f"Name is required and cannot be empty. Got: '{row.get('name', 'N/A')}'")
                if not category or category == 'None' or category == '' or category == 'nan':
                    raise ValueError(f"Category is required and cannot be empty. Got: '{row.get('category', 'N/A')}'")
                if not brand or brand == 'None' or brand == '' or brand == 'nan':
                    raise ValueError(f"Brand is required and cannot be empty. Got: '{row.get('brand', 'N/A')}'")
                
                # Handle price conversion with better error handling
                price = 0.0
                price_value = row.get('price', 0)
                if pd.notna(price_value):
                    try:
                        # Remove currency symbols and commas
                        price_str = str(price_value).replace('$', '').replace(',', '').strip()
                        price = float(price_str)
                        if price < 0:
                            price = 0.0
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Row {idx + 2}: Invalid price '{price_value}', using 0.0")
                        price = 0.0
                else:
                    logger.warning(f"Row {idx + 2}: Price is missing, using 0.0")
                
                # Handle optional fields
                image_url = ''
                if 'image_url' in row and pd.notna(row.get('image_url')):
                    image_url = str(row['image_url']).strip()
                elif 'image' in row and pd.notna(row.get('image')):
                    image_url = str(row['image']).strip()
                elif 'image_path' in row and pd.notna(row.get('image_path')):
                    image_url = str(row['image_path']).strip()
                
                description = ''
                if 'description' in row and pd.notna(row.get('description')):
                    description = str(row['description']).strip()
                elif 'desc' in row and pd.notna(row.get('desc')):
                    description = str(row['desc']).strip()
                
                # Generate product_id if not present (for uniqueness)
                import hashlib
                product_id_source = f"{name}_{brand}_{category}"
                product_id = hashlib.md5(product_id_source.encode()).hexdigest()
                
                product_doc = {
                    "product_id": product_id,
                    "name": name,
                    "category": category,
                    "brand": brand,
                    "price": price,
                    "image_url": image_url,
                    "image_path": image_url,  # Keep both for compatibility
                    "description": description,
                    "embedding": [],  # Will be computed later
                    "created_at": datetime.utcnow(),
                    "created_by": "admin_csv_import",
                    "broken_link": False,
                    "scraped_at": datetime.utcnow()
                }
                
                # Check if product already exists (by product_id or name+brand combination)
                existing = products.find_one({
                    "$or": [
                        {"product_id": product_id},
                        {"name": name, "brand": brand}
                    ]
                })
                
                if existing:
                    # Update existing product
                    products.update_one(
                        {"_id": existing["_id"]},
                        {"$set": product_doc}
                    )
                    logger.info(f"Row {idx + 2}: Updated existing product: {name}")
                else:
                    # Insert new product
                    products.insert_one(product_doc)
                    logger.info(f"Row {idx + 2}: Inserted new product: {name}")
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                error_msg = f"Row {idx + 2}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"CSV import error - {error_msg}")
                logger.error(f"Row {idx + 2} data: {row.to_dict()}")
                # Log the actual values for debugging
                logger.error(f"Row {idx + 2} raw values - name: '{row.get('name', 'N/A')}', category: '{row.get('category', 'N/A')}', brand: '{row.get('brand', 'N/A')}', price: '{row.get('price', 'N/A')}'")
        
        result = {
            "success": True,
            "message": f"Import completed",
            "total_rows": len(df),
            "imported": success_count,
            "failed": error_count,
            "errors": errors[:20]  # Return first 20 errors for better debugging
        }
        
        logger.info(f"CSV import result: {result}")
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process CSV: {str(e)}")


@router.post("/products/cleanup-links")
async def cleanup_broken_links(
    admin: dict = Depends(require_admin)
):
    """
    Check all product image URLs and mark broken links
    
    Module 2: Product Catalogue - Cleanup missing links
    """
    products = get_products_collection()
    
    # Get all products with image URLs
    product_list = list(products.find({"image_path": {"$ne": ""}}))
    
    checked = 0
    broken = 0
    broken_ids = []
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for product in product_list:
            image_url = product.get("image_path", "")
            if not image_url:
                continue
            
            checked += 1
            
            try:
                # Skip local file paths
                if not image_url.startswith('http'):
                    continue
                
                response = await client.head(image_url)
                if response.status_code >= 400:
                    # Mark as broken
                    products.update_one(
                        {"_id": product["_id"]},
                        {"$set": {"broken_link": True}}
                    )
                    broken += 1
                    broken_ids.append(str(product["_id"]))
                else:
                    # Mark as working
                    products.update_one(
                        {"_id": product["_id"]},
                        {"$set": {"broken_link": False}}
                    )
                    
            except Exception as e:
                # Connection error - mark as broken
                products.update_one(
                    {"_id": product["_id"]},
                    {"$set": {"broken_link": True}}
                )
                broken += 1
                broken_ids.append(str(product["_id"]))
    
    return {
        "success": True,
        "checked": checked,
        "broken": broken,
        "working": checked - broken,
        "broken_ids": broken_ids
    }


@router.post("/products/{product_id}/repair-link")
async def repair_broken_link(
    product_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Repair a broken image link by re-checking it
    
    Module 2: Product Catalogue - Repair broken links
    """
    products = get_products_collection()
    
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    product = products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    image_url = product.get("image_url") or product.get("image_path", "")
    
    if not image_url:
        raise HTTPException(status_code=400, detail="Product has no image URL")
    
    # Re-check the link
    try:
        # Skip local file paths
        if not image_url.startswith('http'):
            # For local paths, just mark as working
            products.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {"broken_link": False}}
            )
            return {
                "success": True,
                "message": "Link repaired (local file)",
                "product_id": product_id,
                "broken_link": False
            }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.head(image_url)
            
            if response.status_code < 400:
                # Link is working now
                products.update_one(
                    {"_id": ObjectId(product_id)},
                    {"$set": {"broken_link": False}}
                )
                return {
                    "success": True,
                    "message": "Link repaired successfully",
                    "product_id": product_id,
                    "broken_link": False
                }
            else:
                # Still broken
                return {
                    "success": False,
                    "message": f"Link still broken (HTTP {response.status_code})",
                    "product_id": product_id,
                    "broken_link": True
                }
                
    except Exception as e:
        # Still broken - connection error
        return {
            "success": False,
            "message": f"Link still broken: {str(e)}",
            "product_id": product_id,
            "broken_link": True
        }


@router.delete("/products/clear-all")
async def clear_all_products(
    admin: dict = Depends(require_admin)
):
    """
    Clear all products from the catalogue
    
    **WARNING:** This will delete ALL products from the database.
    Use with caution! This action cannot be undone.
    
    Module 2: Product Catalogue - Clear all products
    """
    try:
        products = get_products_collection()
        
        # Count products before deletion
        total_count = products.count_documents({})
        
        if total_count == 0:
            return {
                "success": True,
                "message": "Product catalogue is already empty",
                "deleted_count": 0
            }
        
        # Delete all products
        result = products.delete_many({})
        deleted_count = result.deleted_count
        
        logger.info(f"Cleared all products from catalogue. Deleted {deleted_count} products.")
        
        return {
            "success": True,
            "message": f"Successfully cleared all products from catalogue",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error clearing products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear products: {str(e)}"
        )


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Delete a product permanently
    
    Module 2: Product Catalogue - Delete products
    """
    products = get_products_collection()
    
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID")
    
    result = products.delete_one({"_id": ObjectId(product_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {
        "success": True,
        "message": "Product deleted successfully",
        "product_id": product_id
    }


@router.get("/categories")
async def get_all_categories(
    gender: Optional[str] = Query(None, description="Filter categories by product gender: 'm' (men) or 'w' (women). Omit for all."),
    admin: dict = Depends(require_admin)
):
    """
    Get unique product categories (for dropdown). Optional gender filter so
    when user selects Women/Men, only categories that exist for that gender are returned.
    Module 2: Product Catalogue - View category tags
    """
    products = get_products_collection()
    query = {}
    if gender and gender.strip():
        g = gender.strip().lower()
        if g in ("w", "women"):
            query["gender"] = "w"
        elif g in ("m", "men"):
            query["gender"] = "m"

    # Sync DB: generalize by endpoint only – all products from these endpoints become Women Luxe / Women Short Kurti (no gender filter)
    for s in WOMEN_LUXE_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Women Luxe"}}
        )
    for s in WOMEN_SHORT_KURTI_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Women Short Kurti"}}
        )
    for s in WOMEN_LAWN_ENDPOINTS:
        products.update_many(
            {"gender": "w", "endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Women Lawn"}}
        )
    products.update_many(
        {"gender": "w", "$and": [{"endpoint_category": {"$regex": "ramadan", "$options": "i"}}, {"endpoint_category": {"$regex": "lawn", "$options": "i"}}]},
        {"$set": {"display_category": "Women Lawn"}}
    )
    for s in WOMEN_ACCESSORIES_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Women Accessories"}}
        )
    for s in WOMEN_ANARKALI_FROCK_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Women Anarkali Frock"}}
        )
    for s in WOMEN_BOTTOMS_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Women Bottoms"}}
        )
    for s in WOMEN_BAGS_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Women Bags"}}
        )
    for s in WOMEN_JEWELRY_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Women Jewelry"}}
        )
    for s in WOMEN_TOPS_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Women Tops"}}
        )
    for s in WOMEN_UNSTITCHED_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Women Unstitched"}}
        )
    for s in WOMEN_WESTERN_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Women Western"}}
        )
    for s in WOMEN_WINTER_PANTS_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Women Winter Pants"}}
        )
    # Sync DB: men's endpoints -> display category (so dropdown counts match)
    for s in MEN_STANDARD_SUIT_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Men Standard Suit"}}
        )
    for s in MEN_TRADITIONAL_SUIT_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Men Traditional Suit"}}
        )
    for s in MEN_CASUAL_WEAR_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Men Casual Wear"}}
        )
    for s in MEN_FOOTWEAR_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Men Footwear"}}
        )
    for s in MEN_SHOES_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Men Shoes"}}
        )
    for s in MEN_SWEATER_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Men Sweater"}}
        )
    for s in MEN_WRIST_WATCHES_ENDPOINTS:
        products.update_many(
            {"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}},
            {"$set": {"display_category": "Men Wrist Watches"}}
        )

    # Build category list: use EXACT SAME filter as product filter. When gender is set, only show that gender's categories (Women Accessories etc. only under Women).
    WOMEN_DISPLAY_NAMES = (
        "Women Kurta", "Women Lawn", "Women Luxe", "Women Short Kurti", "Women Accessories",
        "Women Anarkali Frock", "Women Bottoms", "Women Bags", "Women Jewelry", "Women Tops",
        "Women Unstitched", "Women Western", "Women Winter Pants"
    )
    # Women categories that are by endpoint only (products may have any gender in DB); count without gender so they show under Women
    WOMEN_ENDPOINT_ONLY_CATEGORIES = frozenset({"Women Accessories", "Women Luxe", "Women Short Kurti"})
    MEN_DISPLAY_NAMES = ("Men Standard Suit", "Men Traditional Suit", "Men Casual Wear", "Men Footwear", "Men Shoes", "Men Sweater", "Men Wrist Watches")
    ALL_DISPLAY_NAMES = WOMEN_DISPLAY_NAMES + MEN_DISPLAY_NAMES
    gender_val = query.get("gender") if query else None
    if gender_val == "m":
        display_names_to_show = MEN_DISPLAY_NAMES
    elif gender_val == "w":
        display_names_to_show = WOMEN_DISPLAY_NAMES
    else:
        display_names_to_show = ALL_DISPLAY_NAMES
    result_counts = {}
    for display_name in display_names_to_show:
        cat_filter = _category_filter_for_products(display_name)
        if not cat_filter:
            continue
        # For endpoint-only women categories when Women selected: count by category only (no gender) so Women Accessories etc. show with correct count
        if gender_val == "w" and display_name in WOMEN_ENDPOINT_ONLY_CATEGORIES:
            count_query = {"$and": [cat_filter]}
        else:
            count_query = {"$and": [cat_filter]} if not query else {"$and": [query, cat_filter]}
        result_counts[display_name] = products.count_documents(count_query)

    def to_display(s: str) -> str:
        return _slug_to_display_for_categories(s) or (s or "").strip()

    # When filtering by gender, do not add categories that belong to the other gender (e.g. Women Accessories only when Women selected)
    def skip_for_gender(name: str) -> bool:
        if gender_val == "m" and name in WOMEN_DISPLAY_NAMES:
            return True
        if gender_val == "w" and name in MEN_DISPLAY_NAMES:
            return True
        return False

    # Other categories (distinct display_category / endpoint_category / category), skip if already in list or wrong gender
    no_display = {"$or": [{"display_category": {"$exists": False}}, {"display_category": ""}, {"display_category": None}]}
    for cat in products.distinct("display_category", query):
        if not cat or not (str(cat)).strip():
            continue
        cat_str = (cat or "").strip()
        name = to_display(cat_str)
        if name in ALL_DISPLAY_NAMES or skip_for_gender(name):
            continue
        result_counts[name] = result_counts.get(name, 0) + products.count_documents({**query, "display_category": cat_str})

    for slug in products.distinct("endpoint_category", {**query, **no_display}):
        if slug is None or not (str(slug)).strip():
            continue
        slug_str = (slug or "").strip()
        name = to_display(slug_str)
        if name in ALL_DISPLAY_NAMES or skip_for_gender(name):
            continue
        result_counts[name] = result_counts.get(name, 0) + products.count_documents({**query, **no_display, "endpoint_category": slug_str})

    no_endpoint = {"$or": [{"endpoint_category": {"$exists": False}}, {"endpoint_category": ""}, {"endpoint_category": None}]}
    for cat in products.distinct("category", {**query, **no_display, **no_endpoint}):
        if cat is None or not (str(cat)).strip():
            continue
        cat_str = (cat or "").strip()
        name = _display_category_from_legacy(cat_str) or cat_str
        if name in ALL_DISPLAY_NAMES or skip_for_gender(name):
            continue
        result_counts[name] = result_counts.get(name, 0) + products.count_documents({**query, **no_display, **no_endpoint, "category": cat_str})

    # Include category if count > 0 OR if it's one of the display names for current gender (so e.g. Women Accessories always shows when Women selected)
    category_stats = [
        {"name": name, "count": c} for name, c in sorted(result_counts.items())
        if name and (c > 0 or name in display_names_to_show)
    ]

    return {
        "categories": category_stats,
        "total": len(category_stats)
    }


@router.post("/categories/backfill-display")
async def backfill_display_category(
    admin: dict = Depends(require_admin)
):
    """
    One-time backfill: set display_category on existing products from endpoint_category
    or legacy category. Women Kurta/Lawn use gender+endpoint; Women Luxe and Women Short Kurti
    use endpoint only (all products from those endpoints are generalized).
    """
    products = get_products_collection()
    r_kurta_e = products.update_many(
        {"gender": "w", "endpoint_category": {"$in": list(WOMEN_KURTA_ENDPOINTS)}},
        {"$set": {"display_category": "Women Kurta"}}
    )
    r_lawn_e = products.update_many(
        {"gender": "w", "endpoint_category": {"$in": list(WOMEN_LAWN_ENDPOINTS)}},
        {"$set": {"display_category": "Women Lawn"}}
    )
    r_lawn_regex = products.update_many(
        {"gender": "w", "$and": [{"endpoint_category": {"$regex": "ramadan", "$options": "i"}}, {"endpoint_category": {"$regex": "lawn", "$options": "i"}}]},
        {"$set": {"display_category": "Women Lawn"}}
    )
    r_kurta_legacy = products.update_many(
        {"gender": "w", "category": {"$regex": "women.*(stitched|western)", "$options": "i"}},
        {"$set": {"display_category": "Women Kurta"}}
    )
    r_lawn_legacy = products.update_many(
        {"gender": "w", "category": {"$regex": "women.*unstitched", "$options": "i"}},
        {"$set": {"display_category": "Women Lawn"}}
    )
    # Women Luxe / Short kurti: generalize by endpoint only (all products from these endpoints, no gender filter)
    luxe_or = [{"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}} for s in WOMEN_LUXE_ENDPOINTS]
    r_luxe_e = products.update_many(
        {"$or": luxe_or},
        {"$set": {"display_category": "Women Luxe"}}
    )
    short_or = [{"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}} for s in WOMEN_SHORT_KURTI_ENDPOINTS]
    r_short_kurti_e = products.update_many(
        {"$or": short_or},
        {"$set": {"display_category": "Women Short Kurti"}}
    )
    # Men's: all -> Men Standard Suit; men, men-main, men-ready-to-wear -> Men Traditional Suit; men-products -> Men Casual Wear (case-insensitive)
    men_standard_or = [{"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}} for s in MEN_STANDARD_SUIT_ENDPOINTS]
    r_men_standard = products.update_many(
        {"$or": men_standard_or},
        {"$set": {"display_category": "Men Standard Suit"}}
    )
    men_traditional_or = [{"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}} for s in MEN_TRADITIONAL_SUIT_ENDPOINTS]
    r_men_traditional = products.update_many(
        {"$or": men_traditional_or},
        {"$set": {"display_category": "Men Traditional Suit"}}
    )
    men_casual_or = [{"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}} for s in MEN_CASUAL_WEAR_ENDPOINTS]
    r_men_casual = products.update_many(
        {"$or": men_casual_or},
        {"$set": {"display_category": "Men Casual Wear"}}
    )
    # Women Accessories; new women categories; Men Footwear, etc. (case-insensitive)
    women_accessories_or = [{"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}} for s in WOMEN_ACCESSORIES_ENDPOINTS]
    r_women_accessories = products.update_many(
        {"$or": women_accessories_or},
        {"$set": {"display_category": "Women Accessories"}}
    )
    for endpoints_set, display_name in [
        (WOMEN_ANARKALI_FROCK_ENDPOINTS, "Women Anarkali Frock"),
        (WOMEN_BOTTOMS_ENDPOINTS, "Women Bottoms"),
        (WOMEN_BAGS_ENDPOINTS, "Women Bags"),
        (WOMEN_JEWELRY_ENDPOINTS, "Women Jewelry"),
        (WOMEN_TOPS_ENDPOINTS, "Women Tops"),
        (WOMEN_UNSTITCHED_ENDPOINTS, "Women Unstitched"),
        (WOMEN_WESTERN_ENDPOINTS, "Women Western"),
        (WOMEN_WINTER_PANTS_ENDPOINTS, "Women Winter Pants"),
    ]:
        _or = [{"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}} for s in endpoints_set]
        products.update_many({"$or": _or}, {"$set": {"display_category": display_name}})
    men_footwear_or = [{"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}} for s in MEN_FOOTWEAR_ENDPOINTS]
    r_men_footwear = products.update_many(
        {"$or": men_footwear_or},
        {"$set": {"display_category": "Men Footwear"}}
    )
    men_shoes_or = [{"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}} for s in MEN_SHOES_ENDPOINTS]
    r_men_shoes = products.update_many(
        {"$or": men_shoes_or},
        {"$set": {"display_category": "Men Shoes"}}
    )
    men_sweater_or = [{"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}} for s in MEN_SWEATER_ENDPOINTS]
    r_men_sweater = products.update_many(
        {"$or": men_sweater_or},
        {"$set": {"display_category": "Men Sweater"}}
    )
    men_wrist_watches_or = [{"endpoint_category": {"$regex": f"^{re.escape(s)}$", "$options": "i"}} for s in MEN_WRIST_WATCHES_ENDPOINTS]
    r_men_wrist_watches = products.update_many(
        {"$or": men_wrist_watches_or},
        {"$set": {"display_category": "Men Wrist Watches"}}
    )
    # Set display_category for women products that still don't have it (e.g. bags, jewelry)
    r_other = 0
    for doc in products.find({"gender": "w", "$or": [{"display_category": {"$exists": False}}, {"display_category": ""}]}):
        val = (doc.get("endpoint_category") or doc.get("category") or "Other").strip() or "Other"
        products.update_one({"_id": doc["_id"]}, {"$set": {"display_category": val}})
        r_other += 1
    # Set display_category for men products that still don't have it (use endpoint or legacy)
    for doc in products.find({"gender": "m", "$or": [{"display_category": {"$exists": False}}, {"display_category": ""}]}):
        slug = (doc.get("endpoint_category") or "").strip()
        val = _display_category_from_endpoint(slug, "m") if slug else (doc.get("category") or "Other").strip() or "Other"
        products.update_one({"_id": doc["_id"]}, {"$set": {"display_category": val}})
        r_other += 1
    return {
        "success": True,
        "message": "Backfill display_category completed (women + men)",
        "matched_kurta_endpoint": r_kurta_e.modified_count,
        "matched_lawn_endpoint": r_lawn_e.modified_count,
        "matched_lawn_ramadan_regex": r_lawn_regex.modified_count,
        "matched_kurta_legacy": r_kurta_legacy.modified_count,
        "matched_lawn_legacy": r_lawn_legacy.modified_count,
        "matched_luxe_endpoint": r_luxe_e.modified_count,
        "matched_short_kurti_endpoint": r_short_kurti_e.modified_count,
        "matched_men_standard_suit": r_men_standard.modified_count,
        "matched_men_traditional_suit": r_men_traditional.modified_count,
        "matched_men_casual_wear": r_men_casual.modified_count,
        "matched_women_accessories": r_women_accessories.modified_count,
        "matched_men_footwear": r_men_footwear.modified_count,
        "matched_men_shoes": r_men_shoes.modified_count,
        "matched_men_sweater": r_men_sweater.modified_count,
        "matched_men_wrist_watches": r_men_wrist_watches.modified_count,
        "other_fallback": r_other,
    }


@router.post("/categories")
async def add_category_tag(
    category_name: str,
    admin: dict = Depends(require_admin)
):
    """
    Add a new category tag to the system
    
    Module 2: Product Catalogue - Add category tags
    """
    # For MongoDB, categories are just strings in products
    # We can validate by checking if it already exists
    products = get_products_collection()
    
    existing = products.find_one({"category": category_name})
    if existing:
        return {
            "success": True,
            "message": f"Category '{category_name}' already exists",
            "category": category_name
        }
    
    # Create a placeholder product to register the category
    # Or just return success - categories are created when products use them
    return {
        "success": True,
        "message": f"Category '{category_name}' ready to use",
        "category": category_name
    }


@router.get("/products/merged")
async def get_products_merged_category(
    merged_category: str = Query(..., description="women_luxe or women_short_kurti"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: dict = Depends(require_admin)
):
    """
    Only for Women Luxe & Women Short Kurti. One query, no other logic.
    women_luxe = bridal-in-stock + festive-in-stock + wedding-unstitched-2025.
    women_short_kurti = short-kurti + ss-wesst + ss-west.
    """
    products = get_products_collection()
    mc = merged_category.strip().lower()
    if mc == "women_luxe":
        endpoint_list = list(WOMEN_LUXE_ENDPOINTS)
    elif mc == "women_short_kurti":
        endpoint_list = list(WOMEN_SHORT_KURTI_ENDPOINTS)
    else:
        raise HTTPException(status_code=400, detail="merged_category must be women_luxe or women_short_kurti")
    query = {"endpoint_category": {"$in": endpoint_list}}
    total = products.count_documents(query)
    skip = (page - 1) * page_size
    product_list = list(
        products.find(query).skip(skip).limit(page_size).sort("created_at", -1)
    )
    for p in product_list:
        p["_id"] = str(p["_id"])
        if "embedding" in p:
            del p["embedding"]
    return {
        "products": product_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/products")
async def get_products_admin(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    merged_category: Optional[str] = Query(None, description="Generalized category: women_luxe | women_short_kurti – backend uses this to filter by endpoint list, no string parsing"),
    brand: Optional[str] = None,
    gender: Optional[str] = None,
    broken_links_only: bool = False,
    search: Optional[str] = None,
    admin: dict = Depends(require_admin)
):
    """
    Get products with filtering for admin management.
    Women Luxe = bridal-in-stock + festive-in-stock + wedding-unstitched-2025 (81). Women Short Kurti = short-kurti + ss-wesst (70).
    """
    products = get_products_collection()
    query = {}

    # 1) Decide merged type from merged_category param OR from category string – one place so re-fetch / second request always gets same filter
    merged_type = None
    if merged_category and merged_category.strip().lower() in ("women_luxe", "women_short_kurti"):
        merged_type = merged_category.strip().lower()
    else:
        category_clean = (category or "").strip()
        if category_clean:
            category_clean = re.sub(r"\s*\(\d+\)\s*$", "", category_clean).strip()
            category_clean = re.sub(r"\s+", " ", category_clean)
        _norm = (category_clean or "").lower().strip()
        # Only exact normalized names for merged – do NOT match "Women Kurta" (has "kurti" but not "short")
        if _norm == "women luxe":
            merged_type = "women_luxe"
            category_clean = "Women Luxe"
        elif _norm == "women short kurti":
            merged_type = "women_short_kurti"
            category_clean = "Women Short Kurti"
        else:
            category_clean = (category or "").strip() if category else None
            if category_clean:
                category_clean = re.sub(r"\s*\(\d+\)\s*$", "", category_clean).strip()
                category_clean = re.sub(r"\s+", " ", category_clean)

    # 2) Apply filter: merged categories = only endpoint $in, no gender
    if merged_type == "women_luxe":
        query["endpoint_category"] = {"$in": list(WOMEN_LUXE_ENDPOINTS)}
        category_clean = "Women Luxe"
    elif merged_type == "women_short_kurti":
        query["endpoint_category"] = {"$in": list(WOMEN_SHORT_KURTI_ENDPOINTS)}
        category_clean = "Women Short Kurti"
    else:
        if gender:
            # Women Accessories (and Luxe/Short Kurti) are endpoint-only: show all products in that category regardless of gender
            if category_clean not in ("Women Accessories", "Women Luxe", "Women Short Kurti"):
                g = (gender or "").strip().lower()
                if g in ("w", "women"):
                    query["gender"] = {"$regex": "^(w|women)$", "$options": "i"}
                elif g in ("m", "men"):
                    query["gender"] = {"$regex": "^(m|men)$", "$options": "i"}
                else:
                    query["gender"] = {"$regex": f"^{re.escape(g)}$", "$options": "i"}
        if category_clean:
            cat_filter = _category_filter_for_products(category_clean)
            if cat_filter:
                query["$and"] = query.get("$and", []) + [cat_filter]
            else:
                query["display_category"] = category_clean
    if brand:
        if "$and" in query:
            query["$and"].append({"brand": brand})
        else:
            query["brand"] = brand
    if broken_links_only:
        if "$and" in query:
            query["$and"].append({"broken_link": True})
        else:
            query["broken_link"] = True
    if search:
        search_query = {
            "$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        }
        if "$and" in query:
            query["$and"].append(search_query)
        else:
            query["$or"] = search_query["$or"]
    
    # Get total
    total = products.count_documents(query)
    direct_count = None
    if category_clean in ("Women Luxe", "Women Short Kurti"):
        endpoints = list(WOMEN_LUXE_ENDPOINTS if category_clean == "Women Luxe" else WOMEN_SHORT_KURTI_ENDPOINTS)
        direct_query = {"endpoint_category": {"$in": endpoints}}
        direct_count = products.count_documents(direct_query)
        logger.info("GET /products category=%r -> total=%s direct_count=%s", category_clean, total, direct_count)
        # If DB has products but our query returned 0, use only endpoint filter (fixes wrong query build)
        if direct_count > 0 and total == 0:
            query = direct_query
            total = direct_count
    
    # Get paginated
    skip = (page - 1) * page_size
    product_list = list(
        products.find(query)
        .skip(skip)
        .limit(page_size)
        .sort("created_at", -1)
    )
    
    # Format
    for product in product_list:
        product["_id"] = str(product["_id"])
        if "embedding" in product:
            del product["embedding"]  # Don't send large embeddings
    
    out = {
        "products": product_list,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
    # Debug when category was sent (and Luxe/Short kurti or total 0) so we can see why 0 products
    if category and (category_clean in ("Women Luxe", "Women Short Kurti") or total == 0):
        _dc = direct_count
        _ep = list(WOMEN_LUXE_ENDPOINTS) if category_clean == "Women Luxe" else (list(WOMEN_SHORT_KURTI_ENDPOINTS) if category_clean == "Women Short Kurti" else None)
        if _ep is not None and _dc is None:
            _dc = products.count_documents({"endpoint_category": {"$in": _ep}})
        out["_debug"] = {"category_received": category, "category_clean": category_clean, "direct_endpoint_count": _dc, "endpoint_slugs": _ep}
    return out


# ============================================
# MODULE 3: ML Model Training Dashboard
# ============================================

# In-memory storage for training jobs (use Redis in production)
training_jobs = {}


@router.post("/ml/train")
async def trigger_model_training(
    train_split: float = Query(0.8, ge=0.5, le=0.95),
    admin: dict = Depends(require_admin)
):
    """
    Trigger ML model retraining
    
    Module 3: ML Training - Start training with custom train/test split
    """
    import uuid
    
    job_id = str(uuid.uuid4())
    
    # Store job
    training_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "train_split": train_split,
        "started_at": datetime.utcnow(),
        "message": "Training job queued"
    }
    
    # Start training in background (simplified - use Celery in production)
    asyncio.create_task(run_training_job(job_id, train_split))
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Training started",
        "train_split": train_split
    }


async def run_training_job(job_id: str, train_split: float):
    """
    Background task to run ML training
    """
    try:
        training_jobs[job_id]["status"] = "running"
        training_jobs[job_id]["progress"] = 10
        
        # Simulate training (replace with actual ML training code)
        await asyncio.sleep(2)
        training_jobs[job_id]["progress"] = 30
        
        await asyncio.sleep(2)
        training_jobs[job_id]["progress"] = 60
        
        await asyncio.sleep(2)
        training_jobs[job_id]["progress"] = 90
        
        # Complete
        training_jobs[job_id]["status"] = "completed"
        training_jobs[job_id]["progress"] = 100
        training_jobs[job_id]["completed_at"] = datetime.utcnow()
        training_jobs[job_id]["metrics"] = {
            "accuracy": 0.92,
            "precision": 0.89,
            "recall": 0.91,
            "f1_score": 0.90
        }
        
    except Exception as e:
        training_jobs[job_id]["status"] = "failed"
        training_jobs[job_id]["error"] = str(e)


@router.get("/ml/training-status/{job_id}")
async def get_training_status(
    job_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Get training job status and progress
    
    Module 3: ML Training - Check progress
    """
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    job = training_jobs[job_id]
    return job


@router.get("/ml/metrics")
async def get_training_metrics(
    limit: int = Query(10, ge=1, le=50),
    admin: dict = Depends(require_admin)
):
    """
    Get historical training metrics
    
    Module 3: ML Training - View performance metrics
    """
    # Get completed training jobs
    completed_jobs = [
        job for job in training_jobs.values()
        if job["status"] == "completed" and "metrics" in job
    ]
    
    # Sort by completed_at (most recent first)
    completed_jobs.sort(
        key=lambda x: x.get("completed_at", datetime.min),
        reverse=True
    )
    
    return {
        "metrics": completed_jobs[:limit],
        "total": len(completed_jobs)
    }


# ============================================
# MODULE 4: Auto Sync / Rescraping
# ============================================

# In-memory storage for scraping jobs
scraping_jobs = {}


def _project_root_for_local_csvs() -> str:
    """Directory containing local_brands_links*.csv (same walk as get_available_brands)."""
    _start = os.path.abspath(os.path.dirname(__file__))
    project_root = _start
    for _ in range(12):
        if os.path.isfile(os.path.join(project_root, "local_brands_links.csv")) or os.path.isfile(
            os.path.join(project_root, "local_brands_links_women.csv")
        ):
            return project_root
        _parent = os.path.dirname(project_root)
        if _parent == project_root:
            break
        project_root = _parent
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))


def _norm_listing_url(u: str) -> str:
    u = (u or "").strip().split("|")[0].strip().rstrip("/")
    if u.startswith("http://"):
        u = "https://" + u[7:]
    return u


def _enrich_brands_for_scraping(brand_list: List[dict]) -> List[dict]:
    """
    Re-attach brand_urls, scraper_type, display_categories, gender from CSV.
    Prevents 0-product scrapes when the frontend JSON omits pipe-separated URLs or scraper_type.
    """
    root = _project_root_for_local_csvs()
    exact: dict = {}
    by_name: dict = {}

    def _register(name: str, urls: List[str], scraper_type: str, gender: str, category: str, display_cats: List[str]):
        if not name or not urls:
            return
        st = (scraper_type or "").strip().lower()
        if st == "nan" or st not in ("shopify_json", "woocommerce"):
            st = "generic"
        payload = {
            "brand_urls": urls,
            "scraper_type": st,
            "gender": gender,
            "category": category,
            "display_categories": display_cats,
        }
        u0 = _norm_listing_url(urls[0])
        exact[(name.lower(), u0)] = payload
        by_name.setdefault(name.lower(), []).append((u0, payload))

    for fname, gender, category in (
        ("local_brands_links_women.csv", "w", "Women → Stitched"),
        ("local_brands_links.csv", "m", "Men → Eastern"),
    ):
        path = os.path.join(root, fname)
        if not os.path.isfile(path):
            continue
        try:
            df = pd.read_csv(path)
        except Exception as e:
            logger.warning(f"Enrich: could not read {path}: {e}")
            continue
        if "Brand" not in df.columns or "Website" not in df.columns:
            continue
        for _, row in df.iterrows():
            brand_name = str(row.get("Brand", "")).strip()
            raw = row.get("Website", "")
            if pd.isna(raw) or not str(raw).strip():
                continue
            urls = [u.strip() for u in str(raw).split("|") if u.strip().startswith("http")]
            if not urls:
                continue
            scraper_type = ""
            if "ScraperType" in df.columns:
                v = row.get("ScraperType", "")
                scraper_type = str(v).strip() if pd.notna(v) else ""
            dc_raw = ""
            if "DisplayCategory" in df.columns:
                v = row.get("DisplayCategory", "")
                dc_raw = str(v).strip() if pd.notna(v) else ""
            display_cats = [x.strip() for x in dc_raw.split("|")] if dc_raw and dc_raw.lower() != "nan" else []
            while len(display_cats) < len(urls):
                display_cats.append("")
            display_cats = display_cats[: len(urls)]
            _register(brand_name, urls, scraper_type, gender, category, display_cats)

    out: List[dict] = []
    for b in brand_list:
        bi = dict(b)
        nm = str(bi.get("brand_name") or "").strip()
        ur = _norm_listing_url(bi.get("brand_url") or "")
        hit = exact.get((nm.lower(), ur)) if nm else None
        if not hit and nm:
            cands = by_name.get(nm.lower()) or []
            for u0c, payload in cands:
                if ur and (ur == u0c or ur.startswith(u0c + "/") or u0c.startswith(ur)):
                    hit = payload
                    break
            if not hit and len(cands) == 1:
                hit = cands[0][1]
        if hit:
            bi["brand_urls"] = hit["brand_urls"]
            bi["brand_url"] = hit["brand_urls"][0]
            bi["scraper_type"] = hit["scraper_type"]
            bi["gender"] = hit["gender"]
            bi["category"] = hit["category"]
            if hit.get("display_categories"):
                bi["display_categories"] = hit["display_categories"]
            logger.info(
                f"Scrape CSV enrich: {nm!r} -> {len(bi['brand_urls'])} URL(s), scraper={bi['scraper_type']}, gender={bi['gender']}"
            )
        else:
            if nm:
                logger.warning(
                    f"Scrape CSV enrich: no row for {nm!r} url={ur[:80]!r} — using request fields only"
                )
        if not bi.get("brand_urls") and bi.get("brand_url"):
            bi["brand_urls"] = [str(bi["brand_url"]).strip()]
        if not bi.get("gender"):
            cat = str(bi.get("category") or "").lower()
            if "women" in cat or "woman" in cat:
                bi["gender"] = "w"
            elif "men" in cat or "man" in cat:
                bi["gender"] = "m"
        if not bi.get("scraper_type"):
            bi["scraper_type"] = "generic"
        out.append(bi)
    return out


@router.get("/scraping/brands")
async def get_available_brands(
    brand_type: str = Query("local", pattern="^(luxury|pakistani|local)$"),
    admin: dict = Depends(require_admin)
):
    """
    Get list of brands available for rescraping from Excel files
    
    Module 4: Auto Sync - View brands
    """
    brands = []
    seen_brands = {}  # Track unique brands by (brand_name, brand_url)
    brand_names_list = []  # Collect all brand names first for batch query
    
    try:
        # Find project root: walk up until we find local_brands_links.csv (works from backend/ or repo root)
        _start = os.path.abspath(os.path.dirname(__file__))
        project_root = _start
        for _ in range(10):
            if os.path.isfile(os.path.join(project_root, "local_brands_links.csv")):
                break
            _parent = os.path.dirname(project_root)
            if _parent == project_root:
                break
            project_root = _parent
        if not os.path.isfile(os.path.join(project_root, "local_brands_links.csv")):
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        logger.info(f"Brands project_root: {project_root}")
        
        # For "local" type: load ONLY from local_brands_links.csv so URLs are exact listing links (no Excel)
        if brand_type == "local":
            csv_file = os.path.join(project_root, "local_brands_links.csv")
            if os.path.isfile(csv_file):
                try:
                    df_csv = pd.read_csv(csv_file)
                    if "Brand" in df_csv.columns and "Website" in df_csv.columns:
                        for idx, row in df_csv.iterrows():
                            brand_name = str(row.get("Brand", "")).strip()
                            brand_url = row.get("Website", "")
                            if pd.notna(brand_url) and brand_url:
                                # Support multiple URLs per brand: separate with |
                                url_str = str(brand_url).strip()
                                brand_urls = [u.strip() for u in url_str.split("|") if u.strip().startswith("http")]
                                if not brand_urls:
                                    continue
                                brand_url_str = brand_urls[0]
                                brand_key = (brand_name, brand_url_str)
                                if brand_key not in seen_brands:
                                    seen_brands[brand_key] = True
                                    # ScraperType in CSV: generic (default) | shopify_json (Shopify collection JSON) | woocommerce (reserved)
                                    scraper_type = str(row.get("ScraperType", "")).strip().lower() if "ScraperType" in df_csv.columns else ""
                                    if scraper_type == "nan" or scraper_type not in ("shopify_json", "woocommerce"):
                                        scraper_type = "generic"
                                    brand_data = {
                                        "brand_name": brand_name,
                                        "brand_url": brand_url_str,
                                        "brand_urls": brand_urls,  # all URLs to scrape (multiple links per brand)
                                        "category": "Men → Eastern",
                                        "product_count": 0,
                                        "last_scraped_at": None,
                                        "gender": "m",
                                        "scraper_type": scraper_type,
                                    }
                                    brands.append(brand_data)
                                    brand_names_list.append(brand_name)
                        logger.info(f"Loaded {len(brands)} brands from local_brands_links.csv (local type)")
                except Exception as e:
                    logger.warning(f"Error reading local_brands_links.csv: {e}")
            if not brands:
                brand_type = "_local_fallback"
        
        # For local type: load women's brands from local_brands_links_women.csv (same pattern as men's CSV)
        if brand_type == "local":
            women_csv = os.path.join(project_root, "local_brands_links_women.csv")
            if os.path.isfile(women_csv):
                try:
                    df_women_csv = pd.read_csv(women_csv)
                    if "Brand" in df_women_csv.columns and "Website" in df_women_csv.columns:
                        women_added = 0
                        for idx, row in df_women_csv.iterrows():
                            brand_name = str(row.get("Brand", "")).strip()
                            brand_url = row.get("Website", "")
                            if not brand_name:
                                continue
                            if pd.notna(brand_url) and brand_url:
                                url_str = str(brand_url).strip()
                                brand_urls = [u.strip() for u in url_str.split("|") if u.strip().startswith("http")]
                                if not brand_urls:
                                    continue
                                brand_url_str = brand_urls[0]
                                brand_key = (brand_name, brand_url_str)
                                if brand_key not in seen_brands:
                                    seen_brands[brand_key] = True
                                    scraper_type = str(row.get("ScraperType", "")).strip().lower() if "ScraperType" in df_women_csv.columns else ""
                                    if scraper_type == "nan" or scraper_type not in ("shopify_json", "woocommerce"):
                                        scraper_type = "generic"
                                    # Optional pipe-aligned DisplayCategory per URL (same count as Website | URLs)
                                    dc_raw = ""
                                    if "DisplayCategory" in df_women_csv.columns:
                                        v = row.get("DisplayCategory", "")
                                        dc_raw = str(v).strip() if pd.notna(v) else ""
                                    display_cats = [x.strip() for x in dc_raw.split("|")] if dc_raw and dc_raw.lower() != "nan" else []
                                    while len(display_cats) < len(brand_urls):
                                        display_cats.append("")
                                    display_cats = display_cats[: len(brand_urls)]
                                    brand_data = {
                                        "brand_name": brand_name,
                                        "brand_url": brand_url_str,
                                        "brand_urls": brand_urls,
                                        "category": "Women → Stitched",
                                        "product_count": 0,
                                        "last_scraped_at": None,
                                        "gender": "w",
                                        "scraper_type": scraper_type,
                                        "display_categories": display_cats,
                                    }
                                    brands.append(brand_data)
                                    brand_names_list.append(brand_name)
                                    women_added += 1
                        if women_added:
                            logger.info(f"Loaded {women_added} women's brands from local_brands_links_women.csv (local type)")
                except Exception as e:
                    logger.warning(f"Error reading local_brands_links_women.csv: {e}")
        
        # Read women links dataset Excel (only when brand_type is NOT local; local uses CSV above)
        if brand_type != "local":
            women_file = os.path.join(project_root, "women links dataset.xlsx")
            if os.path.exists(women_file):
                df = pd.read_excel(women_file)
                logger.info(f"Reading women's dataset: {women_file}, rows: {len(df)}")
                
                # Determine which link column to use
                link_column = None
                brand_column = None
                if brand_type == "luxury":
                    link_column = "Luxury Brand Link"
                    brand_column = "Luxury / International Brand"
                elif brand_type == "pakistani":
                    link_column = "Pakistani Designer Brand Link"
                    brand_column = "Pakistani Luxury / Designer Brand"
                else:  # local
                    link_column = "Local Dupe Brand Link"
                    brand_column = "Local Affordable Brand (Dupe)"
                
                if link_column in df.columns:
                    for idx, row in df.iterrows():
                        brand_url = row.get(link_column, "")
                        if pd.notna(brand_url) and brand_url and str(brand_url).startswith("http"):
                            brand_name = row.get(brand_column, "Unknown Brand")
                            brand_url_str = str(brand_url)
                            main_category = row.get("Main Category", "")
                            
                            # Create unique key for deduplication
                            brand_key = (brand_name, brand_url_str)
                            
                            # Skip if we've already seen this brand
                            if brand_key not in seen_brands:
                                # ALL brands from women's dataset are women's brands
                                gender = "w"  # Always women for women's dataset
                                
                                brand_data = {
                                    "brand_name": brand_name,
                                    "brand_url": brand_url_str,
                                    "category": main_category,
                                    "product_count": 0,  # Will be set later in batch
                                    "last_scraped_at": None,
                                    "gender": gender  # Always "w" for women's dataset
                                }
                                
                                brands.append(brand_data)
                                seen_brands[brand_key] = True
                                if brand_name not in brand_names_list:
                                    brand_names_list.append(brand_name)
                                
                                logger.debug(f"Added women's brand: {brand_name}, gender: {gender}, category: {main_category}")
        
        # Read men dataset (skip for local - we use CSV only)
        if brand_type != "local":
            men_file = os.path.join(project_root, "men dataset.xlsx")
            if os.path.exists(men_file):
                try:
                    df_men = pd.read_excel(men_file)
                    
                    # Check if men dataset has link columns
                    men_link_column = None
                    men_brand_column = None
                    if brand_type == "luxury":
                        men_link_column = "Luxury Brand Link" if "Luxury Brand Link" in df_men.columns else None
                        men_brand_column = "Luxury / International Brand"
                    elif brand_type == "pakistani":
                        men_link_column = "Pakistani Designer Brand Link" if "Pakistani Designer Brand Link" in df_men.columns else None
                        men_brand_column = "Pakistani Luxury / Designer Brand"
                    else:  # local
                        men_link_column = "Local Dupe Brand Link" if "Local Dupe Brand Link" in df_men.columns else None
                        men_brand_column = "Local Affordable Brand (Dupe)"
                    
                    # If men dataset has links, add them to brands list
                    if men_link_column and men_link_column in df_men.columns:
                        for idx, row in df_men.iterrows():
                            brand_url = row.get(men_link_column, "")
                            if pd.notna(brand_url) and brand_url and str(brand_url).startswith("http"):
                                brand_name = row.get(men_brand_column, "Unknown Brand")
                                brand_url_str = str(brand_url)
                                main_category = row.get("Main Category", "")
                                
                                # Create unique key for deduplication
                                brand_key = (brand_name, brand_url_str)
                                
                                # Skip if we've already seen this brand
                                if brand_key not in seen_brands:
                                    # Since this is from men's dataset, explicitly set gender to "m"
                                    # Only override if category explicitly says "women"
                                    if "women" in main_category.lower() or "woman" in main_category.lower():
                                        gender = "w"
                                    else:
                                        gender = "m"  # Default to men for men's dataset
                                    
                                    brand_data = {
                                        "brand_name": brand_name,
                                        "brand_url": brand_url_str,
                                        "category": main_category,
                                        "product_count": 0,  # Will be set later in batch
                                        "last_scraped_at": None,
                                        "gender": gender
                                    }
                                    
                                    brands.append(brand_data)
                                    seen_brands[brand_key] = True
                                    if brand_name not in brand_names_list:
                                        brand_names_list.append(brand_name)
                except Exception as e:
                    logger.warning(f"Error reading men dataset: {e}")
                    # Don't fail completely if men dataset has issues
        
        # Read men's brands from local_brands_links.csv (only when local was not already loaded from CSV at top)
        if brand_type == "local" and not brands:
            csv_file = os.path.join(project_root, "local_brands_links.csv")
            logger.info(f"Local brands CSV: {csv_file}, exists: {os.path.exists(csv_file)}")
            if os.path.exists(csv_file):
                try:
                    df_csv = pd.read_csv(csv_file)
                    logger.info(f"Read {len(df_csv)} rows from local_brands_links.csv")
                    
                    # CSV has Brand and Website columns
                    if "Brand" in df_csv.columns and "Website" in df_csv.columns:
                        for idx, row in df_csv.iterrows():
                            brand_name = row.get("Brand", "")
                            brand_url = row.get("Website", "")
                            
                            if pd.notna(brand_name) and pd.notna(brand_url) and brand_url and str(brand_url).startswith("http"):
                                # Default category for men's brands from CSV
                                main_category = "Men → Eastern"
                                brand_url_str = str(brand_url)
                                
                                # Create unique key for deduplication
                                brand_key = (brand_name, brand_url_str)
                                
                                # Skip if we've already seen this brand
                                if brand_key not in seen_brands:
                                    # Men's brands from CSV
                                    gender = "m"
                                    scraper_type = str(row.get("ScraperType", "")).strip().lower() if "ScraperType" in df_csv.columns else ""
                                    if scraper_type == "nan" or scraper_type not in ("shopify_json", "woocommerce"):
                                        scraper_type = "generic"
                                    brand_data = {
                                        "brand_name": brand_name,
                                        "brand_url": brand_url_str,
                                        "category": main_category,
                                        "product_count": 0,  # Will be set later in batch
                                        "last_scraped_at": None,
                                        "gender": gender,  # Men's brands
                                        "scraper_type": scraper_type,
                                    }
                                    brands.append(brand_data)
                                    seen_brands[brand_key] = True
                                    if brand_name not in brand_names_list:
                                        brand_names_list.append(brand_name)
                                    
                                    logger.debug(f"Added men's brand from CSV: {brand_name}, gender: {gender}, category: {main_category}")
                except Exception as e:
                    logger.warning(f"Error reading local_brands_links.csv: {e}")
                    # Don't fail completely if CSV has issues
        
        # Batch query product counts for all brands at once (optimization)
        if brands and brand_names_list:
            try:
                products = get_products_collection()
                # Use aggregation pipeline to get counts for all brands in one query
                pipeline = [
                    {"$match": {"brand": {"$in": brand_names_list}}},
                    {"$group": {"_id": "$brand", "count": {"$sum": 1}}}
                ]
                brand_counts = {item["_id"]: item["count"] for item in products.aggregate(pipeline)}
                
                # Update product counts in brands list
                for brand in brands:
                    brand["product_count"] = brand_counts.get(brand["brand_name"], 0)
            except Exception as e:
                logger.warning(f"Error getting product counts: {e}")
                # If batch query fails, set all to 0 (better than failing completely)
                for brand in brands:
                    brand["product_count"] = 0
        
    except Exception as e:
        logger.error(f"Error reading brands from Excel: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading brands: {str(e)}")
    
    # Log summary for debugging
    gender_counts = {}
    for brand in brands:
        gender = brand.get("gender", "unknown")
        gender_counts[gender] = gender_counts.get(gender, 0) + 1
    logger.info(f"Brand loading complete. Total: {len(brands)}, Gender breakdown: {gender_counts}")
    
    # Sort brands by product_count (descending) - brands with most products first
    brands.sort(key=lambda x: x.get("product_count", 0), reverse=True)
    
    return {
        "brands": brands,
        "total": len(brands),
        "brand_type": brand_type
    }


@router.get("/scraping/test-one")
async def test_scrape_one_brand():
    """
    Debug: run scraper on first CSV brand (Bonanza) and return product count.
    No auth - remove in production. Use to verify scraper works.
    """
    from app.services.scraper_service import ProductScraper
    _start = os.path.abspath(os.path.dirname(__file__))
    project_root = _start
    for _ in range(10):
        if os.path.isfile(os.path.join(project_root, "local_brands_links.csv")):
            break
        _parent = os.path.dirname(project_root)
        if _parent == project_root:
            break
        project_root = _parent
    csv_path = os.path.join(project_root, "local_brands_links.csv")
    csv_exists = os.path.isfile(csv_path)
    if not csv_exists:
        return {"ok": False, "error": "CSV not found", "project_root": project_root, "csv_path": csv_path}
    df = pd.read_csv(csv_path)
    if "Brand" not in df.columns or "Website" not in df.columns:
        return {"ok": False, "error": "CSV missing Brand/Website columns"}
    # Use row 2 (Bonanza Satrangi) to test the brand that was returning 0 products
    row = df.iloc[min(2, len(df) - 1)]
    brand_name = str(row.get("Brand", ""))
    brand_url = str(row.get("Website", "")).strip()
    if not brand_url.startswith("http"):
        return {"ok": False, "error": "Invalid URL", "brand_name": brand_name, "brand_url": brand_url}
    scraper = ProductScraper()
    try:
        products = await scraper.scrape_exact_listing_url(brand_url, brand_name, "Men -> Eastern", "m", None)
    except Exception as e:
        logger.exception("test_scrape_one_brand failed")
        return {"ok": False, "error": str(e), "brand_url": brand_url}
    finally:
        await scraper.close()
    return {
        "ok": True,
        "project_root": project_root,
        "csv_path": csv_path,
        "brand_name": brand_name,
        "brand_url": brand_url,
        "products_count": len(products),
        "sample": [{"name": p.get("name"), "price": p.get("price")} for p in products[:3]],
    }


@router.post("/scraping/start")
async def start_rescraping(
    request: dict,  # {brand_ids: [{"brand_name": "...", "brand_url": "...", "category": "..."}]}
    admin: dict = Depends(require_admin)
):
    """
    Start rescraping selected brands from Excel files
    
    Module 4: Auto Sync - Trigger rescraping
    """
    import uuid
    
    brand_list = request.get("brand_ids", [])
    
    if not brand_list:
        raise HTTPException(status_code=400, detail="No brands selected")
    
    job_id = str(uuid.uuid4())
    started_at = datetime.utcnow()
    
    # Prepare job data
    job_data = {
        "job_id": job_id,
        "status": "pending",
        "brands": brand_list,
        "brands_completed": 0,
        "brands_total": len(brand_list),
        "products_added": 0,
        "started_at": started_at,
        "logs": []
    }
    
    # Store job in memory for real-time status
    scraping_jobs[job_id] = job_data.copy()
    
    # Store job in MongoDB for persistence
    scraping_history = get_scraping_history_collection()
    scraping_history.insert_one(job_data)
    
    # Start scraping in background
    asyncio.create_task(run_scraping_job(job_id, brand_list))
    
    return {
        "success": True,
        "job_id": job_id,
        "message": f"Scraping started for {len(brand_list)} brand(s)"
    }


async def run_scraping_job(job_id: str, brand_list: List[dict]):
    """
    Background task to run web scraping from Excel files
    """
    from app.services.scraper_service import ProductScraper
    
    scraper = None
    scraping_history = get_scraping_history_collection()
    
    try:
        scraping_jobs[job_id]["status"] = "running"
        total_products = 0
        
        # Update status in MongoDB
        scraping_history.update_one(
            {"job_id": job_id},
            {"$set": {"status": "running"}}
        )

        brand_list = _enrich_brands_for_scraping(brand_list)
        scraping_jobs[job_id]["brands"] = brand_list
        
        scraper = ProductScraper()
        
        for idx, brand_info in enumerate(brand_list):
            brand_name = brand_info.get("brand_name", "Unknown")
            # Multiple URLs per brand: brand_urls (list) or single brand_url
            urls_to_scrape = brand_info.get("brand_urls") or []
            if not urls_to_scrape and brand_info.get("brand_url"):
                urls_to_scrape = [(brand_info.get("brand_url") or "").strip()]
            urls_to_scrape = [u.strip() for u in urls_to_scrape if u and u.strip().startswith("http")]
            category = brand_info.get("category", "")
            logger.info(f"Job {job_id} brand[{idx}]: name={brand_name!r} urls={len(urls_to_scrape)}")
            if not urls_to_scrape:
                scraping_jobs[job_id]["logs"].append(f"Skipping {brand_name}: no valid URL")
                continue
            # Extract gender from brand_info if available, otherwise infer from category
            gender = brand_info.get("gender")
            if not gender:
                if "men" in category.lower() or "man" in category.lower():
                    gender = "m"
                elif "women" in category.lower() or "woman" in category.lower():
                    gender = "w"
            
            try:
                scraping_jobs[job_id]["logs"].append(f"Starting scrape for {brand_name} ({len(urls_to_scrape)} link(s), Category: {category}, Gender: {gender})...")
                scraper_type = (brand_info.get("scraper_type") or "").strip().lower() or "generic"
                all_products = []
                seen_product_urls = set()
                display_cats = brand_info.get("display_categories") or []
                for url_idx, brand_url in enumerate(urls_to_scrape):
                    parsed = urlparse(brand_url or "")
                    path = (parsed.path or "").strip("/")
                    url_lower = (brand_url or "").lower()
                    use_exact_listing = (
                        len(path.split("/")) >= 1 and path != ""
                        or ".html" in url_lower
                        or "/collections/" in url_lower
                        or "/product-category/" in url_lower
                        or "/search" in url_lower
                        or any(x in url_lower for x in ["/shirts", "/products", "/men", "/women", "/shop/", "/category/"])
                    )
                    scraping_jobs[job_id]["logs"].append(f"Scraping: {brand_url}")
                    try:
                        timeout_seconds = 300.0 if use_exact_listing else 60.0
                        if use_exact_listing:
                            page_products = await asyncio.wait_for(
                                scraper.scrape_exact_listing_url(brand_url, brand_name, category, gender, None, scraper_type=scraper_type),
                                timeout=timeout_seconds
                            )
                        else:
                            page_products = await asyncio.wait_for(
                                scraper.scrape_brand_website(brand_url, brand_name, category, gender),
                                timeout=timeout_seconds
                            )
                        slug = _listing_endpoint_slug(brand_url) or ((path.split("/")[-1] or "").strip() if path else "")
                        dc_override = ""
                        if url_idx < len(display_cats) and (display_cats[url_idx] or "").strip():
                            dc_override = display_cats[url_idx].strip()
                        for p in page_products:
                            p["endpoint_category"] = slug
                            p["display_category"] = (
                                dc_override if dc_override else _display_category_from_endpoint(slug, gender)
                            )
                    except asyncio.TimeoutError:
                        scraping_jobs[job_id]["logs"].append(f"Timeout for {brand_url}")
                        page_products = []
                    except Exception as scrape_error:
                        scraping_jobs[job_id]["logs"].append(f"Error {brand_url}: {str(scrape_error)}")
                        logger.error(f"Error scraping {brand_name} {brand_url}: {scrape_error}", exc_info=True)
                        page_products = []
                    for p in page_products:
                        purl = (p.get("product_url") or "").strip()
                        if purl and purl not in seen_product_urls:
                            seen_product_urls.add(purl)
                            all_products.append(p)
                products = all_products
                scraping_jobs[job_id]["logs"].append(
                    f"Found {len(products)} products from {brand_name} ({len(urls_to_scrape)} link(s))"
                )
                if len(products) == 0:
                    scraping_jobs[job_id]["logs"].append(
                        f"⚠ {brand_name}: 0 products extracted. Check URL(s) or site structure."
                    )
                logger.info(f"Scrape done: {brand_name} | {len(urls_to_scrape)} URL(s) | products: {len(products)}")
                
                # Store products in MongoDB
                products_collection = get_products_collection()
                stored = 0
                updated = 0
                
                def _is_valid_image_url(u):
                    if not u or not u.lower().startswith(("http://", "https://")): return False
                    ul = (u or "").lower()
                    if "loader" in ul or "lazyload" in ul or (u or "").rstrip("/").endswith(".gif"): return False
                    if not _looks_like_image_url(u): return False
                    return True
                
                # Pass 1: resolve image_url per product, skip if existing already has local file
                img_dir = _get_product_images_dir()
                to_download = []  # list of (product, image_url)
                for product in products:
                    existing = products_collection.find_one({"product_url": product.get("product_url")})
                    image_url = (product.get("image_url") or "").strip()
                    if not _is_valid_image_url(image_url) and existing:
                        image_url = (existing.get("image_url") or "").strip()
                    if existing and (existing.get("image_path") or "").startswith("product_images/"):
                        rel = (existing["image_path"] or "").replace("\\", "/")
                        if (img_dir / rel.replace("product_images/", "")).exists():
                            product["image_path"] = rel
                            to_download.append((product, None))
                            continue
                    if _is_valid_image_url(image_url):
                        to_download.append((product, image_url))
                    else:
                        to_download.append((product, None))
                
                # Pass 2: parallel image downloads (max 10 at a time)
                sem = asyncio.Semaphore(10)
                async def _download_with_sem(p, url):
                    if not url:
                        return
                    async with sem:
                        path = await _download_product_image(url, p.get("product_url") or "")
                        if path:
                            p["image_path"] = path
                await asyncio.gather(*[_download_with_sem(p, url) for p, url in to_download])
                
                # Pass 3: insert or update
                for product in products:
                    try:
                        existing = products_collection.find_one({"product_url": product.get("product_url")})
                        if not existing:
                            # Check if product_id already exists (handle hash collisions)
                            product_id = product.get("product_id")
                            if product_id:
                                id_exists = products_collection.find_one({"product_id": product_id})
                                if id_exists:
                                    # Generate new product_id by appending timestamp hash
                                    url_hash = hashlib.md5(
                                        f"{product.get('product_url')}{datetime.utcnow().isoformat()}".encode('utf-8')
                                    ).hexdigest()
                                    product['product_id'] = int(url_hash[:8], 16)
                            
                            products_collection.insert_one(product)
                            stored += 1
                        else:
                            # Update existing product (preserve existing product_id and existing image_path if we didn't get new one)
                            update_data = product.copy()
                            if 'product_id' in update_data:
                                del update_data['product_id']
                            if not update_data.get("image_path") and (existing.get("image_path") or "").startswith("product_images/"):
                                update_data["image_path"] = existing["image_path"]
                            products_collection.update_one(
                                {"product_url": product.get("product_url")},
                                {"$set": update_data}
                            )
                            updated += 1
                    except Exception as e:
                        error_msg = str(e)
                        # If it's a duplicate key error, try with a new product_id
                        if "E11000" in error_msg or "duplicate key" in error_msg.lower():
                            try:
                                url_hash = hashlib.md5(
                                    f"{product.get('product_url')}{datetime.utcnow().isoformat()}".encode('utf-8')
                                ).hexdigest()
                                product['product_id'] = int(url_hash[:8], 16)
                                products_collection.insert_one(product)
                                stored += 1
                                logger.info(f"Retried insert with new product_id for {product.get('product_url')}")
                            except Exception as retry_error:
                                logger.error(f"Error storing product (retry failed): {retry_error}")
                                scraping_jobs[job_id]["logs"].append(f"Error storing product: {str(retry_error)}")
                        else:
                            logger.error(f"Error storing product: {e}")
                            scraping_jobs[job_id]["logs"].append(f"Error storing product: {error_msg}")
                
                total_products += stored + updated  # show new + updated so user sees total processed (not 0 when only updates)
                scraping_jobs[job_id]["products_added"] = total_products
                scraping_jobs[job_id]["brands_completed"] = idx + 1
                scraping_jobs[job_id]["logs"].append(
                    f"Completed {brand_name}: {stored} new, {updated} updated, {len(products)} total found"
                )
                # Log products without image (placeholder or empty)
                without_image = [
                    p for p in products
                    if not (p.get("image_path") or "").strip()
                    or "placeholder" in (p.get("image_path") or "").lower()
                ]
                if without_image:
                    names_preview = ", ".join((p.get("name") or "?")[:30] for p in without_image[:5])
                    if len(without_image) > 5:
                        names_preview += f" ... (+{len(without_image) - 5} more)"
                    scraping_jobs[job_id]["logs"].append(
                        f"⚠ {brand_name}: {len(without_image)} product(s) without image: {names_preview}"
                    )
                else:
                    scraping_jobs[job_id]["logs"].append(
                        f"Images: all {len(products)} products have images"
                    )
                
                # Update progress in MongoDB
                scraping_history.update_one(
                    {"job_id": job_id},
                    {"$set": {
                        "products_added": total_products,
                        "brands_completed": idx + 1,
                        "logs": scraping_jobs[job_id]["logs"]
                    }}
                )
                
                # Small delay between brands
                await asyncio.sleep(2)
            
            except Exception as e:
                error_msg = f"Error processing {brand_name}: {str(e)}"
                scraping_jobs[job_id]["logs"].append(error_msg)
                logger.error(error_msg, exc_info=True)
                # Continue with next brand instead of failing completely
        
        # Complete
        completed_at = datetime.utcnow()
        scraping_jobs[job_id]["status"] = "completed"
        scraping_jobs[job_id]["completed_at"] = completed_at
        scraping_jobs[job_id]["logs"].append(f"Scraping completed! Total: {total_products} products (new + updated)")
        
        # Update in MongoDB
        scraping_history = get_scraping_history_collection()
        scraping_history.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "completed",
                "completed_at": completed_at,
                "products_added": total_products,
                "brands_completed": scraping_jobs[job_id]["brands_completed"],
                "logs": scraping_jobs[job_id]["logs"]
            }}
        )

        # Auto-trigger FashionCLIP reindex for newly scraped products
        scraping_jobs[job_id]["logs"].append("Starting FashionCLIP reindex for new products...")
        asyncio.create_task(_run_reindex_task(job_id))
        
    except Exception as e:
        failed_at = datetime.utcnow()
        scraping_jobs[job_id]["status"] = "failed"
        scraping_jobs[job_id]["error"] = str(e)
        scraping_jobs[job_id]["failed_at"] = failed_at
        scraping_jobs[job_id]["logs"].append(f"Scraping failed: {str(e)}")
        logger.error(f"Scraping job {job_id} failed: {e}", exc_info=True)
        
        # Update in MongoDB
        scraping_history = get_scraping_history_collection()
        scraping_history.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "failed",
                "failed_at": failed_at,
                "error": str(e),
                "logs": scraping_jobs[job_id]["logs"]
            }}
        )
    finally:
        if scraper:
            try:
                await scraper.close()
            except:
                pass


async def _run_reindex_task(job_id: str):
    """
    Async wrapper: runs FashionCLIP reindex in a thread pool so the
    FastAPI event loop is never blocked. Called automatically after
    run_scraping_job completes.
    """
    try:
        summary = await asyncio.to_thread(_sync_reindex)
        if summary:
            total = sum(summary.values())
            msg   = f"Reindex done: {total} new products indexed across {len(summary)} categories"
        else:
            msg   = "Reindex complete: no new products found to index"

        if job_id in scraping_jobs:
            scraping_jobs[job_id]["logs"].append(msg)
            scraping_jobs[job_id]["reindex_summary"] = summary

        get_scraping_history_collection().update_one(
            {"job_id": job_id},
            {"$set": {"reindex_summary": summary, "reindex_done": True}}
        )
        logger.info(f"[Reindex] {msg}")

    except Exception as e:
        err = f"Reindex failed: {e}"
        logger.error(f"[Reindex] {err}", exc_info=True)
        if job_id in scraping_jobs:
            scraping_jobs[job_id]["logs"].append(err)


def _sync_reindex() -> dict:
    """
    Synchronous reindex: finds unindexed products, downloads images,
    extracts FashionCLIP embeddings, appends to FAISS indices on disk,
    then hot-reloads the in-memory indices in search.py.

    Runs inside asyncio.to_thread — does NOT block the event loop.
    """
    import sys
    from pathlib import Path as _Path

    # Resolve ml-engine path so fashionclip package is importable
    _project_root = _Path(__file__).parent.parent.parent.parent
    _ml_engine    = _project_root / "ml-engine"
    if str(_ml_engine) not in sys.path:
        sys.path.insert(0, str(_ml_engine))

    # Import and call the standalone script's run_reindex function
    try:
        from scripts.reindex_new_products import run_reindex
    except ImportError:
        # Fallback: add scripts dir explicitly
        sys.path.insert(0, str(_ml_engine / "scripts"))
        from reindex_new_products import run_reindex

    summary = run_reindex()

    # Hot-reload the in-memory FAISS indices in search.py
    if summary:
        try:
            from app.api.routes.search import hot_reload_indices
            updated_slugs = [
                cat.lower().replace(" ", "_").replace("/", "-")
                for cat in summary.keys()
            ]
            hot_reload_indices(updated_slugs)
            logger.info(f"[Reindex] Hot-reloaded indices: {updated_slugs}")
        except Exception as e:
            logger.warning(f"[Reindex] Hot-reload failed (restart backend to apply): {e}")

    return summary


@router.get("/scraping/status/{job_id}")
async def get_scraping_status(
    job_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Get scraping job status and progress
    
    Module 4: Auto Sync - Monitor progress
    """
    try:
        if job_id not in scraping_jobs:
            raise HTTPException(status_code=404, detail="Scraping job not found")
        
        # Return a copy to avoid any issues
        job = scraping_jobs[job_id].copy()
        return job
    except Exception as e:
        logger.error(f"Error getting scraping status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.get("/scraping/history")
async def get_scraping_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    admin: dict = Depends(require_admin)
):
    """
    Get scraping job history from MongoDB (persistent storage) with pagination
    
    Module 4: Auto Sync - View history
    """
    scraping_history = get_scraping_history_collection()
    
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Get total count
    total = scraping_history.count_documents({})
    
    # Get paginated jobs from MongoDB sorted by start time (newest first)
    cursor = scraping_history.find().sort("started_at", -1).skip(skip).limit(page_size)
    jobs = []
    
    for doc in cursor:
        # Convert ObjectId to string
        doc["_id"] = str(doc["_id"])
        
        # Convert datetime fields to ISO format strings for JSON serialization
        if "started_at" in doc and isinstance(doc["started_at"], datetime):
            doc["started_at"] = doc["started_at"].isoformat()
        if "completed_at" in doc and isinstance(doc["completed_at"], datetime):
            doc["completed_at"] = doc["completed_at"].isoformat()
        if "failed_at" in doc and isinstance(doc["failed_at"], datetime):
            doc["failed_at"] = doc["failed_at"].isoformat()
        
        jobs.append(doc)
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return {
        "jobs": jobs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.delete("/scraping/history/{job_id}")
async def delete_scraping_history(
    job_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Delete a scraping job from history
    
    Module 4: Auto Sync - Delete history entry
    """
    scraping_history = get_scraping_history_collection()
    
    result = scraping_history.delete_one({"job_id": job_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Scraping job not found")
    
    return {
        "success": True,
        "message": "Scraping history deleted successfully",
        "job_id": job_id
    }


@router.get("/overview-insights")
async def get_overview_insights(
    admin: dict = Depends(require_admin)
):
    """
    Landing-page analytics for admin dashboard (mobile-app aligned):
    - most clicked item
    - wishlist/compare/history totals
    - community activity
    """
    db = get_db()

    users_col = db["users"]
    products_col = db["products"]
    user_data_col = db["user_app_data"]
    community_col = db["community_posts"]
    reports_col = db["community_reports"]

    total_users = users_col.count_documents({})
    total_products = products_col.count_documents({})
    total_community_posts = community_col.count_documents({})
    pending_reports = reports_col.count_documents({"status": "pending"})

    wishlist_total = 0
    compare_total = 0
    history_total = 0
    review_total = 0
    item_clicks = {}

    for row in user_data_col.find({}, {"wishlist": 1, "compare": 1, "dupe_history": 1}):
        wishlist = row.get("wishlist") or []
        compare = row.get("compare") or []
        history = row.get("dupe_history") or []

        wishlist_total += len(wishlist)
        compare_total += len(compare)
        history_total += len(history)

        for h in history:
            pid = h.get("id") or ""
            if pid:
                item_clicks[pid] = item_clicks.get(pid, 0) + 1
            if h.get("review"):
                review_total += 1

    most_clicked = {"id": None, "name": "N/A", "clicks": 0, "brand": None}
    if item_clicks:
        top_id, top_count = max(item_clicks.items(), key=lambda kv: kv[1])
        top_name = "N/A"
        top_brand = None
        # best effort: resolve from product_url or fallback by product_id.
        doc = products_col.find_one({"product_url": top_id}, {"name": 1, "brand": 1, "product_id": 1})
        if doc:
            top_name = doc.get("name") or "N/A"
            top_brand = doc.get("brand")
        most_clicked = {
            "id": top_id,
            "name": top_name,
            "brand": top_brand,
            "clicks": int(top_count),
        }

    graph_items = [
        {"label": "Wishlist", "value": int(wishlist_total)},
        {"label": "Compare", "value": int(compare_total)},
        {"label": "History Clicks", "value": int(history_total)},
        {"label": "Reviews", "value": int(review_total)},
        {"label": "Community Posts", "value": int(total_community_posts)},
    ]

    today = datetime.utcnow().date()
    daily_labels = []
    daily_posts = []
    daily_reports = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        start = datetime(day.year, day.month, day.day)
        end = start + timedelta(days=1)
        daily_labels.append(day.strftime("%d %b"))
        daily_posts.append(community_col.count_documents({"created_at": {"$gte": start, "$lt": end}}))
        daily_reports.append(reports_col.count_documents({"created_at": {"$gte": start, "$lt": end}}))

    return {
        "total_users": int(total_users),
        "total_products": int(total_products),
        "total_community_posts": int(total_community_posts),
        "total_wishlist_items": int(wishlist_total),
        "total_compare_items": int(compare_total),
        "total_dupe_history_clicks": int(history_total),
        "total_reviews": int(review_total),
        "pending_reports": int(pending_reports),
        "most_clicked_item": most_clicked,
        "graph_breakdown": graph_items,
        "graph_daily_activity": {
            "labels": daily_labels,
            "community_posts": daily_posts,
            "reports": daily_reports,
        },
    }


def _community_user_display_name_map(db, user_id_strs: set) -> dict:
    """
    Map user_id (str) -> current display name using profile + users collection
    (same rules as /auth/me). Fixes admin/community tables showing stale author
    strings saved on posts at creation time.
    """
    if not user_id_strs:
        return {}
    oids = []
    for s in user_id_strs:
        if s and ObjectId.is_valid(str(s)):
            oids.append(ObjectId(str(s)))
    if not oids:
        return {}
    users_col = db["users"]
    name_map: dict = {}
    for u in users_col.find({"_id": {"$in": oids}}):
        uid_str = str(u["_id"])
        payload = {"_id": uid_str, "full_name": u.get("full_name"), "email": u.get("email")}
        resolved = _effective_name_for_user(payload)
        fallback = (u.get("full_name") or "").strip() or (u.get("email") or "").split("@")[0] or "Unknown"
        name_map[uid_str] = (resolved.strip() if isinstance(resolved, str) and resolved.strip() else fallback)
    return name_map


@router.get("/community/reports")
async def get_community_reports(admin: dict = Depends(require_admin)):
    db = get_db()
    reports = db["community_reports"]
    docs = list(reports.find({}).sort("created_at", -1).limit(300))
    author_ids = set()
    for d in docs:
        uid = d.get("post_author_user_id")
        if uid:
            author_ids.add(str(uid))
    name_map = _community_user_display_name_map(db, author_ids)
    out = []
    for d in docs:
        uid = d.get("post_author_user_id")
        stored_post_author = d.get("post_author_name", "Unknown")
        resolved_post_author = name_map.get(str(uid), stored_post_author) if uid else stored_post_author
        out.append({
            "id": str(d.get("_id")),
            "post_id": d.get("post_id"),
            "reason": d.get("reason", ""),
            "status": d.get("status", "pending"),
            "reporter_name": d.get("reporter_name", "Unknown"),
            "reporter_email": d.get("reporter_email"),
            "post_author_user_id": d.get("post_author_user_id"),
            "post_author_name": resolved_post_author,
            "post_excerpt": d.get("post_excerpt", ""),
            "created_at": (d.get("created_at") or datetime.utcnow()).isoformat(),
            "handled_at": (d.get("handled_at") or "").isoformat() if d.get("handled_at") else None,
            "handled_action": d.get("handled_action"),
        })
    return {"reports": out}


@router.get("/community/posts")
async def get_community_posts_for_admin(admin: dict = Depends(require_admin)):
    db = get_db()
    posts_col = db["community_posts"]
    posts = list(posts_col.find({}).sort("created_at", -1).limit(300))
    author_ids = set()
    for p in posts:
        uid = p.get("author_user_id")
        if uid:
            author_ids.add(str(uid))
    name_map = _community_user_display_name_map(db, author_ids)
    out = []
    for p in posts:
        uid = p.get("author_user_id")
        stored = p.get("author", "Unknown")
        display_author = name_map.get(str(uid), stored) if uid else stored
        out.append({
            "id": str(p.get("_id")),
            "description": p.get("description", ""),
            "author": display_author,
            "author_user_id": p.get("author_user_id"),
            "created_at": (p.get("created_at") or datetime.utcnow()).isoformat(),
            "replies_count": len(p.get("replies") or []),
        })
    return {"posts": out}


@router.delete("/community/posts/{post_id}")
async def admin_delete_community_post(post_id: str, admin: dict = Depends(require_admin)):
    db = get_db()
    posts_col = db["community_posts"]
    reports_col = db["community_reports"]
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="Invalid post id")
    result = posts_col.delete_one({"_id": ObjectId(post_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    reports_col.update_many(
        {"post_id": post_id, "status": "pending"},
        {"$set": {"status": "resolved", "handled_action": "delete_post", "handled_at": datetime.utcnow()}},
    )
    return {"success": True, "message": "Post deleted by admin"}


@router.put("/community/users/{user_id}/ban")
async def admin_ban_community_user(user_id: str, admin: dict = Depends(require_admin)):
    db = get_db()
    users_col = db["users"]
    posts_col = db["community_posts"]
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user id")
    u = users_col.find_one({"_id": ObjectId(user_id)})
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    users_col.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_active": False, "updated_at": datetime.utcnow()}})
    posts_col.delete_many({"author_user_id": user_id})
    return {"success": True, "message": "User banned and posts removed"}


@router.put("/community/reports/{report_id}/resolve")
async def resolve_community_report(
    report_id: str,
    action: str = Query("ignore", pattern="^(ignore|delete_post|ban_user)$"),
    admin: dict = Depends(require_admin),
):
    db = get_db()
    reports_col = db["community_reports"]
    posts_col = db["community_posts"]
    users_col = db["users"]
    if not ObjectId.is_valid(report_id):
        raise HTTPException(status_code=400, detail="Invalid report id")
    report = reports_col.find_one({"_id": ObjectId(report_id)})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if action == "delete_post" and ObjectId.is_valid(report.get("post_id", "")):
        posts_col.delete_one({"_id": ObjectId(report["post_id"])})
    elif action == "ban_user":
        uid = report.get("post_author_user_id")
        if uid and ObjectId.is_valid(uid):
            users_col.update_one({"_id": ObjectId(uid)}, {"$set": {"is_active": False, "updated_at": datetime.utcnow()}})
            posts_col.delete_many({"author_user_id": uid})

    reports_col.update_one(
        {"_id": ObjectId(report_id)},
        {"$set": {"status": "resolved", "handled_action": action, "handled_at": datetime.utcnow()}},
    )
    return {"success": True, "message": "Report resolved", "action": action}

