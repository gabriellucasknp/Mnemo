import json
import logging
import random
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import settings
from app.ml.question_model import get_question_quality_model

logger = logging.getLogger("mnemo.question_service")


class QuestaoGerada(BaseModel):
    enunciado: str = Field(description="Texto da questão (enunciado)")
    alternativas: dict[str, str] = Field(
        description="Alternativas de A a E"
    )
    gabarito: str = Field(description="Letra da resposta correta (A-E)")
    explicacao: str | None = Field(
        default=None, description="Explicação da resposta correta"
    )
    dificuldade: Literal["facil", "medio", "dificil"] = Field(
        default="medio", description="Nível de dificuldade"
    )
    disciplina: str | None = Field(
        default=None, description="Disciplina/área de conhecimento"
    )


class SimuladoGerado(BaseModel):
    titulo: str
    materia: str | None = None
    questoes: list[QuestaoGerada]


def _get_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key or None)


def _get_enem_examples(n: int = 3) -> str:
    try:
        from app.ml.question_model import _load_enem_dataset

        dataset = _load_enem_dataset()
        if not dataset:
            return ""
        samples = random.sample(dataset, min(n, len(dataset)))
        examples_text = "EXEMPLOS DE QUESTÕES ENEM (use como referência de estilo):\n\n"
        for i, s in enumerate(samples, 1):
            alts = s.get("alternatives", [])
            alt_lines = []
            for j, alt in enumerate(alts):
                letter = chr(65 + j)
                alt_lines.append(f"  {letter}) {alt}")
            examples_text += f"Exemplo {i}:\nEnunciado: {s['question'][:500]}\n"
            examples_text += "\n".join(alt_lines) + "\n"
            examples_text += f"Gabarito: {s.get('label', 'A')}\n\n"
        return examples_text
    except Exception as e:
        logger.warning("Erro ao carregar exemplos ENEM: %s", e)
        return ""


_SYSTEM = """Você é um gerador de questões de múltipla escolha no estilo ENEM.

REGRA PRINCIPAL: Gere questões densas, com enunciados ricos e alternativas plausíveis.
Cada questão deve ter EXATAMENTE 5 alternativas (A, B, C, D, E) onde apenas uma está correta.

DIRETRIZES:
- Enunciados longos e contextualizados (mínimo 2 frases), como questões de provas reais.
- Alternativas de tamanho similar, todas plausíveis para quem não sabe a resposta.
- A resposta correta pode estar em qualquer posição (não sempre A ou C).
- Inclua explicação detalhada de por que a resposta correta está certa.
- Varie a dificuldade: 3 fáceis, 4 médios, 3 difíceis por simulado.
- Disciplinas: use a matéria dos flashcards como guia.

FORMATO DE SAÍDA (JSON):
{
  "titulo": "Simulado - [Matéria]",
  "materia": "[Matéria]",
  "questoes": [
    {
      "enunciado": "Texto completo da questão...",
      "alternativas": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
      "gabarito": "C",
      "explicacao": "A resposta C está correta porque...",
      "dificuldade": "medio",
      "disciplina": "[Disciplina]"
    }
  ]
}"""


def gerar_simulado(
    flashcards: list[dict],
    titulo: str | None = None,
    materia: str | None = None,
    quantidade: int = 10,
) -> SimuladoGerado:
    """Gera um simulado completo a partir de flashcards."""
    client = _get_client()
    enem_examples = _get_enem_examples(3)

    fc_text = "\n".join(
        f"- {fc.get('pergunta', '')} → {fc.get('resposta', '')}"
        for fc in flashcards
    )

    prompt = (
        f"Gere um simulado com {quantidade} questões de múltipla escolha "
        f"baseado nos seguintes flashcards de estudo:\n\n{fc_text}\n\n"
    )
    if titulo:
        prompt += f"Título do simulado: {titulo}\n"
    if materia:
        prompt += f"Matéria: {materia}\n"
    if enem_examples:
        prompt += f"\n{enem_examples}\n"
    prompt += (
        "\nRetorne APENAS um JSON válido com a estrutura especificada."
    )

    logger.info(
        "Gerando simulado com %d questões a partir de %d flashcards",
        quantidade,
        len(flashcards),
    )

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM,
            response_mime_type="application/json",
            temperature=0.8,
            max_output_tokens=16000,
        ),
    )

    try:
        raw = response.text
        data = json.loads(raw)
        simulado = SimuladoGerado(**data)
    except (json.JSONDecodeError, KeyError, Exception) as e:
        logger.error("Gemini não retornou formato válido: %s", e)
        raise RuntimeError("A IA não devolveu o simulado no formato esperado.") from e

    if not simulado.questoes:
        raise RuntimeError("A IA não gerou nenhuma questão.")

    quality_model = get_question_quality_model()
    if quality_model.is_trained:
        for q in simulado.questoes:
            eval_result = quality_model.evaluate(q.enunciado, list(q.alternativas.values()))
            if eval_result["qualidade"] == "baixa":
                logger.warning(
                    "Questão com baixa qualidade detectada: %s...",
                    q.enunciado[:80],
                )

    logger.info(
        "Simulado gerado: %d questões, materia=%s",
        len(simulado.questoes),
        simulado.materia,
    )
    return simulado
