import numpy as np
from sentence_transformers import SentenceTransformer
from lightrag.utils import wrap_embedding_func_with_attrs

# Initialize the model globally so it's only loaded once per process
_embedding_model = None

def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model

def get_lightrag_embedding_func():
    """
    Return a properly wrapped embedding function for LightRAG.
    """
    model = _get_embedding_model()

    @wrap_embedding_func_with_attrs(
        embedding_dim=model.get_sentence_embedding_dimension(),
        max_token_size=model.max_seq_length,
    )
    async def hf_embed(texts: list[str]) -> np.ndarray:
        return model.encode(texts)

    return hf_embed
