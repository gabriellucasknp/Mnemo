"""Treina os modelos ML no BUILD da imagem Docker — artefatos reproduzíveis.

Motivação: os `.pkl` ficam fora do git (binários) e o filesystem do Render é
efêmero. Sem este passo, o classificador nasce 503 em produção e o modelo de
qualidade se perde a cada deploy. Treinar no build resolve os dois problemas
com dados versionados no repositório:

  - flashcard_classifier.pkl  <- app/ml/data/seed_flashcards.json
  - question_quality_model.pkl <- app/ml/data/enem_2022.json

Determinístico (random_state fixo nos treinos), sem rede, roda em segundos.
Para um modelo melhor que o seed, use scripts/train_model.py (gera dados via
Gemini) e substitua o seed_flashcards.json.

Uso:
    cd API
    python -m scripts.build_models
"""

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml.classifier import FlashcardClassifier
from app.ml.question_model import QuestionQualityModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("build_models")

SEED_PATH = Path(__file__).parent.parent / "app" / "ml" / "data" / "seed_flashcards.json"


def main() -> None:
    # 1. Classificador de flashcards (seed versionado no git)
    with open(SEED_PATH, "r", encoding="utf-8") as f:
        samples = json.load(f)

    texts = [f"{s['pergunta']} {s['resposta']}" for s in samples]
    labels = [s["categoria"] for s in samples]

    classifier = FlashcardClassifier()
    metrics = classifier.train(texts, labels)
    logger.info(
        "flashcard_classifier: %d amostras, accuracy=%.2f",
        len(samples),
        metrics["accuracy"],
    )

    # 2. Modelo de qualidade de questões (dataset ENEM versionado no git)
    quality = QuestionQualityModel()
    q_metrics = quality.train_on_enem()
    logger.info(
        "question_quality_model: dataset=%d, accuracy=%.2f",
        q_metrics["dataset_size"],
        q_metrics["accuracy"],
    )


if __name__ == "__main__":
    main()
