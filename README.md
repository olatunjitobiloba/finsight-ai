# FinSight AI

**Predict. Prevent. Prosper.**

FinSight AI is a financial intelligence platform built for Nigerians.
It predicts when you will run out of money, explains why it keeps happening, and executes a fix instantly using Interswitch.

Built for the **Interswitch x Enyata BeyondTheRails Hackathon 2026**.

---



Paste your bank alerts. In seconds, FinSight tells you:

- The exact day you will go broke
- Why it keeps happening
- What to do next
- And executes the fix via Interswitch

No spreadsheets. No manual tracking. No guesswork.

---

## The Problem

Every Nigerian knows this moment:

You check your account balance and your money is gone.

Not because you did not earn.
But because you did not see it coming.

Most people do not fail financially due to lack of income.
They fail because they lack a system that detects risky financial behavior early and helps them act in time.

FinSight AI solves this by turning everyday financial data into a real-time early warning system.

---

## What Happens in 10 Seconds

1. Paste bank SMS alerts or upload a statement
2. Click Analyze

FinSight instantly returns:

- "You will run out of money in 8 days"
- "You overspend every weekend"
- "Food spending increased 42% this week"

3. Click "Fix This"

- "Reduce food spending by ₦1,500/day"
- "Switch to a weekly data plan to save ₦8,000/month"

4. Execute

- Airtime or bill payment triggered via Interswitch

FinSight does not stop at insight. It takes action.

---

## Signature Capability: Days to Zero

FinSight AI predicts how many days remain before a user's balance reaches zero based on real spending behavior.

This transforms invisible financial risk into a clear, urgent signal that users can act on immediately.

---

## What Makes FinSight Different

Other apps explain your past.
FinSight confronts your future.

| Traditional Finance Apps | FinSight AI |
|---|---|
| Show past transactions | Predict future cash position |
| Require manual tracking | Parse SMS, CSV, and PDF automatically |
| Provide generic advice | Generate precise, personalized actions |
| Stop at insights | Execute actions via Interswitch |

---

## What It Does

- Converts raw financial data (SMS, CSV, PDF) into structured transactions
- Predicts how long a user can sustain their current spending
- Detects behavioral patterns such as weekend overspending and post-salary spikes
- Generates data-driven, personalized financial actions
- Executes those actions instantly using Interswitch payment infrastructure

---

## Why This Matters in Nigeria

Nigeria does not yet have widespread open banking infrastructure.

Most financial tools cannot access user data directly.
FinSight solves this by using what every user already has:

- Bank SMS alerts
- Statement exports

This creates a powerful alternative data layer for financial intelligence without requiring bank integrations.

---

## Interswitch Integration

FinSight connects insight to execution using Interswitch.

Users can:

- Purchase airtime or data based on optimized recommendations
- Pay bills more efficiently (electricity, DSTV, subscriptions)
- Act on financial decisions instantly without leaving the platform

FinSight does not just analyze financial behavior.
It changes it in real time.

All transactions in this build are executed using the Interswitch Sandbox environment.

---

## Architecture Overview

```
Frontend (Vercel)
     |
     |-- SMS / CSV input  -->  /api/analyze
     |-- PDF upload       -->  /parse-statement (HF Space)
     |
     v
Backend (FastAPI on Vercel)
     |
     |-- SMS parser (multi-bank support)
     |-- CSV parser + validation
     |-- Score engine (financial health)
     |-- Behavior detection engine
     |-- AI action generator (data-driven)
     |-- Interswitch integration layer
     |
     v
PDF Parser Service (Hugging Face)
     |
     |-- Bank-specific PDF extraction
     |-- Structured transaction output
     |
     v
Supabase (PostgreSQL)
     transactions, profiles, bill setups
```

---

## Financial Health Score

FinSight computes a Financial Health Score across five pillars:

| Pillar | Weight | What It Measures |
|---|---|---|
| Income Stability | 25% | Consistency and presence of income |
| Spending Control | 25% | Ratio of expenses to income |
| Savings Behavior | 20% | Whether savings transactions exist |
| Bill Regularity | 15% | Recurring bill payment consistency |
| Category Diversity | 15% | Spread of spending across categories |

### Score Grades

| Range | Grade | Status |
|---|---|---|
| 80 - 100 | A | Excellent |
| 65 - 79 | B | Good |
| 50 - 64 | C | Moderate Risk |
| 35 - 49 | D | High Risk |
| 0 - 34 | F | Critical |

---

## Core Insight Engine

FinSight's intelligence is driven by:

- Spending velocity (burn rate)
- Income vs expense ratio
- Temporal patterns (daily, weekly behavior)
- Category-level analysis

Outputs are generated dynamically from user data, not hardcoded responses.

---

## Live Services

| Service | URL |
|---|---|
| Application | https://finsightng.vercel.app |
| PDF Parser API Docs | https://margaret-06-finsight-pdf.hf.space/docs |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Database | Supabase (PostgreSQL) |
| AI | Groq (LLaMA 3.3) |
| PDF Parsing | pdfplumber, pikepdf |
| Payments | Interswitch Sandbox API |
| Hosting | Vercel, Hugging Face Spaces |
| Frontend | HTML, CSS, JavaScript (PWA) |

---

## Team Contributions

### Olatunji Oluwatobiloba (Toby) — ML Engineer
- Designed and implemented the Financial Health Score engine across 5 pillars
- Built the AI action generator (data-driven, personalized recommendations)
- Developed the spending behavior detection engine (burn rate, temporal patterns)
- Built and deployed the main FastAPI backend on Vercel
- Built the frontend (landing page, dashboard, PWA manifest, service worker)
- Integrated Groq LLaMA 3.3 for AI-generated financial insights
- Wrote project documentation and README

### Margaret Adeniran — Backend Engineer
- Built the PDF parser service deployed on Hugging Face Spaces (Docker)
- Implemented precision text parsers for UBA and Access Bank PDF statements
- Built config-based parsers for GTBank, Zenith, FirstBank, and 7 additional banks
- Integrated Supabase for transaction storage and user profile management
- Built the /parse-statement, /transactions, and /insights API endpoints
- Managed Hugging Face deployment, secrets configuration, and environment setup

### Pogbe — Systems Engineer
- Built and integrated the Interswitch Sandbox API layer (savings, bills, airtime, data)
- Implemented the Nigerian bank SMS parser supporting Access, GTBank, UBA, Zenith, FirstBank
- Built the API gateway routing layer and route architecture
- Implemented the CSV transaction parser and validation logic
- Configured the Supabase bill_setups table and bill optimization endpoints
- Handled API testing and endpoint verification across all services

---

Covenant University — Computer Engineering
BeyondTheRails Hackathon 2026

---

## Final Thought

FinSight AI is not a budgeting app.

It is a financial early warning system that predicts failure before it happens and intervenes in time.

It ensures users are never surprised by their own money again.

---

## License

This project was built for the Interswitch x Enyata BeyondTheRails Hackathon 2026.
All rights reserved by the contributors.
