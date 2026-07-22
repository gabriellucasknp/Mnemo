import pytest

from app.models.simulado import QuestaoSimulado, RespostaSimulado, Simulado


@pytest.fixture
def simulado_criado(db, ia_mockada):
    from app.models import Aula

    aula = Aula(titulo="Aula Teste", materia="Biologia")
    db.add(aula)
    db.flush()

    from app.models.flashcard import Flashcard

    fc = Flashcard(
        aula_id=aula.id,
        categoria="definição",
        pergunta="O que é mitocôndria?",
        resposta="Organela da respiração celular.",
    )
    db.add(fc)
    db.flush()

    simulado = Simulado(
        titulo="Simulado Teste",
        materia="Biologia",
        quantidade_questoes=2,
        dificuldade="medio",
        aula_id=aula.id,
    )
    db.add(simulado)
    db.flush()

    q1 = QuestaoSimulado(
        simulado_id=simulado.id,
        enunciado="Qual organela realiza respiração celular?",
        alternativas={"A": "Ribossomo", "B": "Mitocôndria", "C": "Lisossomo", "D": "Complexo de Golgi", "E": "Retículo endoplasmático"},
        gabarito="B",
        explicacao="A mitocôndria é a organela responsável pela respiração celular.",
        dificuldade="medio",
        disciplina="Biologia",
        fonte="ia",
    )
    q2 = QuestaoSimulado(
        simulado_id=simulado.id,
        enunciado="Qual a função principal dos ribossomos?",
        alternativas={"A": "Síntese de proteínas", "B": "Digestão", "C": "Transporte", "D": "Energia", "E": "Armazenamento"},
        gabarito="A",
        explicacao="Ribossomos são responsáveis pela síntese de proteínas.",
        dificuldade="facil",
        disciplina="Biologia",
        fonte="ia",
    )
    db.add(q1)
    db.add(q2)
    db.commit()
    db.refresh(simulado)

    return simulado


def test_listar_simulados_vazio(client):
    response = client.get("/api/simulados")
    assert response.status_code == 200
    assert response.json() == []


def test_detalhar_simulado(client, simulado_criado):
    response = client.get(f"/api/simulados/{simulado_criado.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["titulo"] == "Simulado Teste"
    assert data["materia"] == "Biologia"
    assert len(data["questoes"]) == 2


def test_detalhar_simulado_nao_encontrado(client):
    response = client.get("/api/simulados/9999")
    assert response.status_code == 404


def test_responder_simulado(client, simulado_criado):
    questoes = simulado_criado.questoes
    respostas = {q.id: "B" if q.gabarito == "B" else "A" for q in questoes}

    response = client.post(
        f"/api/simulados/{simulado_criado.id}/responder",
        json={"respostas": respostas},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_questoes"] == 2
    assert data["acertadas"] >= 0
    assert data["percentual"] >= 0


def test_deletar_simulado(client, simulado_criado):
    response = client.delete(f"/api/simulados/{simulado_criado.id}")
    assert response.status_code == 204

    response = client.get(f"/api/simulados/{simulado_criado.id}")
    assert response.status_code == 404


def test_deletar_simulado_nao_encontrado(client):
    response = client.delete("/api/simulados/9999")
    assert response.status_code == 404


def test_criar_simulado_aula_nao_encontrada(client):
    response = client.post(
        "/api/simulados",
        json={"aula_id": 9999, "quantidade": 5},
    )
    assert response.status_code == 404


def test_criar_simulado_sem_flashcards(client, db):
    from app.models import Aula

    aula = Aula(titulo="Aula Vazia", materia="História")
    db.add(aula)
    db.commit()

    response = client.post(
        "/api/simulados",
        json={"aula_id": aula.id, "quantidade": 5},
    )
    assert response.status_code == 400


def test_pagina_simulados(client, simulado_criado):
    response = client.get("/simulados")
    assert response.status_code == 200
    assert "Simulados" in response.text


def test_pagina_simulado_detalhe(client, simulado_criado):
    response = client.get(f"/simulados/{simulado_criado.id}")
    assert response.status_code == 200
    assert simulado_criado.titulo in response.text


def test_pagina_simulado_nao_encontrado(client):
    response = client.get("/simulados/9999")
    assert response.status_code == 404
