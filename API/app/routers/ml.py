import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ml.classifier import get_classifier

logger = logging.getLogger("mnemo.api.ml")

router = APIRouter(prefix="/api/ml", tags=["machine-learning"])


class ClassificarRequest(BaseModel):
    texto: str = Field(description="Texto do flashcard (pergunta + resposta)")


class ClassificarResponse(BaseModel):
    categoria: str
    confianca: float
    probabilidades: dict[str, float]


class ClassificarBatchRequest(BaseModel):
    textos: list[str] = Field(description="Lista de textos para classificar")


class ClassificarBatchResponse(BaseModel):
    resultados: list[ClassificarResponse]


class TreinarRequest(BaseModel):
    textos: list[str] = Field(description="Textos de treino")
    labels: list[str] = Field(description="Labels correspondentes")


class TreinarResponse(BaseModel):
    accuracy: float
    report: str
    train_size: int
    test_size: int


@router.post("/classificar", response_model=ClassificarResponse)
def classificar_flashcard(req: ClassificarRequest):
    """Classifica um texto de flashcard em: conceito, definição, processo ou exemplo."""
    classifier = get_classifier()
    if not classifier.is_trained:
        raise HTTPException(
            status_code=503,
            detail="Modelo ainda não treinado. Execute POST /api/ml/treinar primeiro.",
        )
    return classifier.predict(req.texto)


@router.post("/classificar-batch", response_model=ClassificarBatchResponse)
def classificar_batch(req: ClassificarBatchRequest):
    """Classifica múltiplos textos de flashcards."""
    classifier = get_classifier()
    if not classifier.is_trained:
        raise HTTPException(
            status_code=503,
            detail="Modelo ainda não treinado. Execute POST /api/ml/treinar primeiro.",
        )
    return ClassificarBatchResponse(resultados=classifier.predict_batch(req.textos))


@router.post("/treinar", response_model=TreinarResponse)
def treinar_modelo(req: TreinarRequest):
    """Treina o classificador com os dados fornecidos."""
    if len(req.textos) != len(req.labels):
        raise HTTPException(status_code=400, detail="textos e labels devem ter o mesmo tamanho")
    if len(req.textos) < 10:
        raise HTTPException(status_code=400, detail="Mínimo de 10 amostras para treinar")

    classifier = get_classifier()
    metrics = classifier.train(req.textos, req.labels)

    return TreinarResponse(
        accuracy=metrics["accuracy"],
        report=metrics["report"],
        train_size=metrics["train_size"],
        test_size=metrics["test_size"],
    )


@router.get("/status")
def status_modelo():
    """Verifica se o modelo está treinado."""
    classifier = get_classifier()
    return {
        "treinado": classifier.is_trained,
        "modelo": "flashcard_classifier.pkl",
    }
