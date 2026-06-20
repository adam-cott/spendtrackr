"""
Send email notification with receipt attachment via Gmail SMTP.
Completely FREE - uses Gmail's built-in SMTP server.

Required environment variables:
- GMAIL_ADDRESS: Your Gmail address (e.g., yourname@gmail.com)
- GMAIL_APP_PASSWORD: App Password generated from Google Account settings
- RECEIPT_NOTIFICATION_EMAIL: Email address to receive notifications
"""

import os
import sys
import re
import smtplib
import base64
import traceback
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formatdate, formataddr

from flask import Flask, request, jsonify

app = Flask(__name__)

# Gmail SMTP settings (free)
GMAIL_SMTP_SERVER = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587


def log(message: str):
    """Log to stderr for Vercel serverless function logs."""
    print(f"[send-email] {message}", file=sys.stderr)


def format_date_no_leading_zeros(date_str: str) -> str:
    """
    Convert date from YYYY-MM-DD to M/D/YYYY format (no leading zeros).
    Example: 2026-01-23 -> 1/23/2026
    """
    try:
        parts = date_str.split('-')
        if len(parts) == 3:
            year, month, day = parts
            return f"{int(month)}/{int(day)}/{year}"
    except (ValueError, AttributeError) as e:
        log(f"Date formatting error: {e}")
    return date_str


