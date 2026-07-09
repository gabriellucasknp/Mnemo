# Infra compartilhada dos testes.
#
# Estratégia: testar a API de verdade (rotas -> serviços -> banco), trocando
# só as bordas caras/externas:
#   - Postgres  -> SQLite em memória (mesmo ORM, zero dependência de container)
#   - Whisper   -> mock (transcrever um áudio real levaria minutos)
#   - Anthropic -> mock (sem custo de API nem rede nos testes)
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
    """Banco limpo por teste: cria as tabelas antes, derruba depois."""
    Base.metadata.create_all(bind=engine_teste)
    sessao = SessionTeste()
    try:
        yield sessao
    finally:
        sessao.close()
        Base.metadata.drop_all(bind=engine_teste)


@pytest.fixture()
def client(db):
    """TestClient com o get_db apontando pro SQLite de teste."""

    def get_db_teste():
        yield db

    app.dependency_overrides[get_db] = get_db_teste
    # Sem `with`: o lifespan (create_all no Postgres) não roda.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def storage_temporario(tmp_path, monkeypatch):
    """Uploads dos testes vão pra uma pasta temporária, não pra storage/."""
    monkeypatch.setattr(settings, "storage_dir", str(tmp_path))
    return tmp_path


TRANSCRICAO_FAKE = {
    "texto": "A mitocôndria é a organela responsável pela respiração celular.",
    "idioma": "pt",
    "duracao_segundos": 42,
}


@pytest.fixture()
def whisper_mockado(monkeypatch):
    """Substitui o Whisper por uma transcrição instantânea e conhecida."""
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
    ],
)


@pytest.fixture()
def ia_mockada(monkeypatch):
    """Substitui a chamada à Anthropic por um deck fixo e válido."""
    monkeypatch.setattr(
        aula_service.flashcard_service,
        "gerar_flashcards",
        lambda texto: DECK_FAKE.model_copy(deep=True),
    )
    return DECK_FAKE
