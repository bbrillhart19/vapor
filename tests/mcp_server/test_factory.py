import os

import pytest
from fastmcp import FastMCP

from vapor.core.dao import driver
from vapor.core.models import embeddings
from vapor.core.models.embeddings import VaporEmbeddings
from vapor.mcp_server import factory

from helpers import globals


@pytest.mark.neo4j
async def test_lifespan(mocker, neo4j_driver):
    """Tests the lifespan context manager initializes and cleans up resources."""
    # Mock environment variables
    mocker.patch.dict(
        os.environ,
        {
            "NEO4J_DOCKER_HOST_NAME": globals.NEO4J_DOCKER_HOST_NAME,
            "NEO4J_BOLT_PORT": globals.NEO4J_BOLT_PORT,
            "NEO4J_USER": globals.NEO4J_USER,
            "NEO4J_PW": globals.NEO4J_PW,
            "NEO4J_DATABASE": globals.NEO4J_DATABASE,
            "OLLAMA_EMBEDDING_MODEL": globals.OLLAMA_EMBEDDING_MODEL,
        },
    )

    # Mock create_driver to return our test driver
    mocker.patch.object(driver, "create_driver", return_value=neo4j_driver)

    # Create a mock embedder
    mock_embedder = mocker.MagicMock(spec=VaporEmbeddings)
    mock_embedder.pull = mocker.MagicMock(return_value=None)

    # Mock embedder initialization
    mocker.patch.object(VaporEmbeddings, "from_env", return_value=mock_embedder)

    # Create a mock MCP instance
    mock_mcp = mocker.MagicMock(spec=FastMCP)

    # Save original values
    original_driver = driver._driver
    original_embedder = embeddings._embedder

    try:
        # Enter lifespan
        async with factory.lifespan(mock_mcp):
            # Verify driver is initialized
            assert driver._driver is neo4j_driver
            # Verify embedder is initialized
            assert embeddings._embedder is mock_embedder
            # Verify pull was called
            mock_embedder.pull.assert_called_once()

        # After exiting, driver should be closed
        # Note: neo4j_driver is a real driver from fixture, so close() was called
    finally:
        # Restore original values
        driver._driver = original_driver
        embeddings._embedder = original_embedder


def test_create_mcp_server(mocker):
    """Tests create_mcp_server creates and configures an MCP server."""
    # Mock FastMCP to avoid actual initialization
    mock_mcp_instance = mocker.MagicMock(spec=FastMCP)
    mocker.patch.object(FastMCP, "__init__", return_value=None)
    mocker.patch.object(FastMCP, "tool", return_value=None)

    # We need to return the mocked instance
    mocker.patch("vapor.mcp_server.factory.FastMCP", return_value=mock_mcp_instance)

    result = factory.create_mcp_server()

    # Verify MCP server was created
    assert result is mock_mcp_instance
