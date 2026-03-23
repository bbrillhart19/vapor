"""Chat streaming endpoint using Server-Sent Events (SSE)."""

import json
import re
from typing import AsyncGenerator, Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from loguru import logger

from vapor.app.agent import get_agent
from vapor.app.schemas import ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])

# Patterns for internal model markup that should be filtered from output
_OPEN_TAG_PATTERN = re.compile(r"<(function_calls?|tool_calls?|invoke)>", re.IGNORECASE)
_CLOSE_TAG_PATTERN = re.compile(
    r"</(function_calls?|tool_calls?|invoke)>", re.IGNORECASE
)


async def stream_chat_response(message: str) -> AsyncGenerator[str, None]:
    """Generator that streams SSE events from the agent.

    Args:
        message: The user's chat message.

    Yields:
        SSE-formatted event strings.
    """

    def _safe_json_dumps(obj: Any):
        """Serialize to JSON, everything to strings"""
        return json.dumps(obj, default=lambda o: str(o))

    # Retrieve the agent from factory, setup the user's message
    agent = get_agent()
    human_msg = HumanMessage(content=message)

    # Track when to stream response
    # (no tools were called or if a tool was started don't stream until it has ended)
    stream_content = False
    seen_tool_start = False

    # Track order of tool calls
    tool_call_index = 0

    # State for filtering internal model markup that spans chunks
    inside_markup = False
    content_buffer = ""

    # Stream events with tools calls and final response
    async for event in agent.astream_events(
        {"messages": [human_msg]},
        version="v2",
    ):

        event_name = event.get("event")
        event_data = {}
        # Match case based on the event type
        match event_name:
            # Tool call has started, emit event with the name and input parameters
            case "on_tool_start":
                seen_tool_start = True
                tool_name = event.get("name", "Unknown Tool")
                tool_input = event.get("data", {}).get("input")
                if isinstance(tool_input, dict) and "runtime" in tool_input:
                    del tool_input["runtime"]
                event_data = {
                    "tool_name": tool_name,
                    "index": tool_call_index,
                    "tool_input": tool_input,
                }
                tool_call_index += 1
            # Tool call ended, emit event with name and output, enable stream_content
            case "on_tool_end":
                stream_content = True
                tool_output = event.get("data", {}).get("output", {})
                event_data = {
                    "tool_name": tool_name,
                    "tool_output": tool_output,
                }
            # Stream chat, only if tool calls are complete so we don't accidentally
            # stream intermediary outputs
            case "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    # Add chunk to buffer for processing
                    content_buffer += chunk.content

                    # Process buffer to filter out internal markup
                    clean_text = ""
                    while content_buffer:
                        if inside_markup:
                            # Look for closing tag
                            close_match = _CLOSE_TAG_PATTERN.search(content_buffer)
                            if close_match:
                                # Found closing tag, skip everything up to it
                                content_buffer = content_buffer[close_match.end() :]
                                inside_markup = False
                            else:
                                # No closing tag yet, keep buffer for next chunk
                                # But limit buffer size to avoid memory issues
                                if len(content_buffer) > 500:
                                    content_buffer = content_buffer[-100:]
                                break
                        else:
                            # Look for opening tag
                            open_match = _OPEN_TAG_PATTERN.search(content_buffer)
                            if open_match:
                                # Emit content before the tag
                                clean_text += content_buffer[: open_match.start()]
                                content_buffer = content_buffer[open_match.end() :]
                                inside_markup = True
                            else:
                                # No opening tag - check for potential partial tag at end
                                last_lt = content_buffer.rfind("<")
                                if last_lt != -1 and last_lt > len(content_buffer) - 20:
                                    # Potential partial tag, emit up to it
                                    clean_text += content_buffer[:last_lt]
                                    content_buffer = content_buffer[last_lt:]
                                else:
                                    # Safe to emit all
                                    clean_text += content_buffer
                                    content_buffer = ""
                                break

                    # Only emit if we have clean content AND streaming is allowed
                    # Don't enable streaming just because we got a chat event -
                    # only enable it if we have real content (not just markup)
                    if clean_text:
                        if not seen_tool_start:
                            # No tools seen yet and we have real content - enable streaming
                            stream_content = True
                        if stream_content:
                            event_data = {"text": clean_text}

        # Yield SSE with event name and data
        if event_name and event_data:
            yield f"event: {event_name}\ndata: {_safe_json_dumps(event_data)}\n\n"

    # Flush any remaining clean content from buffer (outside markup blocks)
    if content_buffer and not inside_markup:
        # Strip any potential partial opening tags at the end
        last_lt = content_buffer.rfind("<")
        if last_lt != -1:
            remaining = content_buffer[:last_lt]
        else:
            remaining = content_buffer
        if remaining:
            yield f"event: on_chat_model_stream\ndata: {_safe_json_dumps({'text': remaining})}\n\n"

    # Streaming complete
    yield f"event: done\ndata: {_safe_json_dumps({'status': 'complete'})}\n\n"


@router.post(
    "",
    response_class=StreamingResponse,
    summary="Stream a chat response",
    description="Send a message and receive a streaming response via Server-Sent Events.",
)
async def chat(request: ChatRequest) -> StreamingResponse:
    """Stream chat responses using Server-Sent Events.

    The response stream emits events of the following types:
    - `tool_call`: Agent calling a tool with name and inputs
    - `tool_result`: Result returned from a tool
    - `content`: Final answer text chunks
    - `done`: Stream completion signal
    """
    logger.info(f"Chat request: {request.message[:50]}...")

    return StreamingResponse(
        stream_chat_response(request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
