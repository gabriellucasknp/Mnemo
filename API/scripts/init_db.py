"""Inicializa o schema do banco (cria as tabelas se não existirem).

Usado no entrypoint de produção antes de subir a API. Idempotente: roda
`create_all`, que não altera tabelas existentes. Migrações de estrutura
futuras devem migrar para Alembic.

  python scripts/init_db.py
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.models  # noqa: F401  (registra as tabelas no metadata)
from app.database import Base, engine

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s | %(message)s")
logger = logging.getLogger("mnemo.init_db")


def main() -> None:
    logger.info("Aplicando schema em %s", engine.url)
    Base.metadata.create_all(bind=engine)
    logger.info("Schema pronto")


if __name__ == "__main__":
    main()
