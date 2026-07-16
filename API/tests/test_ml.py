import pytest

from app.ml.classifier import FlashcardClassifier, MODEL_PATH, get_classifier


@pytest.fixture
def classifier(tmp_path, monkeypatch):
    """Retorna um classificador fresh (sem modelo salvo)."""
    monkeypatch.setattr("app.ml.classifier.MODEL_PATH", tmp_path / "fake.pkl")
    return FlashcardClassifier()


@pytest.fixture
def trained_classifier():
    """Retorna um classificador já treinado com dados mínimos."""
    clf = FlashcardClassifier()
    texts = [
        "O que é mitocôndria? A mitocôndria é a organela da respiração celular.",
        "Como se divide a célula? Por mitose e meiose.",
        "Qual exemplo de protista? A ameba.",
        "Defina fotossíntese. Processo de conversão de luz em energia química.",
        "O que é osmose? Transporte de água através de membrana semipermeável.",
        "Como ocorre a digestão? Processo mecânico e químico dos alimentos.",
        "Exemplo de planariana? A minhoca-sola.",
        "Conceito de célula. Unidade fundamental da vida.",
        "Definição de DNA. Molécula que armazena informação genética.",
        "Processo de respiração celular. Glicólise + ciclo de Krebs.",
        "Exemplo de bactéria. E. coli.",
        "O que é energia? Capacidade de realizar trabalho.",
        "Como ocorre a meiose? Divisão reducional do núcleo.",
        "Defina citoplasma. Parte da célula entre membrana e núcleo.",
        "Exemplo de fungo? A levedura.",
        "Conceito de ecossistema. Conjunto de seres vivos e ambiente.",
        "Processo de fermentação. Conversão de glicose em álcool.",
        "O que é proteína? Macromolécula essencial para o corpo.",
    ]
    labels = [
        "conceito", "processo", "exemplo", "definição",
        "definição", "processo", "exemplo", "conceito",
        "definição", "processo", "exemplo", "conceito",
        "processo", "definição", "exemplo", "conceito",
        "processo", "conceito",
    ]
    clf.train(texts, labels)
    return clf


def test_classificador_nao_treinado(classifier):
    assert not classifier.is_trained
    with pytest.raises(RuntimeError):
        classifier.predict("teste")


def test_treino(classifier):
    texts = [
        "O que é mitocôndria? A organela da respiração.",
        "Como se divide a célula? Por mitose.",
        "Qual exemplo de protista? A ameba.",
        "Defina fotossíntese. Conversão de luz em energia.",
        "O que é osmose? Transporte de água.",
        "Como ocorre a digestão? Processo mecânico e químico.",
        "Exemplo de planariana? Minhoca-sola.",
        "Conceito de célula. Unidade da vida.",
        "Definição de DNA. Molécula de informação genética.",
        "Processo de respiração celular. Glicólise.",
        "Exemplo de bactéria. E. coli.",
        "O que é energia? Capacidade de realizar trabalho.",
        "Como ocorre a meiose? Divisão reducional.",
        "Defina citoplasma. Fluido entre membrana e núcleo.",
        "Exemplo de fungo? A levedura.",
        "Conceito de ecossistema. Seres vivos e ambiente.",
        "Processo de fermentação. Glicose em álcool.",
        "O que é proteína? Macromolécula essencial.",
    ]
    labels = [
        "conceito", "processo", "exemplo", "definição",
        "definição", "processo", "exemplo", "conceito",
        "definição", "processo", "exemplo", "conceito",
        "processo", "definição", "exemplo", "conceito",
        "processo", "conceito",
    ]
    metrics = classifier.train(texts, labels)
    assert classifier.is_trained
    assert "accuracy" in metrics
    assert metrics["train_size"] + metrics["test_size"] == len(texts)


def test_predict(trained_classifier):
    result = trained_classifier.predict("O que é mitocôndria?")
    assert "categoria" in result
    assert "confianca" in result
    assert result["categoria"] in ["conceito", "definição", "processo", "exemplo"]
    assert 0 <= result["confianca"] <= 1


def test_predict_batch(trained_classifier):
    texts = ["O que é DNA?", "Como funciona a mitose?"]
    results = trained_classifier.predict_batch(texts)
    assert len(results) == 2
    for r in results:
        assert r["categoria"] in ["conceito", "definição", "processo", "exemplo"]


def test_get_classifier():
    clf = get_classifier()
    assert isinstance(clf, FlashcardClassifier)
