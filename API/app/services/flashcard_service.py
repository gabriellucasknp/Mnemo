import json
import logging
from typing import Literal

from google import genai
from google.genai import types
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


def _get_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key or None)


def gerar_flashcards(texto_transcricao: str) -> DeckGerado:
    client = _get_client()
    logger.info(
        "Enviando transcrição (%d chars) para %s",
        len(texto_transcricao),
        settings.gemini_model,
    )

    prompt = (
        "Gere os flashcards desta transcrição de aula e retorne APENAS um JSON "
        "válido com a estrutura: "
        '{"titulo": "...", "materia": "...", "flashcards": ['
        '{"categoria": "conceito|definição|processo|exemplo", '
        '"pergunta": "...", "resposta": "...", "explicacao": "... ou null"}'
        "]}\n\n"
        f"<transcricao>\n{texto_transcricao}\n</transcricao>"
    )

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM,
            response_mime_type="application/json",
            temperature=0.7,
            max_output_tokens=16000,
        ),
    )

    try:
        raw = response.text
        deck_dict = json.loads(raw)
        deck = DeckGerado(**deck_dict)
    except (json.JSONDecodeError, KeyError, Exception) as e:
        logger.error("Gemini não retornou formato válido: %s", e)
        raise RuntimeError("A IA não devolveu flashcards no formato esperado.") from e

    logger.info(
        "Deck gerado: %d flashcards, materia=%s, titulo=%s",
        len(deck.flashcards),
        deck.materia,
        deck.titulo,
    )
    return deck
