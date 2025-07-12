import json
import logging

import requests

from src.config.config import Config
from src.llm.llm_client_base import LLMClientBase


class OllamaClient(LLMClientBase):
    """
    Client wrapper for Ollama
    """

    def __init__(self, model: str, base_url: str):
        self.model = model
        self.api_endpoint = f"{base_url.rstrip('/')}/api/generate"
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = Config()

    def generate(self, **kwargs) -> str:
        prompt = kwargs.get("prompt")
        system_prompt = kwargs.get("system_prompt", None)
        stream_callback = kwargs.get("stream_callback", None)
        temperature = kwargs.get("temperature", 0.7)
        full_prompt = f"{system_prompt.strip()}\n\n{prompt}" if system_prompt else prompt

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "temperature": temperature,
            "stream": stream_callback is not None,
            "num_predict": self.config.max_token,
        }

        try:
            if stream_callback:
                full_response = []
                with requests.post(self.api_endpoint, json=payload, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    for line in r.iter_lines():
                        if line:
                            try:
                                data = json.loads(line.decode("utf-8"))
                                token = data.get("response", "")
                                if token:
                                    full_response.append(token)
                                    stream_callback(token)
                            except json.JSONDecodeError:
                                continue  # skip malformed line
                return "".join(full_response)
            else:
                response = requests.post(self.api_endpoint, json=payload, timeout=30)
                response.raise_for_status()
                return response.json().get("response", "").strip()

        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error("[OllamaClient] Generation error: %s", e, exc_info=True)
            return "Error: Failed to generate response from Ollama."
