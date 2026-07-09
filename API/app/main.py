# Ponto de entrada da aplicação.
# Cria a instância FastAPI, inclui os routers de cada etapa e serve os
# arquivos estáticos das telas.
from contextlib import asynccontextmanager

from fastapi import FastAPI
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

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(health.router)          # Etapa 1
app.include_router(transcription.router)   # Etapas 3+4
app.include_router(flashcards.router)      # Etapa 5
app.include_router(pages.router)           # Etapa 6
