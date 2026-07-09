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

Requires environment variables — create a `.env` file:
```
OCR_SPACE_API_KEY=...
GMAIL_ADDRESS=...
GMAIL_APP_PASSWORD=...
RECEIPT_NOTIFICATION_EMAIL=...
APP_PIN=...
FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account",...}
```

## Architecture

This is a receipt expense tracking app. The frontend is a single `index.html` file; the backend is three Python serverless functions deployed on Vercel.

**Backend (`api/analyze.py`)**: OCR endpoint
- `POST /api/analyze` accepts base64-encoded receipt images
- Calls OCR.space API (Engine 2) to extract text
- Parses OCR text with regex to extract vendor, total amount, and date
- Auto-categorizes vendors using `VENDOR_CATEGORIES` dict (partial string matching)
- Returns JSON with extracted fields

**Backend (`api/send-email.py`)**: Email notification endpoint
- `POST /api/send-email` accepts amount, date, and base64 image
- Sends receipt photo as email attachment via Gmail SMTP
- Credentials come from `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `RECEIPT_NOTIFICATION_EMAIL` env vars

**Backend (`api/verify-pin.py`)**: PIN authentication endpoint
- `POST /api/verify-pin` accepts a 4-digit PIN
- Compares against `APP_PIN` env var using constant-time comparison (timing-attack safe)
- Rate limits by IP: 8 attempts max, 5-minute lockout
- On success, mints a Firebase Auth custom token via the Admin SDK (`firebase-admin`) using `FIREBASE_SERVICE_ACCOUNT_KEY` env var
- Returns the custom token to the client

**Frontend (`index.html`)**: Single-page vanilla JS application
- PIN screen shown on load; calls `/api/verify-pin`, then calls `signInWithCustomToken` to establish a Firebase Auth session
- `onAuthStateChanged` drives data loading — Firestore queries only run once a valid auth session exists
- Handles image upload via drag-drop, file picker, or in-browser camera
- Compresses images client-side (canvas) before sending to OCR
- Sends images to `/api/analyze` for OCR, pre-fills expense form with results
- On save: uploads receipt photo to Firebase Storage, writes expense record to Firestore with the Storage download URL attached as `imageUrl`
- Expense list renders a receipt icon per row that opens the stored image in a new tab
- Exports to Excel using SheetJS library (loaded from CDN)

**Firebase (client-side SDK loaded via CDN — `firebase-app`, `firebase-firestore`, `firebase-storage`, `firebase-auth`)**:
- Initialized in a `<script type="module">` block; instances exposed on `window` (e.g. `window.db`, `window.storage`, `window.auth`) for use by the main script
- **Firestore**: `receipts` collection stores expense records (date, vendor, amount, category, description, payment_source, imageUrl)
- **Storage**: receipt images stored at `receipts/{timestamp}-receipt.jpg`
- **Auth**: custom token flow — server mints token, client signs in with `signInWithCustomToken`; persistence set based on "Remember me" checkbox (`browserLocalPersistence` vs `browserSessionPersistence`)

**Vercel Config (`vercel.json`)**: Routes `/api/*` to Python functions, everything else to `index.html`.

## Key Implementation Details

- OCR uses Engine 2 (`OCREngine: 2`) which works better for receipts
- Total extraction: first looks for lines containing "total", falls back to largest dollar amount found
- Vendor extraction: checks first 10 lines against `KNOWN_VENDORS` list, falls back to first non-numeric line
- Date parsing: supports MM/DD/YYYY, YYYY-MM-DD, and "Month DD, YYYY" formats
- Image upload to Storage is non-blocking — if it fails, the expense still saves to Firestore without an `imageUrl`, and the toast notes the photo wasn't stored
- Firestore and Storage security rules require `request.auth != null`, so all reads/writes require a valid Firebase Auth session
- Firebase Admin SDK initialized once per cold start using `if not firebase_admin._apps` guard
- `logout()` calls `signOut(window.auth)` to end the Firebase session, then clears the expense list before showing the PIN screen
