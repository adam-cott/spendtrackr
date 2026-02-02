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

# Default vendor to category mapping (lowercase categories)
# Available categories: food, gas, retail, entertainment, other
VENDOR_CATEGORIES = {
    # Food (restaurants, fast food)
    "mcdonald": "food",
    "burger king": "food",
    "wendy": "food",
    "taco bell": "food",
    "chick-fil-a": "food",
    "subway": "food",
    "chipotle": "food",
    "starbucks": "food",
    "dunkin": "food",
    "peet": "food",
    # Grocery stores (dedicated food retailers)
    "kroger": "food",
    "whole foods": "food",
    "trader joe": "food",
    "safeway": "food",
    "aldi": "food",
    "publix": "food",
    "albertsons": "food",
    "vons": "food",
    "ralphs": "food",
    "food lion": "food",
    "giant": "food",
    "stop & shop": "food",
    "wegmans": "food",
    "heb": "food",
    "h-e-b": "food",
    "meijer": "food",
    "winco": "food",
    "food 4 less": "food",
    "grocery outlet": "food",
    "sprouts": "food",
    "smiths": "food",
    "frys": "food",
    "harmons": "food",
    "maceys": "food",
    # Gas stations
    "shell": "gas",
    "exxon": "gas",
    "chevron": "gas",
    "bp": "gas",
    "mobil": "gas",
    "speedway": "gas",
    "maverik": "gas",
    "sinclair": "gas",
    "phillips": "gas",
    "conoco": "gas",
    "valero": "gas",
    # Retail (non-food stores)
    "amazon": "retail",
    "best buy": "retail",
    "home depot": "retail",
    "lowes": "retail",
    "ikea": "retail",
    "bed bath": "retail",
    "office depot": "retail",
    "staples": "retail",
    # Entertainment
    "amc": "entertainment",
    "regal": "entertainment",
    "cinemark": "entertainment",
    "netflix": "entertainment",
    "spotify": "entertainment",
    "disney": "entertainment",
    "hulu": "entertainment",
    "xbox": "entertainment",
    "playstation": "entertainment",
    "steam": "entertainment",
    "dave & buster": "entertainment",
    "topgolf": "entertainment",
    "bowling": "entertainment",
    "arcade": "entertainment",
}

# Mixed retailers - stores that sell both food and non-food items
# These get special handling: check receipt text for food items
MIXED_RETAILERS = {
    "target", "walmart", "costco", "sam's club", "sams club",
    "cvs", "walgreens", "rite aid",
    "dollar tree", "dollar general", "family dollar",
    "7-eleven", "7 eleven", "circle k",
}

