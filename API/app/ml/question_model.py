import json
import logging
import pickle
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

logger = logging.getLogger("mnemo.ml.question_model")

DATA_DIR = Path(__file__).parent / "data"
DATASET_PATH = DATA_DIR / "enem_2022.json"

MODEL_DIR = Path(__file__).parent / "models"
QUALITY_MODEL_PATH = MODEL_DIR / "question_quality_model.pkl"


def _load_enem_dataset() -> list[dict]:
    if not DATASET_PATH.exists():
        logger.warning("Dataset ENEM não encontrado em %s", DATASET_PATH)
        return []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_features(question: dict) -> dict:
    text = question.get("question", "")
    alternatives = question.get("alternatives", [])
    label = question.get("label", "")
    description = question.get("description", [])

    has_image = bool(description)
    text_len = len(text)
    alt_lengths = [len(a) for a in alternatives]
    avg_alt_len = np.mean(alt_lengths) if alt_lengths else 0
    alt_len_std = np.std(alt_lengths) if alt_lengths else 0
    num_alternatives = len(alternatives)
    has_context = "##" in text or "TEXTO" in text.upper()
    has_author = any(
        w in text.lower()
        for w in ["poema", "romance", "conto", "crônica", "letra", "texto de"]
    )

    words = text.split()
    word_count = len(words)
    unique_ratio = len(set(w.lower() for w in words)) / max(word_count, 1)

    return {
        "text_len": text_len,
        "word_count": word_count,
        "unique_ratio": unique_ratio,
        "avg_alt_len": avg_alt_len,
        "alt_len_std": alt_len_std,
        "num_alternatives": num_alternatives,
        "has_image": int(has_image),
        "has_context": int(has_context),
        "has_author": int(has_author),
        "label_ord": ord(label) - ord("A") if label else 2,
    }


class QuestionQualityModel:
    """Avalia a qualidade de questões geradas por IA usando padrões do ENEM."""

    def __init__(self):
        self.pipeline: Pipeline | None = None
        self._trained_on_enem = False
        self._load_model()

    def _load_model(self):
        if QUALITY_MODEL_PATH.exists():
            with open(QUALITY_MODEL_PATH, "rb") as f:
                self.pipeline = pickle.load(f)
            self._trained_on_enem = True
            logger.info("Modelo de qualidade carregado de %s", QUALITY_MODEL_PATH)
        else:
            logger.warning(
                "Nenhum modelo de qualidade encontrado em %s", QUALITY_MODEL_PATH
            )

    def _save_model(self):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with open(QUALITY_MODEL_PATH, "wb") as f:
            pickle.dump(self.pipeline, f)
        logger.info("Modelo de qualidade salvo em %s", QUALITY_MODEL_PATH)

    def train_on_enem(self) -> dict:
        """Treina o modelo usando o dataset ENEM como referência de alta qualidade."""
        dataset = _load_enem_dataset()
        if len(dataset) < 10:
            raise RuntimeError("Dataset ENEM insuficiente para treino")

        texts = []
        labels_binary = []

        for q in dataset:
            text = q.get("question", "")
            alternatives = q.get("alternatives", [])
            combined = text + " " + " ".join(alternatives)
            texts.append(combined)
            labels_binary.append("alta")

        synthetic_low = _generate_low_quality_samples(len(dataset))
        texts.extend([s["text"] for s in synthetic_low])
        labels_binary.extend(["baixa"] * len(synthetic_low))

        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels_binary, test_size=0.2, random_state=42, stratify=labels_binary
        )

        self.pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        max_features=5000,
                        ngram_range=(1, 2),
                        sublinear_tf=True,
                        strip_accents="unicode",
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=1000,
                        C=1.0,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        )

        self.pipeline.fit(X_train, y_train)
        y_pred = self.pipeline.predict(X_test)
        report = classification_report(y_test, y_pred, output_dict=True)

        self._save_model()
        self._trained_on_enem = True

        logger.info(
            "Modelo de qualidade treinado. Accuracy: %.2f%%",
            report["accuracy"] * 100,
        )
        return {
            "accuracy": report["accuracy"],
            "report": classification_report(y_test, y_pred),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "dataset_size": len(dataset),
        }

    def evaluate(self, question_text: str, alternatives: list[str] | None = None) -> dict:
        """Avalia a qualidade de uma questão gerada."""
        if self.pipeline is None:
            return {"qualidade": "media", "confianca": 0.5, "detalhes": "Modelo não treinado"}

        combined = question_text
        if alternatives:
            combined += " " + " ".join(alternatives)

        proba = self.pipeline.predict_proba([combined])[0]
        classes = self.pipeline.classes_

        idx_high = list(classes).index("alta") if "alta" in classes else 0
        quality_score = float(proba[idx_high])

        if quality_score >= 0.7:
            qualidade = "alta"
        elif quality_score >= 0.4:
            qualidade = "media"
        else:
            qualidade = "baixa"

        features = _extract_features({
            "question": question_text,
            "alternatives": alternatives or [],
            "label": "",
            "description": [],
        })

        return {
            "qualidade": qualidade,
            "confianca": quality_score,
            "features": features,
        }

    @property
    def is_trained(self) -> bool:
        return self.pipeline is not None


def _generate_low_quality_samples(n: int) -> list[dict]:
    templates = [
        "O que é X?",
        "Qual é a definição de Y?",
        "Como funciona Z?",
        "Explique o processo de W.",
        "Qual a importância de V?",
        "Descreva U.",
        "Quais são as características de T?",
        "Como ocorre S?",
        "O que significa R?",
        "Qual a função de Q?",
    ]
    samples = []
    for i in range(n):
        tmpl = templates[i % len(templates)]
        samples.append({
            "text": tmpl + " " + " ".join(["resposta genérica"] * (i % 3 + 1)),
        })
    return samples


_quality_model: QuestionQualityModel | None = None


def get_question_quality_model() -> QuestionQualityModel:
    global _quality_model
    if _quality_model is None:
        _quality_model = QuestionQualityModel()
    return _quality_model
