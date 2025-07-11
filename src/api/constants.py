from enum import StrEnum, auto


class ALLOWED_LLMS(StrEnum):
    def _generate_next_value_(name, start, count, last_values):
        return name  # Use the name itself as the value

    LLAMA_CPP_BACKEND = auto()
    OLLAMA_BACKEND = auto()


class ALLOWED_EXTENSIONS(StrEnum):
    def _generate_next_value_(name, start, count, last_values):
        return name  # Use the name itself as the value

    md = auto()
    markdown = auto()
    txt = auto()
