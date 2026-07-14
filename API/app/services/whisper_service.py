import logging

from app.config import settings

logger = logging.getLogger("mnemo.whisper")

_model = None


def _get_model():
    global _model
    if _model is None:
        logger.info("Carregando modelo Whisper: %s", settings.whisper_model)
        import whisper

        _model = whisper.load_model(settings.whisper_model)
        logger.info("Modelo Whisper carregado com sucesso")
    return _model


def transcrever(caminho_audio: str) -> dict:
    logger.info("Transcrevendo: %s", caminho_audio)
    resultado = _get_model().transcribe(caminho_audio, fp16=False)
    segmentos = resultado.get("segments") or []
    duracao = int(segmentos[-1]["end"]) if segmentos else None
    texto = resultado["text"].strip()
    logger.info(
        "Transcrição OK: %d chars, idioma=%s, duração=%ds",
        len(texto),
        resultado.get("language"),
        duracao or 0,
    )
    return {
        "texto": texto,
        "idioma": resultado.get("language"),
        "duracao_segundos": duracao,
    }
