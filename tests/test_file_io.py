import os
import tempfile
import shutil
from fastapi.testclient import TestClient
from fastapi import status
from src.api.app import app
from src.api.dependencies.services import config

client = TestClient(app)


def setup_module(module):
    module.original_doc_folder = config.documents_folder
    module.temp_dir = tempfile.mkdtemp()
    config.documents_folder = module.temp_dir
    config.max_upload_files = 2


def teardown_module(module):
    config.documents_folder = module.original_doc_folder
    shutil.rmtree(module.temp_dir)


def test_upload_valid_txt_file():
    files = {"file": ("example.txt", b"Hello, world!", "text/plain")}
    response = client.post("/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["filename"].endswith(".txt")
    saved_path = os.path.join(config.documents_folder, data["filename"])
    assert os.path.exists(saved_path)


def test_upload_invalid_extension():
    files = {"file": ("example.exe", b"bad file", "application/octet-stream")}
    response = client.post("/upload", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "files allowed" in response.json()["detail"]


def test_upload_over_file_limit():
    for i in range(config.max_upload_files):
        with open(
            os.path.join(config.documents_folder, f"dummy{i}.txt"),
            "w",
            encoding="UTF-8",
        ) as f:
            f.write("dummy")

    files = {"file": ("overflow.txt", b"should fail", "text/plain")}
    response = client.post("/upload", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "folder is full" in response.json()["detail"]


def test_clear_uploaded_documents():
    with open(os.path.join(config.documents_folder, "to_delete.txt"), "w", encoding="UTF-8") as f:
        f.write("delete me")

    response = client.delete("/upload/clear")
    assert response.status_code == 200
    assert response.json()["status"] == "cleared"
    assert response.json()["deleted_files"] >= 1
    assert len(os.listdir(config.documents_folder)) == 0
