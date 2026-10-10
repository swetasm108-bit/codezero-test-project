from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_missing_key_rejected():
    assert client.get("/protected").status_code in (401, 429)


def test_valid_key_accepted():
    r = client.get("/protected", headers={"X-API-Key": "dev-key"})
    assert r.status_code in (200, 429)