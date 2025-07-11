from src.config.config import Config
from src.llm.llm_client_base import LLMClientBase
from src.store.vector_store_client import VectorStoreClient
from src.llm.llama_cpp_client import LlamaCppClient
from src.llm.ollama_client import OllamaClient
from src.agent.rag_agent import RAGAgent
from src.api.constants import ALLOWED_LLMS
from src.store.memory_buffer import MemoryBuffer

config = Config()
vectorstore = VectorStoreClient(path=config.chroma_db_path, name=config.chromadb_name)
memory = MemoryBuffer(max_turns=5)
llm: LLMClientBase

match config.llm_backend:
    case ALLOWED_LLMS.LLAMA_CPP_BACKEND.value:
        llm = LlamaCppClient(model_path=config.llama_cpp_model_file)
    case ALLOWED_LLMS.OLLAMA_BACKEND.value:
        llm = OllamaClient(model=config.ollama_model_name, base_url=config.ollama_client_url)
    case _:
        pass
rag_agent = RAGAgent(
    vectorstore=vectorstore, llm_client=llm, memory=memory, use_tool=config.use_tool
)
