import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Aula, Flashcard
from app.schemas import AulaDetalheOut, AulaOut
from app.services import aula_service

logger = logging.getLogger("mnemo.api")

router = APIRouter(prefix="/api", tags=["aulas"])


@router.post("/aulas", response_model=AulaDetalheOut, status_code=201)
def enviar_aula(
    audio: UploadFile = File(..., description="Áudio da aula (mp3, mp4, wav...)"),
    titulo: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    try:
        caminho = aula_service.salvar_audio(audio)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    aula = aula_service.criar_aula_com_transcricao(db, caminho, titulo)
    aula.flashcards_count = 0
    return aula


@router.get("/aulas", response_model=list[AulaOut])
def listar_aulas(db: Session = Depends(get_db)):
    aulas = db.query(Aula).order_by(Aula.criada_em.desc()).all()
    contagens = dict(
        db.query(Flashcard.aula_id, func.count(Flashcard.id)).group_by(Flashcard.aula_id).all()
    )
    for aula in aulas:
        aula.flashcards_count = contagens.get(aula.id, 0)
    return aulas


@router.get("/aulas/{aula_id}", response_model=AulaDetalheOut)
def detalhar_aula(aula_id: int, db: Session = Depends(get_db)):
    aula = db.get(Aula, aula_id)
    if aula is None:
        raise HTTPException(status_code=404, detail="Aula não encontrada")
    aula.flashcards_count = len(aula.flashcards)
    return aula


@router.delete("/aulas/{aula_id}", status_code=204)
def deletar_aula(aula_id: int, db: Session = Depends(get_db)):
    aula = db.get(Aula, aula_id)
    if aula is None:
        raise HTTPException(status_code=404, detail="Aula não encontrada")
    titulo = aula.titulo
    db.delete(aula)
    db.commit()
    logger.info("Aula #%d '%s' removida", aula_id, titulo)
