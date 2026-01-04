from __future__ import annotations
from langchain_ollama import ChatOllama

from vapor.core.utils import utils


DEFAULT_OLLAMA_LLM = "granite4:micro-h"


class VaporLLM(ChatOllama):
    @classmethod
    def from_env(cls, **kwargs) -> VaporLLM:
        model = utils.get_env_var("OLLAMA_LLM", DEFAULT_OLLAMA_LLM)
        api_key = utils.get_env_var("OLLAMA_API_KEY", None)
        base_url = "https://ollama.com"
        return cls(
            model=model,
            base_url=base_url,
            client_kwargs={"headers": {"Authorization": f"Bearer {api_key}"}},
            **kwargs,
        )
