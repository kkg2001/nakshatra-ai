import pytest
from fastapi.testclient import TestClient

from backend.app import main
from backend.app.llm.base import LLMError
from backend.app.llm.mock import MockClient

BODY = {"profile": {"name": "Asha", "dob": "1995-08-14"}, "question": "What are my traits?"}


@pytest.fixture
def client():
    main._hits.clear()
    main.app.dependency_overrides[main.get_client] = lambda: MockClient("As a Leo, you shine.")
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_chat_returns_answer_and_evidence(client):
    r = client.post("/api/chat", json=BODY).json()
    assert r["answer"] and r["chart"]["tropical_sun"]["sign"] == "Leo"
    assert {"sources", "flags", "model", "prompt_version"} <= set(r)


@pytest.mark.parametrize("patch", [{"profile": {"name": "A", "dob": "not-a-date"}},
                                   {"profile": {"name": "A", "dob": "2999-01-01"}},
                                   {"profile": {"name": "A", "dob": "1995-08-14", "tob": "25:99"}},
                                   {"question": ""}, {"persona": "pirate"}])
def test_validation_errors_are_422(client, patch):
    assert client.post("/api/chat", json={**BODY, **patch}).status_code == 422


def test_llm_failure_is_503_with_friendly_message(client):
    class Down(MockClient):
        def generate(self, *a, **k):
            raise LLMError("quota")
    main.app.dependency_overrides[main.get_client] = lambda: Down()
    r = client.post("/api/chat", json=BODY)
    assert r.status_code == 503 and "quota" not in r.text


def test_rate_limit(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "2")
    codes = [client.post("/api/chat", json=BODY).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_chart_endpoint(client):
    r = client.post("/api/chart?persona=vedic", json={"name": "A", "dob": "1990-11-05"})
    assert r.json()["sun"]["sign"] == "Libra"


def test_frontend_served(client):
    assert "Nakshatra" in client.get("/").text
