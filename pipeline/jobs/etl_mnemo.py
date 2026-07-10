# ============================================================
# Pipeline de dados do Mnemo (PySpark) — arquitetura medallion.
#
#   BRONZE  cópia crua das tabelas do Postgres, particionada por data
#           de ingestão (histórico barato: dá pra reprocessar qualquer dia).
#   SILVER  dados limpos e padronizados: texto aparado, matéria normalizada,
#           duplicatas removidas, colunas derivadas (nº de palavras...).
#   GOLD    tabelas analíticas prontas pra consumo (BI/estudo), gravadas
#           no data lake (Parquet) E de volta no Postgres, schema "analytics".
#
# Rodar:  docker compose --profile pipeline run --rm pipeline
# ============================================================
import os
from datetime import date
from urllib.parse import urlparse

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


# ---------------------------------------------------------------- config ----
def _config_jdbc() -> tuple[str, dict]:
    """Converte a DATABASE_URL da API (SQLAlchemy) pra URL JDBC + credenciais."""
    url = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://mnemo:mnemo@db:5432/mnemo"
    )
    partes = urlparse(url)
    jdbc_url = f"jdbc:postgresql://{partes.hostname}:{partes.port or 5432}{partes.path}"
    props = {
        "user": partes.username or "mnemo",
        "password": partes.password or "",
        "driver": "org.postgresql.Driver",
    }
    return jdbc_url, props


LAKE = os.environ.get("DATALAKE_DIR", "/data/lake")
JDBC_URL, JDBC_PROPS = _config_jdbc()
DATA_INGESTAO = date.today().isoformat()


