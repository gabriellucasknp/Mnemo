# Imagem do PIPELINE de dados (PySpark).
# Separada da imagem da API: Spark precisa de Java, a API não; a API precisa
# de ffmpeg/torch, o pipeline não. Cada container carrega só o que usa.
#
#   rodar: docker compose --profile pipeline run --rm pipeline
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Spark roda na JVM — o PySpark é só a "casca" Python por cima.
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /pipeline

COPY requirements.txt .
RUN pip install -r requirements.txt

# Driver JDBC do Postgres: é por ele que o Spark lê/escreve no banco.
ARG POSTGRES_JDBC_VERSION=42.7.4
RUN curl -fsSL -o /opt/postgresql-jdbc.jar \
    "https://jdbc.postgresql.org/download/postgresql-${POSTGRES_JDBC_VERSION}.jar"
ENV POSTGRES_JDBC_JAR=/opt/postgresql-jdbc.jar

COPY . .

# Usuário não-root (mesmo princípio da imagem prod da API).
RUN useradd --create-home --uid 1000 spark \
    && mkdir -p /data/lake \
    && chown -R spark:spark /data/lake
USER spark

CMD ["python", "jobs/etl_mnemo.py"]
