from pathlib import Path
from dotenv import load_dotenv
import os

from src.api.constants import ALLOWED_LLMS


class Config:
    _instance = None

    ROOT_DIR = Path(__file__).resolve().parents[2]
    models_dir = os.path.join(ROOT_DIR, "models")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            load_dotenv()
            cls._instance._init()
        return cls._instance

    def _init(self):
        # pylint: disable=attribute-defined-outside-init

        self.ollama_model_name = os.getenv("OLLAMA_MODEL_NAME", "phi3")
        self.llama_cpp_model_file = os.path.join(
            self.models_dir, os.getenv("LLAMA_CPP_MODEL_FILE", "")
        )
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", 8000))
        self.max_memory_turns = int(os.getenv("MAX_MEMORY_TURNS", 5))
        self.llm_backend = os.getenv("LLM_BACKEND", str(ALLOWED_LLMS.OLLAMA_BACKEND.value))
        self.chromadb_name = os.getenv("CHROMADB_NAME", "documents")
        self.ollama_client_url = os.getenv("OLLAMA_CLIENT_URL", "http://ollama:11434")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2-onnx")
        self.max_token = int(os.getenv("MAX_TOKEN", 512))
        self.context_window = int(os.getenv("CONTEXT_WINDOW", 4096))
        self.use_tool = os.getenv("USE_TOOL", "false").lower() == "true"
        self.llama_cpp_gpu_layers = int(os.getenv("LLAMA_CPP_GPU_LAYERS", 0))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", 30))
        self.tooling_threshold = float(os.getenv("TOOLING_THRESHOLD", 0.3))

        # Fixed paths
        self.chroma_db_path = os.path.join(self.ROOT_DIR, "chroma_store")
        self.models_dir = os.path.join(self.ROOT_DIR, "models")
        self.documents_folder = os.path.join(self.ROOT_DIR, "sample_data")
        self.embedder_path = os.path.join(self.ROOT_DIR, "encoders")
        self.max_upload_files = int(os.getenv("MAX_UPLOAD_FILES", 5))
        self.log_dir = os.path.join(self.ROOT_DIR, "logs")
