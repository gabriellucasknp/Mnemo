# Serviço de GERAÇÃO DE FLASHCARDS com IA (Etapa 5).
# Decisão tomada: modelo VIA API (Anthropic / Claude), não local.
#
# Os dois conceitos-chave da etapa, materializados aqui:
# (a) o PROMPT molda o que sai -> instruções explícitas em PT-BR, com a regra
#     da fonte (SDD §5): os cartões devem refletir SOMENTE o que o professor disse.
# (b) a saída precisa ser ESTRUTURADA -> usamos `client.messages.parse()` com um
#     schema Pydantic: a API garante JSON válido e o SDK valida e devolve objetos.
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from app.config import settings


# --- Schema da saída estruturada (o que a IA é OBRIGADA a devolver) ---
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


def gerar_flashcards(texto_transcricao: str) -> DeckGerado:
    """Manda a transcrição pro Claude e devolve o deck estruturado e validado."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)

    response = client.messages.parse(
        model=settings.anthropic_model,
        max_tokens=16000,
        thinking={"type": "adaptive"},  # o modelo decide quanto "pensar"
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
        output_format=DeckGerado,  # saída estruturada: JSON garantido pelo schema
    )
    deck = response.parsed_output
    if deck is None:
        raise RuntimeError("A IA não devolveu flashcards no formato esperado.")
    return deck
