from langchain_ollama import OllamaEmbeddings

from vapor.utils import utils

DEFAULT_OLLAMA_EMBEDDING_MODEL = "embeddinggemma"


def embedding_model_from_env() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=utils.get_env_var(
            "OLLAMA_EMBEDDING_MODEL", DEFAULT_OLLAMA_EMBEDDING_MODEL
        )
    )
