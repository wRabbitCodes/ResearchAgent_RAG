import tempfile
import shutil
from src.store.vector_store_client import VectorStoreClient


class TestVectorStoreClient:
    temp_dir: str
    client: VectorStoreClient

    def setup_method(self):
        # Create temporary directory for chroma DB
        self.temp_dir = tempfile.mkdtemp()
        self.client = VectorStoreClient(path=self.temp_dir, name="testDocument")

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_add_and_count_documents(self):
        self.client.add_documents(
            ids=["1"],
            documents=["test document"],
            embeddings=[[0.1] * 384],
            metadatas=[{"source": "test.txt"}],
        )
        assert self.client.count() == 1

    def test_query_text(self):
        self.client.add_documents(
            ids=["1"],
            documents=["This is a test document about AI."],
            embeddings=[[0.1] * 384],
            metadatas=[{"source": "test.txt"}],
        )
        result = self.client.query("AI", k=1)
        assert "documents" in result
        assert result["documents"][0][0] == "This is a test document about AI."

    def test_query_by_vector(self):
        self.client.add_documents(
            ids=["1"],
            documents=["Another test document."],
            embeddings=[[0.2] * 384],
            metadatas=[{"source": "test2.txt"}],
        )
        result = self.client.query_by_vector([0.2] * 384, k=1)
        assert "documents" in result
        assert len(result["documents"][0]) == 1

    def test_get_all(self):
        self.client.add_documents(
            ids=["1", "2"],
            documents=["Doc 1", "Doc 2"],
            embeddings=[[0.1] * 384, [0.2] * 384],
            metadatas=[{"source": "a"}, {"source": "b"}],
        )
        result = self.client.get_all()
        assert "documents" in result

    def test_delete_by_source_removes_correct_documents(self):
        self.client.add_documents(
            ids=["1", "2", "3"],
            documents=["doc1", "doc2", "doc3"],
            embeddings=[[0.1] * 3] * 3,
            metadatas=[
                {"source": "a.txt", "chunk": 0},
                {"source": "b.txt", "chunk": 0},
                {"source": "a.txt", "chunk": 1},
            ],
        )

        self.client.delete_by_source("a.txt")

        result = self.client.get_all()
        remaining_sources = [meta["source"] for meta in result["metadatas"]]
        assert all(src != "a.txt" for src in remaining_sources)
        assert any(src == "b.txt" for src in remaining_sources)
