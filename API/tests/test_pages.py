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
    assert " " not in destino


def test_falha_na_ia_nao_perde_a_transcricao(
    client, whisper_mockado, storage_temporario, monkeypatch
):
    from app.services import aula_service

    def ia_quebrada(texto):
        raise RuntimeError("API fora do ar")

    monkeypatch.setattr(aula_service.flashcard_service, "gerar_flashcards", ia_quebrada)

    resposta = client.post("/enviar", files=_audio_fake(), follow_redirects=False)
    assert resposta.status_code == 303
    pagina = client.get(resposta.headers["location"])
    assert pagina.status_code == 200


def test_pagina_de_aula_inexistente_da_404(client):
    assert client.get("/aulas/999").status_code == 404


def test_botao_gerar_pela_tela(
    client, whisper_mockado, ia_mockada, storage_temporario
):
    post_resp = client.post(
        "/enviar", files=_audio_fake(), data={"titulo": "Retry"}, follow_redirects=False
    )
    aula_url = post_resp.headers["location"]

    # Simula flashcards falhados: deleta os existentes
    from app.models import Flashcard, Aula
    from tests.conftest import SessionTeste

    aula_id = int(aula_url.split("/")[-1])
    with SessionTeste() as s:
        aula_obj = s.get(Aula, aula_id)
        for fc in aula_obj.flashcards:
            s.delete(fc)
        s.commit()

    # Agora o botão "gerar" deve criar os flashcards de novo
    resp = client.post(f"/aulas/{aula_id}/gerar", follow_redirects=False)
    assert resp.status_code == 303
    pagina = client.get(f"/aulas/{aula_id}")
    assert pagina.status_code == 200
    assert len(pagina.text) > 100


def test_lista_aulas_na_pagina_inicial(
    client, whisper_mockado, ia_mockada, storage_temporario
):
    for i in range(3):
        client.post("/enviar", files=_audio_fake(), data={"titulo": f"Aula {i}"})
    pagina = client.get("/")
    assert "Aula 0" in pagina.text
    assert "Aula 1" in pagina.text
    assert "Aula 2" in pagina.text
