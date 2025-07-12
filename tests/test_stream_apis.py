from fastapi.testclient import TestClient
from src.api.app import app


def test_websocket_stream(monkeypatch):
    # --- Mock llm.generate to simulate streaming tokens ---
    def mock_generate(prompt, stream_callback=None, **__):
        for token in ["Hello", " ", "world", "!"]:
            stream_callback(token)

    from src.api.dependencies.services import llm

    monkeypatch.setattr(llm, "generate", mock_generate)

    client = TestClient(app)

    with client.websocket_connect("/ws/ask/stream") as websocket:
        websocket.send_json({"prompt": "Hi!"})

        tokens = []
        while True:
            try:
                token = websocket.receive_text()
                tokens.append(token)
            except Exception:
                break

        assert "".join(tokens) == "Hello world!"

