"""Script de treinamento do classificador de flashcards.

Uso:
    cd API
    python -m scripts.train_model [--batches N] [--data-file PATH]

O script:
1. Gera dados sintéticos via API da Anthropic (ou carrega de arquivo existente)
2. Combina com flashcards existentes do banco (se houver)
3. Treina o classificador TF-IDF + LogisticRegression
4. Salva o modelo em app/ml/models/flashcard_classifier.pkl
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml.classifier import FlashcardClassifier
from app.ml.generator import (
    augment_with_existing_flashcards,
    generate_training_data,
    load_training_data,
    save_training_data,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("train")


def main():
    parser = argparse.ArgumentParser(description="Treina o classificador de flashcards")
    parser.add_argument("--batches", type=int, default=5, help="Número de batches para gerar via API")
    parser.add_argument("--data-file", type=str, default=None, help="Arquivo JSON existente com dados de treino")
    parser.add_argument("--save-data", type=str, default="training_data.json", help="Salvar dados gerados em JSON")
    parser.add_argument("--existing-flashcards", type=str, default=None, help="JSON com flashcards existentes do banco")
    args = parser.parse_args()

    # 1. Carregar ou gerar dados
    if args.data_file and Path(args.data_file).exists():
        logger.info("Carregando dados de %s...", args.data_file)
        samples = load_training_data(args.data_file)
    else:
        logger.info("Gerando dados sintéticos via Anthropic API (%d batches)...", args.batches)
        samples = generate_training_data(n_batches=args.batches)
        if samples:
            save_training_data(samples, args.save_data)

    # 2. Adicionar flashcards existentes do banco (se disponível)
    if args.existing_flashcards and Path(args.existing_flashcards).exists():
        with open(args.existing_flashcards, "r", encoding="utf-8") as f:
            existing = json.load(f)
        extra = augment_with_existing_flashcards(existing)
        samples.extend(extra)

    if len(samples) < 10:
        logger.error("Dados insuficientes: %d amostras (mínimo 10)", len(samples))
        sys.exit(1)

    # 3. Preparar features e labels
    texts = [f"{s['pergunta']} {s['resposta']}" for s in samples]
    labels = [s["categoria"] for s in samples]

    logger.info("Amostras: %d | Categorias: %s", len(texts), dict(zip(*[sorted(set(labels))] * 2, [labels.count(c) for c in sorted(set(labels))])))

    # 4. Treinar
    classifier = FlashcardClassifier()
    metrics = classifier.train(texts, labels)

    # 5. Resultados
    logger.info("=" * 50)
    logger.info("TREINO CONCLUÍDO")
    logger.info("Accuracy: %.2f%%", metrics["accuracy"] * 100)
    logger.info("Treino: %d | Teste: %d", metrics["train_size"], metrics["test_size"])
    logger.info("=" * 50)
    logger.info("\n%s", metrics["report"])


if __name__ == "__main__":
    main()
