from unittest.mock import MagicMock, patch
from src.agent.rag_agent import RAGAgent
from src.config.config import Config


class TestRAGAgent:
    def setup_method(self):
        # Mocks
        self.mock_vectorstore = MagicMock()
        self.mock_llm = MagicMock()
        self.mock_memory = MagicMock()
        self.mock_tool = MagicMock()

        # Dummy config for thresholds
        self.config = Config()
        self.config.chromadb_name = "documents"
        self.config.context_window = 4096
        self.config.max_token = 512

        self.mock_tool.run.return_value = "Tool fallback result"
        self.mock_memory.get_context.return_value = "Past conversation..."

        self.mock_vectorstore.query_by_vector.return_value = {
            "documents": [["Unrelated cat document"]],
            "metadatas": [[{"source": "test.txt"}]],
            "distances": [[1.9]],  # very low match score (~0.05)
        }

        self.mock_llm.generate.return_value = "Generated response"

        # Patch EmbeddingGenerator.get_embedding globally to avoid loading real model
        patcher = patch(
            "src.utils.embedding_generator.EmbeddingGenerator.get_embedding",
            return_value=MagicMock(
                flatten=lambda: MagicMock(
                    # example embedding vector length
                    tolist=lambda: [0.1]
                    * 384
                )
            ),
        )
        self.mock_get_embedding = patcher.start()
        self._patcher = patcher

        self.agent = RAGAgent(
            vectorstore=self.mock_vectorstore,
            llm_client=self.mock_llm,
            memory=self.mock_memory,
            use_tool=True,
            tool=self.mock_tool,
        )

    def test_tool_used_when_low_score(self):
        self.mock_vectorstore.query_by_vector.return_value["distances"] = [
            [2.0, 2.0]
        ]  # worst scores
        self.mock_tool.run.return_value = "Tool fallback result"

        response = self.agent.answer_question("What is quantum computing?")

        # Validate that tool was actually called
        self.mock_tool.run.assert_called_once_with("What is quantum computing?")
        # Optional: you can still check if tool output was included
        assert (
            "Tool fallback result" in response["answer"]
            or "Tool fallback result" in self.mock_llm.generate.call_args[1]["prompt"]
        )

    def test_no_tool_when_high_score(self):
        # Update mock to return high similarity
        self.mock_vectorstore.query_by_vector.return_value["distances"] = [[0.1]]
        self.mock_tool.run.reset_mock()

        response = self.agent.answer_question("Tell me about cats")
        assert "Tool fallback result" not in response["answer"] or ""
        self.mock_tool.run.assert_not_called()

    def test_context_truncation_respected(self):
        long_text = "A" * 20000
        self.mock_vectorstore.query_by_vector.return_value["documents"] = [[long_text]]
        self.mock_vectorstore.query_by_vector.return_value["metadatas"] = [[{"source": "doc.md"}]]
        self.mock_vectorstore.query_by_vector.return_value["distances"] = [[0.2]]

        self.agent.answer_question("Trim test")
        prompt = self.mock_llm.generate.call_args[1]["prompt"]

        # Extract just the full_context part that was truncated (between header and Question)
        trimmed = prompt.split("Question:")[0]
        full_context = trimmed.split("prior conversation.")[-1].strip()

        max_chars = (self.config.context_window - self.config.max_token) * 4
        assert len(full_context) <= max_chars

    def test_sources_returned_correctly(self):
        self.mock_vectorstore.query_by_vector.return_value["documents"] = [["Some context"]]
        self.mock_vectorstore.query_by_vector.return_value["metadatas"] = [[{"source": "doc1.md"}]]
        self.mock_vectorstore.query_by_vector.return_value["distances"] = [
            [2.0]
        ]  # low score triggers tool
        self.mock_tool.run.return_value = "Tool fallback result"

        response = self.agent.answer_question("test")

        sources = [meta["source"] for meta in response["sources"]]
        assert set(sources) == {"doc1.md", "Wikipedia"}
