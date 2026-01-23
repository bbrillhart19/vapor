"""Tests for the CLI chat client that communicates with the Vapor REST API."""

import json

import httpx
import pytest

from vapor import chat


class MockResponse:
    """Mock HTTP response for streaming."""

    def __init__(self, lines: list[str], status_code: int = 200):
        self.lines = lines
        self.status_code = status_code

    async def aiter_lines(self):
        for line in self.lines:
            yield line


class MockStreamContextManager:
    """Mock context manager for httpx streaming."""

    def __init__(self, response: MockResponse):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


async def test_handle_chat(mocker):
    """Tests the inner handling of each user chat request via API."""
    # Mock console input
    mocker.patch("rich.console.Console.input", return_value="Test question")
    mocker.patch("rich.console.Console.print")

    # Create mock SSE response
    sse_lines = [
        "event: content",
        f"data: {json.dumps({'text': 'Hello '})}",
        "",
        "event: content",
        f"data: {json.dumps({'text': 'World!'})}",
        "",
        "event: done",
        f"data: {json.dumps({'status': 'complete'})}",
    ]
    mock_response = MockResponse(sse_lines)

    # Create mock client
    mock_client = mocker.MagicMock(spec=httpx.AsyncClient)
    mock_client.stream = mocker.MagicMock(
        return_value=MockStreamContextManager(mock_response)
    )

    # Run the method
    await chat.handle_chat(mock_client, "http://localhost:8000")

    # Verify stream was called with correct parameters
    mock_client.stream.assert_called_once_with(
        "POST",
        "http://localhost:8000/chat",
        json={"message": "Test question"},
        timeout=120.0,
    )


async def test_handle_chat_with_tool_calls(mocker):
    """Tests handle_chat displays tool call and result events."""
    # Mock console
    mocker.patch("rich.console.Console.input", return_value="Test question")
    mock_print = mocker.patch("rich.console.Console.print")

    # Create mock SSE response with tool events
    # The result format matches MCP content blocks: [{"type": "text", "text": "..."}]
    sse_lines = [
        "event: tool_call",
        f"data: {json.dumps({'tool_name': 'search', 'tool_input': {}})}",
        "",
        "event: tool_result",
        f"data: {json.dumps({'tool_name': 'search', 'result': [{'type': 'text', 'text': 'Found data'}]})}",
        "",
        "event: content",
        f"data: {json.dumps({'text': 'Answer based on search'})}",
        "",
        "event: done",
        f"data: {json.dumps({'status': 'complete'})}",
    ]
    mock_response = MockResponse(sse_lines)

    mock_client = mocker.MagicMock(spec=httpx.AsyncClient)
    mock_client.stream = mocker.MagicMock(
        return_value=MockStreamContextManager(mock_response)
    )

    await chat.handle_chat(mock_client, "http://localhost:8000")

    # Should have printed tool call panel and tool result panel
    assert mock_print.call_count >= 2


async def test_chat_connects_to_api(mocker):
    """Tests the chat entry point connects to API and handles exit."""
    mocker.patch.dict("os.environ", {"APP_PORT": "8000"})

    # Mock health check response
    mock_health_response = mocker.MagicMock()
    mock_health_response.status_code = 200

    # Create async mock for get
    async def mock_get(*args, **kwargs):
        return mock_health_response

    # Mock handle_chat to raise KeyboardInterrupt to exit loop
    mocker.patch.object(chat, "handle_chat", side_effect=KeyboardInterrupt)

    # Mock AsyncClient
    mock_client = mocker.MagicMock(spec=httpx.AsyncClient)
    mock_client.get = mock_get
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=None)

    mocker.patch("httpx.AsyncClient", return_value=mock_client)

    # Run chat - should connect and exit via KeyboardInterrupt
    await chat.chat()


async def test_chat_raises_when_api_unhealthy(mocker):
    """Tests that chat raises RuntimeError when API is not healthy."""
    mocker.patch.dict("os.environ", {"APP_PORT": "8000"})

    # Mock unhealthy response
    mock_health_response = mocker.MagicMock()
    mock_health_response.status_code = 500

    async def mock_get(*args, **kwargs):
        return mock_health_response

    mock_client = mocker.MagicMock(spec=httpx.AsyncClient)
    mock_client.get = mock_get
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=None)

    mocker.patch("httpx.AsyncClient", return_value=mock_client)

    with pytest.raises(RuntimeError, match="Vapor API is not healthy"):
        await chat.chat()


async def test_handle_chat_tool_call_stops_live_display(mocker):
    """Tests that a tool_call event stops an active live display."""
    # Mock console
    mocker.patch("rich.console.Console.input", return_value="Test question")
    mock_print = mocker.patch("rich.console.Console.print")

    # Mock Live display
    mock_live = mocker.MagicMock()
    mocker.patch("vapor.chat.Live", return_value=mock_live)

    # SSE response: content first (starts Live), then tool_call (should stop Live)
    sse_lines = [
        "event: content",
        f"data: {json.dumps({'text': 'Starting response...'})}",
        "",
        "event: tool_call",
        f"data: {json.dumps({'tool_name': 'search', 'tool_input': {'query': 'test'}})}",
        "",
        "event: done",
        f"data: {json.dumps({'status': 'complete'})}",
    ]
    mock_response = MockResponse(sse_lines)

    mock_client = mocker.MagicMock(spec=httpx.AsyncClient)
    mock_client.stream = mocker.MagicMock(
        return_value=MockStreamContextManager(mock_response)
    )

    await chat.handle_chat(mock_client, "http://localhost:8000")

    # Verify live.stop() was called when tool_call came in
    mock_live.stop.assert_called()
    # Verify tool call panel was printed
    assert mock_print.call_count >= 1
