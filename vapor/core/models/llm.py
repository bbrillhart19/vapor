from __future__ import annotations

from loguru import logger
from langchain_ollama import ChatOllama

from vapor.core.utils import utils


class VaporLLM(ChatOllama):

    @classmethod
    def from_env(cls, **kwargs) -> VaporLLM:
        model = utils.get_env_var("OLLAMA_LLM", None)
        base_url = utils.get_env_var("OLLAMA_CLOUD_HOST", "https://ollama.com")
        api_key = utils.get_env_var("OLLAMA_API_KEY", None)
        client_kwargs = {"headers": {"Authorization": f"Bearer {api_key}"}}

        return cls(
            model=model,
            base_url=base_url,
            client_kwargs=client_kwargs,
            **kwargs,
        )
