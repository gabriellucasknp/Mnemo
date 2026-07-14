import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.services import aula_service
from app.services.flashcard_service import DeckGerado, FlashcardGerado

# --- Banco de teste: SQLite em memória, uma conexão compartilhada ---
engine_teste = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionTeste = sessionmaker(bind=engine_teste, autocommit=False, autoflush=False)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine_teste)
    sessao = SessionTeste()
    try:
        yield sessao
    finally:
        sessao.close()
        Base.metadata.drop_all(bind=engine_teste)


@pytest.fixture()
def client(db):
    def get_db_teste():
        yield db

    app.dependency_overrides[get_db] = get_db_teste
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def storage_temporario(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    return tmp_path


TRANSCRICAO_FAKE = {
    "texto": "A mitocôndria é a organela responsável pela respiração celular.",
    "idioma": "pt",
    "duracao_segundos": 42,
}


@pytest.fixture()
def whisper_mockado(monkeypatch):
    chamadas = []

    def transcrever_fake(caminho_audio: str) -> dict:
        chamadas.append(caminho_audio)
        return dict(TRANSCRICAO_FAKE)

    monkeypatch.setattr(aula_service.whisper_service, "transcrever", transcrever_fake)
    return chamadas


DECK_FAKE = DeckGerado(
    titulo="Respiração celular",
    materia="Biologia",
    flashcards=[
        FlashcardGerado(
            categoria="definição",
            pergunta="O que é a mitocôndria?",
            resposta="A organela responsável pela respiração celular.",
            explicacao=None,
        ),
        FlashcardGerado(
            categoria="conceito",
            pergunta="Qual processo ocorre na mitocôndria?",
            resposta="A respiração celular.",
            explicacao="Segundo a fala do professor.",
        ),
        FlashcardGerado(
            categoria="exemplo",
            pergunta="Quais organelas realizam respiração celular?",
            resposta="As mitocôndrias.",
            explicacao=None,
        ),
        FlashcardGerado(
            categoria="processo",
            pergunta="Como funciona a respiração celular?",
            resposta="A mitocôndria converte nutrientes em energia.",
            explicacao="Processo aeróbico.",
        ),
    ],
)


@pytest.fixture()
def ia_mockada(monkeypatch):
    monkeypatch.setattr(
        aula_service.flashcard_service,
        "gerar_flashcards",
        lambda texto: DECK_FAKE.model_copy(deep=True),
    )
    return DECK_FAKE
