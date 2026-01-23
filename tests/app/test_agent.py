"""Tests for the agent singleton module."""

import pytest

from vapor.app import agent


def test_get_agent_raises_when_not_initialized():
    """Tests get_agent raises RuntimeError when agent is None."""
    original = agent._agent
    try:
        agent._agent = None
        with pytest.raises(RuntimeError, match="Agent not initialized"):
            agent.get_agent()
    finally:
        agent._agent = original


def test_get_agent_returns_agent_when_initialized(mocker):
    """Tests get_agent returns the agent when initialized."""
    original = agent._agent
    try:
        mock_agent = mocker.MagicMock()
        agent._agent = mock_agent
        result = agent.get_agent()
        assert result is mock_agent
    finally:
        agent._agent = original


def test_get_mcp_client_raises_when_not_initialized():
    """Tests get_mcp_client raises RuntimeError when client is None."""
    original = agent._mcp_client
    try:
        agent._mcp_client = None
        with pytest.raises(RuntimeError, match="MCP client not initialized"):
            agent.get_mcp_client()
    finally:
        agent._mcp_client = original


def test_get_mcp_client_returns_client_when_initialized(mocker):
    """Tests get_mcp_client returns the client when initialized."""
    original = agent._mcp_client
    try:
        mock_client = mocker.MagicMock()
        agent._mcp_client = mock_client
        result = agent.get_mcp_client()
        assert result is mock_client
    finally:
        agent._mcp_client = original
