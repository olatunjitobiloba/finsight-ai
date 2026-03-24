from fastapi import APIRouter

router = APIRouter()

@router.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "FinSight AI",
        "version": "1.0.0"
    }