import pytest

from langchain.messages import AIMessage
from langgraph.graph.state import CompiledStateGraph
from langchain_mcp_adapters.client import MultiServerMCPClient

from vapor.core.clients import Neo4jClient
from vapor.core.models.llm import VaporLLM
from vapor.core.models.embeddings import VaporEmbeddings

from vapor import chat


# NOTE: Not sure the appropriate place to put these yet
class MockCompiledStateGraph(CompiledStateGraph):
    def __init__(self, *, builder=None, schema_to_mapper=None, **kwargs):
        super().__init__(builder=builder, schema_to_mapper=schema_to_mapper, **kwargs)


async def async_iterator_wrapper(sync_list: list):
    """An asynchronous generator that yields items from a synchronous list.
    Useful to wrap streamed results for astream to work in `handle_chat`.
    """
    for item in sync_list:
        yield item


async def test_handle_chat(mocker, mock_embedder: VaporEmbeddings):
    """Tests the inner handling of each user chat request"""
    # Each chat message requires the agent and context -
    # First mock them so they aren't actually required to do
    # anything, then create them to input to the method
    mocker.patch.object(Neo4jClient, "from_env")

    # Mock the agent to ensure we don't create a real agent
    mocker.patch("vapor.chat.create_agent", return_value=MockCompiledStateGraph)
    agent: MockCompiledStateGraph = chat.create_agent(model="foo")

    # Mock the built input to return something from the "user"
    mocker.patch("rich.console.Console.input", return_value="Test In")
    # Mock the agent (CompiledStateGraph) stream method to return some output
    mocker.patch.object(
        MockCompiledStateGraph,
        "astream",
        return_value=async_iterator_wrapper([{"messages": [AIMessage("Test Out")]}]),
    )
    # Run the method
    await chat.handle_chat(agent)


async def test_chat(mocker):
    """Tests the chat entry point with Vapor agent
    NOTE: This tests only the setup and quickly exiting the chat.
    The `handle_chat` method controls the handling of user messages and
    is tested separately to avoid getting stuck in an infinite loop.
    """
    mocker.patch.object(Neo4jClient, "from_env")
    mocker.patch.object(VaporEmbeddings, "from_env")
    mocker.patch.object(VaporLLM, "from_env")
    mocker.patch.object(
        MultiServerMCPClient,
        "get_tools",
        return_value=async_iterator_wrapper(["fake tool"]),
    )
    mocker.patch("vapor.chat.create_agent", return_value=MockCompiledStateGraph)
    mocker.patch("vapor.chat.handle_chat", side_effect=KeyboardInterrupt)
    await chat.chat()
