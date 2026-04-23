"""
Email Service
Send OTP emails via Resend (HTTPS) when RESEND_API_KEY is set, else SMTP.
"""

import random
import aiosmtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app.core.config import settings
from app.core.database import get_otps_collection


# ============================================
# OTP Generation
# ============================================

def generate_otp(length: int = None) -> str:
    """
    Generate a random numeric OTP
    
    Args:
        length: OTP length (default: from settings)
        
    Returns:
        OTP string
    """
    if length is None:
        length = settings.OTP_LENGTH
    
    # Generate random digits
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp


# ============================================
# Email Sending
# ============================================

_resend_onboarding_warned: bool = False

_CONSUMER_FROM_MARKERS = (
    "@gmail.com",
    "@googlemail.com",
    "@yahoo.",
    "@hotmail.",
    "@outlook.",
    "@live.",
    "@icloud.",
)


def effective_resend_from_address() -> str:
    """
    From header for Resend. Resend rejects consumer addresses (Gmail, etc.) as From
    unless you use their sandbox sender — use a verified domain in production.
    """
    explicit = (settings.RESEND_FROM or "").strip()
    if explicit:
        return explicit
    combined = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>".strip()
    low = combined.lower()
    if any(m in low for m in _CONSUMER_FROM_MARKERS):
        return f"{settings.EMAIL_FROM_NAME} <onboarding@resend.dev>"
    return combined


async def _send_email_resend(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str],
) -> Tuple[bool, Optional[str]]:
    """POST to Resend API (no outbound SMTP). Returns (ok, error_code)."""
    key = (settings.RESEND_API_KEY or "").strip()
    if not key:
        return False, None
    from_addr = effective_resend_from_address()
    global _resend_onboarding_warned
    if (
        not _resend_onboarding_warned
        and (settings.RESEND_FROM or "").strip() == ""
        and "onboarding@resend.dev" in from_addr
    ):
        _resend_onboarding_warned = True
        print(
            "[WARN] Resend From is onboarding@resend.dev (EMAIL_FROM is a consumer inbox). "
            "Verify a domain in Resend and set RESEND_FROM=DupeFinder <noreply@yourdomain.com> for production."
        )

    payload: dict = {
        "from": from_addr,
        "to": [to_email],
        "subject": subject,
        "html": body_html,
    }
    if body_text:
        payload["text"] = body_text

    print(f"[INFO] Sending email to {to_email} via Resend API (from={from_addr!r})")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=15.0)) as client:
            r = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if r.status_code in (200, 201):
            try:
                rid = r.json().get("id")
            except Exception:
                rid = None
            print(f"[OK] Resend accepted email to {to_email} id={rid}")
            return True, None
        snippet = (r.text or "")[:800].lower()
        if r.status_code == 403 and (
            "verify a domain" in snippet
            or "only send testing" in snippet
            or "your own email address" in snippet
        ):
            return False, "resend_needs_verified_domain"
        print(f"[ERROR] Resend HTTP {r.status_code}: {r.text[:500]}")
        return False, None
    except Exception as e:
        import traceback
        print(f"[ERROR] Resend request failed: {e}\n{traceback.format_exc()}")
        return False, None


