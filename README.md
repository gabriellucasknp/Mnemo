# Mnemo

Capta o áudio de uma aula, transcreve com Whisper e gera flashcards de estudo
com IA (Claude). A fala do professor é a fonte de verdade — todo dado carrega
sua origem marcada (`professor` / `ia`) desde o banco até a tela.

Stack: **FastAPI + PostgreSQL + SQLAlchemy + Whisper + Anthropic API + Docker**.
Contexto e decisões: [sdd.md](sdd.md) · [plano de execução.md](plano%20de%20execução.md).

## Rodar (desenvolvimento)

```bash
cp API/.env.example API/.env   # e preencha ANTHROPIC_API_KEY
docker compose up --build
```

- App: <http://localhost:8000> (tela de upload)
- API interativa: <http://localhost:8000/docs>
- Saúde: `/health` (app) e `/health/db` (banco)
- Postgres exposto em `localhost:5432` (user/senha/db: `mnemo`) pra SQL puro.

O código em `API/` está bind-mounted no container: editar → `--reload` aplica.

## Testes

```bash
docker compose exec api pytest          # dentro do container
# ou local: cd API && python -m pytest
```

A suíte (18 testes) roda em ~1 s: usa SQLite em memória e mocks do Whisper e
da Anthropic — nada de rede, custo de API ou espera de transcrição.

## Ensaio de produção (local)

```bash
ANTHROPIC_API_KEY=sk-ant-... docker compose -f compose.prod.yml up --build
```

Sobe a imagem fechada (target `prod` do [Dockerfile](API/Dockerfile)): sem
reload, usuário não-root, healthcheck, banco sem porta exposta.

## Deploy AWS (via GitHub)

A cada push na `main`, o GitHub Actions roda os testes e, se passarem, publica
a imagem no ECR e atualiza o serviço ECS
([.github/workflows/deploy.yml](.github/workflows/deploy.yml)). Todo push/PR
também roda o CI de testes ([ci.yml](.github/workflows/ci.yml)).

Setup inicial (uma vez): [deploy/aws.md](deploy/aws.md) — ECR + RDS + Secrets
Manager + ECS Fargate + role OIDC pro GitHub, com task definition de exemplo
em [deploy/ecs-task-definition.json](deploy/ecs-task-definition.json).

## Estrutura

```
API/
  app/
    main.py          # instância FastAPI + routers
    config.py        # settings via variáveis de ambiente
    database.py      # engine/sessão SQLAlchemy
    models/          # Aula, Transcricao, Flashcard (origem marcada)
    routers/         # health, aulas (API), flashcards (API), páginas (telas)
    services/        # whisper, geração de flashcards (IA), orquestração
    templates/ static/  # telas server-rendered (Jinja2)
  tests/             # suíte com mocks (SQLite in-memory)
  Dockerfile         # targets: dev (reload) e prod (AWS-ready)
compose.yml          # dev: api + postgres
compose.prod.yml     # ensaio local de produção
deploy/              # guia AWS + task definition ECS
```
