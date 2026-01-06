from __future__ import annotations
from typing import Any

from loguru import logger
from langchain_ollama import OllamaEmbeddings
from ollama import Client

from vapor.core.utils import utils

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
        if utils.in_docker():
            ollama_hostname = utils.get_env_var(
                "OLLAMA_DOCKER_HOST_NAME", "vapor-ollama"
            )
        else:
            ollama_hostname = "localhost"
        ollama_port = utils.get_env_var("OLLAMA_PORT", "11434")
        base_url = f"http://{ollama_hostname}:{ollama_port}"
        logger.info(f"Initializing embedding model={model} @ {base_url}")
        return cls(model=model, base_url=base_url, **kwargs)

    def _get_param(self, param: str) -> Any:
        return EMBEDDING_PARAMS[self.model][param]

    @property
    def embedding_size(self) -> int:
        return self._get_param("embedding_size")

    def pull(self) -> None:
        assert isinstance(self._client, Client)
        # Get all available models with ollama client
        list_response = self._client.list()
        # Parse ListResponse for model names
        models = [
            m.model.split(":")[0]
            for m in list_response.models
            if isinstance(m.model, str)
        ]
        # Check if model available, if not pull it
        if self.model in models:
            logger.info(f"Embedding model={self.model} found, skipping pull")
        else:
            logger.info(f"Embedding model={self.model} not found, pulling...")
            pull_response = self._client.pull(self.model)
            if pull_response.status == "success":
                logger.success(f"Pulled {self.model} successfully!")
            else:
                raise RuntimeError(
                    f"Unable to pull {self.model}, aborting!"
                    + f"\nPull Response: {pull_response}"
                )
