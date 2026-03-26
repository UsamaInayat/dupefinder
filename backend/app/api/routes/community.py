"""
Community routes: persistent feed + replies backed by MongoDB.
Posts are kept for 7 days.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from bson import ObjectId

from app.core.database import db_manager
from app.dependencies.auth import get_current_user, get_optional_user

router = APIRouter(tags=["Community"])

COMMUNITY_COLLECTION = "community_posts"
COMMUNITY_REPORTS_COLLECTION = "community_reports"
RETENTION_DAYS = 7
_index_ready = False


class CommunityReplyIn(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)
    author: Optional[str] = "Anonymous"
    author_pfp: Optional[str] = None


class CommunityPostIn(BaseModel):
    description: str = Field(..., min_length=1, max_length=4000)
    author: Optional[str] = "You"
    author_pfp: Optional[str] = None
    image_base64: Optional[str] = None


class CommunityReportIn(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)

class CommunityPostUpdateIn(BaseModel):
    description: str = Field(..., min_length=1, max_length=4000)


def _col():
    if not db_manager.is_connected():
        raise RuntimeError("Database not connected")
    return db_manager.get_collection(COMMUNITY_COLLECTION)


def _reports_col():
    if not db_manager.is_connected():
        raise RuntimeError("Database not connected")
    return db_manager.get_collection(COMMUNITY_REPORTS_COLLECTION)


def _ensure_indexes():
    global _index_ready
    if _index_ready:
        return
    c = _col()
    # Auto-delete posts older than 7 days.
    c.create_index("created_at", expireAfterSeconds=RETENTION_DAYS * 24 * 60 * 60)
    c.create_index([("created_at", -1)])
    c.create_index([("author_user_id", 1)])
    c.create_index([("replies.author_user_id", 1)])
    r = _reports_col()
    r.create_index([("post_id", 1)])
    r.create_index([("status", 1), ("created_at", -1)])
    _index_ready = True


def _serialize(doc: dict) -> dict:
    return {
        "id": str(doc.get("_id")),
        "description": doc.get("description", ""),
        "author": doc.get("author", "You"),
        "authorPfp": doc.get("author_pfp"),
        "imageBase64": doc.get("image_base64"),
        "createdAt": (doc.get("created_at") or datetime.utcnow()).isoformat(),
        "authorUserId": doc.get("author_user_id"),
        "replies": [
            {
                "id": r.get("id"),
                "body": r.get("body", ""),
                "author": r.get("author", "Anonymous"),
                "authorPfp": r.get("author_pfp"),
                "createdAt": (r.get("created_at") or datetime.utcnow()).isoformat(),
                "authorUserId": r.get("author_user_id"),
            }
            for r in (doc.get("replies") or [])
        ],
    }


@router.get("/posts")
async def get_posts():
    _ensure_indexes()
    c = _col()
    # Defensive cleanup in addition to TTL monitor.
    c.delete_many({"created_at": {"$lt": datetime.utcnow() - timedelta(days=RETENTION_DAYS)}})
    docs: List[dict] = list(c.find({}).sort("created_at", -1))
    return {"posts": [_serialize(d) for d in docs]}


@router.post("/posts")
async def add_post(payload: CommunityPostIn, current_user: Optional[dict] = Depends(get_optional_user)):
    _ensure_indexes()
    c = _col()
    resolved_author = (payload.author or "You").strip() or "You"
    author_user_id = None
    author_email = None
    if current_user:
        author_user_id = current_user.get("_id")
        author_email = current_user.get("email")
        resolved_author = (current_user.get("full_name") or current_user.get("email") or resolved_author).strip()
    doc = {
        "description": payload.description.strip(),
        "author": resolved_author,
        "author_user_id": author_user_id,
        "author_email": author_email,
        "author_pfp": payload.author_pfp,
        "image_base64": payload.image_base64,
        "created_at": datetime.utcnow(),
        "replies": [],
    }
    result = c.insert_one(doc)
    created = c.find_one({"_id": result.inserted_id})
    return {"post": _serialize(created)}


@router.post("/posts/{post_id}/replies")
async def add_reply(post_id: str, payload: CommunityReplyIn, current_user: Optional[dict] = Depends(get_optional_user)):
    _ensure_indexes()
    c = _col()
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="Invalid post id")
    resolved_author = (payload.author or "Anonymous").strip() or "Anonymous"
    author_user_id = None
    author_email = None
    if current_user:
        author_user_id = current_user.get("_id")
        author_email = current_user.get("email")
        resolved_author = (current_user.get("full_name") or current_user.get("email") or resolved_author).strip()
    reply_doc = {
        "id": str(ObjectId()),
        "body": payload.body.strip(),
        "author": resolved_author,
        "author_pfp": payload.author_pfp,
        "author_user_id": author_user_id,
        "author_email": author_email,
        "created_at": datetime.utcnow(),
    }
    result = c.update_one(
        {"_id": ObjectId(post_id)},
        {"$push": {"replies": reply_doc}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    updated = c.find_one({"_id": ObjectId(post_id)})
    return {"post": _serialize(updated)}


@router.delete("/posts/{post_id}/replies/{reply_id}")
async def delete_own_reply(
    post_id: str,
    reply_id: str,
    current_user: dict = Depends(get_current_user),
):
    _ensure_indexes()
    c = _col()
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="Invalid post id")
    post = c.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    reply = None
    for r in (post.get("replies") or []):
        if (r.get("id") or "") == reply_id:
            reply = r
            break
    if reply is None:
        raise HTTPException(status_code=404, detail="Reply not found")

    is_owner_by_id = reply.get("author_user_id") == current_user.get("_id")
    current_name = ((current_user.get("full_name") or current_user.get("email") or "").strip().lower())
    reply_author = (reply.get("author") or "").strip().lower()
    is_owner_by_name = bool(current_name) and reply_author == current_name
    if not (is_owner_by_id or is_owner_by_name):
        raise HTTPException(status_code=403, detail="You can only delete your own reply")

    c.update_one(
        {"_id": ObjectId(post_id)},
        {"$pull": {"replies": {"id": reply_id}}},
    )
    updated = c.find_one({"_id": ObjectId(post_id)})
    return {"post": _serialize(updated), "success": True}


@router.delete("/posts/{post_id}")
async def delete_own_post(post_id: str, current_user: dict = Depends(get_current_user)):
    _ensure_indexes()
    c = _col()
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="Invalid post id")
    post = c.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.get("author_user_id") != current_user.get("_id"):
        raise HTTPException(status_code=403, detail="You can only delete your own post")
    c.delete_one({"_id": ObjectId(post_id)})
    return {"success": True, "message": "Post deleted"}


@router.put("/posts/{post_id}")
async def edit_own_post(post_id: str, payload: CommunityPostUpdateIn, current_user: dict = Depends(get_current_user)):
    _ensure_indexes()
    c = _col()
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="Invalid post id")
    post = c.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    is_owner_by_id = post.get("author_user_id") == current_user.get("_id")
    is_owner_by_author = (post.get("author") or "").strip().lower() == (
        (current_user.get("full_name") or current_user.get("email") or "").strip().lower()
    )
    if not (is_owner_by_id or is_owner_by_author):
        raise HTTPException(status_code=403, detail="You can only edit your own post")
    c.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"description": payload.description.strip(), "updated_at": datetime.utcnow()}},
    )
    updated = c.find_one({"_id": ObjectId(post_id)})
    return {"post": _serialize(updated)}


@router.post("/posts/{post_id}/report")
async def report_post(post_id: str, payload: CommunityReportIn, current_user: dict = Depends(get_current_user)):
    _ensure_indexes()
    c = _col()
    r = _reports_col()
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="Invalid post id")
    post = c.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    reporter_id = current_user.get("_id")
    existing = r.find_one({"post_id": post_id, "reporter_user_id": reporter_id, "status": "pending"})
    if existing:
        return {"success": True, "message": "Already reported", "report_id": str(existing["_id"])}
    doc = {
        "post_id": post_id,
        "reason": payload.reason.strip(),
        "status": "pending",
        "reporter_user_id": reporter_id,
        "reporter_name": current_user.get("full_name") or current_user.get("email"),
        "reporter_email": current_user.get("email"),
        "post_author_user_id": post.get("author_user_id"),
        "post_author_name": post.get("author"),
        "post_excerpt": (post.get("description") or "")[:300],
        "created_at": datetime.utcnow(),
    }
    out = r.insert_one(doc)
    return {"success": True, "report_id": str(out.inserted_id)}
