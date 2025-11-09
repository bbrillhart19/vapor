from langchain_ollama import OllamaEmbeddings

from vapor.utils import utils

EMBEDDING_MODEL_PARAMS = {
    "embeddinggemma": {
        "embedding_size": 768,
    }
}
DEFAULT_OLLAMA_EMBEDDING_MODEL = "embeddinggemma"
OLLAMA_EMBEDDING_MODEL = utils.get_env_var(
    "OLLAMA_EMBEDDING_MODEL", DEFAULT_OLLAMA_EMBEDDING_MODEL
)


def embedding_model_from_env() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)
