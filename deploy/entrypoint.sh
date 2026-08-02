#!/bin/sh
# Entrypoint de produção: sobe a API (uvicorn) e o nginx juntos.
#
#   PORT          porta exposta do nginx (Render injeta a dela aqui)
#   API_UPSTREAM  endereço da API pra fazer proxy (padrão: local, mesma imagem)
set -e

PORT="${PORT:-80}"
API_UPSTREAM="${API_UPSTREAM:-127.0.0.1:8000}"
export PORT API_UPSTREAM

rm -f /etc/nginx/sites-enabled/default

envsubst '${PORT} ${API_UPSTREAM}' < /etc/nginx/nginx.template > /etc/nginx/conf.d/default.conf

UVICORN_LOG_LEVEL="$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')"

uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 \
  --log-level "${UVICORN_LOG_LEVEL}" &

exec nginx -g 'daemon off;'
