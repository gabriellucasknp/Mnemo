# POC ISOLADA DO WHISPER (Etapa 2).
# Script solto, RODA FORA DA WEB E DO BANCO: recebe o caminho de um áudio de
# teste e imprime a transcrição no terminal. Serve pra provar a peça mais
# incerta sozinha antes de embrulhá-la em FastAPI + Postgres + Docker.
#
# Uso:  python scripts/transcribe_poc.py caminho/do/audio.m4a [--modelo base]
#
# Aprendizados-alvo:
# - "carregar um modelo" = ler os pesos do disco pra memória (demora na 1ª vez);
# - a PRIMEIRA execução baixa o modelo (~140MB pro "base") pra ~/.cache/whisper;
# - trade-off tamanho: tiny (rápido, erra mais) <-> large (lento, erra menos).
import argparse
import time


def main() -> None:
    parser = argparse.ArgumentParser(description="POC: transcreve um áudio com Whisper")
    parser.add_argument("audio", help="caminho do arquivo de áudio")
    parser.add_argument(
        "--modelo",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="tamanho do modelo (padrão: base)",
    )
    args = parser.parse_args()

    import whisper  # import aqui pra que --help responda rápido

    print(f"Carregando modelo '{args.modelo}'... (a 1ª vez baixa o modelo)")
    t0 = time.perf_counter()
    modelo = whisper.load_model(args.modelo)
    print(f"Modelo carregado em {time.perf_counter() - t0:.1f}s")

    print(f"Transcrevendo {args.audio}...")
    t0 = time.perf_counter()
    resultado = modelo.transcribe(args.audio, fp16=False)  # fp16 só ajuda em GPU
    print(f"Transcrito em {time.perf_counter() - t0:.1f}s")

    print(f"\nIdioma detectado: {resultado.get('language')}")
    print("--- TRANSCRIÇÃO ---")
    print(resultado["text"].strip())


if __name__ == "__main__":
    main()
