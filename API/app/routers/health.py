import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

logger = logging.getLogger("mnemo.health")

router = APIRouter()


@router.get("/health")
def check_health():
    return {"status": "ok", "version": "0.1.0", "debug": settings.debug}


@router.get("/health/db")
def check_health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception:
        logger.exception("Health check do banco falhou")
        # 503, não 200: probes (Render/k8s/nginx) olham o status code —
        # "degraded" com 200 passa despercebido por qualquer supervisório.
        return JSONResponse(
            status_code=503, content={"status": "degraded", "database": "error"}
        )


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
    """Readiness probe: pronto pra receber tráfego?"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        logger.warning("Readiness check falhou")
        return JSONResponse(status_code=503, content={"status": "not_ready"})