# Known vendor names with correct formatting (key: lowercase for matching, value: display name)
KNOWN_VENDOR_NAMES = {
    # BYU
    "byu": "BYU",
    "byu campus store": "BYU Campus Store",
    "byu bookstore": "BYU Bookstore",
    "byu creamery": "BYU Creamery",
    "byu dining": "BYU Dining",
    # Fast Food
    "mcdonalds": "McDonalds",
    "mcdonald's": "McDonalds",
    "burger king": "Burger King",
    "wendys": "Wendys",
    "wendy's": "Wendys",
    "taco bell": "Taco Bell",
    "chick-fil-a": "Chick-fil-A",
    "chickfila": "Chick-fil-A",
    "subway": "Subway",
    "chipotle": "Chipotle",
    "five guys": "Five Guys",
    "in-n-out": "In-N-Out",
    "arbys": "Arbys",
    "arby's": "Arbys",
    "popeyes": "Popeyes",
    "kfc": "KFC",
    "papa johns": "Papa Johns",
    "dominos": "Dominos",
    "domino's": "Dominos",
    "pizza hut": "Pizza Hut",
    "little caesars": "Little Caesars",
    "sonic": "Sonic",
    "jack in the box": "Jack in the Box",
    "carls jr": "Carls Jr",
    "carl's jr": "Carls Jr",
    "hardees": "Hardees",
    "hardee's": "Hardees",
    "del taco": "Del Taco",
    "panda express": "Panda Express",
    "raising canes": "Raising Canes",
    "raising cane's": "Raising Canes",
    "wingstop": "Wingstop",
    "buffalo wild wings": "Buffalo Wild Wings",
    "zaxbys": "Zaxbys",
    "zaxby's": "Zaxbys",
    # Gas Stations
    "shell": "Shell",
    "exxon": "Exxon",
    "chevron": "Chevron",
    "bp": "BP",
    "mobil": "Mobil",
    "speedway": "Speedway",
    "76": "76",
    "phillips 66": "Phillips 66",
    "conoco": "Conoco",
    "marathon": "Marathon",
    "valero": "Valero",
    "sinclair": "Sinclair",
    "circle k": "Circle K",
    "7-eleven": "7-Eleven",
    "7 eleven": "7-Eleven",
    "maverik": "Maverik",
    # Retail
    "target": "Target",
    "walmart": "Walmart",
    "costco": "Costco",
    "amazon": "Amazon",
    "best buy": "Best Buy",
    "home depot": "Home Depot",
    "lowes": "Lowes",
    "lowe's": "Lowes",
    "ikea": "IKEA",
    "dollar tree": "Dollar Tree",
    "dollar general": "Dollar General",
    "family dollar": "Family Dollar",
    "big lots": "Big Lots",
    "tj maxx": "TJ Maxx",
    "tjmaxx": "TJ Maxx",
    "marshalls": "Marshalls",
    "ross": "Ross",
    "kohls": "Kohls",
    "kohl's": "Kohls",
    "jcpenney": "JCPenney",
    "macys": "Macys",
    "macy's": "Macys",
    "nordstrom": "Nordstrom",
    "sephora": "Sephora",
    "ulta": "Ulta",
    "bath & body works": "Bath and Body Works",
    "bed bath & beyond": "Bed Bath and Beyond",
    "office depot": "Office Depot",
    "staples": "Staples",
    "michaels": "Michaels",
    "hobby lobby": "Hobby Lobby",
    "joann": "Joann",
    "jo-ann": "Joann",
    "ace hardware": "Ace Hardware",
    "autozone": "AutoZone",
    "oreilly": "OReilly",
    "o'reilly": "OReilly",
    "advance auto": "Advance Auto",
    # Groceries
    "kroger": "Kroger",
    "whole foods": "Whole Foods",
    "trader joes": "Trader Joes",
    "trader joe's": "Trader Joes",
    "safeway": "Safeway",
    "aldi": "Aldi",
    "publix": "Publix",
    "albertsons": "Albertsons",
    "vons": "Vons",
    "ralphs": "Ralphs",
    "food lion": "Food Lion",
    "giant": "Giant",
    "stop & shop": "Stop and Shop",
    "wegmans": "Wegmans",
    "heb": "HEB",
    "h-e-b": "HEB",
    "meijer": "Meijer",
    "winco": "WinCo",
    "food 4 less": "Food 4 Less",
    "grocery outlet": "Grocery Outlet",
    "sprouts": "Sprouts",
    "smiths": "Smiths",
    "smith's": "Smiths",
    "frys": "Frys",
    "fry's": "Frys",
    "harmons": "Harmons",
    "maceys": "Maceys",
    # Coffee
    "starbucks": "Starbucks",
    "dunkin": "Dunkin",
    "dunkin donuts": "Dunkin Donuts",
    "peets": "Peets",
    "peet's": "Peets",
    "dutch bros": "Dutch Bros",
    "swig": "Swig",
    "sodalicious": "Sodalicious",
    # Pharmacy
    "cvs": "CVS",
    "walgreens": "Walgreens",
    "rite aid": "Rite Aid",
}

# Words that should stay lowercase in titles (unless first word)
LOWERCASE_WORDS = {'and', 'the', 'of', 'at', 'in', 'on', 'for', 'to', 'a', 'an'}

# Words/acronyms that should always be uppercase
UPPERCASE_WORDS = {'byu', 'cvs', 'bp', 'kfc', 'heb', 'ikea', 'atm', 'usa'}

# Special capitalization patterns (prefix: replacement)
SPECIAL_CAPS = {
    'mc': 'Mc',  # McDonald, McDonalds
}

# Keywords in vendor names that indicate food establishments
FOOD_VENDOR_KEYWORDS = {
    'restaurant', 'cafe', 'café', 'grill', 'kitchen', 'food', 'bagel', 'pizza',
    'burger', 'taco', 'sushi', 'bakery', 'deli', 'market', 'grocery', 'diner',
    'bistro', 'eatery', 'cantina', 'pizzeria', 'steakhouse', 'bbq', 'barbecue',
    'seafood', 'noodle', 'ramen', 'pho', 'thai', 'chinese', 'mexican', 'italian',
    'indian', 'korean', 'japanese', 'vietnamese', 'mediterranean', 'greek',
    'wings', 'chicken', 'sandwich', 'sub', 'wrap', 'salad', 'soup', 'buffet',
    'creamery', 'ice cream', 'frozen yogurt', 'smoothie', 'juice', 'boba',
    'bubble tea', 'tea house', 'donut', 'doughnut', 'pastry', 'dessert',
    'breakfast', 'brunch', 'lunch', 'dinner', 'catering', 'food truck',
    'el salvador', 'los ', 'la ', 'el ', 'taqueria', 'carniceria',
}

