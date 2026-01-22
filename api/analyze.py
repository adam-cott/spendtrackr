"""
Receipt analysis using OCR.space free API.
No installation required - just a free API key from ocr.space
"""

import os
import re
import requests
from datetime import datetime

from flask import Flask, request, jsonify

app = Flask(__name__)

# OCR.space API endpoint
OCR_SPACE_URL = "https://api.ocr.space/parse/image"

# Default vendor to category mapping
VENDOR_CATEGORIES = {
    "mcdonald": "Fast Food",
    "burger king": "Fast Food",
    "wendy": "Fast Food",
    "taco bell": "Fast Food",
    "chick-fil-a": "Fast Food",
    "subway": "Fast Food",
    "chipotle": "Fast Food",
    "shell": "Gas",
    "exxon": "Gas",
    "chevron": "Gas",
    "bp": "Gas",
    "mobil": "Gas",
    "speedway": "Gas",
    "target": "Retail",
    "walmart": "Retail",
    "costco": "Retail",
    "amazon": "Retail",
    "best buy": "Retail",
    "kroger": "Groceries",
    "whole foods": "Groceries",
    "trader joe": "Groceries",
    "safeway": "Groceries",
    "aldi": "Groceries",
    "publix": "Groceries",
    "starbucks": "Coffee",
    "dunkin": "Coffee",
    "peet": "Coffee",
    "cvs": "Pharmacy",
    "walgreens": "Pharmacy",
    "rite aid": "Pharmacy",
}

# Common vendor names to look for in receipts
KNOWN_VENDORS = [
    "McDonald's", "Burger King", "Wendy's", "Taco Bell", "Chick-fil-A",
    "Subway", "Chipotle", "Shell", "Exxon", "Chevron", "BP", "Mobil",
    "Speedway", "Target", "Walmart", "Costco", "Amazon", "Best Buy",
    "Kroger", "Whole Foods", "Trader Joe's", "Safeway", "Aldi", "Publix",
    "Starbucks", "Dunkin", "Peet's", "CVS", "Walgreens", "Rite Aid",
    "Home Depot", "Lowe's", "7-Eleven", "Circle K"
]


def get_category(vendor: str) -> str:
    """Get category for a vendor based on the mapping."""
    vendor_lower = vendor.lower()
    for known_vendor, category in VENDOR_CATEGORIES.items():
        if known_vendor in vendor_lower:
            return category
    return "Other"


def extract_total(text: str) -> float | None:
    """Extract total amount from receipt text."""
    lines = text.split('\n')

    # Patterns for total amount (prioritized)
    total_patterns = [
        r'(?:total|grand total|amount due|balance due|total due)\s*[:\$]?\s*\$?\s*(\d+[.,]\d{2})',
        r'(?:total|grand total)\s+(\d+[.,]\d{2})',
        r'\$\s*(\d+[.,]\d{2})\s*$',
    ]

    # First, look for explicit "total" lines
    for line in reversed(lines):  # Check from bottom up
        line_lower = line.lower().strip()
        for pattern in total_patterns:
            match = re.search(pattern, line_lower, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '.')
                try:
                    return float(amount_str)
                except ValueError:
                    continue

    # Fallback: find the largest dollar amount (likely the total)
    all_amounts = re.findall(r'\$?\s*(\d+[.,]\d{2})', text)
    if all_amounts:
        amounts = []
        for amt in all_amounts:
            try:
                amounts.append(float(amt.replace(',', '.')))
            except ValueError:
                continue
        if amounts:
            return max(amounts)

    return None


def extract_date(text: str) -> str:
    """Extract date from receipt text."""
    # Common date patterns
    date_patterns = [
        # MM/DD/YYYY or MM-DD-YYYY
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        # Month DD, YYYY
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{2,4})',
        # YYYY-MM-DD
        r'(\d{4}-\d{2}-\d{2})',
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            # Try to parse and normalize the date
            for fmt in ['%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y',
                       '%Y-%m-%d', '%B %d, %Y', '%b %d, %Y', '%b %d %Y']:
                try:
                    parsed = datetime.strptime(date_str.replace(',', ''), fmt)
                    return parsed.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            # Return as-is if parsing fails
            return date_str

    # Default to today
    return datetime.now().strftime('%Y-%m-%d')


def extract_vendor(text: str) -> str:
    """Extract vendor name from receipt text."""
    lines = text.split('\n')

    # Check first few lines for known vendors
    for line in lines[:10]:
        line_clean = line.strip()
        if not line_clean:
            continue

        # Check against known vendors
        for vendor in KNOWN_VENDORS:
            if vendor.lower() in line_clean.lower():
                return vendor

        # Check category mapping
        for vendor_key in VENDOR_CATEGORIES.keys():
            if vendor_key in line_clean.lower():
                return line_clean[:50]

    # Fallback: use first non-empty line that looks like a name
    for line in lines[:5]:
        line_clean = line.strip()
        if line_clean and len(line_clean) > 3:
            if not re.match(r'^[\d\s\-\/\.\$]+$', line_clean):
                return line_clean[:50]

    return "Unknown Vendor"


def ocr_space_api(image_base64: str, api_key: str) -> str:
    """Call OCR.space API to extract text from image."""
    payload = {
        'apikey': api_key,
        'base64Image': image_base64,
        'language': 'eng',
        'isOverlayRequired': False,
        'detectOrientation': True,
        'scale': True,
        'OCREngine': 2,  # Engine 2 is better for receipts
    }

    response = requests.post(OCR_SPACE_URL, data=payload, timeout=30)
    response.raise_for_status()

    result = response.json()

    if result.get('IsErroredOnProcessing'):
        error_msg = result.get('ErrorMessage', ['Unknown error'])
        raise Exception(f"OCR.space error: {error_msg}")

    # Extract text from all parsed results
    parsed_results = result.get('ParsedResults', [])
    if not parsed_results:
        raise Exception("No text found in image")

    text = '\n'.join([r.get('ParsedText', '') for r in parsed_results])
    return text


@app.route("/api/analyze", methods=["POST"])
def analyze_receipt():
    """Analyze a receipt image and return extracted data."""
    try:
        # Get API key from environment
        api_key = os.environ.get("OCR_SPACE_API_KEY")
        if not api_key:
            return jsonify({
                "error": "OCR_SPACE_API_KEY not configured. Get a free key at ocr.space"
            }), 500

        # Get image data from request
        data = request.get_json()
        if not data or "image" not in data:
            return jsonify({"error": "No image data provided"}), 400

        image_data = data["image"]

        # Ensure proper base64 format for OCR.space
        if not image_data.startswith("data:"):
            media_type = data.get("media_type", "image/jpeg")
            image_data = f"data:{media_type};base64,{image_data}"

        # Call OCR.space API
        text = ocr_space_api(image_data, api_key)

        # Extract data from OCR text
        total = extract_total(text)
        vendor = extract_vendor(text)
        date = extract_date(text)
        category = get_category(vendor)

        return jsonify({
            "success": True,
            "data": {
                "total": total,
                "vendor": vendor,
                "date": date,
                "category": category,
            }
        })

    except requests.exceptions.Timeout:
        return jsonify({"error": "OCR service timeout. Please try again."}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"OCR service error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    api_key = os.environ.get("OCR_SPACE_API_KEY")
    return jsonify({
        "status": "ok" if api_key else "missing_api_key",
        "ocr_configured": bool(api_key)
    })


# For local development
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    app.run(debug=True, port=5000)
