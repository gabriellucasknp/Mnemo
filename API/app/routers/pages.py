import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Aula
from app.models.simulado import Simulado
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


@router.get("/simulados")
def pagina_simulados(request: Request, db: Session = Depends(get_db)):
    simulados = db.query(Simulado).order_by(Simulado.criada_em.desc()).all()
    aulas = db.query(Aula).order_by(Aula.criada_em.desc()).all()
    return templates.TemplateResponse(
        request, "simulados.html", {"simulados": simulados, "aulas": aulas}
    )


@router.get("/simulados/{simulado_id}")
def pagina_simulado_detalhe(simulado_id: int, request: Request, db: Session = Depends(get_db)):
    simulado = db.get(Simulado, simulado_id)
    if simulado is None:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
    return templates.TemplateResponse(
        request, "simulado_detalhe.html", {"simulado": simulado}
    )


@router.post("/simulados/criar")
def criar_simulado_pela_tela(
    aula_id: int = Form(...),
    titulo: str | None = Form(default=None),
    quantidade: int = Form(default=10),
    db: Session = Depends(get_db),
):
    aula = db.get(Aula, aula_id)
    if aula is None:
        return RedirectResponse(url="/simulados?erro=Aula não encontrada", status_code=303)

    if not aula.flashcards:
        return RedirectResponse(
            url=f"/simulados?erro=Gere os flashcards da aula primeiro",
            status_code=303,
        )

    from app.services.question_service import gerar_simulado
    from app.models.simulado import QuestaoSimulado

    flashcards = [{"pergunta": fc.pergunta, "resposta": fc.resposta} for fc in aula.flashcards]

    try:
        simulado_gerado = gerar_simulado(
            flashcards=flashcards,
            titulo=titulo or f"Simulado — {aula.materia or aula.titulo}",
            materia=aula.materia,
            quantidade=quantidade,
        )
    except Exception:
        logger.exception("Falha ao gerar simulado para aula %s", aula_id)
        return RedirectResponse(
            url="/simulados?erro=Falha ao gerar simulado via IA",
            status_code=303,
        )

    simulado = Simulado(
        titulo=simulado_gerado.titulo,
        materia=simulado_gerado.materia,
        quantidade_questoes=len(simulado_gerado.questoes),
        dificuldade="medio",
        aula_id=aula.id,
    )
    db.add(simulado)
    db.flush()

    for q in simulado_gerado.questoes:
        questao = QuestaoSimulado(
            simulado_id=simulado.id,
            enunciado=q.enunciado,
            alternativas=q.alternativas,
            gabarito=q.gabarito,
            explicacao=q.explicacao,
            dificuldade=q.dificuldade,
            disciplina=q.disciplina,
            fonte="ia",
        )
        db.add(questao)

    db.commit()
    return RedirectResponse(url=f"/simulados/{simulado.id}", status_code=303)
