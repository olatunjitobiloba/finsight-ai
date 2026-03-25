from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.analyze import router as analyze_router
from api.routes.score import router as score_router
from api.routes.health import router as health_router
from api.routes.parse import router as parse_router
from api.routes.execute import router as execute_router
from api.routes.bank_verify import router as bank_verify_router

app = FastAPI(
    title="FinSight AI",
    description="Predict. Prevent. Prosper. - Nigerian Financial Decision Engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)
app.include_router(score_router)
app.include_router(health_router)
app.include_router(parse_router)
app.include_router(execute_router)
app.include_router(bank_verify_router)


@app.get("/")
def root():
    return {
        "service": "FinSight AI",
        "status": "running",
        "endpoints": [
            "POST /api/analyze",
            "POST /api/score",
            "GET /api/history/{user_id}",
            "GET /api/health",
            "POST /api/parse/sms",
            "POST /api/parse/sms/batch",
            "POST /api/parse/csv",
            "POST /api/parse/csv/text",
            "POST /api/parse/pdf",
            "POST /api/savings/plan",
            "POST /api/savings/analyze",
            "POST /api/savings/bills/optimize",
            "POST /api/execute/pay",
            "GET /api/execute/billers",
            "GET /api/execute/payment-items?biller_id=...",
            "GET /api/execute/status",
            "GET /api/bank-verify/banks",
            "POST /api/bank-verify/verify",
            "GET /api/parse/banks",
            "GET /api/parse/demo"
        ],
    }
