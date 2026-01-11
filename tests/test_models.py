import os

import pytest
from ollama import ListResponse, ProgressResponse

from vapor.core.models import embeddings, llm, prompts
from vapor.core.utils import utils

from helpers import globals


@pytest.mark.parametrize("in_docker", [True, False])
def test_embeddings_from_env(mocker, in_docker):
    """Tests creation of `VaporEmbeddings` object and properties"""
    # Mock this to get behavior of connecting from host or docker
    mocker.patch.object(utils, "in_docker", return_value=in_docker)
    mocker.patch.dict(
        os.environ, {"OLLAMA_EMBEDDING_MODEL": globals.OLLAMA_EMBEDDING_MODEL}
    )
    mocker.patch.dict(
        embeddings.EMBEDDING_PARAMS,
        {globals.OLLAMA_EMBEDDING_MODEL: {"embedding_size": 10}},
    )
    embedder = embeddings.VaporEmbeddings.from_env()
    assert embedder.model == utils.get_env_var("OLLAMA_EMBEDDING_MODEL")
    assert (
        embedder.embedding_size
        == embeddings.EMBEDDING_PARAMS[embedder.model]["embedding_size"]
    )


@pytest.mark.parametrize(
    "available_models,pull_status",
    [([], "success"), ([], "failure"), ([globals.OLLAMA_EMBEDDING_MODEL], None)],
)
def test_embeddings_pull(
    mocker,
    mock_embedder: embeddings.VaporEmbeddings,
    available_models: list[str],
    pull_status: str | None,
):
    """Tests `embedder.pull()` method to retrieve manifest"""
    list_response = ListResponse(models=[{"model": m} for m in available_models])
    mocker.patch.object(mock_embedder._client, "list", return_value=list_response)

    pull_response = ProgressResponse(status=pull_status)
    mocker.patch.object(mock_embedder._client, "pull", return_value=pull_response)
    spy = mocker.spy(mock_embedder._client, "pull")

    # Failed pull -> raise error
    if not available_models and pull_status == "failure":
        with pytest.raises(RuntimeError):
            mock_embedder.pull()
    else:
        mock_embedder.pull()
        # Model not available -> should call "pull" and "succeed"
        if not available_models:
            assert spy.call_count == 1
        # Otherwise, this should skip the call to "pull"
        else:
            assert spy.call_count == 0


def test_llm_from_env(mocker):
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
