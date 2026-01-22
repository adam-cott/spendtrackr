# Receipt Spend Tracker

A web application that scans receipt photos using OCR and tracks expenses. Works locally without any external APIs.

## Features

- Upload receipt images (JPG, PNG)
- OCR-powered receipt scanning (Tesseract)
- Auto-extracts vendor, total amount, and date
- Auto-categorization of vendors
- Edit extracted data before saving
- Export expenses to Excel (.xlsx)
- Data persists in browser localStorage

---

## Setup

### 1. Install Tesseract OCR

**Windows:**
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (default path: `C:\Program Files\Tesseract-OCR`)
3. Add to PATH or the app will auto-detect it

**Mac:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt install tesseract-ocr
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the App

```bash
python api/analyze.py
```

Then open `index.html` in your browser, or serve it:

```bash
# In another terminal
python -m http.server 8000
# Open http://localhost:8000
```

---

## Deploy to Vercel

> **Note:** Vercel's serverless environment doesn't include Tesseract by default. For cloud deployment, you'd need to use a custom runtime or Docker. This app is designed primarily for local use.

For local/self-hosted deployment:
1. Push to GitHub
2. Deploy on a server with Tesseract installed
3. Run with gunicorn or similar

---

## Project Structure

```
.
├── api/
│   └── analyze.py      # Flask API with Tesseract OCR
├── index.html          # Web frontend
├── vercel.json         # Vercel config (limited support)
├── requirements.txt    # Python dependencies
└── README.md
```

## How It Works

1. Upload a receipt image
2. Tesseract OCR extracts text from the image
3. Parser identifies:
   - **Vendor**: Matches known vendors or uses first text line
   - **Total**: Looks for "Total" labels or largest dollar amount
   - **Date**: Recognizes common date formats
4. Auto-categorizes based on vendor name
5. Review/edit and save to your expense list
6. Export to Excel anytime

## Supported Vendors (Auto-categorized)

| Category | Vendors |
|----------|---------|
| Fast Food | McDonald's, Burger King, Wendy's, Taco Bell, Chick-fil-A, Subway, Chipotle |
| Gas | Shell, Exxon, Chevron, BP, Mobil, Speedway |
| Retail | Target, Walmart, Costco, Amazon, Best Buy |
| Groceries | Kroger, Whole Foods, Trader Joe's, Safeway, Aldi, Publix |
| Coffee | Starbucks, Dunkin', Peet's |
| Pharmacy | CVS, Walgreens, Rite Aid |

Unknown vendors are categorized as "Other".

## Tech Stack

- **Frontend**: HTML/CSS/JavaScript
- **Backend**: Python Flask
- **OCR**: Tesseract via pytesseract
- **Excel Export**: SheetJS (browser-side)
