import logging
import os
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, engine
from app.routers import flashcards, health, ml, pages, transcription

import app.models  # noqa: F401

# ── Logging estruturado ──────────────────────────────────────────────
LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    if not settings.debug
    else "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
)
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format=LOG_FORMAT,
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger("mnemo")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando Mnemo v%s (debug=%s)", app.version, settings.debug)
    Base.metadata.create_all(bind=engine)
    logger.info("Banco de dados conectado e tabelas criadas")
    yield
    logger.info("Mnemo encerrando")


app = FastAPI(
    title="Mnemo",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.debug,
)

# ── CORS (necessário pra API JSON e futuros frontends separados) ─────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Middleware de timing + security headers ───────────────────────────
_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "frame-ancestors 'none'"
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000

    # Security headers
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Content-Security-Policy", _CSP)
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"

    # Log de todas as requisições (exceto health check pra não poluir)
    if not request.url.path.startswith("/health"):
        logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
    return response


# ── Global exception handlers ────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Erro não tratado em %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.warning("ValueError em %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


# ── Rota de debug (só em modo debug) ────────────────────────────────
if settings.debug:

    @app.get("/debug/config")
    def debug_config():
        """Mostra config ativa (SEM expor chaves sensíveis)."""
        return {
            "whisper_model": settings.whisper_model,
            "anthropic_model": settings.anthropic_model,
            "max_upload_mb": settings.max_upload_mb,
            "storage_dir": settings.storage_dir,
            "debug": settings.debug,
            "log_level": settings.log_level,
            "anthropic_key_set": bool(settings.anthropic_api_key),
            "database_configured": "postgresql" in settings.database_url,
        }


app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(health.router)
app.include_router(transcription.router)
app.include_router(flashcards.router)
app.include_router(ml.router)
app.include_router(pages.router)