async def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Send email via Resend when RESEND_API_KEY is set, otherwise SMTP.

    Returns:
        (success, error_code). error_code is e.g. resend_needs_verified_domain when
        Resend blocks non-account recipients until a domain is verified.
    """
    try:
        if (settings.RESEND_API_KEY or "").strip():
            return await _send_email_resend(to_email, subject, body_html, body_text)

        # Create message
        message = MIMEMultipart("alternative")
        message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        message["To"] = to_email
        message["Subject"] = subject
        
        # Add plain text part (fallback)
        if body_text:
            part1 = MIMEText(body_text, "plain")
            message.attach(part1)
        
        # Add HTML part
        part2 = MIMEText(body_html, "html")
        message.attach(part2)
        
        # Send email via SMTP
        print(f"[INFO] Attempting to send email to {to_email} via {settings.SMTP_HOST}:{settings.SMTP_PORT}")
        print(f"[INFO] Using username: {settings.SMTP_USERNAME}")
        
        if settings.SMTP_USE_TLS:
            print(f"[INFO] Using TLS connection")
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                start_tls=True,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
            )
        else:
            print(f"[INFO] Using non-TLS connection")
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
            )
        
        print(f"[OK] Email sent successfully to {to_email}")
        return True, None

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Failed to send email to {to_email}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        print(f"[ERROR] Error message: {str(e)}")
        print(f"[ERROR] Full traceback:\n{error_trace}")
        return False, None


def create_otp_email_html(otp: str, email: str) -> tuple[str, str]:
    """
    Create HTML and text versions of OTP email
    
    Args:
        otp: OTP code
        email: Recipient email
        
    Returns:
        Tuple of (html_body, text_body)
    """
    # HTML version
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .header {{
                background-color: #000;
                color: #fff;
                padding: 20px;
                text-align: center;
            }}
            .content {{
                background-color: #fff;
                padding: 30px;
                border: 1px solid #ddd;
            }}
            .otp-code {{
                font-size: 32px;
                font-weight: bold;
                letter-spacing: 8px;
                text-align: center;
                padding: 20px;
                background-color: #f0f0f0;
                border: 2px dashed #333;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>DupeFinder</h1>
            </div>
            <div class="content">
                <h2>Email Verification</h2>
                <p>Hello,</p>
                <p>Thank you for signing up with DupeFinder! To complete your registration, please use the following One-Time Password (OTP):</p>
                
                <div class="otp-code">
                    {otp}
                </div>
                
                <p><strong>This OTP will expire in {settings.OTP_EXPIRY_MINUTES} minutes.</strong></p>
                
                <p>If you didn't request this verification, please ignore this email.</p>
                
                <p>Best regards,<br>The DupeFinder Team</p>
            </div>
            <div class="footer">
                <p>This is an automated email. Please do not reply.</p>
                <p>&copy; 2025 DupeFinder. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
DupeFinder - Email Verification

Hello,

Thank you for signing up with DupeFinder! To complete your registration, please use the following One-Time Password (OTP):

{otp}

This OTP will expire in {settings.OTP_EXPIRY_MINUTES} minutes.

If you didn't request this verification, please ignore this email.

Best regards,
The DupeFinder Team

---
This is an automated email. Please do not reply.
© 2025 DupeFinder. All rights reserved.
    """
    
    return html_body, text_body


# ============================================
# OTP Database Operations
# ============================================


async def store_otp(email: str, otp: str) -> bool:
    """
    Store OTP in database with expiration
    
    Args:
        email: User email
        otp: OTP code
        
    Returns:
        True if stored successfully, False otherwise
    """
    try:
        otps_collection = get_otps_collection()
        
        # Delete any existing OTPs for this email
        otps_collection.delete_many({"email": email})
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        
        # Store new OTP
        otps_collection.insert_one({
            "email": email,
            "otp_code": otp,
            "expires_at": expires_at,
            "is_used": False,
            "created_at": datetime.utcnow()
        })
        
        print(f"[OK] OTP stored for {email}, expires at {expires_at}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to store OTP: {e}")
        return False


def verify_otp(email: str, otp: str) -> bool:
    """
    Verify OTP from database
    
    Args:
        email: User email
        otp: OTP code to verify
        
    Returns:
        True if valid, False otherwise
    """
    try:
        otps_collection = get_otps_collection()
        
        # Find OTP
        otp_doc = otps_collection.find_one({
            "email": email,
            "otp_code": otp,
            "is_used": False
        })
        
        if not otp_doc:
            print(f"[WARN] OTP not found or already used for {email}")
            return False
        
        # Check if expired
        if datetime.utcnow() > otp_doc["expires_at"]:
            print(f"[WARN] OTP expired for {email}")
            return False
        
        # Mark as used
        otps_collection.update_one(
            {"_id": otp_doc["_id"]},
            {"$set": {"is_used": True}}
        )
        
        print(f"[OK] OTP verified for {email}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to verify OTP: {e}")
        return False


# ============================================
# Combined OTP Operations
# ============================================

async def generate_and_send_otp(email: str) -> Tuple[bool, Optional[str]]:
    """
    Generate OTP, store it, and send email.

    Returns:
        (success, error_code). See send_email for error_code values.
    """
    try:
        # Generate OTP
        otp = generate_otp()
        print(f"[INFO] Generated OTP for {email}: {otp}")

        # Store in database
        stored = await store_otp(email, otp)
        if not stored:
            return False, None

        # Create email content
        html_body, text_body = create_otp_email_html(otp, email)

        # Send email
        sent, send_err = await send_email(
            to_email=email,
            subject="DupeFinder - Email Verification Code",
            body_html=html_body,
            body_text=text_body,
        )

        if sent:
            print(f"[OK] OTP sent successfully to {email}")
            return True, None
        print(f"[ERROR] Failed to send OTP email to {email}")
        return False, send_err

    except Exception as e:
        print(f"[ERROR] Failed to generate and send OTP: {e}")
        return False, None






