import logging
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Aula, Flashcard, Origem, Transcricao
from app.services import flashcard_service, whisper_service

logger = logging.getLogger("mnemo.aula")

EXTENSOES_ACEITAS = {".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".webm", ".flac"}
TITULO_PADRAO = "Aula sem título"


def salvar_audio(arquivo: UploadFile) -> Path:
    sufixo = Path(arquivo.filename or "audio").suffix.lower()
    if sufixo not in EXTENSOES_ACEITAS:
        raise ValueError(f"Formato não suportado: {sufixo or '(sem extensão)'}")

    nome = f"{uuid.uuid4().hex}{sufixo}"
    destino = Path(settings.storage_dir) / nome
    destino.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Salvando áudio: %s -> %s (%s)", arquivo.filename, nome, arquivo.content_type)

    limite_bytes = settings.max_upload_mb * 1024 * 1024
    total = 0
    try:
        with destino.open("wb") as f:
            while pedaco := arquivo.file.read(1024 * 1024):
                total += len(pedaco)
                if total > limite_bytes:
                    raise ValueError(
                        f"Arquivo excede o limite de {settings.max_upload_mb} MB."
                    )
                f.write(pedaco)
    except ValueError:
        destino.unlink(missing_ok=True)
        raise

    logger.info("Áudio salvo: %s (%.1f MB)", nome, total / (1024 * 1024))
    return destino


def criar_aula_com_transcricao(db: Session, caminho_audio: Path, titulo: str | None) -> Aula:
    logger.info("Iniciando transcrição de %s", caminho_audio.name)
    try:
        resultado = whisper_service.transcrever(str(caminho_audio))
    finally:
        caminho_audio.unlink(missing_ok=True)

    logger.info(
        "Transcrição concluída: %d palavras, idioma=%s, duração=%ds",
        len(resultado["texto"].split()),
        resultado["idioma"],
        resultado["duracao_segundos"] or 0,
    )

    aula = Aula(
        titulo=titulo or TITULO_PADRAO,
        duracao_segundos=resultado["duracao_segundos"],
    )
    aula.transcricao = Transcricao(
        texto=resultado["texto"],
        idioma=resultado["idioma"],
        origem=Origem.PROFESSOR,
    )
    db.add(aula)
    db.commit()
    db.refresh(aula)
    logger.info("Aula #%d criada com transcrição", aula.id)
    return aula


def gerar_e_salvar_flashcards(db: Session, aula: Aula) -> Aula:
    if aula.transcricao is None or not aula.transcricao.texto.strip():
        raise ValueError("A aula não tem transcrição para gerar flashcards.")

    logger.info("Gerando flashcards para aula #%d via %s", aula.id, settings.anthropic_model)
    deck = flashcard_service.gerar_flashcards(aula.transcricao.texto)

    if aula.titulo == TITULO_PADRAO and deck.titulo:
        aula.titulo = deck.titulo
    aula.materia = deck.materia

    for carta in deck.flashcards:
        db.add(
            Flashcard(
                aula_id=aula.id,
                categoria=carta.categoria,
                pergunta=carta.pergunta,
                resposta=carta.resposta,
                explicacao=carta.explicacao,
                origem=Origem.PROFESSOR,
            )
        )
    db.commit()
    db.refresh(aula)
    logger.info(
        "Flashcards gerados: %d cartões para aula #%d (%s)",
        len(deck.flashcards),
        aula.id,
        deck.materia,
    )
    return aula
