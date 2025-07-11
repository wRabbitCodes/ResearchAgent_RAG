from chromadb import GetResult, PersistentClient, QueryResult
from chromadb.api.models.Collection import Collection
from chromadb.api.types import EmbeddingFunction
from typing import List, Dict, Callable, Optional, Any, Mapping, Sequence, Union, cast

import numpy as np


class VectorStoreClient:
    def __init__(
        self, path: str, name: str, embedding_function: Optional[Callable[..., Any]] = None
    ):
        self.path = path
        self.name = name
        self.client = PersistentClient(path=path)
        self.embedding_function = embedding_function

        if embedding_function is not None:
            collection = self.client.get_or_create_collection(
                name=name, embedding_function=cast(EmbeddingFunction, embedding_function)
            )
        else:
            collection = self.client.get_or_create_collection(name=name)
        self.collection: Collection = collection

    def add_documents(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
    ) -> None:
        embeddings_np = np.array(embeddings, dtype=np.float32)
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings_np,
            metadatas=cast(List[Mapping[str, Union[str, int, float, bool, None]]], metadatas),
        )

    def query(self, query: str, k: int = 3) -> QueryResult:
        return self.collection.query(query_texts=[query], n_results=k)

    def count(self) -> int:
        return self.collection.count()

    def get_all(self) -> GetResult:
        return self.collection.get()

    def query_by_vector(self, query_vector: List[float], k: int = 3) -> QueryResult:
        # Casted to satisfy mypy
        return self.collection.query(
            query_embeddings=cast(List[Sequence[float]], [query_vector]), n_results=k
        )

    def delete_by_source(self, source_filename: str) -> None:
        """
        Deletes all chunks associated with a specific source file.
        """
        all_data = self.collection.get(include=["metadatas"])
        ids: List[str] = all_data["ids"]
        metadatas: Optional[List[Mapping[str, Union[str, int, float, bool, None]]]] = all_data.get(
            "metadatas"
        )

        ids_to_delete = [
            doc_id
            for doc_id, metadata in zip(ids, metadatas or [])
            if metadata.get("source") == source_filename
        ]
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
