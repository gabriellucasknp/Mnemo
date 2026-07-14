import io

from app.services import aula_service


def test_salvar_audio_extensoes_suportadas(tmp_path, monkeypatch):
    monkeypatch.setattr(aula_service.settings, "storage_dir", str(tmp_path))
    for ext in ["mp3", "mp4", "wav", "m4a", "ogg", "webm", "flac"]:
        arquivo = io.BytesIO(b"fake audio data")
        arquivo.name = f"aula.{ext}"
        caminho = aula_service.salvar_audio(arquivo)
        assert caminho.exists()
        assert caminho.suffix == f".{ext}"
        caminho.unlink()


def test_salvar_audio_rejeita_extensao_invalida(tmp_path, monkeypatch):
    monkeypatch.setattr(aula_service.settings, "storage_dir", str(tmp_path))
    arquivo = io.BytesIO(b"fake data")
    arquivo.name = "documento.pdf"
    try:
        aula_service.salvar_audio(arquivo)
        assert False, "Deveria ter levantado ValueError"
    except ValueError as e:
        assert "não suportado" in str(e).lower()


def test_salvar_audio_limite_de_tamanho(tmp_path, monkeypatch):
    monkeypatch.setattr(aula_service.settings, "storage_dir", str(tmp_path))
    monkeypatch.setattr(aula_service.settings, "max_upload_mb", 1)
    arquivo = io.BytesIO(b"x" * (2 * 1024 * 1024))
    arquivo.name = "grande.mp3"
    try:
        aula_service.salvar_audio(arquivo)
        assert False, "Deveria ter levantado ValueError"
    except ValueError as e:
        assert "limite" in str(e).lower()
    assert list(tmp_path.iterdir()) == []


def test_salvar_audio_nome_unico(tmp_path, monkeypatch):
    monkeypatch.setattr(aula_service.settings, "storage_dir", str(tmp_path))
    caminhos = set()
    for _ in range(5):
        arquivo = io.BytesIO(b"data")
        arquivo.name = "aula.mp3"
        caminho = aula_service.salvar_audio(arquivo)
        caminhos.add(caminho.name)
    assert len(caminhos) == 5
