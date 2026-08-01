# ============================================================
# Imagem de PRODUÇÃO do Mnemo (um único container):
#   · Frontend Angular compilado e servido pelo nginx
#   · API FastAPI (uvicorn) rodando em 127.0.0.1:8000
#   · nginx (na porta $PORT) serve o SPA e faz proxy da API
# ============================================================

# ---- Estágio 1: compila o frontend Angular -------------------
FROM node:22-alpine AS frontend-build

WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build -- --configuration production

# ---- Estágio 2: base da API (Python + deps + Whisper) --------
FROM python:3.12-slim AS api-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl nginx gettext-base \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip "setuptools<71" wheel

COPY API/requirements.txt .
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-build-isolation -r requirements.txt

ARG WHISPER_MODEL=base
ENV XDG_CACHE_HOME=/opt/cache
RUN python -c "import whisper; whisper.load_model('${WHISPER_MODEL}')" \
    && chmod -R a+rX /opt/cache

COPY API/ .

# ---- Estágio 3: unifica SPA + API atrás do nginx -------------
FROM api-base

COPY --from=frontend-build /fe/dist/frontend/browser /srv/web
COPY deploy/nginx.template /etc/nginx/nginx.template
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && mkdir -p /app/storage

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
