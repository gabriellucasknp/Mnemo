<div align="center">

# 🎓 Mnemo

**Grave a aula. Ganhe a transcrição. Estude com flashcards.**

Capta o áudio de uma aula, transcreve com Whisper e gera flashcards de estudo com IA.
A fala do professor é a fonte de verdade — todo dado carrega sua origem marcada
(`professor` / `ia`) desde o banco até a tela.


![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![PySpark](https://img.shields.io/badge/PySpark-E25A1C?logo=apachespark&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)

</div>

---

## 🧭 Como funciona

```
🎙️ áudio da aula ──▶ Whisper (transcrição) ──▶ IA (flashcards) ──▶ 🃏 deck de estudo
                              │                                          │
                              ▼                                          ▼
                         PostgreSQL ◀────── PySpark (medallion) ──▶ analytics
```

**Stack:** FastAPI · PostgreSQL · SQLAlchemy · Whisper · Google Gemini · PySpark · Docker · GitHub Actions

Contexto e decisões: [sdd.md](sdd.md) · [plano de execução.md](plano%20de%20execução.md)

## 🚀 Rodar (desenvolvimento)

```bash
cp API/.env.example API/.env   # e preencha GEMINI_API_KEY
docker compose up --build
```

| Onde | O quê |
|---|---|
| <http://localhost:8000> | Tela de upload |
| <http://localhost:8000/docs> | API interativa (Swagger) |
| `/health` · `/health/db` | Saúde do app e do banco |
| `localhost:5432` | Postgres exposto (user/senha/db: `mnemo`) pra SQL puro |

O código em `API/` está bind-mounted no container: editar → `--reload` aplica.

## ✅ Testes

```bash
docker compose exec api pytest          # dentro do container
# ou local: cd API && python -m pytest
```

A suíte (20 testes) roda em ~1 s: usa SQLite em memória e mocks do Whisper e
da Anthropic — nada de rede, custo de API ou espera de transcrição.

## 📊 Pipeline de dados (PySpark)

```bash
docker compose --profile pipeline run --rm pipeline
```

ETL em arquitetura **medallion** ([pipeline/jobs/etl_mnemo.py](pipeline/jobs/etl_mnemo.py)):

| Camada | O que acontece |
|---|---|
| 🥉 **Bronze** | Snapshot cru das tabelas do Postgres, em Parquet particionado por data de ingestão (volume `mnemo_datalake`) |
| 🥈 **Silver** | Dados limpos: texto aparado, matéria normalizada, duplicatas removidas, colunas derivadas (nº de palavras) |
| 🥇 **Gold** | Métricas prontas pra consumo, gravadas no lake **e** de volta no Postgres (schema `analytics`): `metricas_aulas`, `resumo_materias`, `distribuicao_categorias` |

Consulta rápida depois de rodar:

```sql
SELECT * FROM analytics.resumo_materias;
```


