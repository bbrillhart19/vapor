from langchain_ollama import OllamaEmbeddings

from vapor.utils import utils

EMBEDDING_PARAMS = {
    "embeddinggemma": {
        "embedding_size": 768,
    }
}
DEFAULT_OLLAMA_EMBEDDING_MODEL = "embeddinggemma"
OLLAMA_EMBEDDING_MODEL = utils.get_env_var(
    "OLLAMA_EMBEDDING_MODEL", DEFAULT_OLLAMA_EMBEDDING_MODEL
)
EMBEDDER = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)
EMBEDDER_PARAMS = EMBEDDING_PARAMS[OLLAMA_EMBEDDING_MODEL]
