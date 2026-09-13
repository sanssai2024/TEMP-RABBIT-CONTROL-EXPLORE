from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_returns_app_identity() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TEMP_RABBIT" in response.text


def test_healthcheck_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
