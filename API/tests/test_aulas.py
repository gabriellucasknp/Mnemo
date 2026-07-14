import io

from app.config import settings
from app.models import Aula, Origem, Transcricao
from tests.conftest import TRANSCRICAO_FAKE


def _audio_fake(nome: str = "aula.mp3"):
    return {"audio": (nome, io.BytesIO(b"bytes-de-audio-fake"), "audio/mpeg")}


def test_enviar_aula_cria_aula_e_transcricao(client, db, whisper_mockado, storage_temporario):
    resposta = client.post("/api/aulas", files=_audio_fake(), data={"titulo": "Bio 01"})

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["titulo"] == "Bio 01"
    assert corpo["duracao_segundos"] == TRANSCRICAO_FAKE["duracao_segundos"]
    assert corpo["transcricao"]["texto"] == TRANSCRICAO_FAKE["texto"]
    assert corpo["transcricao"]["origem"] == "professor"

    assert db.query(Aula).count() == 1
    assert db.query(Transcricao).one().origem is Origem.PROFESSOR


def test_enviar_aula_sem_titulo_usa_padrao(client, whisper_mockado, storage_temporario):
    resposta = client.post("/api/aulas", files=_audio_fake())
    assert resposta.status_code == 201
    assert resposta.json()["titulo"] == "Aula sem título"


def test_enviar_aula_rejeita_extensao_invalida(client, storage_temporario):
    resposta = client.post("/api/aulas", files=_audio_fake("notas.txt"))
    assert resposta.status_code == 400
    assert "não suportado" in resposta.json()["detail"].lower()


def test_enviar_aula_rejeita_arquivo_grande_demais(client, storage_temporario, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    grande = {"audio": ("aula.mp3", io.BytesIO(b"x" * (2 * 1024 * 1024)), "audio/mpeg")}
    resposta = client.post("/api/aulas", files=grande)
    assert resposta.status_code == 400
    assert "limite" in resposta.json()["detail"].lower()
    assert list(storage_temporario.iterdir()) == []


def test_audio_temporario_e_apagado_apos_transcricao(client, whisper_mockado, storage_temporario):
    client.post("/api/aulas", files=_audio_fake())
    assert len(whisper_mockado) == 1
    assert list(storage_temporario.iterdir()) == []


def test_listar_aulas(client, whisper_mockado, storage_temporario):
    client.post("/api/aulas", files=_audio_fake(), data={"titulo": "Primeira"})
    client.post("/api/aulas", files=_audio_fake(), data={"titulo": "Segunda"})
    resposta = client.get("/api/aulas")
    assert resposta.status_code == 200
    titulos = [a["titulo"] for a in resposta.json()]
    assert set(titulos) == {"Primeira", "Segunda"}


def test_detalhar_aula(client, whisper_mockado, storage_temporario):
    post_resp = client.post("/api/aulas", files=_audio_fake(), data={"titulo": "Detalhe"})
    aula_id = post_resp.json()["id"]
    resposta = client.get(f"/api/aulas/{aula_id}")
    assert resposta.status_code == 200
    assert resposta.json()["titulo"] == "Detalhe"
    assert resposta.json()["transcricao"] is not None


def test_detalhar_aula_inexistente_da_404(client):
    resposta = client.get("/api/aulas/999")
    assert resposta.status_code == 404


def test_deletar_aula(client, db, whisper_mockado, storage_temporario):
    post_resp = client.post("/api/aulas", files=_audio_fake(), data={"titulo": "Deletar"})
    aula_id = post_resp.json()["id"]
    assert db.query(Aula).count() == 1

    del_resp = client.delete(f"/api/aulas/{aula_id}")
    assert del_resp.status_code == 204
    assert db.query(Aula).count() == 0


def test_deletar_aula_inexistente_da_404(client):
    assert client.delete("/api/aulas/999").status_code == 404


def test_deletar_aula_remove_cascade(client, db, whisper_mockado, ia_mockada, storage_temporario):
    post_resp = client.post("/api/aulas", files=_audio_fake(), data={"titulo": "Cascade"})
    aula_id = post_resp.json()["id"]
    client.post(f"/api/aulas/{aula_id}/flashcards")

    from app.models import Flashcard
    assert db.query(Flashcard).filter_by(aula_id=aula_id).count() > 0

    client.delete(f"/api/aulas/{aula_id}")
    assert db.query(Flashcard).filter_by(aula_id=aula_id).count() == 0


def test_formas_audio_suportadas(client, whisper_mockado, storage_temporario):
    for ext in ["mp3", "mp4", "wav", "m4a", "ogg", "webm", "flac"]:
        nome = f"aula.{ext}"
        resp = client.post("/api/aulas", files=_audio_fake(nome))
        assert resp.status_code == 201, f"Formato {ext} deveria ser aceito"
