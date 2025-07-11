from abc import ABC, abstractmethod


class LLMClientBase(ABC):
    @abstractmethod
    def generate(self, **kwargs) -> str:
        pass
