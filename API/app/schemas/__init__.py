# Schemas Pydantic — o "contrato" das respostas JSON da API.
# São a versão serializável dos modelos do banco (from_attributes=True
# permite criar direto de um objeto SQLAlchemy).
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.transcription import Origem


class TranscricaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    texto: str
    idioma: str | None
    origem: Origem  # serializa como "professor" / "ia" no JSON
    criada_em: datetime


class FlashcardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    categoria: str
    pergunta: str
    resposta: str
    explicacao: str | None
    origem: Origem


class AulaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    materia: str | None
    duracao_segundos: int | None
    criada_em: datetime


class AulaDetalheOut(AulaOut):
    transcricao: TranscricaoOut | None = None
    flashcards: list[FlashcardOut] = []


class SimuladoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    materia: str | None
    quantidade_questoes: int
    dificuldade: str
    aula_id: int | None
    criada_em: datetime


class QuestaoSimuladoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    enunciado: str
    alternativas: dict
    explicacao: str | None
    dificuldade: str
    disciplina: str | None


class SimuladoDetalheOut(SimuladoOut):
    questoes: list[QuestaoSimuladoOut] = []
