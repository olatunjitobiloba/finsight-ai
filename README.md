# FinSight AI

> Predict. Prevent. Prosper.

FinSight AI is a financial intelligence platform built for Nigerians. It turns bank SMS alerts, PDF statements, and CSV exports into a real-time financial health score, behavioral pattern analysis, and actionable AI-generated recommendations — powered by Interswitch for payment execution.

Built for the Interswitch x Enyata BeyondTheRails Hackathon 2026.

---

## Live Deployments

| Service | URL |
|---|---|
| Main Backend | https://finsightng.vercel.app |
| PDF Parser Service | https://margaret-06-finsight-pdf.hf.space |
| Frontend | https://finsightng.vercel.app |

---

## What It Does

Most Nigerians do not run out of money because they are poor. They run out because they have no warning system.

FinSight AI solves this by:

- Parsing Nigerian bank SMS alerts, PDF statements, and CSV exports automatically
- Computing a Financial Health Score (0-100) across 5 pillars
- Predicting days until zero balance based on current burn rate
- Detecting behavioral patterns such as post-income spending spikes and weekend overspending
- Generating personalized AI financial advice via Groq LLM
- Executing savings and bill payment actions through Interswitch Sandbox APIs

---

## Architecture

```
Frontend (Vercel Static)
     |
     |-- SMS / CSV input  -->  POST /api/analyze       (Vercel)
     |-- PDF upload       -->  POST /parse-statement   (Hugging Face)
     |
     v
Main Backend (Vercel Serverless - FastAPI)
     |
     |-- services/sms_parser.py      SMS extraction (Access, GTBank, UBA, Zenith, FirstBank)
     |-- services/csv_parser.py      CSV transaction parsing
     |-- services/score_engine.py    Financial Health Score engine
     |-- services/ai_actions.py      Data-driven action generator
     |-- services/interswitch.py     Interswitch Sandbox integration
     |-- services/db.py              Supabase database layer
     |
     v
PDF Parser Service (Hugging Face Spaces - Docker)
     |
     |-- UBA precision text parser
     |-- Access Bank precision text parser
     |-- 10 additional bank configs (GTBank, Zenith, FirstBank, etc.)
     |-- Supabase save on parse
     |-- Groq AI insights generation
     v
Supabase (PostgreSQL)
     transactions, user_bank_profiles, bill_setups
```

---

## Project Structure

```
finsight-ai/
|
|-- api/
|   |-- __init__.py
|   |-- main.py                  FastAPI app entry point
|   |-- routes/
|       |-- __init__.py
|       |-- analyze.py           POST /api/analyze
|       |-- score.py             POST /api/score
|       |-- parse.py             POST /api/parse/sms, /api/parse/csv
|       |-- health.py            GET  /health
|
|-- services/
|   |-- __init__.py
|   |-- sms_parser.py            Nigerian bank SMS parser
|   |-- csv_parser.py            CSV transaction parser
|   |-- score_engine.py          Financial Health Score engine
|   |-- ai_actions.py            AI-driven action generator
|   |-- interswitch.py           Interswitch Sandbox API client
|   |-- db.py                    Supabase database layer
|   |-- demo_seeder.py           Sample data for testing
|
|-- frontend/
|   |-- index.html               Landing page
|   |-- dashboard.html           Main app dashboard
|   |-- assets/
|       |-- app.js
|       |-- style.css
|   |-- manifest.json            PWA manifest
|   |-- sw.js                    Service worker (offline support)
|
|-- pdf_service/                 Deployed separately on Hugging Face
|   |-- main.py                  PDF parser + /insights endpoint
|   |-- requirements.txt
|   |-- Dockerfile
|
|-- vercel.json
|-- requirements.txt
|-- .env.local                   Not committed
```

---

## API Endpoints

### Main Backend (Vercel)

| Method | Endpoint | Description |
|---|---|---|
| GET | /health | Health check |
| POST | /api/analyze | Full analysis from SMS or CSV input |
| POST | /api/score | Standalone score calculation |
| POST | /api/parse/sms | Parse single Nigerian bank SMS |
| POST | /api/parse/sms/batch | Parse multiple SMS messages |
| POST | /api/parse/csv | Parse CSV bank statement |
| POST | /api/savings/plan | Create savings plan via Interswitch |
| POST | /api/savings/analyze | Analyze spending and recommend savings |
| POST | /api/savings/bills/optimize | Bill optimization via Interswitch |
| GET | /api/parse/banks | List supported banks |
| GET | /api/parse/demo | Sample data for testing |

