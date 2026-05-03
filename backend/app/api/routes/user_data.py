"""
User data persistence routes (wishlist, compare, dupe history).
Data is stored per authenticated user in MongoDB.
"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, Field
from bson import ObjectId

from app.core.database import db_manager
from app.dependencies.auth import get_current_user

router = APIRouter(tags=["User Data"])

USER_DATA_COLLECTION = "user_app_data"


class JsonListPayload(BaseModel):
    items: List[Dict[str, Any]] = Field(default_factory=list)

class ProfilePayload(BaseModel):
    display_name: str | None = None
    profile_image: str | None = None


class ImageSearchPayload(BaseModel):
    """Optional category label from image search (for per-user insights)."""
    category: str | None = None


def _col():
    if not db_manager.is_connected():
        raise RuntimeError("Database not connected")
    return db_manager.get_collection(USER_DATA_COLLECTION)


def _ensure_doc(user_id: str) -> Dict[str, Any]:
    c = _col()
    doc = c.find_one({"user_id": user_id})
    if doc is None:
        base = {
            "user_id": user_id,
            "wishlist": [],
            "compare": [],
            "dupe_history": [],
            "image_search_count": 0,
            "search_category_history": [],
            "display_name": None,
            "profile_image": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        c.insert_one(base)
        doc = c.find_one({"user_id": user_id})
    return doc


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "wishlist": doc.get("wishlist", []),
        "compare": doc.get("compare", []),
        "dupe_history": doc.get("dupe_history", []),
        "image_search_count": int(doc.get("image_search_count") or 0),
        "search_category_history": list(doc.get("search_category_history") or []),
        "display_name": doc.get("display_name"),
        "profile_image": doc.get("profile_image"),
    }


@router.get("")
async def get_user_data(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user["_id"]
    doc = _ensure_doc(user_id)
    return _serialize(doc)


@router.put("/wishlist")
async def put_wishlist(
    payload: JsonListPayload,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user["_id"]
    _ensure_doc(user_id)
    _col().update_one(
        {"user_id": user_id},
        {"$set": {"wishlist": payload.items, "updated_at": datetime.utcnow()}},
    )
    return {"ok": True, "count": len(payload.items)}


@router.put("/compare")
async def put_compare(
    payload: JsonListPayload,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user["_id"]
    _ensure_doc(user_id)
    _col().update_one(
        {"user_id": user_id},
        {"$set": {"compare": payload.items, "updated_at": datetime.utcnow()}},
    )
    return {"ok": True, "count": len(payload.items)}


@router.put("/dupe-history")
async def put_dupe_history(
    payload: JsonListPayload,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user["_id"]
    _ensure_doc(user_id)
    _col().update_one(
        {"user_id": user_id},
        {"$set": {"dupe_history": payload.items, "updated_at": datetime.utcnow()}},
    )
    return {"ok": True, "count": len(payload.items)}


@router.post("/analytics/image-search")
async def record_image_search(
    current_user: Dict[str, Any] = Depends(get_current_user),
    payload: ImageSearchPayload = Body(default_factory=ImageSearchPayload),
):
    """Increment per-user image search count; optionally append category for insights."""
    user_id = current_user["_id"]
    _ensure_doc(user_id)
    c = _col()
    p = payload
    cat = (p.category or "").strip()
    now = datetime.utcnow()
    update: Dict[str, Any] = {
        "$inc": {"image_search_count": 1},
        "$set": {"updated_at": now},
    }
    if cat:
        update["$push"] = {
            "search_category_history": {"$each": [cat], "$slice": -400},
        }
    c.update_one({"user_id": user_id}, update)
    doc = c.find_one({"user_id": user_id})
    n = int((doc or {}).get("image_search_count") or 0)
    return {"ok": True, "image_search_count": n}


@router.get("/profile")
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user["_id"]
    doc = _ensure_doc(user_id)
    display_name = (doc.get("display_name") or "").strip() or (current_user.get("full_name") or "")
    profile_image = doc.get("profile_image")
    return {
        "display_name": display_name,
        "profile_image": profile_image,
    }


@router.put("/profile")
async def put_user_profile(
    payload: ProfilePayload,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user["_id"]
    _ensure_doc(user_id)
    set_doc: Dict[str, Any] = {"updated_at": datetime.utcnow()}
    if payload.display_name is not None:
        set_doc["display_name"] = payload.display_name.strip() or None
    if payload.profile_image is not None:
        set_doc["profile_image"] = payload.profile_image
    _col().update_one(
        {"user_id": user_id},
        {"$set": set_doc},
    )

    # Keep auth user full_name aligned with mobile profile edit.
    if payload.display_name is not None:
        users = db_manager.get_collection("users")
        uid = current_user.get("_id")
        if isinstance(uid, str) and ObjectId.is_valid(uid):
            users.update_one(
                {"_id": ObjectId(uid)},
                {"$set": {"full_name": payload.display_name.strip() or None, "updated_at": datetime.utcnow()}},
            )
        else:
            users.update_one(
                {"email": current_user.get("email")},
                {"$set": {"full_name": payload.display_name.strip() or None, "updated_at": datetime.utcnow()}},
            )
    return {"ok": True}
