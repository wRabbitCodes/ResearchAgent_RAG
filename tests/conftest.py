import logging
import pytest
import os
import tempfile
import shutil

logger = logging.getLogger(__name__)


@pytest.fixture
def dummy_folder():
    # Create a temp folder with two text files for testing
    temp_dir = tempfile.mkdtemp()
    file1 = os.path.join(temp_dir, "file1.txt")
    file2 = os.path.join(temp_dir, "file2.md")
    with open(file1, "w") as f:
        f.write("Hello world " * 200)
    with open(file2, "w") as f:
        f.write("Test markdown content " * 150)
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def vectorstore():
    class MockVectorStoreClient:
        def __init__(self):
            self.store = []

        def add_documents(self, ids, documents, embeddings, metadatas):
            for i in range(len(documents)):
                self.store.append(
                    {
                        "id": ids[i],
                        "document": documents[i],
                        "embedding": embeddings[i],
                        "metadata": metadatas[i],
                    }
                )

        def get_sources(self):
            return list({entry["metadata"].get("source") for entry in self.store})

        def delete_by_source(self, source_filename: str):
            before = len(self.store)
            self.store = [
                entry for entry in self.store if entry["metadata"].get("source") != source_filename
            ]
            after = len(self.store)
            logger.info(f"[MockVectorStore] Deleted {before - after} entries for {source_filename}")

        def count(self):
            return len(self.store)

        def get_all(self):
            return {
                "documents": [item["document"] for item in self.store],
                # <== this is the key fix
                "metadatas": [item["metadata"] for item in self.store],
                # optionally include ids if needed
                "ids": [item["id"] for item in self.store],
            }

        def query(self, query, k=3):
            return {
                "documents": [[item["document"] for item in self.store[:k]]],
                "metadatas": [[item["metadata"] for item in self.store[:k]]],
            }

        def query_by_vector(self, query_vector, k=3):
            return {
                "documents": [[item["document"] for item in self.store[:k]]],
                "metadatas": [[item["metadata"] for item in self.store[:k]]],
            }

    return MockVectorStoreClient()
