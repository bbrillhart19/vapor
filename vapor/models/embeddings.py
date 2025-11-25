from __future__ import annotations
from typing import Any

from langchain_ollama import OllamaEmbeddings

from vapor.utils import utils

DEFAULT_OLLAMA_EMBEDDING_MODEL = "embeddinggemma"

EMBEDDING_PARAMS = {
    "embeddinggemma": {
        "embedding_size": 768,
    }
}


class VaporEmbeddings(OllamaEmbeddings):
    """Vapor model integration with `OllamaEmbeddings`

    Has additional properties (such as `embedding_size`)
    and ability to initialize from environment.
    """

    @classmethod
    def from_env(cls, **kwargs) -> VaporEmbeddings:
        model = utils.get_env_var(
            "OLLAMA_EMBEDDING_MODEL", DEFAULT_OLLAMA_EMBEDDING_MODEL
        )
        return cls(model=model, **kwargs)

    def _get_param(self, param: str) -> Any:
        return EMBEDDING_PARAMS[self.model][param]

    @property
    def embedding_size(self) -> int:
        return self._get_param("embedding_size")
