# Router de TRANSCRIÇÃO (Etapa 3 + Etapa 4).
# Recebe o upload do áudio (multipart/form-data), salva em storage/,
# chama o whisper_service e PERSISTE a transcrição com a origem marcada.
# Teste tudo pelo /docs — não precisa de tela nenhuma.
#
# Nota da Etapa 3 (assumida de propósito): o Whisper demora, então a requisição
# fica "pensando" um tempo. É isso que o Celery vai resolver numa fase futura.
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Aula
from app.schemas import AulaDetalheOut, AulaOut
from app.services import aula_service

router = APIRouter(prefix="/api", tags=["aulas"])


@router.post("/aulas", response_model=AulaDetalheOut, status_code=201)
def enviar_aula(
    audio: UploadFile = File(..., description="Áudio da aula (mp3, mp4, wav...)"),
    titulo: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    """Sobe um áudio, transcreve com Whisper e salva aula + transcrição."""
    try:
        caminho = aula_service.salvar_audio(audio)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return aula_service.criar_aula_com_transcricao(db, caminho, titulo)


@router.get("/aulas", response_model=list[AulaOut])
def listar_aulas(db: Session = Depends(get_db)):
    return db.query(Aula).order_by(Aula.criada_em.desc()).all()


@router.get("/aulas/{aula_id}", response_model=AulaDetalheOut)
def detalhar_aula(aula_id: int, db: Session = Depends(get_db)):
    aula = db.get(Aula, aula_id)
    if aula is None:
        raise HTTPException(status_code=404, detail="Aula não encontrada")
    return aula
