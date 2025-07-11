from unittest.mock import patch, MagicMock
from src.llm.llama_cpp_client import LlamaCppClient


class TestLlamaCppClient:
    fake_path: str

    def setup_method(self):
        self.fake_path = "models/fake-model.gguf"

    @patch("src.llm.llama_cpp_client.Llama")
    def test_generate_non_streaming_success(self, mock_llama_class):
        mock_llama = MagicMock()
        mock_llama.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "Hello from LlamaCpp!"}}]
        }
        mock_llama_class.return_value = mock_llama

        client = LlamaCppClient(model_path=self.fake_path)
        result = client.generate(prompt="Hi!")

        assert result == "Hello from LlamaCpp!"

    @patch("src.llm.llama_cpp_client.Llama")
    def test_generate_streaming_success(self, mock_llama_class):
        mock_llama = MagicMock()

        def stream_response():
            yield {"choices": [{"delta": {"content": "Hello"}}]}
            yield {"choices": [{"delta": {"content": " world"}}]}
            yield {"choices": [{"delta": {"content": "!"}}]}

        mock_llama.create_chat_completion.return_value = stream_response()
        mock_llama_class.return_value = mock_llama

        client = LlamaCppClient(model_path=self.fake_path)
        tokens = []

        def cb(t):
            tokens.append(t)

        result = client.generate(prompt="Stream this", stream_callback=cb)

        assert result == "Hello world!"
        assert tokens == ["Hello", " world", "!"]

    @patch("src.llm.llama_cpp_client.Llama")
    def test_generate_error_handling(self, mock_llama_class):
        def raise_exception(prompt, max_tokens, temperature, stream, callback=None):
            raise Exception("simulated error")  # pylint: disable=broad-exception-raised

        mock_llama_instance = MagicMock()
        mock_llama_instance.__call__ = raise_exception
        mock_llama_class.return_value = mock_llama_instance

        client = LlamaCppClient(model_path=self.fake_path)
        result = client.generate(prompt="trigger error")

        assert result.startswith("Error: Failed")
