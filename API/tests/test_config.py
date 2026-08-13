import pytest

from app.config import Settings


@pytest.mark.parametrize(
    "entrada",
    [
        "postgres://mnemo:senha@host:5432/mnemo",
        "postgresql://mnemo:senha@host:5432/mnemo",
    ],
)
def test_url_sem_driver_vira_psycopg3(entrada):
    """O único driver instalado é o psycopg 3.

    Sem driver explícito o SQLAlchemy cai no psycopg2, que não está no
    requirements — é assim que o Render entrega a connection string.
    """
    settings = Settings(database_url=entrada)
    assert settings.sqlalchemy_database_url.startswith("postgresql+psycopg://")
    assert "mnemo:senha@host:5432/mnemo" in settings.sqlalchemy_database_url


def test_url_com_driver_explicito_nao_e_alterada():
    url = "postgresql+asyncpg://mnemo:senha@host/mnemo"
    assert Settings(database_url=url).sqlalchemy_database_url == url


def test_sqlite_nao_e_alterada():
    url = "sqlite:///./local.db"
    assert Settings(database_url=url).sqlalchemy_database_url == url


def test_credenciais_sobrevivem_a_normalizacao():
    """A senha não pode ser corrompida ao trocar o prefixo."""
    settings = Settings(database_url="postgres://u:p@ss@host/db")
    assert settings.sqlalchemy_database_url == "postgresql+psycopg://u:p@ss@host/db"


def test_cors_padrao_libera_tudo():
    assert Settings().cors_origins == ["*"]


def test_cors_aceita_json():
    origins = Settings(cors_origins='["https://app.onrender.com", "http://localhost:4200"]')
    assert origins.cors_origins == ["https://app.onrender.com", "http://localhost:4200"]


def test_cors_aceita_lista_separada_por_virgula():
    origins = Settings(cors_origins="https://app.onrender.com,http://localhost:4200")
    assert origins.cors_origins == ["https://app.onrender.com", "http://localhost:4200"]


def test_cors_vazio_volta_a_liberar_tudo():
    assert Settings(cors_origins="").cors_origins == ["*"]
