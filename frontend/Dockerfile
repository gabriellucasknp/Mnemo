# Imagem do FRONTEND (Angular + nginx).
# Estágio 1: compila o bundle estático de produção.
# Estágio 2: serve o bundle com nginx e faz proxy das rotas da API pro
#            serviço `api` (hostname resolvido no docker compose / rede).
#
#   rodar: docker compose up --build web
FROM node:22-alpine AS build

WORKDIR /fe

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build -- --configuration production

# -------------------------------------------------------------- nginx ----
# Variante "unprivileged": roda como usuário não-root (uid 101) e escuta na
# 8080 — portas <1024 exigem root. O compose mapeia 80 -> 8080.
FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /fe/dist/frontend/browser /usr/share/nginx/html

EXPOSE 8080

USER nginx

CMD ["nginx", "-g", "daemon off;"]
