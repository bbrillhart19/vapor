import os

import pytest
from fastapi import FastAPI

from vapor.app.factory import create_app, lifespan
from vapor.app import agent

from helpers import globals


def test_create_app():
    """Tests the `create_app` start up process for Vapor application layer."""
    app = create_app()
    assert isinstance(app, FastAPI)
    assert app.title == "Vapor API"


def test_create_app_includes_status_router():
    """Tests that the status router is included in the app."""
    app = create_app()
    # Check that the status routes are registered
    routes = [route.path for route in app.routes]
    assert "/status/health" in routes


def test_create_app_includes_chat_router():
    """Tests that the chat router is included in the app."""
    app = create_app()
    routes = [route.path for route in app.routes]
    assert "/chat" in routes


def test_create_app_has_lifespan():
    """Tests that the app has a lifespan context manager."""
    app = create_app()
    assert app.router.lifespan_context is not None


@pytest.mark.parametrize("in_docker", [True, False])
async def test_lifespan_initializes_agent(mocker, in_docker: bool):
    """Tests that the lifespan initializes the LLM agent."""
    # Mock environment variables
    mocker.patch.dict(
        os.environ,
        {
            "MCP_PORT": globals.MCP_PORT,
            "MCP_DOCKER_HOST_NAME": globals.MCP_DOCKER_HOST_NAME,
            "OLLAMA_CLOUD_HOST": "https://ollama.com",
            "OLLAMA_LLM": globals.OLLAMA_LLM,
            "OLLAMA_API_KEY": "test-key",
        },
    )

    # Mock in_docker to return False (running locally)
    mocker.patch("vapor.app.factory.utils.in_docker", return_value=in_docker)

    # Mock VaporLLM
    mock_llm = mocker.MagicMock()
    mocker.patch("vapor.app.factory.VaporLLM.from_env", return_value=mock_llm)

    # Mock load_prompt
    mocker.patch("vapor.app.factory.load_prompt", return_value="System prompt")

    # Mock MCP client and tools
    mock_mcp_client = mocker.MagicMock()
    mock_mcp_client.get_tools = mocker.AsyncMock(return_value=["tool1", "tool2"])
    mocker.patch(
        "vapor.app.factory.MultiServerMCPClient",
        return_value=mock_mcp_client,
    )

    # Mock create_agent
    mock_agent = mocker.MagicMock()
    mocker.patch("vapor.app.factory.create_agent", return_value=mock_agent)

    # Save original values
    original_agent = agent._agent
    original_client = agent._mcp_client

    try:
        # Create a mock FastAPI app
        mock_app = mocker.MagicMock(spec=FastAPI)

        # Enter lifespan
        async with lifespan(mock_app):
            # Verify agent is initialized
            assert agent._agent is mock_agent
            # Verify MCP client is initialized
            assert agent._mcp_client is mock_mcp_client

        # After exiting, agent should be cleaned up
        assert agent._agent is None
        assert agent._mcp_client is None
    finally:
        # Restore original values
        agent._agent = original_agent
        agent._mcp_client = original_client
