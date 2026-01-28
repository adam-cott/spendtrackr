# SpendTrackr

A free receipt expense tracking web app that scans receipt photos using OCR, automatically extracts expense data, stores it in a cloud database, and sends email notifications with receipt attachments.

**Live Demo:** [spendtrackr-five.vercel.app](https://spendtrackr-five.vercel.app)

## Features

- **Receipt Scanning** - Upload receipt photos (JPG, PNG) from phone or computer
- **Auto-Extraction** - OCR extracts vendor, total amount, date, and category
- **Smart Categorization** - Auto-categorizes 100+ known vendors (food, gas, retail, etc.)
- **Image Compression** - Automatically compresses large phone photos before processing
- **Cloud Database** - Expenses saved to Supabase (PostgreSQL) - accessible anywhere
- **Email Notifications** - Sends receipt photo to a configurable email address when saved
- **Excel Export** - Download all expenses as .xlsx spreadsheet
- **529 Tracking** - Marks education-eligible expenses (food, textbooks)
- **Mobile Responsive** - Works great on phones for scanning receipts on-the-go

## Cost: $0/month

All services used have generous free tiers:
- **OCR.space** - 25,000 requests/month free
- **Supabase** - 500MB database free
- **Gmail SMTP** - ~500 emails/day free
- **Vercel** - Hobby tier free hosting

---

## Quick Start

### 1. Get Free API Keys

**OCR.space** (for receipt scanning):
1. Go to [ocr.space/ocrapi](https://ocr.space/ocrapi)
2. Click "Get Free API Key"
3. Enter your email and get your key instantly

**Supabase** (for database):
1. Go to [supabase.com](https://supabase.com) and create a project
2. Go to Project Settings → API
3. Copy your Project URL and `anon` public key

**Gmail App Password** (for email notifications):
1. Enable 2-Step Verification at [myaccount.google.com/security](https://myaccount.google.com/security)
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Create an App Password for "Mail" → "Other (SpendTrackr)"
4. Copy the 16-character password (remove spaces)

### 2. Set Up Supabase Database

Run this SQL in Supabase SQL Editor to create the receipts table:

```sql
CREATE TABLE receipts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  date DATE NOT NULL,
  vendor TEXT NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  category TEXT NOT NULL,
  description TEXT,
  payment_source TEXT
);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE receipts ENABLE ROW LEVEL SECURITY;

-- Allow all operations for anonymous users (for simple setup)
CREATE POLICY "Allow all" ON receipts FOR ALL USING (true);
```

### 3. Deploy to Vercel

1. Fork/push this repo to GitHub
2. Go to [vercel.com](https://vercel.com) and import the repo
3. Add environment variables (see below)
4. Deploy!

---

## Environment Variables

Configure these in Vercel Dashboard → Project → Settings → Environment Variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `OCR_SPACE_API_KEY` | Your OCR.space API key | `K83a7b2c...` |
| `GMAIL_ADDRESS` | Gmail account for sending notifications | `myapp@gmail.com` |
| `GMAIL_APP_PASSWORD` | 16-char App Password (no spaces) | `abcdefghijklmnop` |
| `RECEIPT_NOTIFICATION_EMAIL` | Where to send receipt notifications | `expenses@company.com` |

**Note:** The sender (`GMAIL_ADDRESS`) and recipient (`RECEIPT_NOTIFICATION_EMAIL`) can be different. You can send notifications to any email address - yourself, a family member, an accountant, etc.

---

## Email Notifications

When a receipt is saved, an email is automatically sent with:
- **Subject:** `$Amount   Date` (e.g., `$24.99   1/28/2026`)
- **Body:** Brief receipt summary
- **Attachment:** The receipt photo as a JPG

The recipient email is fully configurable via the `RECEIPT_NOTIFICATION_EMAIL` environment variable. This allows you to:
- Send to yourself for record-keeping
- Send to a family member for shared expense tracking
- Send to an accountant or bookkeeper
- Send to any email that needs receipt copies

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
│   └── send-email.py    # Email notification endpoint
├── index.html           # Single-page web app (HTML/CSS/JS)
├── vercel.json          # Vercel serverless configuration
├── requirements.txt     # Python dependencies
├── CLAUDE.md            # AI assistant context
└── README.md
```

## How It Works

1. **Upload** - Select or drag-drop a receipt photo
2. **Compress** - Large images auto-compressed to under 1MB
3. **Scan** - OCR.space extracts text from the image
4. **Parse** - Extracts vendor, amount, date from OCR text
5. **Categorize** - Matches vendor against 100+ known businesses
6. **Review** - Edit any fields before saving
7. **Save** - Stores to Supabase database
8. **Notify** - Sends email with receipt attachment
9. **Export** - Download all expenses as Excel anytime

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
- **Database:** Supabase (PostgreSQL)
- **OCR:** OCR.space API
- **Email:** Gmail SMTP
- **Excel Export:** SheetJS (client-side)
- **Hosting:** Vercel

## License

MIT
