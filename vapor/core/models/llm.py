from __future__ import annotations

from loguru import logger
from langchain_ollama import ChatOllama

from vapor.core.utils import utils


class VaporLLM(ChatOllama):

    @classmethod
    def from_env(cls, **kwargs) -> VaporLLM:
        model = utils.get_env_var("OLLAMA_LLM", None)
        if cls._check_cloud(model):
            base_url = utils.get_env_var("OLLAMA_CLOUD_HOST", "https://ollama.com")
            api_key = utils.get_env_var("OLLAMA_API_KEY", None)
            client_kwargs = {"headers": {"Authorization": f"Bearer {api_key}"}}
            logger.info(f"Detected cloud model ({model}) - connecting to {base_url}")
        else:
            base_url = utils.get_env_var("OLLAMA_LOCAL_HOST", "http://ollama:11434")
            client_kwargs = {}
            logger.info(f"Detected local model ({model}) - connecting to {base_url}")

        return cls(
            model=model,
            base_url=base_url,
            client_kwargs=client_kwargs,
            **kwargs,
        )

    @staticmethod
    def _check_cloud(model: str) -> bool:
        return model.endswith(":cloud")

    @property
    def is_cloud(self) -> bool:
        return self._check_cloud(self.model)
