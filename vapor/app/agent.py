"""Agent singleton module for the Vapor API.

This module provides module-level singletons for the LLM agent and MCP client,
following the same pattern used in vapor/core/dao/driver.py and
vapor/core/models/embeddings.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langgraph.graph.state import CompiledStateGraph

if TYPE_CHECKING:
    from langchain_mcp_adapters.client import MultiServerMCPClient  # pragma: nocover

# Module-level singletons (set by factory lifespan)
_agent: CompiledStateGraph | None = None
_mcp_client: MultiServerMCPClient | None = None


def get_agent() -> CompiledStateGraph:
    """Get the initialized agent instance.

    Returns:
        CompiledStateGraph: The LLM agent with MCP tools.

    Raises:
        RuntimeError: If agent has not been initialized.
    """
    if _agent is None:
        raise RuntimeError("Agent not initialized")
    return _agent


def get_mcp_client() -> MultiServerMCPClient:
    """Get the MCP client instance.

    Returns:
        MultiServerMCPClient: The MCP client for tool access.

    Raises:
        RuntimeError: If client has not been initialized.
    """
    if _mcp_client is None:
        raise RuntimeError("MCP client not initialized")
    return _mcp_client
