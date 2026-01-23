"""Chat streaming endpoint using Server-Sent Events (SSE)."""

import json
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, ToolMessage
from loguru import logger

from vapor.app.agent import get_agent
from vapor.app.schemas import ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])


async def stream_chat_response(message: str) -> AsyncGenerator[str, None]:
    """Generator that streams SSE events from the agent.

    Args:
        message: The user's chat message.

    Yields:
        SSE-formatted event strings.
    """
    from langchain_core.messages import HumanMessage, AIMessageChunk

    agent = get_agent()
    human_msg = HumanMessage(content=message)

    async for event, metadata in agent.astream(
        {"messages": [human_msg]},
        stream_mode="messages",
    ):
        # Handle AI message chunks (streaming tokens)
        if isinstance(event, AIMessageChunk):
            # Check for tool calls
            if event.tool_call_chunks:
                for tool_chunk in event.tool_call_chunks:
                    # Only emit when we have the tool name (first chunk of a tool call)
                    if tool_chunk.get("name"):
                        event_data = {
                            "tool_name": tool_chunk["name"],
                            "tool_input": tool_chunk.get("args", {}),
                        }
                        yield f"event: tool_call\ndata: {json.dumps(event_data)}\n\n"
            # Stream content tokens
            elif event.content:
                yield f"event: content\ndata: {json.dumps({'text': event.content})}\n\n"

        # Handle tool results
        elif isinstance(event, ToolMessage):
            event_data = {
                "tool_name": event.name,
                "result": event.content,
            }
            yield f"event: tool_result\ndata: {json.dumps(event_data)}\n\n"

    # Signal completion
    yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"


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
