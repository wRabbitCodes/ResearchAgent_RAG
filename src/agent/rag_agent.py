import logging
from typing import Dict
from src.config.config import Config
from src.llm.llm_client_base import LLMClientBase
from src.store.memory_buffer import MemoryBuffer
from src.store.vector_store_client import VectorStoreClient
from src.agent.tools.tool_base import ToolBase
from src.agent.tools.wikipedia_search_tool import WikipediaSearchTool
from src.utils.embedding_generator import EmbeddingGenerator


class RAGAgent:
    def __init__(
        self,
        vectorstore: VectorStoreClient,
        llm_client: LLMClientBase,
        memory: MemoryBuffer,
        use_tool: bool = False,
        tool: ToolBase = WikipediaSearchTool(),
    ):
        self.vectorstore = vectorstore
        self.llm = llm_client
        self.embedding_generator = EmbeddingGenerator()
        # self.embedder = SentenceTransformer(embedding_model_name)
        self.memory = memory
        self.use_tool = use_tool
        self.tool_runner = tool.run

        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)

    def answer_question(self, query: str, top_k: int = 3) -> Dict:
        query_embedding = self.embedding_generator.get_embedding(query).flatten().tolist()
        results = self.vectorstore.query_by_vector(query_embedding, k=top_k)

        # Just to make MyPy feel safe SMH!!!
        safe_first = lambda x: (x[0] if isinstance(x, list) and len(x) > 0 else [])  # noqa: E731

        documents = safe_first(results.get(self.config.chromadb_name))
        metadatas = safe_first(results.get("metadatas"))
        distances = safe_first(results.get("distances"))

        # Compute similarity scores (normalized between 0 and 1)
        scores = [max(0.0, min(1.0, 1.0 - (d / 2))) for d in distances]
        max_score = max(scores) if scores else 0.0

        # Tool fallback if needed
        if self.use_tool and max_score < self.config.tooling_threshold:
            self.logger.info(
                "No highly relevant match (max_score=%.2f < %.2f); using tool fallback.",
                max_score,
                self.config.tooling_threshold,
            )

            documents.append(self.tool_runner(query))
            metadatas.append({"source": "Wikipedia"})

        # Compose full context
        context_chunks = "\n\n".join(f"{i+1}. {doc}" for i, doc in enumerate(documents))
        memory_context = self.memory.get_context()
        full_context = f"{context_chunks}\n\nConversation history:\n{memory_context}"

        # Truncate to model context window
        max_chars = (self.config.context_window - self.config.max_token) * 4
        if len(full_context) > max_chars:
            full_context = full_context[:max_chars]

        prompt = f"""You are a helpful assistant. Answer the question using only the provided context and prior conversation.

    {full_context}

    Question:
    {query}

    Answer:"""

        response = self.llm.generate(prompt=prompt)
        self.memory.add_turn(query, response)

        return {"answer": response, "sources": metadatas}
