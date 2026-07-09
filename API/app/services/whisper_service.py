# Serviço de TRANSCRIÇÃO com Whisper (Etapa 2 -> Etapa 3).
# Função validada na POC (scripts/transcribe_poc.py), promovida pro app:
# recebe o caminho de um áudio, usa o modelo Whisper e devolve texto + metadados.
#
# Pontos importantes:
# - O modelo é carregado UMA vez (na primeira chamada) e fica em memória.
#   Carregar a cada requisição custaria segundos e RAM à toa.
# - Tamanho do modelo vem da config (WHISPER_MODEL). "base" = escolha do MVP:
#   equilíbrio entre qualidade em PT-BR e velocidade na CPU.
# - fp16=False porque rodamos em CPU (fp16 só ajuda em GPU; em CPU gera warning).
from app.config import settings

_model = None  # cache do modelo carregado (singleton simples)


def _get_model():
    global _model
    if _model is None:
        import whisper  # import tardio: só paga o custo quando realmente transcreve

        _model = whisper.load_model(settings.whisper_model)
    return _model


def transcrever(caminho_audio: str) -> dict:
    """Transcreve um arquivo de áudio e devolve {texto, idioma, duracao_segundos}."""
    resultado = _get_model().transcribe(caminho_audio, fp16=False)
    segmentos = resultado.get("segments") or []
    duracao = int(segmentos[-1]["end"]) if segmentos else None
    return {
        "texto": resultado["text"].strip(),
        "idioma": resultado.get("language"),
        "duracao_segundos": duracao,
    }
