# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run API server (port 5000)
python api/analyze.py

# Serve frontend (port 8000, run in separate terminal)
python -m http.server 8000
```

Requires `OCR_SPACE_API_KEY` environment variable. Create a `.env` file or set it directly.

## Architecture

This is a receipt expense tracking app with two components:

**Backend (`api/analyze.py`)**: Flask API deployed as a Vercel serverless function
- Single endpoint `POST /api/analyze` accepts base64-encoded receipt images
- Calls OCR.space API to extract text from images
- Parses OCR text with regex to extract vendor, total amount, and date
- Auto-categorizes vendors using `VENDOR_CATEGORIES` dict (partial string matching)
- Returns JSON with extracted fields

**Frontend (`index.html`)**: Single-page vanilla JS application
- Handles image upload via drag-drop or file picker
- Sends images to `/api/analyze` endpoint
- Stores expenses in browser localStorage
- Exports to Excel using SheetJS library (loaded from CDN)

**Vercel Config (`vercel.json`)**: Routes `/api/analyze` to the Python function, everything else to `index.html`.

## Key Implementation Details

- OCR uses Engine 2 (`OCREngine: 2`) which works better for receipts
- Total extraction: first looks for lines containing "total", falls back to largest dollar amount found
- Vendor extraction: checks first 10 lines against `KNOWN_VENDORS` list, falls back to first non-numeric line
- Date parsing: supports MM/DD/YYYY, YYYY-MM-DD, and "Month DD, YYYY" formats
- Frontend expense IDs use `Date.now()` timestamps
