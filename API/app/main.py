import logging
import os
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import Base, engine
from app.limiter import limiter
from app.routers import flashcards, health, ml, ml_questoes, pages, simulados, transcription

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


# Swagger/OpenAPI só em modo debug: em produção o app não tem auth de leitura,
# então publicar o mapa completo da API é dar o roteiro de abuso de graça.
app = FastAPI(
    title="Mnemo",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# ── Rate limiting (slowapi) ──────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS (necessário pra API JSON e futuros frontends separados) ─────
#
# Em produção o nginx serve o SPA e a API no mesmo domínio, então o caminho
# normal nem passa por CORS. O curinga existe só pra facilitar dev//docs.
#
# `*` junto de credenciais deixaria qualquer site fazer requisição autenticada
# em nome do usuário — o Starlette, nesse combo, ecoa a origem de volta em vez
# de mandar `*`, o que derruba a proteção. Só habilita credenciais quando a
# lista de origens é explícita (defina CORS_ORIGINS pra isso).
_cors_liberado = "*" in settings.cors_origins
if _cors_liberado:
    logger.warning(
        "CORS liberado para qualquer origem; credenciais desabilitadas. "
        "Defina CORS_ORIGINS com a lista de domínios em produção."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=not _cors_liberado,
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
            "gemini_model": settings.gemini_model,
            "max_upload_mb": settings.max_upload_mb,
            "storage_dir": settings.storage_dir,
            "debug": settings.debug,
            "log_level": settings.log_level,
            "gemini_key_set": bool(settings.gemini_api_key),
            "database_configured": "postgresql" in settings.database_url,
        }


app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(health.router)
app.include_router(transcription.router)
app.include_router(flashcards.router)
app.include_router(ml.router)
app.include_router(ml_questoes.router)
app.include_router(simulados.router)
app.include_router(pages.router)