def is_valid_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def send_receipt_email(
    recipient_email: str,
    amount: float,
    date: str,
    image_data: str,
    gmail_address: str,
    gmail_app_password: str
) -> dict:
    """
    Send email with receipt attachment.
    Returns dict with 'success' and (on failure) 'error' keys.
    """
    try:
        # Format subject line - THREE spaces between amount and date (required format)
        formatted_amount = f"${amount:.2f}"
        formatted_date = format_date_no_leading_zeros(date)
        three_spaces = "   "
        subject = f"{formatted_amount}{three_spaces}{formatted_date}"

        # Validate email addresses
        if not is_valid_email(gmail_address):
            raise ValueError(f"Invalid sender email format: {gmail_address}")
        if not is_valid_email(recipient_email):
            raise ValueError(f"Invalid recipient email format: {recipient_email}")

        # Create email message with proper headers
        msg = MIMEMultipart('mixed')

        # Required headers for Gmail compliance
        msg['From'] = formataddr(('SpendTrackr', gmail_address))
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = f"<{uuid.uuid4()}@spendtrackr.app>"
        msg['MIME-Version'] = '1.0'
        msg['X-Mailer'] = 'SpendTrackr/1.0'

        # Add a minimal text body (helps avoid spam filters)
        body_text = f"Receipt: {formatted_amount} on {formatted_date}"
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

        # Process image data
        if image_data.startswith('data:'):
            if ',' in image_data:
                _, image_data = image_data.split(',', 1)
            else:
                raise ValueError("Invalid data URL format - no comma found")

        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as decode_err:
            raise ValueError(f"Failed to decode base64 image: {decode_err}")

        # Validate attachment size (Gmail limit is 25MB, but keep under 10MB for reliability)
        max_attachment_size = 10 * 1024 * 1024  # 10MB
        if len(image_bytes) > max_attachment_size:
            raise ValueError(f"Attachment too large: {len(image_bytes) / 1024 / 1024:.1f}MB (max 10MB)")

        # Create image attachment with proper headers
        try:
            image_attachment = MIMEImage(image_bytes, _subtype='jpeg')
            filename = f"receipt_{formatted_date.replace('/', '-')}.jpg"
            image_attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=filename
            )
            image_attachment.add_header('Content-Transfer-Encoding', 'base64')
            msg.attach(image_attachment)
        except Exception as attach_err:
            raise ValueError(f"Failed to create image attachment: {attach_err}")

        # Connect to Gmail SMTP
        try:
            server = smtplib.SMTP(GMAIL_SMTP_SERVER, GMAIL_SMTP_PORT, timeout=30)
        except Exception as connect_err:
            raise ConnectionError(f"Failed to connect to Gmail SMTP: {connect_err}")

        try:
            server.starttls()
            server.login(gmail_address, gmail_app_password)
            server.send_message(msg)
        finally:
            server.quit()

        log(f"Email sent to {recipient_email}")
        return {'success': True}

    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Gmail authentication failed (code {e.smtp_code})"
        log(f"AUTH ERROR: {error_msg}")
        return {'success': False, 'error': error_msg}
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error: {str(e)}"
        log(f"SMTP ERROR: {error_msg}")
        return {'success': False, 'error': error_msg}
    except ConnectionError as e:
        error_msg = str(e)
        log(f"CONNECTION ERROR: {error_msg}")
        return {'success': False, 'error': error_msg}
    except ValueError as e:
        error_msg = str(e)
        log(f"VALUE ERROR: {error_msg}")
        return {'success': False, 'error': error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log(f"UNEXPECTED ERROR: {error_msg}")
        log(traceback.format_exc())
        return {'success': False, 'error': error_msg}


@app.route("/api/send-email", methods=["POST"])
def handle_send_email():
    """API endpoint to send receipt email notification."""
    gmail_address = os.environ.get("GMAIL_ADDRESS")
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient_email = os.environ.get("RECEIPT_NOTIFICATION_EMAIL")

    if not gmail_address or not gmail_app_password:
        error_msg = "Email not configured. Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD."
        log(f"ERROR: {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 500

    if not recipient_email:
        error_msg = "No recipient configured. Missing RECEIPT_NOTIFICATION_EMAIL."
        log(f"ERROR: {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 500

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
    except Exception as parse_err:
        log(f"ERROR parsing JSON: {parse_err}")
        return jsonify({"success": False, "error": f"Failed to parse JSON: {str(parse_err)}"}), 400

    amount = data.get("amount")
    date = data.get("date")
    image_data = data.get("image")

    if amount is None or not date:
        return jsonify({"success": False, "error": "Missing required fields: amount and date"}), 400

    if not image_data:
        return jsonify({"success": False, "error": "No receipt image provided"}), 400

    result = send_receipt_email(
        recipient_email=recipient_email,
        amount=float(amount),
        date=date,
        image_data=image_data,
        gmail_address=gmail_address,
        gmail_app_password=gmail_app_password
    )

    if result['success']:
        return jsonify({"success": True, "message": f"Email sent to {recipient_email}"})
    else:
        log(f"Email failed: {result.get('error')}")
        return jsonify({"success": False, "error": result.get('error', 'Unknown error')}), 500


@app.route("/api/send-email/health", methods=["GET"])
def health_check():
    """Health check endpoint for email service."""
    gmail_address = os.environ.get("GMAIL_ADDRESS")
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient_email = os.environ.get("RECEIPT_NOTIFICATION_EMAIL")

    gmail_configured = bool(gmail_address and gmail_app_password)
    recipient_configured = bool(recipient_email)

    return jsonify({
        "status": "ok" if (gmail_configured and recipient_configured) else "not_configured",
        "gmail_configured": gmail_configured,
        "recipient_configured": recipient_configured,
        "gmail_address": gmail_address if gmail_address else None,
        "recipient_email": recipient_email if recipient_email else None,
        "app_password_length": len(gmail_app_password) if gmail_app_password else 0
    })


@app.route("/api/send-email/test-smtp", methods=["GET"])
def test_smtp():
    """Test SMTP connection without sending an email."""
    log("Testing SMTP connection...")

    gmail_address = os.environ.get("GMAIL_ADDRESS")
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")

    if not gmail_address or not gmail_app_password:
        return jsonify({
            "success": False,
            "error": "Missing credentials"
        }), 500

    steps = []
    try:
        log("Step 1: Connecting to SMTP server...")
        server = smtplib.SMTP(GMAIL_SMTP_SERVER, GMAIL_SMTP_PORT, timeout=30)
        steps.append("connected")
        log("  Connected!")

        log("Step 2: Starting TLS...")
        server.starttls()
        steps.append("tls_started")
        log("  TLS started!")

        log("Step 3: Logging in...")
        server.login(gmail_address, gmail_app_password)
        steps.append("logged_in")
        log("  Login successful!")

        server.quit()
        steps.append("disconnected")

        return jsonify({
            "success": True,
            "message": "SMTP connection test passed!",
            "steps": steps
        })

    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Authentication failed: {e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else e.smtp_error}"
        log(f"Auth error: {error_msg}")
        return jsonify({
            "success": False,
            "error": error_msg,
            "error_code": e.smtp_code,
            "steps": steps
        }), 500

    except Exception as e:
        log(f"Error: {str(e)}")
        log(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "steps": steps,
            "traceback": traceback.format_exc()
        }), 500


# For local development
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    app.run(debug=True, port=5001)
