"""
Send email notification with receipt attachment via Gmail SMTP.
Completely FREE - uses Gmail's built-in SMTP server.

Required environment variables:
- GMAIL_ADDRESS: Your Gmail address (e.g., yourname@gmail.com)
- GMAIL_APP_PASSWORD: App Password generated from Google Account settings
- RECEIPT_NOTIFICATION_EMAIL: Email address to receive notifications
"""

import os
import smtplib
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from flask import Flask, request, jsonify

app = Flask(__name__)

# Gmail SMTP settings (free)
GMAIL_SMTP_SERVER = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587


def format_date_no_leading_zeros(date_str: str) -> str:
    """
    Convert date from YYYY-MM-DD to M/D/YYYY format (no leading zeros).
    Example: 2026-01-23 -> 1/23/2026
    """
    try:
        parts = date_str.split('-')
        if len(parts) == 3:
            year, month, day = parts
            # Remove leading zeros by converting to int then back to string
            return f"{int(month)}/{int(day)}/{year}"
    except (ValueError, AttributeError):
        pass
    return date_str


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

    Args:
        recipient_email: Email address to send to
        amount: Receipt amount (e.g., 2.67)
        date: Date in YYYY-MM-DD format
        image_data: Base64 encoded image (with or without data URL prefix)
        gmail_address: Sender's Gmail address
        gmail_app_password: Gmail App Password

    Returns:
        dict with 'success' and optional 'error' keys
    """
    try:
        # Format subject line: $Amount   Date (3 spaces between)
        formatted_amount = f"${amount:.2f}"
        formatted_date = format_date_no_leading_zeros(date)
        subject = f"{formatted_amount}   {formatted_date}"

        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_address
        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Empty body (as requested)
        msg.attach(MIMEText('', 'plain'))

        # Process image data
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',', 1)[1]

        # Decode base64 image
        image_bytes = base64.b64decode(image_data)

        # Attach image
        image_attachment = MIMEImage(image_bytes, _subtype='jpeg')
        image_attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename=f"receipt_{formatted_date.replace('/', '-')}.jpg"
        )
        msg.attach(image_attachment)

        # Send email via Gmail SMTP
        with smtplib.SMTP(GMAIL_SMTP_SERVER, GMAIL_SMTP_PORT) as server:
            server.starttls()  # Enable TLS encryption
            server.login(gmail_address, gmail_app_password)
            server.send_message(msg)

        return {'success': True}

    except smtplib.SMTPAuthenticationError as e:
        return {
            'success': False,
            'error': 'Gmail authentication failed. Check your App Password.'
        }
    except smtplib.SMTPException as e:
        return {
            'success': False,
            'error': f'Email sending failed: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


@app.route("/api/send-email", methods=["POST"])
def handle_send_email():
    """API endpoint to send receipt email notification."""

    # Get credentials from environment variables
    gmail_address = os.environ.get("GMAIL_ADDRESS")
    gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient_email = os.environ.get("RECEIPT_NOTIFICATION_EMAIL")

    # Check for missing configuration
    if not gmail_address or not gmail_app_password:
        return jsonify({
            "success": False,
            "error": "Email not configured. Missing GMAIL_ADDRESS or GMAIL_APP_PASSWORD."
        }), 500

    if not recipient_email:
        return jsonify({
            "success": False,
            "error": "No recipient configured. Missing RECEIPT_NOTIFICATION_EMAIL."
        }), 500

    # Get request data
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "error": "No data provided"
        }), 400

    amount = data.get("amount")
    date = data.get("date")
    image_data = data.get("image")

    if amount is None or not date:
        return jsonify({
            "success": False,
            "error": "Missing required fields: amount and date"
        }), 400

    if not image_data:
        return jsonify({
            "success": False,
            "error": "No receipt image provided"
        }), 400

    # Send the email
    result = send_receipt_email(
        recipient_email=recipient_email,
        amount=float(amount),
        date=date,
        image_data=image_data,
        gmail_address=gmail_address,
        gmail_app_password=gmail_app_password
    )

    if result['success']:
        return jsonify({
            "success": True,
            "message": f"Email sent to {recipient_email}"
        })
    else:
        return jsonify({
            "success": False,
            "error": result.get('error', 'Unknown error')
        }), 500


@app.route("/api/send-email/health", methods=["GET"])
def health_check():
    """Health check endpoint for email service."""
    gmail_configured = bool(
        os.environ.get("GMAIL_ADDRESS") and
        os.environ.get("GMAIL_APP_PASSWORD")
    )
    recipient_configured = bool(os.environ.get("RECEIPT_NOTIFICATION_EMAIL"))

    return jsonify({
        "status": "ok" if (gmail_configured and recipient_configured) else "not_configured",
        "gmail_configured": gmail_configured,
        "recipient_configured": recipient_configured
    })


# For local development
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    app.run(debug=True, port=5001)
