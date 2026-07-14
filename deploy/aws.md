# Deploy do Mnemo na AWS

## Arquitetura

```
Local (compose)                  AWS
─────────────────────────────────────────────────────
docker build (imagem)       →   ECR
serviço api                 →   ECS Fargate / App Runner / Lambda
serviço db                  →   RDS Postgres
.env                        →   Secrets Manager
ports: 8000:8000            →   ALB / ALB embutido
```

A imagem `prod` já está pronta: sem reload, usuário não-root, healthcheck em `/health`.

---

## Pré-requisitos

- Conta AWS + AWS CLI configurada (`aws configure`)
- Docker funcionando
- `docker compose -f compose.prod.yml up --build` aprovado local

---

## Opção 1 — ECS Fargate (recomendado para produção)

### Passo 1: ECR

```bash
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1

aws ecr create-repository --repository-name mnemo-api --region $REGION

aws ecr get-login-password --region $REGION \
  | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com

docker build --target prod --platform linux/amd64 -t mnemo-api ./API
docker tag mnemo-api:latest $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/mnemo-api:latest
docker push $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/mnemo-api:latest
```

### Passo 2: RDS

Console → RDS → Create database → PostgreSQL 16:
- Template: Free tier (`db.t4g.micro`)
- DB name: `mnemo`, user: `mnemo`, senha: gerada
- Public access: **No** (subnet privada)
- Security group: 5432 apenas do ECS

Endpoint: `mnemo.xxxxx.us-east-1.rds.amazonaws.com`

```
postgresql+psycopg://mnemo:<senha>@<endpoint>:5432/mnemo
```

### Passo 3: Secrets Manager

```bash
aws secretsmanager create-secret --name mnemo/database-url \
  --secret-string 'postgresql+psycopg://mnemo:<senha>@<endpoint>:5432/mnemo'

aws secretsmanager create-secret --name mnemo/anthropic-api-key \
  --secret-string 'sk-ant-...'
```

### Passo 4: ECS

1. Cluster: `mnemo` (Fargate)
2. Task definition: usar `deploy/ecs-task-definition.json` (trocar `<ACCOUNT>`/`<REGION>`)
   - 2 vCPU / 6 GB RAM (Whisper precisa de folga)
   - Segredos do Secrets Manager
   - Health check em `/health`
   - Logs no CloudWatch
3. Service: 1 task, ALB na porta 8000

### Passo 5: GitHub Actions (CD)

A cada push na `main`: testes → build → scan Trivy → ECR → ECS.

Setup OIDC (uma vez):

```bash
# Provedor OIDC
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com

# Role de deploy
aws iam create-role --role-name mnemo-github-deploy \
  --assume-role-policy-document file://deploy/github-oidc-trust.json

# Permissões: ECR + ECS
aws iam attach-role-policy --role-name mnemo-github-deploy \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser
```

Repo Settings → Secrets: `AWS_ROLE_ARN`
Repo Settings → Variables: `AWS_REGION`, `ECS_CLUSTER`, `ECS_SERVICE`, `ECS_TASK_FAMILY`

---

## Opção 2 — App Runner (mais simples, menos peças)

App Runner: imagem no ECR + auto-deploy, load balancer e HTTPS embutidos.

1. Console → App Runner → Create service
2. Source: ECR → `mnemo-api:latest`
3. Build: não precisa (imagem já construída)
4. Port: 8000
5. Environment variables: mesmos secrets (via ARN do Secrets Manager)
6. Health check: `/health`
7. CPU/Memory: 2 vCPU / 6 GB

Custo estimado: ~US$ 30/mês (sob demanda).

---

## Opção 3 — Lambda (container image, sob demanda)

Para fluxos assíncronos ou custo mínimo.

1. ECR: mesma imagem `prod`
2. Lambda: Create function → Container image → apontar pro ECR
3. Config:
   - Memory: 6144 MB (mínimo pra Whisper)
   - Timeout: 15 min (limite do Lambda)
   - VPC: mesma do RDS
4. ALB: forward `/api/*` pro Lambda via target group
5. Variáveis: Secrets Manager via ARN

**Atenção:** O Lambda cold start com Whisper pode levar 30-60s. Use Provisioned Concurrency se precisar de resposta rápida.

---

## Opção 4 — EC2 (manual, controle total)

Para quem quer SSH e acesso direto.

```bash
# Na EC2 (Amazon Linux 2023 ou Ubuntu):
sudo yum install docker -y
sudo systemctl start docker
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clonar e rodar
git clone <repo>
cd Mnemo
cp API/.env.example API/.env
# Editar .env com os valores do RDS + Secrets Manager
docker compose -f compose.prod.yml up -d
```

---

## Custos (estimativa, us-east-1)

| Serviço | Custo mensal |
|---------|-------------|
| ECS Fargate 2vCPU/6GB 24/7 | ~US$ 70 |
| RDS free tier | ~US$ 0 (1º ano) |
| ALB | ~US$ 16 |
| App Runner (sob demanda) | ~US$ 30 |
| Lambda (sob demanda) | ~US$ 5-20 |
| EC2 t3.large | ~US$ 60 |

**Dica:** Para projetos pessoais, rode sob demanda (desired count 0). Subir leva ~1 min.

---

## Verificação pós-deploy

```bash
# Health check
curl https://<endpoint>/health
# → {"status":"ok","version":"0.1.0","debug":false}

# Health check do banco
curl https://<endpoint>/health/db
# → {"status":"ok","database":"ok"}

# Readiness (Kubernetes/ECS)
curl https://<endpoint>/health/ready
# → {"status":"ready"}
```

---

## Evoluções futuras

- **S3** para áudios (hoje apaga após transcrever)
- **Celery + Redis (ElastiCache/SQS)** para transcrição assíncrona
- **Alembic** para migrações do banco
- **CloudFront** para CDN dos assets estáticos
- **WAF** para proteção contra ataques
