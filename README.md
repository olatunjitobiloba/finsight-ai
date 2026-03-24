# FinSight AI

**Predict. Prevent. Prosper.**

FinSight AI is a Nigerian financial decision engine that turns raw bank SMS alerts into actionable financial intelligence. Paste your bank alerts, get your financial health score, see how many days until your money runs out, and receive AI-generated recommendations to fix your habits.

Live at: [finsightng.vercel.app](https://finsightng.vercel.app)

---

## What It Does

Most Nigerians have no idea where their money goes. FinSight AI solves that by reading the SMS alerts already sitting on your phone and turning them into a clear financial picture — no bank login, no manual entry.

- Parses Nigerian bank SMS alerts from GTBank, Access Bank, First Bank, Zenith Bank, and UBA
- Calculates a Financial Health Score from 0 to 100 across five pillars
- Predicts how many days until your balance hits zero based on your actual burn rate
- Detects spending behavior patterns
- Generates specific AI-powered actions to improve your financial position
- Stores transaction history per user via Supabase

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Frontend | HTML, CSS, JavaScript (static) |
| Database | Supabase (PostgreSQL) |
| Deployment | Vercel |
| AI Actions | Custom rule-based engine with LLM integration |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Service status and endpoint list |
| GET | `/api/health` | Health check |
| POST | `/api/analyze` | Master endpoint — paste SMS, get full analysis |
| POST | `/api/score` | Score a list of transactions directly |
| GET | `/api/history/{user_id}` | Retrieve and re-analyze saved transactions |
| POST | `/api/parse/sms` | Parse a single SMS |
| POST | `/api/parse/sms/batch` | Parse multiple SMS messages |
| POST | `/api/parse/csv` | Parse transactions from CSV file |
| POST | `/api/parse/csv/text` | Parse transactions from CSV text |
| POST | `/api/savings/plan` | Generate a savings plan |
| POST | `/api/savings/analyze` | Analyze savings behavior |
| POST | `/api/savings/bills/optimize` | Optimize bill payments |
| GET | `/api/parse/banks` | List supported banks |
| GET | `/api/parse/demo` | Demo parse output |

---

## Financial Health Score

The score is built from five weighted pillars:

| Pillar | Weight | What It Measures |
|---|---|---|
| Income Stability | 25% | Consistency and frequency of income |
| Spending Control | 25% | Whether spending stays below income |
| Savings Behavior | 20% | Evidence of savings activity |
| Bill Regularity | 15% | Whether bills are paid consistently |
| Category Diversity | 15% | Spread of spending across categories |

Score ranges:

- 80 to 100 — Financially Healthy
- 55 to 79 — Moderate Risk
- 40 to 54 — Financially Unstable
- 0 to 39 — Critical

---

## Days to Zero Predictor

Using actual daily spending data from parsed transactions, the engine calculates a daily burn rate and predicts the number of days before the current balance reaches zero. A volatility buffer is applied when spending is highly concentrated on specific days.

---

## Supported Banks

- GTBank
- Access Bank
- First Bank
- Zenith Bank
- UBA

---

## Project Structure

```
finsight-ai/
|
|-- api/
|   |-- main.py                  # FastAPI app entry point
|   |-- routes/
|       |-- analyze.py           # Master analysis endpoint
|       |-- score.py             # Score endpoint
|       |-- health.py            # Health check
|       |-- parse.py             # SMS and CSV parsing routes
|
|-- services/
|   |-- sms_parser.py            # Bank SMS parsing logic
|   |-- score_engine.py          # Scoring, prediction, pattern detection
|   |-- ai_actions.py            # AI recommendation engine
|   |-- db.py                    # Supabase database layer
|
|-- frontend/                    # Static HTML/CSS/JS frontend
|-- vercel.json                  # Vercel deployment configuration
|-- requirements.txt
```

---

## Local Setup

**Requirements:** Python 3.10+

```bash
# Clone the repository
git clone https://github.com/olatunjitobiloba/finsight-ai.git
cd finsight-ai

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Fill in SUPABASE_URL and SUPABASE_KEY in .env

# Run the server
uvicorn api.main:app --reload
```

Server runs at `http://localhost:8000`

---

## Environment Variables

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Your Supabase service role key (backend only) |

---

## Deployment

The project is deployed on Vercel. The `vercel.json` configuration routes all `/api/*` requests to the FastAPI backend and all other requests to the static frontend.

To deploy your own instance:

1. Fork the repository
2. Connect to Vercel
3. Add `SUPABASE_URL` and `SUPABASE_KEY` as environment variables in Vercel project settings
4. Push to the `main` branch to trigger a production deployment

---

## Contributors

| Name | GitHub | Role |
|---|---|---|
| Olatunjitobi Loba | [@olatunjitobiloba](https://github.com/olatunjitobiloba) | Project Lead, Score Engine, Architecture |
| Margaret | [@madeniran2300324-beep](https://github.com/madeniran2300324-beep) | Analysis Endpoint, Core Backend Logic |
| Emmanuel Pogbe | [@emmanuel-pogbe](https://github.com/emmanuel-pogbe) | Backend Contributions |

---

## License

MIT License. See `LICENSE` for details.