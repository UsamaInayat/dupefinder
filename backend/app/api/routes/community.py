"""
Community routes: persistent feed + replies backed by MongoDB.
Posts are kept for 7 days.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel, Field
from bson import ObjectId

from app.core.database import db_manager
from app.dependencies.auth import get_current_user, get_optional_user

router = APIRouter(tags=["Community"])

COMMUNITY_COLLECTION = "community_posts"
COMMUNITY_REPORTS_COLLECTION = "community_reports"
COMMUNITY_NOTIFICATIONS_COLLECTION = "community_notifications"
COMMUNITY_BLOCKS_COLLECTION = "community_user_blocks"
RETENTION_DAYS = 7
_index_ready = False


class CommunityReplyIn(BaseModel):
    body: str = Field(..., min_length=1, max_length=2000)
    author: Optional[str] = "Anonymous"
    author_pfp: Optional[str] = None
    parent_reply_id: Optional[str] = None


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


def _notifications_col():
    if not db_manager.is_connected():
        raise RuntimeError("Database not connected")
    return db_manager.get_collection(COMMUNITY_NOTIFICATIONS_COLLECTION)


def _blocks_col():
    if not db_manager.is_connected():
        raise RuntimeError("Database not connected")
    return db_manager.get_collection(COMMUNITY_BLOCKS_COLLECTION)


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
    n = _notifications_col()
    n.create_index([("recipient_user_id", 1), ("is_read", 1), ("created_at", -1)])
    n.create_index([("post_id", 1), ("reply_id", 1)])
    n.create_index([("created_at", -1)])
    b = _blocks_col()
    b.create_index([("blocker_user_id", 1), ("blocked_user_id", 1)], unique=True)
    b.create_index([("blocker_user_id", 1)])
    _index_ready = True


def _viewer_like_key(current_user: Optional[dict], device_id: Optional[str]) -> Optional[str]:
    if current_user and current_user.get("_id"):
        return f"u:{current_user.get('_id')}"
    d = (device_id or "").strip()
    if len(d) >= 8:
        return f"d:{d}"
    return None


def _device_id_from_request(request: Request) -> Optional[str]:
    return request.headers.get("x-community-like-id") or request.headers.get("X-Community-Like-Id")


def _serialize(doc: dict, viewer_like_key: Optional[str] = None) -> dict:
    like_keys = list(doc.get("like_keys") or [])
    liked = bool(viewer_like_key and viewer_like_key in like_keys)
    return {
        "id": str(doc.get("_id")),
        "description": doc.get("description", ""),
        "author": doc.get("author", "You"),
        "authorPfp": doc.get("author_pfp"),
        "imageBase64": doc.get("image_base64"),
        "createdAt": (doc.get("created_at") or datetime.utcnow()).isoformat(),
        "authorUserId": doc.get("author_user_id"),
        "likeCount": len(like_keys),
        "likedByMe": liked,
        "replies": [
            {
                "id": r.get("id"),
                "body": r.get("body", ""),
                "author": r.get("author", "Anonymous"),
                "authorPfp": r.get("author_pfp"),
                "createdAt": (r.get("created_at") or datetime.utcnow()).isoformat(),
                "authorUserId": r.get("author_user_id"),
                "parentReplyId": r.get("parent_reply_id"),
            }
            for r in (doc.get("replies") or [])
        ],
    }

def _serialize_notification(doc: dict) -> dict:
    return {
        "id": str(doc.get("_id")),
        "recipientUserId": doc.get("recipient_user_id"),
        "postId": doc.get("post_id"),
        "replyId": doc.get("reply_id"),
        "message": doc.get("message", "Someone replied to your post"),
        "isRead": bool(doc.get("is_read", False)),
        "createdAt": (doc.get("created_at") or datetime.utcnow()).isoformat(),
        "actorName": doc.get("actor_name", "Someone"),
        "replyPreview": doc.get("reply_preview", ""),
    }


@router.get("/posts")
async def get_posts(
    request: Request,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    _ensure_indexes()
    c = _col()
    b = _blocks_col()
    # Defensive cleanup in addition to TTL monitor.
    c.delete_many({"created_at": {"$lt": datetime.utcnow() - timedelta(days=RETENTION_DAYS)}})
    docs: List[dict] = list(c.find({}).sort("created_at", -1))
    blocked_ids = set()
    if current_user and current_user.get("_id"):
        blocked_cursor = b.find({"blocker_user_id": current_user.get("_id")})
        blocked_ids = {str(x.get("blocked_user_id")) for x in blocked_cursor if x.get("blocked_user_id")}
    safe_docs: List[dict] = []
    for d in docs:
        if blocked_ids and (d.get("author_user_id") in blocked_ids):
            continue
        replies = d.get("replies") or []
        if blocked_ids:
            replies = [r for r in replies if r.get("author_user_id") not in blocked_ids]
        next_doc = dict(d)
        next_doc["replies"] = replies
        safe_docs.append(next_doc)
    vk = _viewer_like_key(current_user, _device_id_from_request(request))
    return {"posts": [_serialize(d, vk) for d in safe_docs]}


@router.post("/posts")
async def add_post(
    request: Request,
    payload: CommunityPostIn,
    current_user: Optional[dict] = Depends(get_optional_user),
):
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
        "like_keys": [],
    }
    result = c.insert_one(doc)
    created = c.find_one({"_id": result.inserted_id})
    vk = _viewer_like_key(current_user, _device_id_from_request(request))
    return {"post": _serialize(created, vk)}


@router.post("/posts/{post_id}/replies")
async def add_reply(
    post_id: str,
    request: Request,
    payload: CommunityReplyIn,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    _ensure_indexes()
    c = _col()
    n = _notifications_col()
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="Invalid post id")
    post = c.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
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
        "parent_reply_id": (payload.parent_reply_id or "").strip() or None,
        "created_at": datetime.utcnow(),
    }
    existing_replies = post.get("replies") or []
    if existing_replies:
        latest = existing_replies[-1]
        latest_author_id = latest.get("author_user_id")
        latest_author = (latest.get("author") or "").strip().lower()
        now_author = (resolved_author or "").strip().lower()
        latest_body = (latest.get("body") or "").strip().lower()
        now_body = reply_doc["body"].strip().lower()
        latest_parent_id = (latest.get("parent_reply_id") or "").strip()
        now_parent_id = (reply_doc.get("parent_reply_id") or "").strip()
        latest_created = latest.get("created_at")
        if (
            latest_body == now_body
            and latest_parent_id == now_parent_id
            and (
                (author_user_id and latest_author_id == author_user_id)
                or (not author_user_id and latest_author == now_author)
            )
            and isinstance(latest_created, datetime)
            and (datetime.utcnow() - latest_created).total_seconds() <= 8
        ):
            # Treat rapid duplicate sends as an idempotent success.
            vk = _viewer_like_key(current_user, _device_id_from_request(request))
            return {"post": _serialize(post, vk), "duplicate_ignored": True}
    result = c.update_one(
        {"_id": ObjectId(post_id)},
        {"$push": {"replies": reply_doc}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    updated = c.find_one({"_id": ObjectId(post_id)})
    post_owner_id = post.get("author_user_id")
    is_self_reply = bool(post_owner_id) and post_owner_id == author_user_id
    if post_owner_id and not is_self_reply:
        n.insert_one(
            {
                "recipient_user_id": post_owner_id,
                "post_id": str(post.get("_id")),
                "reply_id": reply_doc["id"],
                "message": f'{resolved_author} replied to your post',
                "actor_name": resolved_author,
                "reply_preview": reply_doc["body"][:140],
                "is_read": False,
                "created_at": datetime.utcnow(),
            }
        )
    vk = _viewer_like_key(current_user, _device_id_from_request(request))
    return {"post": _serialize(updated, vk)}


@router.post("/posts/{post_id}/like")
async def toggle_post_like(
    post_id: str,
    request: Request,
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Toggle like for the current user (JWT) or device id (X-Community-Like-Id header)."""
    _ensure_indexes()
    c = _col()
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="Invalid post id")
    vk = _viewer_like_key(current_user, _device_id_from_request(request))
    if not vk:
        raise HTTPException(
            status_code=400,
            detail="Sign in or send header X-Community-Like-Id (8+ characters)",
        )
    post = c.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    like_keys = list(post.get("like_keys") or [])
    if vk in like_keys:
        like_keys = [x for x in like_keys if x != vk]
    else:
        like_keys.append(vk)
    c.update_one({"_id": ObjectId(post_id)}, {"$set": {"like_keys": like_keys}})
    updated = c.find_one({"_id": ObjectId(post_id)})
    return {"post": _serialize(updated, vk)}


