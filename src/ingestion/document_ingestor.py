import logging
import os
import uuid
from typing import List, Tuple

from src.api.constants import ALLOWED_EXTENSIONS
from src.store.vector_store_client import VectorStoreClient
from src.utils.embedding_generator import EmbeddingGenerator


class DocumentIngestor:
    def __init__(self, vectorstore: VectorStoreClient):
        # self.embedder = SentenceTransformer(embedding_model_name)
        self.embedder = EmbeddingGenerator()
        self.vectorstore = vectorstore
        self.allowed_extensions = [v.value for v in ALLOWED_EXTENSIONS]
        self.logger = logging.getLogger(self.__class__.__name__)

    def read_text_files_from_folder(self, folder_path: str) -> List[Tuple[str, str]]:
        documents = []
        for filename in os.listdir(folder_path):
            if any(filename.endswith(ext) for ext in self.allowed_extensions):
                with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as f:
                    text = f.read()
                    documents.append((filename, text))
        return documents

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
        return chunks

    def ingest(self, folder_path: str, overwrite_existing: bool = False):
        docs = self.read_text_files_from_folder(folder_path)
        total_new_chunks = 0
        total_skipped = 0
        total_deleted = 0

        # Get existing metadata from vectorstore
        existing_docs = self.vectorstore.get_all()
        existing_meta = existing_docs.get("metadatas", [])
        if existing_meta is None:
            existing_meta = []
        # Set of (source filename, chunk idx) tuples already in store
        existing_keys = {
            (m["source"], m["chunk"]) for m in existing_meta if "source" in m and "chunk" in m
        }

        # Set of all source filenames in store
        existing_sources = {m["source"] for m in existing_meta if "source" in m}

        for filename, text in docs:
            # If overwrite flag is true and source exists, delete all chunks for that source first
            if overwrite_existing and filename in existing_sources:
                self.vectorstore.delete_by_source(filename)
                total_deleted += 1

                # Remove deleted source chunks from existing_keys so we don't skip them
                existing_keys = {key for key in existing_keys if key[0] != filename}

                self.logger.info("[Ingestor] Existing chunks for %s deleted.", filename)

            chunks = self.chunk_text(text)
            new_chunks = []
            new_embeddings = []
            new_ids = []
            new_metadatas = []

            for i, chunk in enumerate(chunks):
                key = (filename, i)

                # If not overwriting and chunk exists, skip it
                if not overwrite_existing and key in existing_keys:
                    total_skipped += 1
                    continue

                # Otherwise, prepare to add new chunk
                new_chunks.append(chunk)
                new_metadatas.append({"source": filename, "chunk": i})
                new_ids.append(str(uuid.uuid4()))

            if new_chunks:
                new_embeddings = self.embedder.get_embedding(new_chunks).flatten().tolist()
                self.vectorstore.add_documents(
                    ids=new_ids,
                    documents=new_chunks,
                    embeddings=new_embeddings,
                    metadatas=new_metadatas,
                )

                self.logger.info(
                    "[Ingestor] Ingested %d new chunks from %s",
                    len(new_chunks),
                    filename,
                )

                total_new_chunks += len(new_chunks)
            else:
                self.logger.info(
                    "[Ingestor] Skipped all chunks for %s (already ingested)", filename
                )

        self.logger.info(
            "[Ingestor] Ingestion complete: %d added, %d skipped, %d files overwritten.",
            total_new_chunks,
            total_skipped,
            total_deleted,
        )
