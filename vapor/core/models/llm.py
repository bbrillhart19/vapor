from __future__ import annotations
from langchain_ollama import ChatOllama

from vapor.core.utils import utils


DEFAULT_OLLAMA_LLM = "granite4:micro-h"


class VaporLLM(ChatOllama):
    @classmethod
    def from_env(cls, **kwargs) -> VaporLLM:
        model = utils.get_env_var("OLLAMA_LLM", DEFAULT_OLLAMA_LLM)
        return cls(model=model, **kwargs)
