import io

from app.models import Flashcard, Origem


def _criar_aula(client, titulo: str | None = None) -> int:
    files = {"audio": ("aula.mp3", io.BytesIO(b"fake"), "audio/mpeg")}
    data = {"titulo": titulo} if titulo else {}
    return client.post("/api/aulas", files=files, data=data).json()["id"]


def test_gerar_flashcards_persiste_com_origem(
    client, db, whisper_mockado, ia_mockada, storage_temporario
):
    aula_id = _criar_aula(client, "Bio 01")

    resposta = client.post(f"/api/aulas/{aula_id}/flashcards")
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert len(corpo["flashcards"]) == len(ia_mockada.flashcards)
    assert corpo["flashcards"][0]["pergunta"] == ia_mockada.flashcards[0].pergunta

    salvos = db.query(Flashcard).all()
    assert all(f.aula_id == aula_id for f in salvos)
    assert all(f.origem is Origem.PROFESSOR for f in salvos)


def test_ia_infere_titulo_e_materia_quando_sem_titulo(
    client, whisper_mockado, ia_mockada, storage_temporario
):
    aula_id = _criar_aula(client)
    corpo = client.post(f"/api/aulas/{aula_id}/flashcards").json()
    assert corpo["titulo"] == ia_mockada.titulo
    assert corpo["materia"] == ia_mockada.materia


def test_titulo_do_usuario_nao_e_sobrescrito(
    client, whisper_mockado, ia_mockada, storage_temporario
):
    aula_id = _criar_aula(client, "Meu título")
    corpo = client.post(f"/api/aulas/{aula_id}/flashcards").json()
    assert corpo["titulo"] == "Meu título"
    assert corpo["materia"] == ia_mockada.materia


def test_gerar_flashcards_de_aula_inexistente_da_404(client):
    assert client.post("/api/aulas/999/flashcards").status_code == 404


def test_listar_flashcards(client, whisper_mockado, ia_mockada, storage_temporario):
    aula_id = _criar_aula(client)
    client.post(f"/api/aulas/{aula_id}/flashcards")
    resposta = client.get(f"/api/aulas/{aula_id}/flashcards")
    assert resposta.status_code == 200
    assert len(resposta.json()) == len(ia_mockada.flashcards)


def test_listar_flashcards_de_aula_inexistente_da_404(client):
    assert client.get("/api/aulas/999/flashcards").status_code == 404


def test_sem_transcricao_nao_gera_flashcards(client, db, whisper_mockado, storage_temporario):
    from app.models import Aula

    aula = Aula(titulo="Sem transcricao")
    db.add(aula)
    db.commit()
    db.refresh(aula)

    resp = client.post(f"/api/aulas/{aula.id}/flashcards")
    assert resp.status_code == 400
    assert "transcrição" in resp.json()["detail"].lower()


def test_flashcards_sem_explicacao(client, whisper_mockado, ia_mockada, storage_temporario):
    aula_id = _criar_aula(client)
    client.post(f"/api/aulas/{aula_id}/flashcards")
    cards = client.get(f"/api/aulas/{aula_id}/flashcards").json()
    # Pelo menos um flashcard sem explicacao
    sem_exp = [c for c in cards if c["explicacao"] is None]
    assert len(sem_exp) >= 1


def test_varias_categorias(client, whisper_mockado, ia_mockada, storage_temporario):
    aula_id = _criar_aula(client)
    client.post(f"/api/aulas/{aula_id}/flashcards")
    cards = client.get(f"/api/aulas/{aula_id}/flashcards").json()
    categorias = {c["categoria"] for c in cards}
    assert len(categorias) >= 2
