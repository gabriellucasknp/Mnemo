# Testes do fluxo de AULAS (Etapas 3+4): upload -> transcrição -> persistência.
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
    # A regra da fonte (SDD §5): origem marcada como fala do professor.
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


def test_enviar_aula_rejeita_arquivo_grande_demais(
    client, storage_temporario, monkeypatch
):
    # Limite baixado pra 1 MB só neste teste; o upload de 2 MB deve ser cortado.
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    grande = {"audio": ("aula.mp3", io.BytesIO(b"x" * (2 * 1024 * 1024)), "audio/mpeg")}

    resposta = client.post("/api/aulas", files=grande)

    assert resposta.status_code == 400
    assert "limite" in resposta.json()["detail"].lower()
    # O arquivo parcial não pode sobrar no storage.
    assert list(storage_temporario.iterdir()) == []


def test_audio_temporario_e_apagado_apos_transcricao(
    client, whisper_mockado, storage_temporario
):
    client.post("/api/aulas", files=_audio_fake())
    # O Whisper foi chamado com um arquivo salvo em storage...
    assert len(whisper_mockado) == 1
    # ...e depois da transcrição o arquivo temporário não existe mais.
    assert list(storage_temporario.iterdir()) == []


def test_listar_aulas(client, whisper_mockado, storage_temporario):
    client.post("/api/aulas", files=_audio_fake(), data={"titulo": "Primeira"})
    client.post("/api/aulas", files=_audio_fake(), data={"titulo": "Segunda"})

    resposta = client.get("/api/aulas")
    assert resposta.status_code == 200
    titulos = [a["titulo"] for a in resposta.json()]
    assert set(titulos) == {"Primeira", "Segunda"}


def test_detalhar_aula_inexistente_da_404(client):
    resposta = client.get("/api/aulas/999")
    assert resposta.status_code == 404
