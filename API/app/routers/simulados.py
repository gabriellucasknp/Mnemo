import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Aula
from app.models.simulado import QuestaoSimulado, RespostaSimulado, Simulado
from app.services.question_service import gerar_simulado

logger = logging.getLogger("mnemo.api.simulados")

router = APIRouter(prefix="/api/simulados", tags=["simulados"])


class CriarSimuladoRequest(BaseModel):
    aula_id: int = Field(description="ID da aula para basear o simulado")
    titulo: str | None = Field(default=None, description="Título do simulado")
    quantidade: int = Field(default=10, ge=3, le=20, description="Número de questões")


class QuestaoOut(BaseModel):
    id: int
    enunciado: str
    alternativas: dict
    explicacao: str | None
    dificuldade: str
    disciplina: str | None


class SimuladoOut(BaseModel):
    id: int
    titulo: str
    materia: str | None
    quantidade_questoes: int
    dificuldade: str
    aula_id: int | None
    criado_em: str
    questoes: list[QuestaoOut] = []
    total_acertadas: int = 0
    total_respondidas: int = 0


class ResponderRequest(BaseModel):
    respostas: dict[int, str] = Field(
        description="Mapa questao_id -> alternativa (A-E)"
    )


class RespostaResultado(BaseModel):
    questao_id: int
    alternativa_marcada: str | None
    gabarito: str
    acertou: bool
    explicacao: str | None


class ResultadoSimulado(BaseModel):
    simulado_id: int
    total_questoes: int
    acertadas: int
    erros: int
    percentual: float
    detalhes: list[RespostaResultado]


@router.post("", response_model=SimuladoOut, status_code=201)
def criar_simulado(req: CriarSimuladoRequest, db: Session = Depends(get_db)):
    aula = db.get(Aula, req.aula_id)
    if aula is None:
        raise HTTPException(status_code=404, detail="Aula não encontrada")

    if not aula.flashcards:
        raise HTTPException(
            status_code=400,
            detail="Aula não possui flashcards. Gere flashcards primeiro.",
        )

    flashcards = [
        {"pergunta": fc.pergunta, "resposta": fc.resposta}
        for fc in aula.flashcards
    ]

    try:
        simulado_gerado = gerar_simulado(
            flashcards=flashcards,
            titulo=req.titulo or f"Simulado — {aula.materia or aula.titulo}",
            materia=aula.materia,
            quantidade=req.quantidade,
        )
    except Exception as e:
        logger.exception("Erro ao gerar simulado para aula %s", req.aula_id)
        raise HTTPException(status_code=500, detail=str(e)) from e

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
    db.refresh(simulado)

    return _simulado_para_out(simulado)


@router.get("", response_model=list[SimuladoOut])
def listar_simulados(db: Session = Depends(get_db)):
    simulados = (
        db.query(Simulado).order_by(Simulado.criado_em.desc()).all()
    )
    return [_simulado_para_out(s) for s in simulados]


@router.get("/{simulado_id}", response_model=SimuladoOut)
def detalhar_simulado(simulado_id: int, db: Session = Depends(get_db)):
    simulado = db.get(Simulado, simulado_id)
    if simulado is None:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
    return _simulado_para_out(simulado)


@router.post("/{simulado_id}/responder", response_model=ResultadoSimulado)
def responder_simulado(
    simulado_id: int, req: ResponderRequest, db: Session = Depends(get_db)
):
    simulado = db.get(Simulado, simulado_id)
    if simulado is None:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")

    questoes = {q.id: q for q in simulado.questoes}
    acertadas = 0
    detalhes = []

    for questao_id, alternativa in req.respostas.items():
        questao = questoes.get(questao_id)
        if questao is None:
            continue

        acertou = alternativa.upper() == questao.gabarito.upper()
        if acertadas is not None and acertou:
            acertadas += 1

        resposta = RespostaSimulado(
            simulado_id=simulado.id,
            questao_id=questao_id,
            alternativa_marcada=alternativa.upper(),
            acertou=acertou,
        )
        db.add(resposta)

        detalhes.append(
            RespostaResultado(
                questao_id=questao_id,
                alternativa_marcada=alternativa.upper(),
                gabarito=questao.gabarito,
                acertou=acertou,
                explicacao=questao.explicacao,
            )
        )

    db.commit()

    total = len(questoes)
    erros = total - acertadas
    percentual = (acertadas / total * 100) if total > 0 else 0

    return ResultadoSimulado(
        simulado_id=simulado.id,
        total_questoes=total,
        acertadas=acertadas,
        erros=erros,
        percentual=round(percentual, 1),
        detalhes=detalhes,
    )


@router.delete("/{simulado_id}", status_code=204)
def deletar_simulado(simulado_id: int, db: Session = Depends(get_db)):
    simulado = db.get(Simulado, simulado_id)
    if simulado is None:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
    titulo = simulado.titulo
    db.delete(simulado)
    db.commit()
    logger.info("Simulado #%d '%s' removido", simulado_id, titulo)


def _simulado_para_out(simulado: Simulado) -> SimuladoOut:
    questoes_out = [
        QuestaoOut(
            id=q.id,
            enunciado=q.enunciado,
            alternativas=q.alternativas,
            explicacao=q.explicacao,
            dificuldade=q.dificuldade,
            disciplina=q.disciplina,
        )
        for q in simulado.questoes
    ]

    total_respostas = len(simulado.respostas) if simulado.respostas else 0
    acertadas = sum(1 for r in simulado.respostas if r.acertou) if simulado.respostas else 0

    return SimuladoOut(
        id=simulado.id,
        titulo=simulado.titulo,
        materia=simulado.materia,
        quantidade_questoes=simulado.quantidade_questoes,
        dificuldade=simulado.dificuldade,
        aula_id=simulado.aula_id,
        criado_em=str(simulado.criado_em) if simulado.criado_em else "",
        questoes=questoes_out,
        total_acertadas=acertadas,
        total_respondidas=total_respostas,
    )
