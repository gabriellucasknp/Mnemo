import io
from unittest.mock import MagicMock

from app.services import aula_service


def _fake_upload(nome: str, data: bytes = b"fake audio data"):
    arquivo = MagicMock()
    arquivo.filename = nome
    arquivo.file = io.BytesIO(data)
    arquivo.content_type = "audio/mpeg"
    return arquivo


def test_salvar_audio_extensoes_suportadas(tmp_path, monkeypatch):
    monkeypatch.setattr(aula_service.settings, "storage_dir", str(tmp_path))
    for ext in ["mp3", "mp4", "wav", "m4a", "ogg", "webm", "flac"]:
        upload = _fake_upload(f"aula.{ext}")
        caminho = aula_service.salvar_audio(upload)
        assert caminho.exists()
        assert caminho.suffix == f".{ext}"
        caminho.unlink()


def test_salvar_audio_rejeita_extensao_invalida(tmp_path, monkeypatch):
    monkeypatch.setattr(aula_service.settings, "storage_dir", str(tmp_path))
    upload = _fake_upload("documento.pdf")
    try:
        aula_service.salvar_audio(upload)
        assert False, "Deveria ter levantado ValueError"
    except ValueError as e:
        assert "não suportado" in str(e).lower()


def test_salvar_audio_limite_de_tamanho(tmp_path, monkeypatch):
    monkeypatch.setattr(aula_service.settings, "storage_dir", str(tmp_path))
    monkeypatch.setattr(aula_service.settings, "max_upload_mb", 1)
    upload = _fake_upload("grande.mp3", b"x" * (2 * 1024 * 1024))
    try:
        aula_service.salvar_audio(upload)
        assert False, "Deveria ter levantado ValueError"
    except ValueError as e:
        assert "limite" in str(e).lower()
    assert list(tmp_path.iterdir()) == []


def test_salvar_audio_nome_unico(tmp_path, monkeypatch):
    monkeypatch.setattr(aula_service.settings, "storage_dir", str(tmp_path))
    caminhos = set()
    for _ in range(5):
        upload = _fake_upload("aula.mp3")
        caminho = aula_service.salvar_audio(upload)
        caminhos.add(caminho.name)
    assert len(caminhos) == 5
