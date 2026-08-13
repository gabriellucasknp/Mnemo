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
| <http://localhost:80> | Frontend Angular (nginx) |
| <http://localhost:8000> | API (Swagger em `/docs`) |
| `/health` · `/health/db` · `/health/ready` | Saúde do app e do banco |
| `localhost:5432` | Postgres exposto (user/senha/db: `mnemo`) pra SQL puro |

O código em `API/` está bind-mounted no container: editar → `--reload` aplica.
O serviço `api` tem healthcheck (`start_period: 20s`); o `web` só sobe depois
que a API estiver saudável.

### Frontend sozinho (hot reload)

```bash
cd frontend
npm install        # ou npm ci
npm start          # http://localhost:4200 (proxy /api -> localhost:8000)
```

O build de produção segue a mesma estratégia de "servir via backend":
o Dockerfile da raiz compila o Angular e o nginx da **mesma imagem** serve o
SPA e faz proxy da API — um único serviço no Render, sem CORS.

## ✅ Testes, lint e build

```bash
# API — só dependências base (nada de torch/whisper: o CI roda exatamente isto)
cd API
python -m venv .venv && .venv\Scripts\activate   # Windows; `source .venv/bin/activate` no Linux
pip install -r requirements-base.txt
python -m pytest tests -q

# Lint + formatação (ruff)
pip install ruff
ruff check app tests scripts
ruff format --check app tests scripts

# Frontend
cd frontend
npm ci
npm run build -- --configuration production   # gera dist/frontend/browser
```

Ou, dentro do container:

```bash
docker compose exec api pytest -q
```

## 🐳 Imagem de produção (unificada)

```bash
docker build -t mnemo .
docker run --rm -p 80:80 -e PORT=80 -e GEMINI_API_KEY=... mnemo
```

O entrypoint (`deploy/entrypoint.sh`) aplica o schema do banco
(`python scripts/init_db.py`), sobe o uvicorn em `127.0.0.1:8000` e o nginx na
`$PORT`, e supervisiona os dois processos.

## 🔑 Variáveis de ambiente

Copie `.env.example` (raiz) ou `API/.env.example` e preencha. Nada de segredo
é versionado — os nomes exatos são estes:

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DATABASE_URL` | ✅ | Connection string do Postgres. O Render injeta a dela via add-on. |
| `GEMINI_API_KEY` | ✅ | Chave do Google AI Studio (gera flashcards). |
| `GEMINI_MODEL` | | Modelo Gemini (padrão `gemini-2.0-flash`). |
| `WHISPER_MODEL` | | Tamanho do Whisper: `tiny` \| `base` \| `small` \| `medium` \| `large`. |
| `MAX_UPLOAD_MB` | | Limite de upload de áudio (padrão `200`). |
| `CORS_ORIGINS` | | Origens permitidas na API: JSON (`["https://app.onrender.com"]`) ou lista separada por vírgula. Padrão `["*"]`. |
| `ADMIN_TOKEN` | ⚠️ reservado | Não usado pelo código hoje; reservado p/ endpoints administrativos. Exigido no workflow de deploy. |
| `DEBUG` | | `true` ativa docs/reload no dev (padrão `false`). |
| `LOG_LEVEL` | | `INFO`/`DEBUG`/etc. |
| `PORT` | | Porta do nginx na imagem unificada (Render injeta a dela). |
| `API_UPSTREAM` | | Endereço da API pro proxy nginx (padrão `127.0.0.1:8000`). |
| `RENDER_SERVICE_ID` / `RENDER_API_KEY` / `RENDER_DEPLOY_HOOK` | | Usadas pelo workflow de deploy (secrets do GitHub, não do app). |

> **CI é leve por design:** o workflow instala só `requirements-base.txt` nos
> testes. Torch/openai-whisper/ffmpeg só entram na imagem de produção
> (`requirements-ml.txt` + `apt-get install ffmpeg` no Dockerfile).

## 🚢 Deploy no Render

1. Conecte o repositório `gabriellucasknp/Mnemo` no Render.
2. "New Blueprint Instance" usando o [render.yaml](render.yaml):
   - cria o Postgres gerenciado e injeta `DATABASE_URL`;
   - cria o serviço web `mnemo` (runtime docker, `healthCheckPath: /health`);
   - pede `GEMINI_API_KEY` (e outros valores com `sync: false`).
3. Configure os secrets no GitHub (Settings → Secrets and variables → Actions):
   `GEMINI_API_KEY`, `DATABASE_URL`, `ADMIN_TOKEN` e `RENDER_DEPLOY_HOOK`
   (ou `RENDER_API_KEY` + `RENDER_SERVICE_ID`).
4. O workflow [deploy-render.yml](.github/workflows/deploy-render.yml) roda em
   push para `main` ou manualmente (`workflow_dispatch`): ele valida os secrets
   e dispara o deploy via hook/API do Render.

Health check do deploy: `GET /health` → `200 {"status":"ok",...}`.

## 🤖 CI/CD (GitHub Actions)

| Job | O que valida |
|---|---|
| `tests` | pytest com **apenas** `requirements-base.txt` (python 3.12, cache pip) |
| `lint` | ruff `check` + `format --check` |
| `frontend` | `npm ci` + build de produção (Node 20) |
| `security-audit` | `pip-audit` em `requirements-base.txt` |
| `Deploy Render` | valida secrets + dispara deploy (push `main`/manual) |

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
