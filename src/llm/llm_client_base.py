from abc import ABC, abstractmethod


class LLMClientBase(ABC):
    """
    Base client wrapper
    """

    @abstractmethod
    def generate(self, **kwargs) -> str:
        pass
