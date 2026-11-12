"""Focused tests for request hardening and provider failure handling."""

import pytest
from fastapi.testclient import TestClient

from app import main
from app.schemas import ChatRequest


client = TestClient(main.app)


def test_chat_request_normalizes_supported_content() -> None:
    request = ChatRequest.model_validate(
        {
            "messages": [
                {"role": "user", "content": "  question  "},
                {"role": "model", "content": "answer"},
            ]
        }
    )

    assert [message.role for message in request.messages] == ["user", "model"]
    assert request.messages[0].content == "question"


@pytest.mark.parametrize(
    "payload",
    [
        {"messages": [{"role": "assistant", "content": "not allowed"}]},
        {"messages": [{"role": "user", "content": " "}]},
        {"messages": [{"role": "user", "content": "x"} for _ in range(21)]},
        {"message": "legacy payload"},
        {"history": [{"role": "user", "content": "legacy payload"}]},
    ],
)
def test_chat_rejects_invalid_or_oversized_payloads(payload: dict) -> None:
    response = client.post("/chat", json=payload)

    assert response.status_code == 422


def test_health_and_readiness_are_distinct(monkeypatch) -> None:
    monkeypatch.setattr(main.settings, "gemini_api_key", "")
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 503


def test_provider_failure_does_not_leak_exception_details(monkeypatch) -> None:
    class FailingModels:
        def generate_content(self, **kwargs):
            del kwargs
            raise RuntimeError("private provider response")

    class FailingClient:
        models = FailingModels()

    monkeypatch.setattr(main, "get_genai_client", lambda: FailingClient())

    response = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "Where is my parcel?"}]},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "The language model could not generate a response."
    )
    assert "private provider response" not in response.text
