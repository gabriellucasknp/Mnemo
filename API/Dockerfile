FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip "setuptools<71" wheel

COPY requirements.txt .
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-build-isolation -r requirements.txt

ARG WHISPER_MODEL=base
ENV XDG_CACHE_HOME=/opt/cache
RUN python -c "import whisper; whisper.load_model('${WHISPER_MODEL}')" \
    && chmod -R a+rX /opt/cache

COPY . .

# ----------------------------------------------------------------- dev ----
FROM base AS dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------------------------------------------------------------- prod ----
FROM base AS prod

RUN useradd --create-home --uid 1000 mnemo \
    && mkdir -p /app/storage \
    && chown -R mnemo:mnemo /app/storage
USER mnemo

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
