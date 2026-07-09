# Teste do checkpoint da Etapa 1: o corpo está vivo?
# Rode dentro do container:  docker compose exec api pytest


def test_health(client):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_health_db(client):
    resposta = client.get("/health/db")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "database": "ok"}