def criar_spark() -> SparkSession:
    return (
        SparkSession.builder.appName("mnemo-etl")
        .master("local[*]")
        .config("spark.jars", os.environ.get("POSTGRES_JDBC_JAR", ""))
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


# --------------------------------------------------------------- bronze ----
def extrair_bronze(spark: SparkSession) -> dict[str, DataFrame]:
    """Lê as tabelas operacionais do Postgres e grava o snapshot cru no lake."""
    tabelas = {}
    for nome in ("aulas", "transcricoes", "flashcards"):
        df = spark.read.jdbc(JDBC_URL, nome, properties=JDBC_PROPS)
        (
            df.withColumn("data_ingestao", F.lit(DATA_INGESTAO))
            .write.mode("overwrite")
            .partitionBy("data_ingestao")
            .parquet(f"{LAKE}/bronze/{nome}")
        )
        tabelas[nome] = df
        print(f"[bronze] {nome}: {df.count()} linhas")
    return tabelas


# --------------------------------------------------------------- silver ----
def transformar_silver(bronze: dict[str, DataFrame]) -> dict[str, DataFrame]:
    """Limpa e padroniza: é a versão do dado em que dá pra confiar."""
    aulas = (
        bronze["aulas"]
        .withColumn("titulo", F.trim("titulo"))
        # Matéria vem da IA — normaliza capitalização ("biologia" == "Biologia").
        .withColumn("materia", F.initcap(F.trim("materia")))
        .dropDuplicates(["id"])
    )

    transcricoes = (
        bronze["transcricoes"]
        .withColumn("texto", F.trim("texto"))
        .filter(F.length("texto") > 0)  # transcrição vazia não alimenta métrica
        .withColumn("num_palavras", F.size(F.split("texto", r"\s+")))
        .dropDuplicates(["id"])
    )

    flashcards = (
        bronze["flashcards"]
        .withColumn("pergunta", F.trim("pergunta"))
        .withColumn("resposta", F.trim("resposta"))
        # Mesma pergunta gerada 2x pra mesma aula = duplicata (IA re-executada).
        .dropDuplicates(["aula_id", "pergunta"])
    )

    for nome, df in {
        "aulas": aulas, "transcricoes": transcricoes, "flashcards": flashcards
    }.items():
        df.write.mode("overwrite").parquet(f"{LAKE}/silver/{nome}")
        print(f"[silver] {nome}: {df.count()} linhas")

    return {"aulas": aulas, "transcricoes": transcricoes, "flashcards": flashcards}


# ----------------------------------------------------------------- gold ----
def agregar_gold(silver: dict[str, DataFrame]) -> dict[str, DataFrame]:
    """Métricas prontas pra consumo — o 'produto de dados' do pipeline."""
    aulas, transcricoes, flashcards = (
        silver["aulas"], silver["transcricoes"], silver["flashcards"]
    )

    cards_por_aula = flashcards.groupBy("aula_id").agg(
        F.count("*").alias("total_flashcards")
    )

    # Métricas POR AULA: tamanho da transcrição, nº de cartões, densidade
    # (cartões por minuto de aula — proxy de quão "denso" foi o conteúdo).
    metricas_aulas = (
        aulas.alias("a")
        .join(
            transcricoes.select("aula_id", "idioma", "num_palavras").alias("t"),
            F.col("a.id") == F.col("t.aula_id"),
            "left",
        )
        .join(cards_por_aula.alias("c"), F.col("a.id") == F.col("c.aula_id"), "left")
        .select(
            F.col("a.id").alias("aula_id"),
            "a.titulo",
            "a.materia",
            "a.duracao_segundos",
            "a.criada_em",
            "t.idioma",
            "t.num_palavras",
            F.coalesce("c.total_flashcards", F.lit(0)).alias("total_flashcards"),
            F.when(
                F.col("a.duracao_segundos") > 0,
                F.round(
                    F.coalesce("c.total_flashcards", F.lit(0))
                    / (F.col("a.duracao_segundos") / 60.0),
                    2,
                ),
            ).alias("flashcards_por_minuto"),
        )
    )

    # Visão POR MATÉRIA: onde o estudo está concentrado.
    resumo_materias = (
        metricas_aulas.groupBy("materia")
        .agg(
            F.count("*").alias("total_aulas"),
            F.sum("total_flashcards").alias("total_flashcards"),
            F.sum("duracao_segundos").alias("duracao_total_segundos"),
            F.round(F.avg("total_flashcards"), 2).alias("media_flashcards_por_aula"),
        )
        .orderBy(F.desc("total_flashcards"))
    )

    # Distribuição por CATEGORIA de cartão (conceito/definição/processo/exemplo).
    distribuicao_categorias = (
        flashcards.groupBy("categoria")
        .agg(F.count("*").alias("total"))
        .orderBy(F.desc("total"))
    )

    return {
        "metricas_aulas": metricas_aulas,
        "resumo_materias": resumo_materias,
        "distribuicao_categorias": distribuicao_categorias,
    }


def carregar_gold(spark: SparkSession, gold: dict[str, DataFrame]) -> None:
    """Grava a camada gold no lake (Parquet) e no Postgres (schema analytics)."""
    # Schema separado: as tabelas analíticas não se misturam com as operacionais
    # da API — quem consome BI enxerga só "analytics.*".
    conexao = spark._jvm.java.sql.DriverManager.getConnection(
        JDBC_URL, JDBC_PROPS["user"], JDBC_PROPS["password"]
    )
    try:
        conexao.createStatement().execute("CREATE SCHEMA IF NOT EXISTS analytics")
    finally:
        conexao.close()

    for nome, df in gold.items():
        df = df.withColumn("gerado_em", F.current_timestamp())
        df.write.mode("overwrite").parquet(f"{LAKE}/gold/{nome}")
        df.write.jdbc(
            JDBC_URL, f"analytics.{nome}", mode="overwrite", properties=JDBC_PROPS
        )
        print(f"[gold] analytics.{nome}: {df.count()} linhas")


# ----------------------------------------------------------------- main ----
def main() -> None:
    spark = criar_spark()
    try:
        bronze = extrair_bronze(spark)
        silver = transformar_silver(bronze)
        gold = agregar_gold(silver)
        carregar_gold(spark, gold)
        print("Pipeline concluído: bronze -> silver -> gold OK.")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
