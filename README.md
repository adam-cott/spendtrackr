# Receipt Spend Tracker

A web application that scans receipt photos using OCR and tracks expenses. Works on Vercel with just a free API key.

## Features

- Upload receipt images (JPG, PNG)
- OCR-powered receipt scanning (OCR.space API)
- Auto-extracts vendor, total amount, and date
- Auto-categorization of vendors
- Edit extracted data before saving
- Export expenses to Excel (.xlsx)
- Data persists in browser localStorage

---

## Quick Start

### 1. Get a Free OCR.space API Key

1. Go to [ocr.space/ocrapi](https://ocr.space/ocrapi)
2. Click "Get Free API Key"
3. Enter your email and get your key instantly

### 2. Deploy to Vercel

1. Push this repo to GitHub
2. Go to [vercel.com](https://vercel.com) and import the repo
3. Add environment variable: `OCR_SPACE_API_KEY` = your key
4. Deploy!

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo "OCR_SPACE_API_KEY=your_key_here" > .env

# Run the API server
python api/analyze.py

# In another terminal, serve the frontend
python -m http.server 8000

# Open http://localhost:8000
```

---

## Project Structure

```
.
├── api/
│   └── analyze.py      # Flask API with OCR.space integration
├── index.html          # Web frontend
├── vercel.json         # Vercel configuration
├── requirements.txt    # Python dependencies
└── README.md
```

## How It Works

1. Upload a receipt image
2. OCR.space extracts text from the image
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
- **OCR**: OCR.space free API
- **Excel Export**: SheetJS (browser-side)
- **Hosting**: Vercel
