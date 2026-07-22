import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.ml.question_model import get_question_quality_model

logger = logging.getLogger("mnemo.api.ml_questoes")

router = APIRouter(prefix="/api/ml", tags=["machine-learning"])


class TreinarQualidadeResponse(BaseModel):
    accuracy: float
    report: str
    train_size: int
    test_size: int
    dataset_size: int


class AvaliarQuestaoRequest(BaseModel):
    enunciado: str
    alternativas: list[str] | None = None


class AvaliarQuestaoResponse(BaseModel):
    qualidade: str
    confianca: float
    features: dict


@router.post("/treinar-questoes", response_model=TreinarQualidadeResponse)
def treinar_modelo_questoes():
    model = get_question_quality_model()
    try:
        metrics = model.train_on_enem()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return TreinarQualidadeResponse(
        accuracy=metrics["accuracy"],
        report=metrics["report"],
        train_size=metrics["train_size"],
        test_size=metrics["test_size"],
        dataset_size=metrics["dataset_size"],
    )


@router.post("/avaliar-questao", response_model=AvaliarQuestaoResponse)
def avaliar_questao(req: AvaliarQuestaoRequest):
    model = get_question_quality_model()
    result = model.evaluate(req.enunciado, req.alternativas)
    return AvaliarQuestaoResponse(**result)


@router.get("/status-questoes")
def status_modelo_questoes():
    model = get_question_quality_model()
    return {
        "treinado": model.is_trained,
        "modelo": "question_quality_model.pkl",
        "dataset": "enem_2022.json",
    }
