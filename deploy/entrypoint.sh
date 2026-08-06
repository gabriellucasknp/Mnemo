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
API_PID=$!

# O nginx sobe já, sem esperar a API: a plataforma precisa ver a $PORT aberta
# rápido pra considerar o deploy no ar. Enquanto o uvicorn carrega o Whisper,
# o /health responde 502 e o health check segura o tráfego.
nginx -g 'daemon off;' &
NGINX_PID=$!

# Encaminha o sinal de parada pros dois (senão o container leva SIGKILL).
trap 'kill -TERM "$API_PID" "$NGINX_PID" 2>/dev/null; exit 0' TERM INT

# Supervisão: a imagem só serve de pé com os dois processos. Se qualquer um
# morrer, derruba o container pra plataforma reiniciar limpo — em vez de ficar
# no ar servindo 502 pra sempre.
while kill -0 "$API_PID" 2>/dev/null && kill -0 "$NGINX_PID" 2>/dev/null; do
  sleep 5
done

kill -0 "$API_PID" 2>/dev/null || echo "entrypoint: uvicorn saiu; encerrando container" >&2
kill -0 "$NGINX_PID" 2>/dev/null || echo "entrypoint: nginx saiu; encerrando container" >&2

kill -TERM "$API_PID" "$NGINX_PID" 2>/dev/null || true
exit 1
