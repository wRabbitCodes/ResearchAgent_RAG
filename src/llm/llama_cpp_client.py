import logging
import os
from typing import Any, cast
from llama_cpp import Llama
from src.config.config import Config
from src.llm.llm_client_base import LLMClientBase


class LlamaCppClient(LLMClientBase):
    def __init__(self, model_path: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = Config()
        self.context_window = self.config.context_window
        self.default_max_tokens = self.config.max_token

        self.llm = Llama(
            model_path=model_path,
            n_threads=os.cpu_count(),
            n_gpu_layers=self.config.llama_cpp_gpu_layers,
            n_ctx=self.context_window,
            use_mmap=True,
            use_mlock=True,
        )

    def _calculate_max_tokens(self, prompt: str) -> int:
        try:
            prompt_tokens = len(self.llm.tokenize(prompt.encode("utf-8")))
            max_context_usage = int(self.context_window * 0.95)
            available = max_context_usage - prompt_tokens
            return max(64, min(self.default_max_tokens, available))
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.warning("[LlamaCppClient] Token count estimation failed: %s", e)
            return self.default_max_tokens

    def generate(self, **kwargs) -> str:
        prompt: str = kwargs.get("prompt") or ""
        temperature = kwargs.get("temperature", 0.7)

        max_tokens = self._calculate_max_tokens(prompt)

        messages = []
        if system_prompt := kwargs.get("system_prompt"):
            messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": prompt.strip()})

        messages_cast = cast(Any, messages)

        try:
            if stream_callback := kwargs.get("stream_callback"):
                full_response: list[str] = []
                for chunk in self.llm.create_chat_completion(
                    messages=messages_cast,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                ):
                    # Type guard to ensure chunk is dict again for mypy
                    if not isinstance(chunk, dict):
                        continue
                    choices = chunk.get("choices")
                    if not isinstance(choices, list) or len(choices) == 0:
                        continue
                    first_choice = choices[0]
                    if not isinstance(first_choice, dict):
                        continue
                    delta = first_choice.get("delta")
                    if not isinstance(delta, dict):
                        continue
                    token = delta.get("content", "")
                    if token:
                        full_response.append(token)
                        stream_callback(token)
                return "".join(full_response)
            else:
                result = self.llm.create_chat_completion(
                    messages=messages_cast,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=False,
                )
                if isinstance(result, dict):
                    choices = result.get("choices")  # type: ignore
                    if (
                        isinstance(choices, list)
                        and len(choices) > 0
                        and isinstance(choices[0], dict)
                    ):
                        message = choices[0].get("message")
                        if isinstance(message, dict):
                            content = message.get("content")
                            if isinstance(content, str):
                                return content
                return "Error: Failed to generate response from llama.cpp."
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.error("[LlamaCppClient] Generation error: %s", e, exc_info=True)
            return "Error: Failed to generate response from llama.cpp."
