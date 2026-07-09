# Orquestrador do fluxo (Etapas 3+4+5): salvar áudio -> transcrever ->
# persistir com origem marcada -> gerar flashcards -> persistir.
# Fica num serviço pra que tanto a API JSON (/docs) quanto as telas (Etapa 6)
# usem exatamente o mesmo caminho de código.
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Aula, Flashcard, Origem, Transcricao
from app.services import flashcard_service, whisper_service

EXTENSOES_ACEITAS = {".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".webm", ".flac"}


def salvar_audio(arquivo: UploadFile) -> Path:
    """Salva o upload em storage/ com nome único e devolve o caminho."""
    sufixo = Path(arquivo.filename or "audio").suffix.lower()
    if sufixo not in EXTENSOES_ACEITAS:
        raise ValueError(f"Formato não suportado: {sufixo or '(sem extensão)'}")
    destino = Path(settings.storage_dir) / f"{uuid.uuid4().hex}{sufixo}"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("wb") as f:
        while pedaco := arquivo.file.read(1024 * 1024):
            f.write(pedaco)
    return destino


def criar_aula_com_transcricao(db: Session, caminho_audio: Path, titulo: str | None) -> Aula:
    """Etapas 3+4: transcreve o áudio e persiste aula + transcrição (origem=PROFESSOR)."""
    try:
        resultado = whisper_service.transcrever(str(caminho_audio))
    finally:
        # O áudio é temporário (a transcrição é a fonte de verdade que persiste);
        # sem essa limpeza, storage/ cresce sem limite a cada upload.
        caminho_audio.unlink(missing_ok=True)

    aula = Aula(
        titulo=titulo or "Aula sem título",
        duracao_segundos=resultado["duracao_segundos"],
    )
    aula.transcricao = Transcricao(
        texto=resultado["texto"],
        idioma=resultado["idioma"],
        origem=Origem.PROFESSOR,  # a regra da fonte, gravada no dado
    )
    db.add(aula)
    db.commit()
    db.refresh(aula)
    return aula


def gerar_e_salvar_flashcards(db: Session, aula: Aula) -> Aula:
    """Etapa 5: gera flashcards a partir da transcrição salva e persiste."""
    if aula.transcricao is None or not aula.transcricao.texto.strip():
        raise ValueError("A aula não tem transcrição para gerar flashcards.")

    deck = flashcard_service.gerar_flashcards(aula.transcricao.texto)

    # A IA infere título/matéria; só sobrescreve se o usuário não deu um título.
    if aula.titulo == "Aula sem título" and deck.titulo:
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
                # Derivados da fala do professor => origem PROFESSOR (SDD §5).
                origem=Origem.PROFESSOR,
            )
        )
    db.commit()
    db.refresh(aula)
    return aula
