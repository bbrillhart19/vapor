import pytest

from langchain.messages import AIMessage
from langgraph.graph.state import CompiledStateGraph

from vapor.clients import Neo4jClient
from vapor.models.llm import VaporLLM
from vapor._types import VaporContext

from vapor import chat


# NOTE: Not sure the appropriate place to put this yet
class MockCompiledStateGraph(CompiledStateGraph):
    def __init__(self, *, builder=None, schema_to_mapper=None, **kwargs):
        super().__init__(builder=builder, schema_to_mapper=schema_to_mapper, **kwargs)


def test_handle_chat(mocker):
    """Tests the inner handling of each user chat request"""
    # Each chat message requires the agent and context -
    # First mock them so they aren't actually required to do
    # anything, then create them to input to the method
    mocker.patch.object(Neo4jClient, "from_env")
    context = VaporContext(neo4j_client=Neo4jClient.from_env())

    # Mock the agent to ensure we don't create a real agent
    mocker.patch("vapor.chat.create_agent", return_value=MockCompiledStateGraph)
    agent = chat.create_agent(model="foo")

    # Mock the built input to return something from the "user"
    mocker.patch("builtins.input", return_value="Test In")
    # Mock the agent (CompiledStateGraph) stream method to return some output
    mocker.patch.object(
        MockCompiledStateGraph,
        "stream",
        return_value=[{"messages": [AIMessage("Test Out")]}],
    )
    # Run the method
    chat.handle_chat(agent, context)


def test_chat(mocker):
    """Tests the chat entry point with Vapor agent
    NOTE: This tests only the setup and quickly exiting the chat.
    The `handle_chat` method controls the handling of user messages and
    is tested separately to avoid getting stuck in an infinite loop.
    """
    mocker.patch.object(Neo4jClient, "from_env")
    mocker.patch.object(VaporLLM, "from_env")
    mocker.patch("vapor.chat.create_agent", return_value=MockCompiledStateGraph)
    mocker.patch("vapor.chat.handle_chat", side_effect=KeyboardInterrupt)
    chat.chat()
