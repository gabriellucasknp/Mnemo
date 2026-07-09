# Testes das TELAS (Etapa 6): upload pela página e visualização da aula.
import io


def _audio_fake(nome: str = "aula.mp3"):
    return {"audio": (nome, io.BytesIO(b"fake"), "audio/mpeg")}


def test_pagina_inicial_renderiza(client):
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]


def test_enviar_pela_tela_redireciona_para_aula(
    client, whisper_mockado, ia_mockada, storage_temporario
):
    resposta = client.post(
        "/enviar", files=_audio_fake(), data={"titulo": "Bio"}, follow_redirects=False
    )
    assert resposta.status_code == 303
    assert resposta.headers["location"].startswith("/aulas/")

    pagina = client.get(resposta.headers["location"])
    assert pagina.status_code == 200
    assert "Bio" in pagina.text


def test_enviar_arquivo_invalido_volta_com_erro_escapado(client, storage_temporario):
    resposta = client.post(
        "/enviar", files=_audio_fake("slide.pdf"), follow_redirects=False
    )
    assert resposta.status_code == 303
    destino = resposta.headers["location"]
    assert destino.startswith("/?erro=")
    # A mensagem tem acento/dois-pontos -> precisa estar percent-encoded na URL.
    assert " " not in destino


def test_falha_na_ia_nao_perde_a_transcricao(
    client, whisper_mockado, storage_temporario, monkeypatch
):
    from app.services import aula_service

    def ia_quebrada(texto):
        raise RuntimeError("API fora do ar")

    monkeypatch.setattr(aula_service.flashcard_service, "gerar_flashcards", ia_quebrada)

    resposta = client.post("/enviar", files=_audio_fake(), follow_redirects=False)
    # Mesmo com a IA fora, a aula foi salva e a tela abre (regra: a transcrição
    # é a fonte de verdade e nunca se perde).
    assert resposta.status_code == 303
    pagina = client.get(resposta.headers["location"])
    assert pagina.status_code == 200


def test_pagina_de_aula_inexistente_da_404(client):
    assert client.get("/aulas/999").status_code == 404
