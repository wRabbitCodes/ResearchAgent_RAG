from abc import ABC, abstractmethod


class ToolBase(ABC):
    @abstractmethod
    def run(self, query: str) -> str:
        pass
