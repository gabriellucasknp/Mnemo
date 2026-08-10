import logging
import secrets

from fastapi import Header, HTTPException

from app.config import settings

logger = logging.getLogger("mnemo.security")


def exigir_admin(x_admin_token: str | None = Header(default=None)) -> None:
    """Dependência de auth para endpoints administrativos (treino de modelos).

    O token é comparado com `ADMIN_TOKEN` (env var). Se a env var não estiver
    configurada, os endpoints ficam indisponíveis (503) — fechado por padrão,
    pra ninguém subir uma instância com treino público sem perceber.
    """
    if not settings.admin_token:
        raise HTTPException(
            status_code=503,
            detail="Endpoint administrativo desabilitado (ADMIN_TOKEN não configurado).",
        )
    if not x_admin_token or not secrets.compare_digest(
        x_admin_token, settings.admin_token
    ):
        logger.warning("Tentativa de acesso administrativo com token inválido")
        raise HTTPException(status_code=401, detail="Token administrativo inválido.")
