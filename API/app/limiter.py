"""Rate limiting dos endpoints caros (upload + Whisper + Gemini).

Limita por IP com armazenamento em memória — suficiente para 1 worker
(o deploy roda `--workers 1`). Se um dia houver múltiplos workers/instâncias,
trocar o storage por Redis (`storage_uri`).

Os testes desligam via `settings.rate_limit_enabled` (conftest).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.rate_limit_enabled,
)

# Limites nomeados — um só lugar pra ajustar.
LIMITE_UPLOAD = "3/hour"       # upload 200 MB + transcrição Whisper (CPU-bound)
LIMITE_GERACAO_IA = "10/hour"  # chamadas ao Gemini (flashcards/simulados)
