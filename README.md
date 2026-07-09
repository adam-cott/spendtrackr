# SpendTrackr

A free receipt expense tracking web app that scans receipt photos using OCR, automatically extracts expense data, stores everything in Firebase, and sends email notifications with receipt attachments.

**Live Demo:** [spendtrackr-five.vercel.app](https://spendtrackr-five.vercel.app)

## Features

- **Receipt Scanning** - Upload receipt photos (JPG, PNG) from phone or computer
- **Auto-Extraction** - OCR extracts vendor, total amount, date, and category
- **Smart Categorization** - Auto-categorizes 100+ known vendors (food, gas, retail, etc.)
- **Image Compression** - Automatically compresses large phone photos before processing
- **Cloud Database** - Expenses saved to Firestore - accessible from any device
- **Receipt Storage** - Original receipt photos stored in Firebase Storage, viewable per expense in the app
- **Email Notifications** - Sends receipt photo to a configurable email address when saved
- **Excel Export** - Download all expenses as .xlsx spreadsheet
- **529 Tracking** - Marks education-eligible expenses (food, textbooks)
- **PIN Authentication** - 4-digit PIN gate backed by Firebase Auth custom tokens
- **Mobile Responsive** - Works great on phones for scanning receipts on-the-go

## Cost: $0/month

All services used have generous free tiers:
- **OCR.space** - 25,000 requests/month free
- **Firebase** - Generous free tier (Spark plan): 1GB Firestore storage, 5GB Storage, 10K Auth verifications/month
- **Gmail SMTP** - ~500 emails/day free
- **Vercel** - Hobby tier free hosting

---

## Quick Start

### 1. Get Free API Keys

**OCR.space** (for receipt scanning):
1. Go to [ocr.space/ocrapi](https://ocr.space/ocrapi)
2. Click "Get Free API Key"
3. Enter your email and get your key instantly

**Gmail App Password** (for email notifications):
1. Enable 2-Step Verification at [myaccount.google.com/security](https://myaccount.google.com/security)
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Create an App Password for "Mail" → "Other (SpendTrackr)"
4. Copy the 16-character password (remove spaces)

### 2. Set Up Firebase

1. Go to [console.firebase.google.com](https://console.firebase.google.com) and create a project
2. Enable **Firestore Database** (start in production mode, then update rules below)
3. Enable **Firebase Storage** (update rules below)
4. Enable **Authentication** (no sign-in providers needed — the app uses custom tokens)
5. Go to **Project Settings → General** and copy the web app config values
6. Go to **Project Settings → Service Accounts → Generate new private key** to download the service account JSON (used by the backend)

**Firestore security rules** (Firestore → Rules):
```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

**Storage security rules** (Storage → Rules):
```
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /{allPaths=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

### 3. Deploy to Vercel

1. Fork/push this repo to GitHub
2. Go to [vercel.com](https://vercel.com) and import the repo
3. Add environment variables (see below)
4. Deploy!

---

## Environment Variables

### Backend (Vercel → Project → Settings → Environment Variables)

| Variable | Description | Example |
|----------|-------------|---------|
| `OCR_SPACE_API_KEY` | Your OCR.space API key | `K83a7b2c...` |
| `GMAIL_ADDRESS` | Gmail account for sending notifications | `myapp@gmail.com` |
| `GMAIL_APP_PASSWORD` | 16-char App Password (no spaces) | `abcdefghijklmnop` |
| `RECEIPT_NOTIFICATION_EMAIL` | Where to send receipt notifications | `expenses@company.com` |
| `APP_PIN` | 4-digit PIN for app access | `1234` |
| `FIREBASE_SERVICE_ACCOUNT_KEY` | Full service account JSON (single line) | `{"type":"service_account",...}` |

### Frontend (hardcoded in `index.html`)

The Firebase web config values are embedded directly in `index.html` (they are safe to include in client-side code — Firebase security rules enforce access control):

| Config key | Where to find it |
|------------|-----------------|
| `apiKey` | Firebase Console → Project Settings → General → Your apps |
| `authDomain` | same |
| `projectId` | same |
| `storageBucket` | same |
| `messagingSenderId` | same |
| `appId` | same |
| `measurementId` | same (Analytics section) |

---

## Email Notifications

When a receipt is saved, an email is automatically sent with:
- **Subject:** `$Amount   Date` (e.g., `$24.99   1/28/2026`)
- **Body:** Brief receipt summary
- **Attachment:** The receipt photo as a JPG

The recipient email is fully configurable via the `RECEIPT_NOTIFICATION_EMAIL` environment variable.

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your credentials
cat > .env << EOF
OCR_SPACE_API_KEY=your_ocr_key
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=your_app_password
RECEIPT_NOTIFICATION_EMAIL=recipient@example.com
APP_PIN=1234
FIREBASE_SERVICE_ACCOUNT_KEY={"type":"service_account",...}
EOF

# Run the API server (port 5000)
python api/analyze.py

# In another terminal, serve the frontend (port 8000)
python -m http.server 8000

# Open http://localhost:8000
```

---

## Project Structure

```
.
├── api/
│   ├── analyze.py       # OCR receipt scanning endpoint
│   ├── send-email.py    # Email notification endpoint
│   └── verify-pin.py    # PIN auth + Firebase custom token minting
├── index.html           # Single-page web app (HTML/CSS/JS)
├── vercel.json          # Vercel serverless configuration
├── requirements.txt     # Python dependencies
├── CLAUDE.md            # AI assistant context
└── README.md
```

## How It Works

1. **PIN** - Enter 4-digit PIN; server verifies it and mints a Firebase custom token
2. **Sign in** - Client calls `signInWithCustomToken` to establish a real Firebase Auth session
3. **Upload** - Select or drag-drop a receipt photo (or use camera)
4. **Compress** - Large images auto-compressed to under 1MB
5. **Scan** - OCR.space extracts text from the image
6. **Parse** - Extracts vendor, amount, date from OCR text
7. **Categorize** - Matches vendor against 100+ known businesses
8. **Review** - Edit any fields before saving
9. **Save** - Uploads photo to Firebase Storage, saves expense record to Firestore with the image URL
10. **Notify** - Sends email with receipt attachment
11. **Export** - Download all expenses as Excel anytime

## Supported Vendors (Auto-categorized)

| Category | Example Vendors |
|----------|-----------------|
| Food | McDonald's, Chipotle, Panda Express, Olive Garden, local restaurants |
| Gas | Shell, Exxon, Chevron, Maverik, Costco Gas |
| Retail | Target, Walmart, Amazon, Best Buy, Home Depot |
| Groceries | Kroger, Whole Foods, Trader Joe's, Costco, Aldi |
| Coffee | Starbucks, Dunkin', Dutch Bros, local cafes |
| Pharmacy | CVS, Walgreens, Rite Aid |
| Entertainment | AMC, Regal, Netflix, Spotify |
| Textbooks | BYU Bookstore, Amazon Books, campus stores |

Unknown vendors default to "Other" category.

## Tech Stack

- **Frontend:** Vanilla HTML/CSS/JavaScript
- **Backend:** Python Flask (Vercel Serverless Functions)
- **Database:** Firebase Firestore
- **Image Storage:** Firebase Storage
- **Authentication:** Firebase Auth (custom tokens minted server-side after PIN verification)
- **OCR:** OCR.space API
- **Email:** Gmail SMTP
- **Excel Export:** SheetJS (client-side)
- **Hosting:** Vercel

## License

MIT
