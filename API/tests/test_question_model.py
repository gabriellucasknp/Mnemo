import pytest

from app.ml.question_model import (
    QuestionQualityModel,
    QUALITY_MODEL_PATH,
    get_question_quality_model,
    _load_enem_dataset,
    _extract_features,
)


@pytest.fixture
def modelo(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.ml.question_model.QUALITY_MODEL_PATH", tmp_path / "fake_quality.pkl"
    )
    return QuestionQualityModel()


@pytest.fixture
def modelo_treinado(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.ml.question_model.QUALITY_MODEL_PATH", tmp_path / "fake_quality.pkl"
    )
    m = QuestionQualityModel()
    m.train_on_enem()
    return m


def test_dataset_existe():
    dataset = _load_enem_dataset()
    assert len(dataset) == 100


def test_dataset_campos():
    dataset = _load_enem_dataset()
    for q in dataset:
        assert "question" in q
        assert "alternatives" in q
        assert "label" in q
        assert len(q["alternatives"]) == 5
        assert q["label"] in ["A", "B", "C", "D", "E"]


def test_extrair_features():
    q = {
        "question": "O que é mitocôndria? A mitocôndria é a organela responsável.",
        "alternatives": ["A", "B", "C", "D", "E"],
        "label": "A",
        "description": [],
    }
    features = _extract_features(q)
    assert "text_len" in features
    assert "word_count" in features
    assert "has_image" in features
    assert features["num_alternatives"] == 5
    assert features["has_image"] == 0


def test_modelo_nao_treinado(modelo):
    assert not modelo.is_trained
    result = modelo.evaluate("O que é célula?")
    assert result["qualidade"] == "media"
    assert result["confianca"] == 0.5


def test_treinar_modelo(modelo):
    metrics = modelo.train_on_enem()
    assert modelo.is_trained
    assert "accuracy" in metrics
    assert metrics["dataset_size"] == 100
    assert metrics["train_size"] + metrics["test_size"] == 200


def test_avaliar_questao_alta(modelo_treinado):
    dataset = _load_enem_dataset()
    q = dataset[0]
    result = modelo_treinado.evaluate(q["question"], q["alternatives"])
    assert result["qualidade"] in ["alta", "media", "baixa"]
    assert 0 <= result["confianca"] <= 1


def test_get_question_quality_model():
    m = get_question_quality_model()
    assert isinstance(m, QuestionQualityModel)
