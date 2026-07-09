# Conexão com o Postgres (Etapa 4).
# Aqui mora o engine do SQLAlchemy, a fábrica de sessões e a dependência
# `get_db()` que as rotas usam pra abrir/fechar conexão por requisição.
#
# Decisão da Etapa 4: ORM (SQLAlchemy 2.0) em vez de driver direto.
# Por quê: você já domina SQL — o ORM não esconde nada de você, e ganha
# de graça o mapeamento linha<->objeto Python que as rotas precisam.
# Quando quiser SQL puro, o checkpoint da Etapa 4 continua valendo:
# conecte com psql/DBeaver em localhost:5432 e consulte as tabelas.
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# pool_pre_ping: testa a conexão antes de usar (evita erro se o banco reiniciou).
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Classe-base de todos os modelos (tabelas)."""


def get_db():
    """Dependência do FastAPI: abre uma sessão por requisição e SEMPRE fecha."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
