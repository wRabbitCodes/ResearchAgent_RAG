from src.store.memory_buffer import MemoryBuffer


class TestMemoryBuffer:
    buffer = MemoryBuffer

    def setup_method(self):
        self.buffer = MemoryBuffer(max_turns=3)

    def test_add_turn_and_get_context(self):
        self.buffer.add_turn("What is AI?", "AI stands for Artificial Intelligence.")
        self.buffer.add_turn("What is ML?", "ML stands for Machine Learning.")

        context = self.buffer.get_context()
        assert "User: What is AI?" in context
        assert "Assistant: AI stands for Artificial Intelligence." in context
        assert "User: What is ML?" in context

    def test_buffer_trims_old_turns(self):
        self.buffer.add_turn("Q1", "A1")
        self.buffer.add_turn("Q2", "A2")
        self.buffer.add_turn("Q3", "A3")
        self.buffer.add_turn("Q4", "A4")

        context = self.buffer.get_context()
        assert "Q1" not in context
        assert "A1" not in context
        assert "Q2" in context
        assert "A4" in context

    def test_get_context_empty(self):
        empty_buffer = MemoryBuffer()
        assert empty_buffer.get_context() == ""
