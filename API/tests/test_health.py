def test_health(client):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "ok"
    assert "version" in corpo


def test_health_db(client):
    resposta = client.get("/health/db")
    assert resposta.status_code == 200
    assert resposta.json()["database"] == "ok"


def test_readiness(client):
    resposta = client.get("/health/ready")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ready"


def test_respostas_incluem_headers_de_seguranca(client):
    resposta = client.get("/health")
    assert resposta.headers["X-Content-Type-Options"] == "nosniff"
    assert resposta.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in resposta.headers["Content-Security-Policy"]
    assert "X-Process-Time-Ms" in resposta.headers
