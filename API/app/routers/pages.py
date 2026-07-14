import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Aula
from app.services import aula_service

logger = logging.getLogger("mnemo.pages")

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def pagina_upload(request: Request, db: Session = Depends(get_db)):
    aulas = db.query(Aula).order_by(Aula.criada_em.desc()).limit(6).all()
    return templates.TemplateResponse(
        request, "upload.html", {"aulas": aulas, "erro": request.query_params.get("erro")}
    )


@router.post("/enviar")
def enviar_pela_tela(
    audio: UploadFile = File(...),
    titulo: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    try:
        caminho = aula_service.salvar_audio(audio)
    except ValueError as e:
        return RedirectResponse(url=f"/?erro={quote(str(e))}", status_code=303)

    aula = aula_service.criar_aula_com_transcricao(db, caminho, titulo or None)
    try:
        aula_service.gerar_e_salvar_flashcards(db, aula)
    except Exception:
        logger.exception("Falha ao gerar flashcards da aula %s", aula.id)
    return RedirectResponse(url=f"/aulas/{aula.id}", status_code=303)


@router.get("/aulas/{aula_id}")
def pagina_aula(aula_id: int, request: Request, db: Session = Depends(get_db)):
    aula = db.get(Aula, aula_id)
    if aula is None:
        raise HTTPException(status_code=404, detail="Aula não encontrada")
    return templates.TemplateResponse(request, "flashcards.html", {"aula": aula})


@router.post("/aulas/{aula_id}/gerar")
def gerar_pela_tela(aula_id: int, db: Session = Depends(get_db)):
    aula = db.get(Aula, aula_id)
    if aula is None:
        raise HTTPException(status_code=404, detail="Aula não encontrada")
    try:
        aula_service.gerar_e_salvar_flashcards(db, aula)
    except Exception:
        logger.exception("Falha ao gerar flashcards da aula %s", aula_id)
    return RedirectResponse(url=f"/aulas/{aula_id}", status_code=303)
