import pytest
from src.ingestion.document_ingestor import DocumentIngestor


@pytest.mark.usefixtures("vectorstore", "dummy_folder")
class TestDocumentIngestor:
    """
    Unit Test for Document Ingector
    """

    @pytest.fixture(autouse=True)
    def setup(self, vectorstore):
        self.vectorstore = vectorstore
        self.ingestor = DocumentIngestor(
            vectorstore=self.vectorstore,
        )

    def test_read_text_files_from_folder_reads_txt_and_md(self, dummy_folder):
        docs = self.ingestor.read_text_files_from_folder(dummy_folder)
        assert len(docs) == 2
        filenames = [doc[0] for doc in docs]
        assert any("file1.txt" in name for name in filenames)
        assert any("file2.md" in name for name in filenames)

    def test_chunk_text_splits_text_correctly(self):
        text = "word " * 1200  # 1200 words
        chunks = self.ingestor.chunk_text(text, chunk_size=500, overlap=50)

        # Expected: 3 chunks
        assert len(chunks) == 3
        assert all(isinstance(chunk, str) for chunk in chunks)
        assert all(len(chunk.split()) <= 500 for chunk in chunks)

    def test_ingest_adds_chunks_to_vectorstore(self, dummy_folder):
        self.ingestor.ingest(dummy_folder, overwrite_existing=True)

        assert len(self.vectorstore.store) > 0
        first_entry = self.vectorstore.store[0]
        assert "id" in first_entry
        assert "document" in first_entry
        assert "embedding" in first_entry
        assert "metadata" in first_entry

    def test_ingest_skips_existing_chunks(self, dummy_folder):
        # First ingestion should store everything
        self.ingestor.ingest(dummy_folder, overwrite_existing=False)
        first_count = len(self.vectorstore.store)

        # Second ingestion should skip all (since same folder & files)
        self.ingestor.ingest(dummy_folder, overwrite_existing=False)
        second_count = len(self.vectorstore.store)

        assert second_count == first_count, "No new chunks should be added on second run"

    def test_ingest_overwrites_chunks(self, dummy_folder):
        # First ingestion
        self.ingestor.ingest(dummy_folder, overwrite_existing=False)
        original_ids = {entry["id"] for entry in self.vectorstore.store}

        # Second ingestion with overwrite should regenerate UUIDs
        self.ingestor.ingest(dummy_folder, overwrite_existing=True)
        new_ids = {entry["id"] for entry in self.vectorstore.store}

        assert len(new_ids) > 0
        assert not original_ids.intersection(new_ids), "Overwritten chunks should have new IDs"
