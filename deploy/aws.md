# Deploy do Mnemo na AWS

Mapa mental: o que o compose faz na sua máquina, três serviços da AWS fazem na nuvem.

| Local (compose)            | AWS                                   | Papel                        |
| -------------------------- | ------------------------------------- | ---------------------------- |
| `docker build` (imagem)    | **ECR** (Elastic Container Registry)  | guarda a imagem              |
| serviço `api`              | **ECS Fargate** (ou App Runner)       | roda o container             |
| serviço `db`               | **RDS Postgres**                      | banco gerenciado             |
| `.env`                     | **Secrets Manager** / SSM Parameters  | segredos fora da imagem      |
| `ports: 8000:8000`         | **Application Load Balancer**         | porta de entrada + HTTPS     |

A imagem `prod` (target `prod` do Dockerfile) já está pronta pra isso: sem
`--reload`, usuário não-root, healthcheck em `/health`, modelo Whisper baixado
no build e **sem o `.env` dentro** (ver `API/.dockerignore`).

---

## Passo 0 — Pré-requisitos

- Conta AWS + [AWS CLI](https://docs.aws.amazon.com/cli/) configurada (`aws configure`).
- Região escolhida (ex.: `us-east-1` ou `sa-east-1`). Use a mesma em tudo.
- Ensaio local aprovado: `docker compose -f compose.prod.yml up --build`
  e o fluxo inteiro funcionando em `localhost:8000`.

## Passo 1 — ECR: publicar a imagem

```bash
AWS_ACCOUNT=<seu-account-id>
REGION=us-east-1

aws ecr create-repository --repository-name mnemo-api --region $REGION

# Login do Docker no ECR
aws ecr get-login-password --region $REGION \
  | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com

# Build do alvo de produção. IMPORTANTE (Fargate roda linux/amd64):
docker build --target prod --platform linux/amd64 -t mnemo-api ./API

docker tag mnemo-api:latest $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/mnemo-api:latest
docker push $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/mnemo-api:latest
```

## Passo 2 — RDS: o banco

Console → RDS → *Create database* → PostgreSQL 16:

- Template **Free tier** (`db.t4g.micro`) — projeto pessoal, custo ~zero no 1º ano.
- DB name `mnemo`, usuário `mnemo`, senha forte (gerada).
- **Public access: No.** O banco vive em subnet privada; só a API alcança ele.
- Security group do RDS: liberar a porta **5432 somente para o security group
  do serviço ECS** (não para 0.0.0.0/0 — esse é o erro clássico).

Anote o endpoint (ex.: `mnemo.xxxxx.us-east-1.rds.amazonaws.com`). A URL fica:

```
postgresql+psycopg://mnemo:<senha>@<endpoint>:5432/mnemo
```

## Passo 3 — Secrets Manager: os segredos

```bash
aws secretsmanager create-secret --name mnemo/database-url \
  --secret-string 'postgresql+psycopg://mnemo:<senha>@<endpoint>:5432/mnemo'

aws secretsmanager create-secret --name mnemo/anthropic-api-key \
  --secret-string 'sk-ant-...'
```

Regra de ouro: segredo **nunca** vai em variável de ambiente plana na task
definition, nunca na imagem, nunca no git. Só referência ao secret.

## Passo 4 — ECS Fargate: rodar o container

1. Cluster: ECS → *Create cluster* → Fargate, nome `mnemo`.
2. Task definition: use o modelo [`ecs-task-definition.json`](ecs-task-definition.json)
   (troque `<ACCOUNT>`/`<REGION>`) — pontos que importam:
   - **2 vCPU / 6 GB de RAM**: o Whisper `base` em CPU precisa de folga;
     com menos que isso a transcrição fica lenta ou o container morre por OOM.
   - Segredos vêm do Secrets Manager (bloco `secrets`).
   - A role de execução precisa da policy que permite ler esses 2 secrets.
3. Service: *Create service* → Launch type Fargate → 1 task →
   Application Load Balancer na porta 8000, health check path `/health`.
4. Security groups: ALB aberto pra internet (80/443); ECS aceita 8000 só do
   ALB; RDS aceita 5432 só do ECS.

Alternativa mais simples (menos peças): **App Runner** apontando direto pra
imagem no ECR — ele cria load balancer, HTTPS e autoscaling sozinho. Limite:
menos controle de rede; o RDS precisa de VPC connector.

## Passo 5 — GitHub Actions: deploy contínuo (o caminho escolhido)

O deploy do dia a dia **não** é manual: a cada push na `main`, o workflow
[.github/workflows/deploy.yml](../.github/workflows/deploy.yml) roda os testes,
constrói a imagem `prod`, publica no ECR e força um novo deployment no ECS.
Os passos 1–4 acima são o setup inicial (feito uma vez); o Actions assume dali em diante.

Autenticação por **OIDC** — o GitHub assume uma role na AWS, sem access key
gravada em secret:

```bash
# 1. Provedor OIDC do GitHub na sua conta (uma vez só)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com

# 2. Role que o workflow assume (restrita ao SEU repo, branch main)
aws iam create-role --role-name mnemo-github-deploy \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Federated": "arn:aws:iam::<ACCOUNT>:oidc-provider/token.actions.githubusercontent.com"},
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
        "StringLike": {"token.actions.githubusercontent.com:sub": "repo:<SEU_USUARIO>/<SEU_REPO>:ref:refs/heads/main"}
      }
    }]
  }'

# 3. Permissões mínimas: push no ECR + update no serviço ECS
aws iam attach-role-policy --role-name mnemo-github-deploy \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser
# (para o ECS, crie uma policy inline com ecs:UpdateService, ecs:DescribeServices
#  e iam:PassRole na task execution role)
```

No repositório GitHub (Settings → Secrets and variables → Actions):

| Onde     | Nome            | Valor                                        |
| -------- | --------------- | -------------------------------------------- |
| Secret   | `AWS_ROLE_ARN`  | `arn:aws:iam::<ACCOUNT>:role/mnemo-github-deploy` |
| Variable | `AWS_REGION`    | ex.: `us-east-1`                             |
| Variable | `ECS_CLUSTER`   | `mnemo`                                      |
| Variable | `ECS_SERVICE`   | `mnemo-api`                                  |

## Passo 6 — Verificação pós-deploy

1. `https://<dns-do-alb>/health` → `{"status":"ok"}`
2. `https://<dns-do-alb>/health/db` → `{"status":"ok","database":"ok"}`
   (prova que ECS→RDS e o security group estão certos)
3. Fluxo real: subir um áudio curto pela tela e ver os flashcards.

## Custos (ordem de grandeza, us-east-1)

- Fargate 2 vCPU/6 GB no ar 24/7: ~US$ 70/mês → **rode sob demanda**
  (`desired count 0` quando não estiver usando; subir de novo leva ~1 min).
- RDS free tier: ~0 no 1º ano; depois ~US$ 15/mês.
- ALB: ~US$ 16/mês (App Runner embute isso e sai mais barato em uso baixo).

## Evoluções que o plano já previa (fases futuras)

- **S3** pros áudios (hoje o áudio é apagado após transcrever; com S3 dá pra
  guardar o original) — trocar `storage/` local por upload ao bucket.
- **Celery + Redis (ElastiCache/SQS)** pra transcrição assíncrona — mata o
  timeout do ALB em áudios longos (limite padrão: 60 s de idle; aumente o
  idle timeout do ALB pra ~300 s enquanto o fluxo for síncrono).
- **Migrações com Alembic** no lugar do `create_all` da subida.
