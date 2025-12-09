"""
Email Service
Send emails via SMTP (Gmail) for OTP verification
"""

import random
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
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

async def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None
) -> bool:
    """
    Send email via SMTP
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML email body
        body_text: Plain text email body (fallback)
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
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
        return True
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Failed to send email to {to_email}")
        print(f"[ERROR] Error type: {type(e).__name__}")
        print(f"[ERROR] Error message: {str(e)}")
        print(f"[ERROR] Full traceback:\n{error_trace}")
        return False


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

async def generate_and_send_otp(email: str) -> bool:
    """
    Generate OTP, store it, and send email
    
    Args:
        email: User email address
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Generate OTP
        otp = generate_otp()
        print(f"[INFO] Generated OTP for {email}: {otp}")
        
        # Store in database
        stored = await store_otp(email, otp)
        if not stored:
            return False
        
        # Create email content
        html_body, text_body = create_otp_email_html(otp, email)
        
        # Send email
        sent = await send_email(
            to_email=email,
            subject="DupeFinder - Email Verification Code",
            body_html=html_body,
            body_text=text_body
        )
        
        if sent:
            print(f"[OK] OTP sent successfully to {email}")
            return True
        else:
            print(f"[ERROR] Failed to send OTP email to {email}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to generate and send OTP: {e}")
        return False






