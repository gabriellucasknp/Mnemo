import logging
import secrets

from fastapi import Form, Header, HTTPException, Request
from fastapi.responses import Response

from app.config import settings

logger = logging.getLogger("mnemo.security")

CSRF_COOKIE = "mnemo_csrf"


def obter_csrf_token(request: Request) -> str:
    """Reaproveita o token já emitido (várias abas abertas) ou gera um novo."""
    return request.cookies.get(CSRF_COOKIE) or secrets.token_urlsafe(32)


def anexar_csrf_cookie(response: Response, token: str) -> None:
    response.set_cookie(CSRF_COOKIE, token, httponly=True, samesite="strict", path="/")


def validar_csrf(request: Request, csrf_token: str = Form(...)) -> None:
    """Proteção CSRF double-submit nos formulários HTML.

    O campo oculto do form precisa bater com o cookie emitido junto com a
    página — um site externo consegue disparar o POST, mas não consegue ler
    o cookie pra preencher o campo.
    """
    esperado = request.cookies.get(CSRF_COOKIE)
    if not esperado or not secrets.compare_digest(esperado, csrf_token):
        logger.warning("POST de formulário rejeitado por token CSRF inválido")
        raise HTTPException(status_code=403, detail="Token CSRF inválido ou ausente.")


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
