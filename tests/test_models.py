import os
import pytest

from vapor.core.models import embeddings, llm, prompts
from vapor.core.utils import utils

from helpers import globals


def test_embeddings():
    """Tests creation of `VaporEmbeddings` object and properties"""
    embedder = embeddings.VaporEmbeddings.from_env()
    assert embedder.model == utils.get_env_var("OLLAMA_EMBEDDING_MODEL")
    assert (
        embedder.embedding_size
        == embeddings.EMBEDDING_PARAMS[embedder.model]["embedding_size"]
    )


# TODO: Test pull() method


def test_llm(mocker):
    """Tests creation of `VaporLLM` object"""
    mocker.patch.dict(
        os.environ,
        {"OLLAMA_LLM": globals.OLLAMA_LLM, "OLLAMA_API_KEY": globals.OLLAMA_API_KEY},
    )
    llm_model = llm.VaporLLM.from_env()
    assert llm_model.model == utils.get_env_var("OLLAMA_LLM")


def test_load_prompt():
    """Tests loading prompt from file"""
    # This should raise error since prompt file doesn't exist
    prompt_name = "foo"
    with pytest.raises(FileNotFoundError):
        prompts.load_prompt(prompt_name)
    # This does exist, and should succeed with a loaded prompt
    prompt_name = "chat"
    prompt = prompts.load_prompt(prompt_name)
    assert prompt
