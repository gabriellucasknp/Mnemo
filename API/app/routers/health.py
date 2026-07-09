# Router de HEALTH (Etapa 1).
# GET /health: "está vivo?" — usado pelo healthcheck do Docker e, na AWS,
# pelo health check do load balancer / App Runner.
# GET /health/db: "consegue falar com o banco?" — separado de propósito, pra
# API continuar respondendo "viva" mesmo se o Postgres cair.
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()


@router.get("/health")
def check_health():
    return {"status": "ok"}


@router.get("/health/db")
def check_health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}