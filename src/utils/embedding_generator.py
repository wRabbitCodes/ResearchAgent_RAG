import os
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer
from typing import Any, Union, List
from src.config.config import Config


class EmbeddingGenerator:
    _instance = None
    model_dir: str
    tokenizer: Any
    session: ort.InferenceSession

    def __new__(cls):
        if cls._instance is None:
            config = Config()
            cls._instance = super().__new__(cls)
            cls._instance._init(config)
        return cls._instance

    def _init(self, config: Config):
        # pylint: disable=attribute-defined-outside-init
        self.model_dir = os.path.join(config.embedder_path, config.embedding_model)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir, local_files_only=True)
        self.session = ort.InferenceSession(os.path.join(self.model_dir, "model.onnx"))

    def get_embedding(self, texts: Union[str, List[str]]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]

        # Tokenize input texts with padding and truncation
        encodings = self.tokenizer(texts, padding=True, truncation=True, return_tensors="np")

        # ONNXRuntime requires int64 inputs
        inputs = {k: v.astype(np.int64) for k, v in encodings.items()}

        # Run inference to get token embeddings: shape (batch_size, seq_len, hidden_dim)
        outputs = self.session.run(None, inputs)[0]

        # Mean pooling with attention mask to ignore padding tokens
        # shape (batch, seq_len, 1)
        attention_mask = encodings["attention_mask"][..., None]
        masked_outputs = outputs * attention_mask  # zero-out pad tokens

        # Sum embeddings over seq_len dimension
        sum_embeddings = masked_outputs.sum(axis=1)  # shape (batch, hidden_dim)

        # Sum of attention mask per sample (to normalize)
        mask_sum = attention_mask.sum(axis=1)  # shape (batch, 1)
        mask_sum = np.maximum(mask_sum, 1e-9)  # avoid division by zero

        pooled = sum_embeddings / mask_sum  # shape (batch, hidden_dim)

        # Normalize embeddings to unit length
        norm = np.linalg.norm(pooled, axis=1, keepdims=True)
        norm = np.maximum(norm, 1e-9)  # avoid division by zero

        normalized_embeddings = pooled / norm

        # If single input, return 1D array
        if len(normalized_embeddings) == 1:
            return normalized_embeddings[0]
        return normalized_embeddings