# Known food vendors that might not have obvious food keywords
KNOWN_FOOD_VENDORS = {
    'mcdonalds', 'wendys', 'burger king', 'taco bell', 'subway', 'chick-fil-a',
    'chickfila', 'chipotle', 'five guys', 'in-n-out', 'arbys', 'popeyes', 'kfc',
    'papa johns', 'dominos', 'pizza hut', 'little caesars', 'sonic',
    'jack in the box', 'carls jr', 'hardees', 'del taco', 'panda express',
    'raising canes', 'wingstop', 'buffalo wild wings', 'zaxbys', 'qdoba',
    'moes', 'panera', 'jersey mikes', 'jimmy johns', 'firehouse subs',
    'potbelly', 'noodles', 'pei wei', 'pf changs', 'olive garden', 'applebees',
    'chilis', 'red lobster', 'outback', 'texas roadhouse', 'cracker barrel',
    'ihop', 'dennys', 'waffle house', 'golden corral', 'cici', 'fazolis',
    'boba bee', 'costa vida', 'cafe rio', 'cafe zupas', 'zupas', 'noodles & co',
    'byu creamery', 'byu dining', 'cougareat', 'cannon center', 'morris center',
    'jamba', 'jamba juice', 'smoothie king', 'tropical smoothie',
    'baskin robbins', 'cold stone', 'dairy queen', 'culvers',
    'in n out', 'shake shack', 'smashburger', 'habit burger', 'fat burger',
    'wienerschnitzel', 'weinerschnitzel', 'hot dog on a stick',
}

# Food item keywords to detect in receipt text (indicates food purchase)
FOOD_ITEM_KEYWORDS = {
    # Meals and dishes
    'bagel', 'sandwich', 'burger', 'pizza', 'taco', 'burrito', 'quesadilla',
    'nachos', 'enchilada', 'fajita', 'salad', 'soup', 'wrap', 'sub',
    'hotdog', 'hot dog', 'corn dog', 'chicken', 'beef', 'pork', 'steak',
    'fish', 'shrimp', 'salmon', 'wings', 'nuggets', 'tender', 'strip',
    'fries', 'tots', 'onion rings', 'mozzarella sticks', 'breadsticks',
    'pasta', 'spaghetti', 'lasagna', 'ravioli', 'noodles', 'rice', 'fried rice',
    'egg roll', 'spring roll', 'dumpling', 'gyoza', 'wonton',
    'sushi', 'sashimi', 'roll', 'teriyaki', 'tempura', 'ramen', 'pho',
    'curry', 'tikka', 'masala', 'biryani', 'naan', 'samosa',
    'gyro', 'falafel', 'hummus', 'pita', 'shawarma', 'kebab',
    # Breakfast items
    'breakfast', 'pancake', 'waffle', 'french toast', 'eggs', 'bacon',
    'sausage', 'hash brown', 'hashbrown', 'omelette', 'omelet', 'biscuit',
    'croissant', 'muffin', 'toast', 'cereal', 'oatmeal', 'yogurt',
    # Drinks
    'drink', 'beverage', 'soda', 'pop', 'coke', 'pepsi', 'sprite', 'fanta',
    'lemonade', 'iced tea', 'sweet tea', 'juice', 'orange juice', 'apple juice',
    'coffee', 'latte', 'cappuccino', 'espresso', 'mocha', 'americano',
    'frappuccino', 'frappe', 'macchiato', 'tea', 'chai', 'matcha',
    'smoothie', 'shake', 'milkshake', 'slushie', 'slurpee', 'icee',
    'boba', 'bubble tea', 'milk tea',
    'water', 'sparkling', 'mineral water',
    # Snacks and sides
    'snack', 'chips', 'pretzel', 'popcorn', 'crackers', 'nuts', 'trail mix',
    'candy', 'chocolate', 'cookie', 'brownie', 'cake', 'pie', 'donut',
    'doughnut', 'pastry', 'danish', 'scone', 'cupcake', 'ice cream',
    'gelato', 'frozen yogurt', 'sundae', 'cone', 'parfait',
    'fruit', 'apple', 'banana', 'orange', 'grapes', 'berries',
    # Generic food terms
    'meal', 'combo', 'value meal', 'kids meal', 'happy meal', 'entree',
    'appetizer', 'side', 'dessert', 'treat', 'food', 'eat', 'dine',
    'order', 'takeout', 'take out', 'to go', 'dine in', 'delivery',
}


