# Ponto de entrada da aplicação.
# Cria a instância FastAPI, inclui os routers de cada etapa e serve os
# arquivos estáticos das telas.
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import flashcards, health, pages, transcription

# Importa os modelos pra registrar as tabelas no Base.metadata.
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Etapa 4: cria as tabelas na subida (idempotente — só cria o que falta).
    # Numa fase futura, migrações (Alembic) substituem isso.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Mnemo", version="0.1.0", lifespan=lifespan)


# Headers de segurança em TODA resposta (API e telas):
#  - nosniff: navegador não "adivinha" tipo de conteúdo (evita XSS por upload).
#  - X-Frame-Options: ninguém embute o Mnemo num iframe (clickjacking).
#  - CSP: só carrega recursos daqui + Google Fonts; scripts inline dos
#    templates continuam funcionando ('unsafe-inline').
_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "frame-ancestors 'none'"
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    response.headers.setdefault("Content-Security-Policy", _CSP)
    return response


app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(health.router)          # Etapa 1
app.include_router(transcription.router)   # Etapas 3+4
app.include_router(flashcards.router)      # Etapa 5
app.include_router(pages.router)           # Etapa 6
