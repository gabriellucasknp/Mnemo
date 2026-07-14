import logging
import pickle
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

logger = logging.getLogger("mnemo.ml.classifier")

CATEGORIES = ["conceito", "definição", "processo", "exemplo"]

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "flashcard_classifier.pkl"


class FlashcardClassifier:
    """Classificador de categorias de flashcards usando TF-IDF + LogisticRegression."""

    def __init__(self):
        self.pipeline: Pipeline | None = None
        self._load_model()

    def _load_model(self):
        if MODEL_PATH.exists():
            with open(MODEL_PATH, "rb") as f:
                self.pipeline = pickle.load(f)
            logger.info("Modelo carregado de %s", MODEL_PATH)
        else:
            logger.warning("Nenhum modelo treinado encontrado em %s", MODEL_PATH)

    def _save_model(self):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(self.pipeline, f)
        logger.info("Modelo salvo em %s", MODEL_PATH)

    def train(
        self,
        texts: list[str],
        labels: list[str],
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> dict:
        """Treina o classificador e retorna métricas."""
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=test_size, random_state=random_state, stratify=labels
        )

        self.pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(
                    max_features=10000,
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                    strip_accents="unicode",
                )),
                ("clf", LogisticRegression(
                    max_iter=1000,
                    C=1.0,
                    class_weight="balanced",
                    random_state=random_state,
                )),
            ]
        )

        self.pipeline.fit(X_train, y_train)

        y_pred = self.pipeline.predict(X_test)
        report = classification_report(y_test, y_pred, output_dict=True)

        self._save_model()

        logger.info("Treino concluído. Accuracy: %.2f%%", report["accuracy"] * 100)
        return {
            "accuracy": report["accuracy"],
            "report": classification_report(y_test, y_pred),
            "train_size": len(X_train),
            "test_size": len(X_test),
        }

    def predict(self, text: str) -> dict:
        """Prediz a categoria de um texto."""
        if self.pipeline is None:
            raise RuntimeError("Modelo não treinado. Execute o treinamento primeiro.")

        proba = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_

        sorted_idx = np.argsort(proba)[::-1]
        return {
            "categoria": classes[sorted_idx[0]],
            "confianca": float(proba[sorted_idx[0]]),
            "probabilidades": {
                classes[i]: float(proba[i]) for i in sorted_idx
            },
        }

    def predict_batch(self, texts: list[str]) -> list[dict]:
        """Prediz categorias para uma lista de textos."""
        return [self.predict(text) for text in texts]

    @property
    def is_trained(self) -> bool:
        return self.pipeline is not None


_classifier: FlashcardClassifier | None = None


def get_classifier() -> FlashcardClassifier:
    global _classifier
    if _classifier is None:
        _classifier = FlashcardClassifier()
    return _classifier