def has_food_items(text: str) -> bool:
    """Check if receipt text contains food-related keywords."""
    text_lower = text.lower()
    for keyword in FOOD_ITEM_KEYWORDS:
        if keyword in text_lower:
            return True
    return False


def get_category(vendor: str, ocr_text: str = "") -> str:
    """
    Get category for a vendor based on mapping, keywords, and receipt contents.

    Checks:
    1. Mixed retailers - scan receipt for food items to decide food vs retail
    2. Known vendor mappings
    3. Food vendor keywords in vendor name
    4. Known food vendor names
    5. Food item keywords in OCR text (1+ match = food)
    """
    vendor_lower = vendor.lower()
    text_lower = ocr_text.lower() if ocr_text else ""

    # Check for mixed retailers first (Target, Walmart, Costco, etc.)
    # These need receipt text analysis to determine food vs retail
    for mixed_vendor in MIXED_RETAILERS:
        if mixed_vendor in vendor_lower:
            if text_lower and has_food_items(text_lower):
                return "food"
            return "retail"

    # Check explicit vendor mappings
    for known_vendor, category in VENDOR_CATEGORIES.items():
        if known_vendor in vendor_lower:
            return category

    # Check if vendor name contains food-related keywords
    for keyword in FOOD_VENDOR_KEYWORDS:
        if keyword in vendor_lower:
            return "food"

    # Check if vendor is a known food establishment
    for food_vendor in KNOWN_FOOD_VENDORS:
        if food_vendor in vendor_lower:
            return "food"

    # Check receipt text for food item keywords (1+ match = food)
    if text_lower and has_food_items(text_lower):
        return "food"

    return "other"


def standardize_vendor_name(raw_name: str) -> str:
    """
    Standardize vendor name with proper capitalization.

    - Removes apostrophes
    - Applies title case with smart exceptions
    - Handles acronyms (BYU, CVS, etc.)
    - Handles special patterns (Mc prefix, etc.)
    """
    if not raw_name:
        return "Unknown Vendor"

    # Remove apostrophes
    name = raw_name.replace("'", "").replace("'", "")

    # Check for exact match in known vendors (case-insensitive)
    name_lower = name.lower().strip()
    if name_lower in KNOWN_VENDOR_NAMES:
        return KNOWN_VENDOR_NAMES[name_lower]

    # Check for partial match with known vendors
    for known_key, known_name in KNOWN_VENDOR_NAMES.items():
        if known_key in name_lower:
            return known_name

    # Apply smart title case
    words = name.split()
    result_words = []

    for i, word in enumerate(words):
        word_lower = word.lower()

        # Check if it's an uppercase acronym
        if word_lower in UPPERCASE_WORDS:
            result_words.append(word.upper())
            continue

        # Check for special capitalization patterns (like Mc)
        handled = False
        for prefix, replacement in SPECIAL_CAPS.items():
            if word_lower.startswith(prefix) and len(word_lower) > len(prefix):
                # Apply pattern: McDonalds, McCafe, etc.
                rest = word[len(prefix):]
                result_words.append(replacement + rest.capitalize())
                handled = True
                break

        if handled:
            continue

        # Lowercase words (unless first word)
        if i > 0 and word_lower in LOWERCASE_WORDS:
            result_words.append(word_lower)
            continue

        # Default: capitalize first letter
        result_words.append(word.capitalize())

    return ' '.join(result_words)


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

        # Remove apostrophes for matching
        line_normalized = line_clean.lower().replace("'", "").replace("'", "")

        # Check against known vendor names dictionary
        for known_key in KNOWN_VENDOR_NAMES.keys():
            if known_key.replace("'", "") in line_normalized:
                return KNOWN_VENDOR_NAMES[known_key]

        # Check category mapping for partial matches
        for vendor_key in VENDOR_CATEGORIES.keys():
            if vendor_key in line_normalized:
                # Found a category match, standardize the line
                return standardize_vendor_name(line_clean[:50])

    # Fallback: use first non-empty line that looks like a name
    for line in lines[:5]:
        line_clean = line.strip()
        if line_clean and len(line_clean) > 3:
            if not re.match(r'^[\d\s\-\/\.\$]+$', line_clean):
                # Standardize the extracted name
                return standardize_vendor_name(line_clean[:50])

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
        category = get_category(vendor, text)

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
