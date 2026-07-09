# Router de FLASHCARDS (Etapa 5).
# A partir de uma transcrição SALVA, dispara a geração dos pares
# pergunta/resposta (flashcard_service) e os persiste, ligados à aula
# de origem e com a origem marcada.
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Aula
from app.schemas import AulaDetalheOut, FlashcardOut
from app.services import aula_service

router = APIRouter(prefix="/api", tags=["flashcards"])


@router.post("/aulas/{aula_id}/flashcards", response_model=AulaDetalheOut, status_code=201)
def gerar_flashcards(aula_id: int, db: Session = Depends(get_db)):
    """Gera e salva flashcards a partir da transcrição da aula."""
    aula = db.get(Aula, aula_id)
    if aula is None:
        raise HTTPException(status_code=404, detail="Aula não encontrada")
    try:
        return aula_service.gerar_e_salvar_flashcards(db, aula)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/aulas/{aula_id}/flashcards", response_model=list[FlashcardOut])
def listar_flashcards(aula_id: int, db: Session = Depends(get_db)):
    aula = db.get(Aula, aula_id)
    if aula is None:
        raise HTTPException(status_code=404, detail="Aula não encontrada")
    return aula.flashcards
