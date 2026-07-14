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
