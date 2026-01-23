"""Tests for the chat streaming endpoint."""

import json

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from langchain_core.messages import AIMessageChunk, ToolMessage

from vapor.app import routes, agent


@pytest.fixture
def mock_agent_fixture(mocker):
    """Fixture to mock the agent singleton."""
    mock = mocker.MagicMock()
    original = agent._agent
    agent._agent = mock
    yield mock
    agent._agent = original


async def test_chat_endpoint_streams_content_events(mocker, mock_agent_fixture):
    """Tests that the /chat endpoint returns SSE stream with content events."""

    async def mock_astream(*args, **kwargs):
        # stream_mode="messages" yields (event, metadata) tuples
        yield (AIMessageChunk(content="Hello world!"), {"langgraph_node": "agent"})

    mock_agent_fixture.astream = mock_astream

    app = FastAPI()
    app.include_router(routes.chat_router)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        async with client.stream(
            "POST",
            "/chat",
            json={"message": "test"},
        ) as response:
            events = []
            data_lines = []
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    events.append(line.split(":", 1)[1].strip())
                elif line.startswith("data:"):
                    data_lines.append(json.loads(line.split(":", 1)[1].strip()))

            assert "content" in events
            assert "done" in events
            # Check content was included
            content_data = [d for d in data_lines if "text" in d]
            assert len(content_data) > 0
            assert content_data[0]["text"] == "Hello world!"


async def test_chat_endpoint_streams_tool_call_events(mocker, mock_agent_fixture):
    """Tests that the /chat endpoint streams tool_call events."""

    # Create AIMessageChunk with tool_call_chunks (used with stream_mode="messages")
    chunk = AIMessageChunk(
        content="",
        tool_call_chunks=[
            {"name": "test_tool", "args": '{"arg1": "value1"}', "id": "1", "index": 0}
        ],
    )

    async def mock_astream(*args, **kwargs):
        yield (chunk, {"langgraph_node": "agent"})

    mock_agent_fixture.astream = mock_astream

    app = FastAPI()
    app.include_router(routes.chat_router)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        async with client.stream(
            "POST",
            "/chat",
            json={"message": "test"},
        ) as response:
            events = []
            data_lines = []
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    events.append(line.split(":", 1)[1].strip())
                elif line.startswith("data:"):
                    data_lines.append(json.loads(line.split(":", 1)[1].strip()))

            assert "tool_call" in events
            # Check tool call data
            tool_data = [
                d for d in data_lines if "tool_name" in d and "tool_input" in d
            ]
            assert len(tool_data) > 0
            assert tool_data[0]["tool_name"] == "test_tool"


async def test_chat_endpoint_streams_tool_result_events(mocker, mock_agent_fixture):
    """Tests that the /chat endpoint streams tool_result events."""

    tool_msg = ToolMessage(
        content="Tool result content", name="test_tool", tool_call_id="1"
    )

    async def mock_astream(*args, **kwargs):
        # stream_mode="messages" yields (event, metadata) tuples
        yield (tool_msg, {"langgraph_node": "tools"})

    mock_agent_fixture.astream = mock_astream

    app = FastAPI()
    app.include_router(routes.chat_router)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        async with client.stream(
            "POST",
            "/chat",
            json={"message": "test"},
        ) as response:
            events = []
            data_lines = []
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    events.append(line.split(":", 1)[1].strip())
                elif line.startswith("data:"):
                    data_lines.append(json.loads(line.split(":", 1)[1].strip()))

            assert "tool_result" in events
            # Check tool result data
            result_data = [d for d in data_lines if "result" in d]
            assert len(result_data) > 0
            assert result_data[0]["tool_name"] == "test_tool"
            assert result_data[0]["result"] == "Tool result content"


async def test_chat_endpoint_requires_message():
    """Tests that /chat requires a message field."""
    # Need to mock agent to avoid RuntimeError
    original = agent._agent
    agent._agent = None

    app = FastAPI()
    app.include_router(routes.chat_router)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post("/chat", json={})
            assert response.status_code == 422
    finally:
        agent._agent = original


async def test_chat_endpoint_requires_non_empty_message():
    """Tests that /chat requires a non-empty message."""
    original = agent._agent
    agent._agent = None

    app = FastAPI()
    app.include_router(routes.chat_router)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post("/chat", json={"message": ""})
            assert response.status_code == 422
    finally:
        agent._agent = original
