# Receipt Spend Tracker

A web application that processes receipt photos and tracks expenses. Works in **demo mode** by default (no API key needed), or enable real AI-powered receipt scanning with a Claude API key.

## Features

- Upload receipt images (JPG, PNG)
- AI-powered receipt analysis (or demo mode with sample data)
- Auto-categorization of vendors
- Edit extracted data before saving
- Track expenses with payment source and descriptions
- Export expenses to Excel (.xlsx)
- Data persists in browser localStorage

---

## Deploy to Vercel (Step-by-Step)

### Step 1: Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Receipt Spend Tracker app"

# Create a new repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/receipt-tracker.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Click **"Add New Project"**
3. Select your `receipt-tracker` repository
4. Click **"Deploy"** (no configuration needed!)
5. Wait for deployment to complete
6. Your app is live at `https://your-project.vercel.app`

That's it! The app works immediately in **demo mode**.

---

## Optional: Enable Real Receipt Scanning

To use Claude AI for actual receipt analysis:

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)
2. In Vercel dashboard, go to your project → **Settings** → **Environment Variables**
3. Add: `ANTHROPIC_API_KEY` = `sk-ant-...your-key...`
4. Redeploy (or it will apply on next deploy)

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

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
│   └── analyze.py      # Vercel serverless function
├── index.html          # Web frontend
├── vercel.json         # Vercel configuration
├── requirements.txt    # Python dependencies
└── README.md
```

## Tech Stack

- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Backend**: Python Flask (Vercel Serverless)
- **AI**: Claude Sonnet (optional)
- **Excel Export**: SheetJS
