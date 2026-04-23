"""
Send one test message using the same path as OTP mail (Resend if RESEND_API_KEY is set, else SMTP).

Run from the backend directory:
  python -m scripts.test_resend you@example.com
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.chdir(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()


async def _main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.test_resend <to_email>")
        return 1
    to = sys.argv[1].strip()
    from app.services.email_service import send_email

    ok = await send_email(
        to_email=to,
        subject="DupeFinder — Resend / email test",
        body_html="<p>If you see this, outbound email from the backend works.</p>",
        body_text="If you see this, outbound email from the backend works.",
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