@router.get("/notifications")
async def get_my_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
    current_user: dict = Depends(get_current_user),
):
    _ensure_indexes()
    n = _notifications_col()
    user_id = current_user.get("_id")
    if not user_id:
        return {"notifications": [], "unreadCount": 0}
    criteria = {"recipient_user_id": user_id}
    if unread_only:
        criteria["is_read"] = False
    docs = list(n.find(criteria).sort("created_at", -1).limit(limit))
    unread_count = n.count_documents({"recipient_user_id": user_id, "is_read": False})
    return {"notifications": [_serialize_notification(d) for d in docs], "unreadCount": unread_count}


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    _ensure_indexes()
    n = _notifications_col()
    if not ObjectId.is_valid(notification_id):
        raise HTTPException(status_code=400, detail="Invalid notification id")
    user_id = current_user.get("_id")
    result = n.update_one(
        {"_id": ObjectId(notification_id), "recipient_user_id": user_id},
        {"$set": {"is_read": True, "read_at": datetime.utcnow()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    unread_count = n.count_documents({"recipient_user_id": user_id, "is_read": False})
    return {"success": True, "unreadCount": unread_count}


@router.delete("/posts/{post_id}/replies/{reply_id}")
async def delete_own_reply(
    post_id: str,
    reply_id: str,
    request: Request,
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
    vk = _viewer_like_key(current_user, _device_id_from_request(request))
    return {"post": _serialize(updated, vk), "success": True}


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
async def edit_own_post(
    post_id: str,
    request: Request,
    payload: CommunityPostUpdateIn,
    current_user: dict = Depends(get_current_user),
):
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
    vk = _viewer_like_key(current_user, _device_id_from_request(request))
    return {"post": _serialize(updated, vk)}


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


@router.post("/posts/{post_id}/replies/{reply_id}/report")
async def report_reply(
    post_id: str,
    reply_id: str,
    payload: CommunityReportIn,
    current_user: dict = Depends(get_current_user),
):
    _ensure_indexes()
    c = _col()
    r = _reports_col()
    if not ObjectId.is_valid(post_id):
        raise HTTPException(status_code=400, detail="Invalid post id")
    post = c.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    target_reply = None
    for x in (post.get("replies") or []):
        if (x.get("id") or "") == reply_id:
            target_reply = x
            break
    if target_reply is None:
        raise HTTPException(status_code=404, detail="Reply not found")
    reporter_id = current_user.get("_id")
    existing = r.find_one(
        {
            "post_id": post_id,
            "reply_id": reply_id,
            "reporter_user_id": reporter_id,
            "status": "pending",
        }
    )
    if existing:
        return {"success": True, "message": "Already reported", "report_id": str(existing["_id"])}
    doc = {
        "post_id": post_id,
        "reply_id": reply_id,
        "reason": payload.reason.strip(),
        "status": "pending",
        "reporter_user_id": reporter_id,
        "reporter_name": current_user.get("full_name") or current_user.get("email"),
        "reporter_email": current_user.get("email"),
        "target_type": "reply",
        "reply_author_user_id": target_reply.get("author_user_id"),
        "reply_author_name": target_reply.get("author"),
        "reply_excerpt": (target_reply.get("body") or "")[:300],
        "created_at": datetime.utcnow(),
    }
    out = r.insert_one(doc)
    return {"success": True, "report_id": str(out.inserted_id)}


@router.post("/users/{target_user_id}/block")
async def block_user(target_user_id: str, current_user: dict = Depends(get_current_user)):
    _ensure_indexes()
    b = _blocks_col()
    if not target_user_id.strip():
        raise HTTPException(status_code=400, detail="Invalid user id")
    me = current_user.get("_id")
    if not me:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if target_user_id == me:
        raise HTTPException(status_code=400, detail="You cannot block yourself")
    b.update_one(
        {"blocker_user_id": me, "blocked_user_id": target_user_id},
        {
            "$set": {
                "blocker_user_id": me,
                "blocked_user_id": target_user_id,
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {"created_at": datetime.utcnow()},
        },
        upsert=True,
    )
    return {"success": True, "message": "User blocked"}
