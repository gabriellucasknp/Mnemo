# Dockerfile multi-target: uma base comum, um alvo "dev" (compose local,
# com --reload) e um alvo "prod" (imagem fechada pra AWS, sem reload,
# usuário não-root e healthcheck).
#
#   dev:  docker compose up            (compose.yml usa target: dev)
#   prod: docker build --target prod -t mnemo-api ./API

# ---------------------------------------------------------------- base ----
FROM python:3.12-slim AS base

# Higiene de runtime Python em container:
#  - sem .pyc no disco, logs saem na hora (sem buffer).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# O Whisper precisa do ffmpeg no sistema pra ler/converter o áudio.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# OTIMIZAÇÃO (corta ~5 GB da imagem): o torch padrão do PyPI traz as
# bibliotecas CUDA/NVIDIA inteiras — inúteis aqui, pois rodamos em CPU
# (fp16=False no whisper_service). Instalar o torch do índice "cpu" ANTES
# do requirements faz o pip pular a versão gigante.
COPY requirements.txt .
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

# Baixa o modelo Whisper no BUILD, não na primeira requisição.
# Sem isso, cada container novo na AWS baixaria ~140 MB ao receber o
# primeiro áudio (e pagaria esse tempo com o usuário esperando).
# XDG_CACHE_HOME fixa o cache num caminho conhecido, legível por qualquer usuário.
ARG WHISPER_MODEL=base
ENV XDG_CACHE_HOME=/opt/cache
RUN python -c "import whisper; whisper.load_model('${WHISPER_MODEL}')" \
    && chmod -R a+rX /opt/cache

COPY . .

# ----------------------------------------------------------------- dev ----
# Compose monta ./API por cima de /app (bind mount), então o --reload pega
# suas edições na hora, sem rebuild.
FROM base AS dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------------------------------------------------------------- prod ----
FROM base AS prod

# Usuário não-root: se alguém explorar a aplicação, não ganha root no container.
RUN useradd --create-home --uid 1000 mnemo \
    && mkdir -p /app/storage \
    && chown -R mnemo:mnemo /app/storage
USER mnemo

# O orquestrador (Docker/ECS) pergunta "está vivo?" direto na rota /health.
# start-period generoso: a subida importa o app e abre o pool do banco.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]

# Sem --reload em produção. 1 worker de propósito: o modelo Whisper vive na
# RAM (~1 GB com "base"); N workers = N cópias do modelo.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
