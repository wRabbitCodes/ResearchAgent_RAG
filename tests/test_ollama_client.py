from unittest.mock import patch, Mock, MagicMock
from src.llm.ollama_client import OllamaClient


class TestOllamaClient:
    def setup_method(self):
        self.client = OllamaClient(model="test-model", base_url="http://localhost:11434")

    @patch("requests.post")
    def test_generate_non_streaming_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Hello, world!"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = self.client.generate(prompt="Hi!")
        assert result == "Hello, world!"
        assert mock_post.called

    @patch("requests.post")
    def test_generate_streaming_success(self, mock_post):
        lines = [
            b'{"response": "Hello", "done": false}',
            b'{"response": " world", "done": false}',
            b'{"response": "!", "done": true}',
        ]
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = lines
        mock_response.__enter__.return_value = mock_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        tokens = []

        def callback(token):
            tokens.append(token)

        result = self.client.generate(prompt="Hi", stream_callback=callback)
        assert result == "Hello world!"
        assert tokens == ["Hello", " world", "!"]

    @patch("requests.post")
    def test_generate_streaming_handles_malformed_json(self, mock_post):
        lines = [
            b'{"response": "Hi", "done": false}',
            b"not a json line",
            b'{"response": "!", "done": true}',
        ]
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = lines
        mock_response.__enter__.return_value = mock_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        tokens = []

        def callback(token):
            tokens.append(token)

        result = self.client.generate(prompt="Test", stream_callback=callback)
        assert result == "Hi!"
        assert tokens == ["Hi", "!"]

    @patch("requests.post", side_effect=Exception("Connection error"))
    def test_generate_handles_request_failure(self, mock_post):
        result = self.client.generate(prompt="Hi")
        assert result.startswith("Error: Failed to generate")
