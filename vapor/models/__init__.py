from . import embeddings

EMBEDDING_MODEL = embeddings.embedding_model_from_env()
EMBEDDING_MODEL_PARAMS = embeddings.EMBEDDING_MODEL_PARAMS[
    embeddings.OLLAMA_EMBEDDING_MODEL
]
