from app.services.flashcard_service import FlashcardGerado, DeckGerado


def test_flashcard_gerado_campos_obrigatorios():
    fc = FlashcardGerado(
        categoria="conceito",
        pergunta="O que é?",
        resposta="É algo.",
    )
    assert fc.categoria == "conceito"
    assert fc.explicacao is None


def test_deck_gerado_serializa_corretamente():
    deck = DeckGerado(
        titulo="Teste",
        materia="Mat",
        flashcards=[
            FlashcardGerado(categoria="definição", pergunta="Q?", resposta="R."),
            FlashcardGerado(categoria="exemplo", pergunta="Q2?", resposta="R2.", explicacao="ctx"),
        ],
    )
    d = deck.model_dump()
    assert d["titulo"] == "Teste"
    assert len(d["flashcards"]) == 2
    assert d["flashcards"][1]["explicacao"] == "ctx"


def test_deck_gerado_categorias_validas():
    for cat in ["conceito", "definição", "processo", "exemplo"]:
        fc = FlashcardGerado(categoria=cat, pergunta="Q", resposta="R")
        assert fc.categoria == cat


def test_deck_sem_flashcards():
    deck = DeckGerado(titulo="Vazio", materia="Nenhuma", flashcards=[])
    assert len(deck.flashcards) == 0


def test_questao_gerada_normaliza_gabarito():
    import pytest

    from app.services.question_service import QuestaoGerada

    base = {
        "enunciado": "Enunciado de teste com contexto suficiente.",
        "alternativas": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
    }

    assert QuestaoGerada(**base, gabarito="c").gabarito == "C"
    assert QuestaoGerada(**base, gabarito=" B ").gabarito == "B"
    # "C)" / "C." vindos do LLM são normalizados pra letra
    assert QuestaoGerada(**base, gabarito="C)").gabarito == "C"

    with pytest.raises(ValueError):
        QuestaoGerada(**base, gabarito="Alternativa C")
    with pytest.raises(ValueError):
        QuestaoGerada(**base, gabarito="F")
