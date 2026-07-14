import logging
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger("mnemo.flashcard")


class FlashcardGerado(BaseModel):
    categoria: Literal["conceito", "definição", "processo", "exemplo"] = Field(
        description="Tipo do cartão"
    )
    pergunta: str = Field(description="Pergunta clara e objetiva, em português")
    resposta: str = Field(description="Resposta direta, fiel à fala do professor")
    explicacao: str | None = Field(
        default=None, description="Contexto adicional curto, opcional"
    )


class DeckGerado(BaseModel):
    titulo: str = Field(description="Título curto da aula, inferido do conteúdo")
    materia: str = Field(description="Matéria/disciplina inferida, ex.: Biologia")
    flashcards: list[FlashcardGerado]


_SYSTEM = """Você gera flashcards de estudo a partir da transcrição de uma aula.

REGRA CRÍTICA: a fala do professor é a fonte de verdade. Cada flashcard deve
refletir SOMENTE o que está na transcrição — não adicione fatos externos, não
corrija o professor, não complete lacunas com conhecimento seu. Se a transcrição
tiver erros de reconhecimento de fala óbvios, interprete pelo contexto.

Diretrizes:
- Perguntas e respostas em português do Brasil, claras e autocontidas.
- Cubra os conceitos-chave da aula (mínimo 6 cartões para aulas com conteúdo suficiente).
- Respostas curtas (1-3 frases); use "explicacao" para contexto extra quando ajudar.
- Classifique cada cartão em: conceito, definição, processo ou exemplo."""

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
    return _client


def gerar_flashcards(texto_transcricao: str) -> DeckGerado:
    logger.info(
        "Enviando transcrição (%d chars) para %s",
        len(texto_transcricao),
        settings.anthropic_model,
    )
    response = _get_client().messages.parse(
        model=settings.anthropic_model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    "Gere os flashcards desta transcrição de aula:\n\n"
                    f"<transcricao>\n{texto_transcricao}\n</transcricao>"
                ),
            }
        ],
        output_format=DeckGerado,
    )
    deck = response.parsed_output
    if deck is None:
        logger.error("Anthropic não retornou formato válido")
        raise RuntimeError("A IA não devolveu flashcards no formato esperado.")
    logger.info(
        "Deck gerado: %d flashcards, materia=%s, titulo=%s",
        len(deck.flashcards),
        deck.materia,
        deck.titulo,
    )
    return deck
