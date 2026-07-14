import json
import logging
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger("mnemo.ml.generator")


class FlashcardSample(BaseModel):
    categoria: Literal["conceito", "definição", "processo", "exemplo"]
    pergunta: str
    resposta: str


class TrainingDataset(BaseModel):
    samples: list[FlashcardSample]


_SYSTEM = """Você é um gerador de dados de treinamento para um classificador de flashcards.

Gere exatamente 10 flashcards de exemplo, com a distribuição equilibrada:
- 3 conceitos
- 3 definições
- 2 processos
- 2 exemplos

Cada flashcard deve ter:
- categoria: "conceito", "definição", "processo" ou "exemplo"
- pergunta: pergunta clara e objetiva em português
- resposta: resposta direta em português (1-3 frases)

Dicas de classificação:
- conceito: explica o que algo É (ex: "O que é mitocôndria?")
- definição: dá o significado preciso de um termo (ex: "Como se define fotossíntese?")
- processo: descreve etapas ou sequência (ex: "Como ocorre a divisão celular?")
- exemplo: apresenta caso concreto (ex: "Qual um exemplo de protista?")

Gere flashcards de DIVERSAS disciplinas: Biologia, Química, Física, Matemática, História, Geografia, Filosofia, Sociologia, Literatura, etc."""

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
    return _client


def generate_training_data(
    n_batches: int = 5,
    disciplinas: list[str] | None = None,
) -> list[dict]:
    """Gera dados de treinamento sintéticos usando a API da Anthropic.

    Cada batch gera ~10 amostras. Com 5 batches, teremos ~50 amostras.
    """
    all_samples = []

    disciplinas_hint = ""
    if disciplinas:
        disciplinas_hint = f"\nFoque nestas disciplinas: {', '.join(disciplinas)}"

    for i in range(n_batches):
        logger.info("Gerando batch %d/%d...", i + 1, n_batches)
        try:
            response = _get_client().messages.parse(
                model=settings.anthropic_model,
                max_tokens=4000,
                system=_SYSTEM + disciplinas_hint,
                messages=[
                    {
                        "role": "user",
                        "content": f"Gere o batch {i + 1} de dados de treinamento. Varie as disciplinas e os exemplos.",
                    }
                ],
                output_format=TrainingDataset,
            )

            if response.parsed_output and response.parsed_output.samples:
                batch = [s.model_dump() for s in response.parsed_output.samples]
                all_samples.extend(batch)
                logger.info("Batch %d: %d amostras geradas", i + 1, len(batch))
            else:
                logger.warning("Batch %d: resposta vazia", i + 1)

        except Exception as e:
            logger.error("Erro no batch %d: %s", i + 1, e)
            continue

    logger.info("Total de amostras geradas: %d", len(all_samples))
    return all_samples


def save_training_data(samples: list[dict], path: str = "training_data.json"):
    """Salva dados de treinamento em JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    logger.info("Dados salvos em %s (%d amostras)", path, len(samples))


def load_training_data(path: str = "training_data.json") -> list[dict]:
    """Carrega dados de treinamento de JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def augment_with_existing_flashcards(
    flashcards: list[dict],
) -> list[dict]:
    """Usa flashcards existentes do banco como dados de treinamento extras.

    Espera dicts com chaves: pergunta, resposta, categoria
    """
    augmented = []
    for fc in flashcards:
        if all(k in fc for k in ("pergunta", "resposta", "categoria")):
            augmented.append({
                "categoria": fc["categoria"],
                "pergunta": fc["pergunta"],
                "resposta": fc["resposta"],
            })
    logger.info("Flashcards existentes adicionados: %d", len(augmented))
    return augmented
