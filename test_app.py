import importlib
import sys

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Build a throwaway config + vault, then mount the app against it."""
    vault = tmp_path / "vault"
    vault.mkdir()

    config = tmp_path / "config.yml"
    config.write_text(
        'llm_provider: "gemini"\n'
        'gemini_api_key: "test-key"\n'
        'gemini_model: "test-model"\n'
        'claude_api_key: "test-key"\n'
        'claude_model: "test-model"\n'
        f'vault_path: "{vault}"\n'
    )

    monkeypatch.chdir(tmp_path)

    import main

    main = importlib.reload(main)

    # Mock the LLM so /start and /ask never hit the network.
    monkeypatch.setattr(main, "call_llm", lambda prompt: "mocked response")

    return TestClient(main.app)


def test_root_serves_index(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "builder" in res.text.lower()


def test_status_returns_projects_list(client):
    res = client.get("/status")
    assert res.status_code == 200
    assert "projects" in res.json()


def test_streak_returns_shape(client):
    res = client.get("/streak")
    assert res.status_code == 200
    body = res.json()
    assert set(body.keys()) == {"current_streak", "total_days", "logged_dates"}
    assert body["current_streak"] == 0
    assert body["total_days"] == 0


def test_backlog_get_and_post(client):
    assert client.get("/backlog").status_code == 200

    res = client.post("/backlog", json={"idea": "ship it"})
    assert res.status_code == 200

    body = client.get("/backlog").json()
    assert "items" in body


def test_project_new_valid(client):
    res = client.post("/project/new", json={"name": "My Cool Project"})
    assert res.status_code == 200
    assert res.json()["name"] == "my-cool-project"


def test_project_new_rejects_traversal(client):
    for bad in ["../../etc", "a/b", "a\\b"]:
        res = client.post("/project/new", json={"name": bad})
        assert res.status_code == 400, f"expected 400 for {bad!r}, got {res.status_code}"


def test_project_new_duplicate(client):
    client.post("/project/new", json={"name": "dup"})
    res = client.post("/project/new", json={"name": "dup"})
    assert res.status_code == 409


def test_start_session_briefing(client):
    res = client.get("/start/anything")
    assert res.status_code == 200
    assert "briefing" in res.json()


def test_ask(client):
    res = client.post("/ask", json={"project": "p", "question": "what did I learn?"})
    assert res.status_code == 200
    assert "answer" in res.json()


def test_end_session_writes(client):
    res = client.post(
        "/end",
        json={
            "project": "demo",
            "worked_on": "stuff",
            "status": "building",
            "learned": "a lesson",
        },
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True
