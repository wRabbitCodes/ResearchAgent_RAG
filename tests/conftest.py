"""
Unit Test AAA Pattern. [Arrange]
"""

import logging
import os
import shutil
import tempfile

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture
def dummy_folder():
    """
    Create a temp folder with two text files for testing
    """
    temp_dir = tempfile.mkdtemp()
    file1 = os.path.join(temp_dir, "file1.txt")
    file2 = os.path.join(temp_dir, "file2.md")
    with open(file1, "w", encoding="UTF-8") as f:
        f.write("Hello world " * 200)
    with open(file2, "w", encoding="UTF-8") as f:
        f.write("Test markdown content " * 150)
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def vectorstore():
    """
    Mock the vector store client
    """

    class MockVectorStoreClient:
        """
        The mock store
        """

        def __init__(self):
            self.store = []

        def add_documents(self, ids, documents, embeddings, metadatas):
            for i, document in enumerate(documents):
                self.store.append(
                    {
                        "id": ids[i],
                        "document": document,
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
            logger.info(
                "[MockVectorStore] Deleted %d entries for %s",
                before - after,
                source_filename,
            )

        def count(self):
            return len(self.store)

        def get_all(self):
            return {
                "documents": [item["document"] for item in self.store],
                "metadatas": [item["metadata"] for item in self.store],
                "ids": [item["id"] for item in self.store],
            }

        def query(self, _, k=3):
            return {
                "documents": [[item["document"] for item in self.store[:k]]],
                "metadatas": [[item["metadata"] for item in self.store[:k]]],
            }

        def query_by_vector(self, _, k=3):
            return {
                "documents": [[item["document"] for item in self.store[:k]]],
                "metadatas": [[item["metadata"] for item in self.store[:k]]],
            }

    return MockVectorStoreClient()
