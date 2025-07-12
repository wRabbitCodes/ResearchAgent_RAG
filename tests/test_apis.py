import os
import shutil
import tempfile
from fastapi.testclient import TestClient
from src.api.app import app
from src.api.dependencies.services import rag_agent
from src.api.dependencies.services import config, vectorstore


client = TestClient(app)


def test_ask_endpoint_success(monkeypatch):
    # Mocking the RAG agent

    def mock_answer_question(_):
        return {"answer": "Mocked answer", "sources": [{"source": "file1.txt"}]}

    monkeypatch.setattr(rag_agent, "answer_question", mock_answer_question)

    response = client.post("/ask", json={"question": "What is Python?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Mocked answer"
    assert "sources" in data


def test_ask_endpoint_validation():
    response = client.post("/ask", json={})
    assert response.status_code == 422  # Unprocessable Entity


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_ingest_endpoint_invalid_path(monkeypatch):

    monkeypatch.setattr(config, "documents_folder", "nonexistent_folder")

    response = client.get("/ingest")
    assert response.status_code == 400
    assert response.json()["status"] == "error"


def test_ingest_endpoint_valid(monkeypatch):

    # Set test path
    monkeypatch.setattr(config, "documents_folder", "tests/test_data")

    # Pretend path exists
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("os.path.isdir", lambda path: True)

    # Pretend DB is empty
    monkeypatch.setattr(vectorstore, "count", lambda: 0)

    # Mock ingestor
    class MockIngestor:
        def __init__(self, _):
            pass

        def ingest(self, _, __=False):
            return None

    monkeypatch.setattr("src.api.routes.ingest.DocumentIngestor", MockIngestor)

    response = client.get("/ingest")
    assert response.status_code == 202


def test_chroma_clear_success(monkeypatch):

    # Setup temp chroma directory with fake files
    temp_dir = tempfile.mkdtemp()
    dummy_file = os.path.join(temp_dir, "dummy.db")
    with open(dummy_file, "w", encoding="UTF-8") as f:
        f.write("test")

    monkeypatch.setattr(config, "chroma_db_path", temp_dir)

    response = client.delete("/chroma/clear")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert os.path.exists(temp_dir)  # Should be re-created

    shutil.rmtree(temp_dir)


def test_chroma_clear_not_found(monkeypatch):
    monkeypatch.setattr(config, "chroma_db_path", "nonexistent/folder/123")

    response = client.delete("/chroma/clear")
    assert response.status_code == 404
    assert "Chroma DB path not found" in response.json()["detail"]
