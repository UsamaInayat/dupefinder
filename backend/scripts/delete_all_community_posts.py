"""
Delete every community post (and related reports / notifications).

Does not touch community_user_blocks (account blocks, not tied to post rows).

Run from repo (Windows):
  cd backend
  python scripts/delete_all_community_posts.py

Or:
  python -m scripts.delete_all_community_posts
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# backend/scripts/ -> backend/
_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))
os.chdir(_backend)

from dotenv import load_dotenv

load_dotenv()

from app.core.database import db_manager

COMMUNITY_POSTS = "community_posts"
COMMUNITY_REPORTS = "community_reports"
COMMUNITY_NOTIFICATIONS = "community_notifications"


def main() -> int:
    print("[DupeFinder] Connecting to MongoDB...")
    db_manager.connect()
    if not db_manager.is_connected():
        print("[ERROR] Could not connect.")
        return 1

    posts = db_manager.get_collection(COMMUNITY_POSTS)
    reports = db_manager.get_collection(COMMUNITY_REPORTS)
    notifs = db_manager.get_collection(COMMUNITY_NOTIFICATIONS)

    n_posts = posts.count_documents({})
    n_reports = reports.count_documents({})
    n_notifs = notifs.count_documents({})

    print(
        f"[DupeFinder] Before: posts={n_posts}, reports={n_reports}, notifications={n_notifs}"
    )

    r1 = posts.delete_many({})
    r2 = reports.delete_many({})
    r3 = notifs.delete_many({})

    print(
        f"[DupeFinder] Deleted: posts={r1.deleted_count}, "
        f"reports={r2.deleted_count}, notifications={r3.deleted_count}"
    )

    db_manager.disconnect()
    print("[DupeFinder] Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
