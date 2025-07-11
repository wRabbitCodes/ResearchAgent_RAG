from typing import List, Tuple


class MemoryBuffer:
    def __init__(self, max_turns: int = 5):
        self.buffer: List[Tuple[str, str]] = []
        self.max_turns = max_turns

    def add_turn(self, question: str, answer: str):
        self.buffer.append((question, answer))
        if len(self.buffer) > self.max_turns:
            self.buffer.pop(0)

    def get_context(self) -> str:
        if not self.buffer:
            return ""
        return "\n\n".join([f"User: {q}\nAssistant: {a}" for q, a in self.buffer])