### PDF Parser Service (Hugging Face)

| Method | Endpoint | Description |
|---|---|---|
| GET | /health | Health check |
| POST | /api/parse/pdf | Upload and parse PDF directly |
| POST | /parse-statement | Parse PDF from URL, save to Supabase |
| GET | /transactions/{user_id} | Fetch saved transactions |
| POST | /insights | AI-generated financial insights via Groq |

---

## Supported Banks

| Bank | SMS Parsing | PDF Parsing |
|---|---|---|
| Access Bank | Yes | Yes (precision parser) |
| UBA | Yes | Yes (precision parser) |
| GTBank | Yes | Config-based |
| Zenith Bank | Yes | Config-based |
| First Bank | Yes | Config-based |
| Stanbic | No | Config-based |
| Fidelity | No | Config-based |
| Sterling | No | Config-based |
| Polaris | No | Config-based |
| FCMB | No | Config-based |
| Wema | No | Config-based |
| Ecobank | No | Config-based |

---

## Financial Health Score

The score is computed across 5 pillars:

| Pillar | Weight | What It Measures |
|---|---|---|
| Income Stability | 25 | Consistency and presence of income |
| Spending Control | 25 | Ratio of expenses to income |
| Savings Behavior | 20 | Whether savings transactions exist |
| Bill Regularity | 15 | Recurring bill payment consistency |
| Category Diversity | 15 | Spread of spending across categories |

Score grades:

- 80-100: Excellent (A)
- 65-79: Good (B)
- 50-64: Moderate Risk (C)
- 35-49: High Risk (D)
- 0-34: Critical (F)

---

## Interswitch Integration

FinSight AI integrates with the Interswitch Sandbox API for:

- Savings simulation via Quickteller
- Bill payment optimization (electricity, water, DSTV, airtime, data)
- Transaction verification

All payment actions in the current build use the Interswitch Sandbox environment. No real money is moved.

---

## Environment Variables

Create a `.env.local` file in the project root:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
INTERSWITCH_CLIENT_ID=your-client-id
INTERSWITCH_CLIENT_SECRET=your-client-secret
GROQ_API_KEY=your-groq-key
PDF_SERVICE_URL=https://margaret-06-finsight-pdf.hf.space
```

For the PDF service (Hugging Face Secrets):

```
SUPABASE_URL
SUPABASE_SERVICE_KEY
GROQ_API_KEY
```

---

## Local Development

```bash
# Clone the repo
git clone https://github.com/olatunjitobiloba/finsight-ai.git
cd finsight-ai

# Install dependencies
pip install -r requirements.txt

# Run the backend locally
uvicorn api.main:app --reload --port 8000

# Visit API docs
http://localhost:8000/docs
```

---

## Database Schema

Run in Supabase SQL Editor:

```sql
CREATE TABLE transactions (
  id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id          TEXT NOT NULL,
  amount           NUMERIC NOT NULL,
  type             TEXT NOT NULL,
  category         TEXT DEFAULT 'Uncategorized',
  description      TEXT,
  transaction_date DATE,
  source           TEXT DEFAULT 'sms',
  bank             TEXT,
  balance          NUMERIC,
  hash             VARCHAR(64) UNIQUE,
  created_at       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_bank_profiles (
  id             UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id        TEXT NOT NULL UNIQUE,
  bank_name      TEXT,
  account_number TEXT,
  created_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE bill_setups (
  id           UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id      TEXT NOT NULL,
  bill_type    TEXT NOT NULL,
  biller_code  TEXT NOT NULL,
  customer_id  TEXT NOT NULL,
  amount       NUMERIC,
  auto_pay     BOOLEAN DEFAULT FALSE,
  created_at   TIMESTAMP DEFAULT NOW()
);
```

---

## Team

| Name | Role |
|---|---|
| Olatunji Franklin (Toby) | ML Engineer — Score engine, AI actions, frontend, deployment |
| Margaret Adeniran | Backend Engineer — PDF parser, Supabase integration, Hugging Face deployment |
| Pogbe | Systems Engineer — Interswitch integration, SMS parser, API gateway |

Covenant University, Computer Engineering — BeyondTheRails Hackathon 2026

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Database | Supabase (PostgreSQL) |
| AI Insights | Groq (llama-3.3-70b-versatile) |
| PDF Parsing | pdfplumber, pikepdf |
| Payments | Interswitch Sandbox API |
| Frontend Hosting | Vercel |
| PDF Service Hosting | Hugging Face Spaces (Docker) |
| PWA | HTML, CSS, Vanilla JS, Service Worker |