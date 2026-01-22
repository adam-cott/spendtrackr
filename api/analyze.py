"""
Vercel serverless function for receipt analysis.
Works in demo mode without API key, or uses Claude Vision if key is provided.
"""

import json
import os
import random
from datetime import datetime, timedelta

from flask import Flask, request, jsonify

app = Flask(__name__)

# Default vendor to category mapping
VENDOR_CATEGORIES = {
    "mcdonald's": "Fast Food",
    "burger king": "Fast Food",
    "wendy's": "Fast Food",
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
    "trader joe's": "Groceries",
    "safeway": "Groceries",
    "aldi": "Groceries",
    "publix": "Groceries",
    "starbucks": "Coffee",
    "dunkin": "Coffee",
    "peet's": "Coffee",
    "cvs": "Pharmacy",
    "walgreens": "Pharmacy",
    "rite aid": "Pharmacy",
}

# Demo vendors with realistic price ranges
DEMO_RECEIPTS = [
    {"vendor": "Starbucks", "category": "Coffee", "min": 4.50, "max": 12.00},
    {"vendor": "McDonald's", "category": "Fast Food", "min": 6.00, "max": 15.00},
    {"vendor": "Target", "category": "Retail", "min": 15.00, "max": 85.00},
    {"vendor": "Shell Gas Station", "category": "Gas", "min": 25.00, "max": 65.00},
    {"vendor": "Whole Foods Market", "category": "Groceries", "min": 35.00, "max": 120.00},
    {"vendor": "CVS Pharmacy", "category": "Pharmacy", "min": 8.00, "max": 45.00},
    {"vendor": "Chipotle", "category": "Fast Food", "min": 9.00, "max": 18.00},
    {"vendor": "Walmart", "category": "Retail", "min": 20.00, "max": 150.00},
    {"vendor": "Trader Joe's", "category": "Groceries", "min": 25.00, "max": 80.00},
    {"vendor": "Dunkin'", "category": "Coffee", "min": 3.50, "max": 10.00},
    {"vendor": "Best Buy", "category": "Retail", "min": 15.00, "max": 200.00},
    {"vendor": "Costco", "category": "Groceries", "min": 50.00, "max": 250.00},
]


def get_category(vendor: str) -> str:
    """Get category for a vendor based on the mapping."""
    vendor_lower = vendor.lower()
    for known_vendor, category in VENDOR_CATEGORIES.items():
        if known_vendor in vendor_lower or vendor_lower in known_vendor:
            return category
    return "Other"


def generate_demo_receipt():
    """Generate realistic mock receipt data."""
    receipt = random.choice(DEMO_RECEIPTS)

    # Random amount within range, rounded to cents
    amount = round(random.uniform(receipt["min"], receipt["max"]), 2)

    # Random date within last 7 days
    days_ago = random.randint(0, 7)
    date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    return {
        "total": amount,
        "vendor": receipt["vendor"],
        "date": date,
        "category": receipt["category"],
    }


def parse_receipt_response(response: str) -> dict:
    """Parse the structured response from Claude."""
    result = {
        "total": None,
        "vendor": "Unknown",
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    for line in response.strip().split("\n"):
        line = line.strip()
        if line.startswith("TOTAL:"):
            amount_str = line.replace("TOTAL:", "").strip()
            amount_str = amount_str.replace("$", "").replace(",", "").strip()
            try:
                result["total"] = float(amount_str)
            except ValueError:
                result["total"] = None
        elif line.startswith("VENDOR:"):
            result["vendor"] = line.replace("VENDOR:", "").strip()
        elif line.startswith("DATE:"):
            date_str = line.replace("DATE:", "").strip()
            if date_str.lower() != "unknown":
                result["date"] = date_str

    return result


def analyze_with_claude(image_data: str, media_type: str, api_key: str) -> dict:
    """Use Claude to analyze a receipt image."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    prompt = """Analyze this receipt image and extract the following information:
1. Total amount (the final total paid, including tax)
2. Vendor/store name
3. Purchase date

Respond in this exact format (use "Unknown" if you cannot determine a value):
TOTAL: [amount as a number, e.g., 25.99]
VENDOR: [store/vendor name]
DATE: [date in YYYY-MM-DD format, or "Unknown" if not visible]

Only provide these three lines, nothing else."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
    )

    response_text = message.content[0].text
    extracted = parse_receipt_response(response_text)
    extracted["category"] = get_category(extracted["vendor"])
    return extracted


@app.route("/api/analyze", methods=["POST"])
def analyze_receipt():
    """Analyze a receipt image and return extracted data."""
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

        # Get image data from request
        data = request.get_json()
        if not data or "image" not in data:
            return jsonify({"error": "No image data provided"}), 400

        # Check if we have a valid API key
        if api_key and api_key.startswith("sk-ant-"):
            # Use Claude Vision for real analysis
            image_data = data["image"]
            media_type = data.get("media_type", "image/jpeg")

            # Remove data URL prefix if present
            if "base64," in image_data:
                image_data = image_data.split("base64,")[1]

            try:
                extracted = analyze_with_claude(image_data, media_type, api_key)
                return jsonify({
                    "success": True,
                    "mode": "live",
                    "data": extracted
                })
            except Exception as e:
                # Fall back to demo mode if API fails
                extracted = generate_demo_receipt()
                return jsonify({
                    "success": True,
                    "mode": "demo",
                    "message": "API error, using demo mode",
                    "data": extracted
                })
        else:
            # Demo mode - generate mock data
            extracted = generate_demo_receipt()
            return jsonify({
                "success": True,
                "mode": "demo",
                "data": extracted
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    has_key = bool(api_key and api_key.startswith("sk-ant-"))
    return jsonify({
        "status": "ok",
        "mode": "live" if has_key else "demo"
    })


# For local development
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    app.run(debug=True, port=5000)
