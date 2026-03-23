import json
import os
from typing import Any

import httpx
import reflex as rx

from vapor._types import QA, ToolCall


def get_vapor_api_url() -> str:
    """Get the Vapor API URL from environment."""
    port = os.getenv("APP_PORT", "8000")
    host = os.getenv("VAPOR_API_HOST", "localhost")
    return f"http://{host}:{port}"


def format_tool_input(tool_input: dict | str | Any) -> str:
    """Format tool input as YAML-like display without JSON syntax.

    Args:
        tool_input: The tool input to format.

    Returns:
        A clean YAML-like formatted string.
    """
    if isinstance(tool_input, str):
        return tool_input

    if not isinstance(tool_input, dict):
        return str(tool_input)

    lines = []
    for key, value in tool_input.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for k, v in value.items():
                lines.append(f"  {k}: {v}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


class State(rx.State):
    """The app state."""

    # A dict from the chat name to the list of questions and answers.
    _chats: dict[str, list[QA]] = {
        "New Chat": [],
    }

    # The current chat name.
    current_chat = "New Chat"

    # Whether we are processing the question.
    processing: bool = False

    # Whether we are awaiting the first response event.
    awaiting_response: bool = False

    # Whether the new chat modal is open.
    is_modal_open: bool = False

    @rx.event
    def create_chat(self, form_data: dict[str, Any]):
        """Create a new chat."""
        # Add the new chat to the list of chats.
        new_chat_name = form_data["new_chat_name"]
        self.current_chat = new_chat_name
        self._chats[new_chat_name] = []
        self.is_modal_open = False

    @rx.event
    def set_is_modal_open(self, is_open: bool):
        """Set the new chat modal open state.

        Args:
            is_open: Whether the modal is open.
        """
        self.is_modal_open = is_open

    @rx.var
    def selected_chat(self) -> list[QA]:
        """Get the list of questions and answers for the current chat.

        Returns:
            The list of questions and answers.
        """
        return (
            self._chats[self.current_chat] if self.current_chat in self._chats else []
        )

    @rx.event
    def delete_chat(self, chat_name: str):
        """Delete the current chat."""
        if chat_name not in self._chats:
            return
        del self._chats[chat_name]
        if len(self._chats) == 0:
            self._chats = {
                "Intros": [],
            }
        if self.current_chat not in self._chats:
            self.current_chat = list(self._chats.keys())[0]

    @rx.event
    def set_chat(self, chat_name: str):
        """Set the name of the current chat.

        Args:
            chat_name: The name of the chat.
        """
        self.current_chat = chat_name

    @rx.event
    def set_new_chat_name(self, new_chat_name: str):
        """Set the name of the new chat.

        Args:
            new_chat_name: The name of the new chat.
        """
        self.new_chat_name = new_chat_name

    @rx.var
    def chat_titles(self) -> list[str]:
        """Get the list of chat titles.

        Returns:
            The list of chat names.
        """
        return list(self._chats.keys())

    @rx.event
    async def process_question(self, form_data: dict[str, Any]):
        """Process a question from the form."""
        question = form_data["question"]

        if not question:
            return

        async for value in self.vapor_process_question(question):
            yield value

    @rx.event
    def toggle_tools_collapsed(self, qa_index: int):
        """Toggle the collapsed state of tool calls for a QA pair.

        Args:
            qa_index: The index of the QA pair in the current chat.
        """
        if 0 <= qa_index < len(self._chats[self.current_chat]):
            qa = self._chats[self.current_chat][qa_index]
            qa["tools_collapsed"] = not qa["tools_collapsed"]
            self._chats = self._chats

    @rx.event
    async def vapor_process_question(self, question: str):
        """Get the response from the Vapor API.

        Args:
            question: The user's question.
        """
        # Add the question to the list of questions with new fields.
        qa = QA(
            question=question,
            answer="",
            tool_calls=[],
            tools_collapsed=False,
        )
        self._chats[self.current_chat].append(qa)

        # Clear the input and start the processing.
        self.processing = True
        self.awaiting_response = True
        yield

        api_url = get_vapor_api_url()
        event_type = None
        has_started_streaming = False

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{api_url}/chat",
                    json={"message": question},
                    timeout=120.0,
                ) as response:
                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        if line.startswith("event:"):
                            event_type = line.split(":", 1)[1].strip()
                        elif line.startswith("data:"):
                            data = json.loads(line.split(":", 1)[1].strip())

                            if event_type == "on_tool_start":
                                # Add new tool call with pending status
                                # Keep awaiting_response=True to show ellipsis during tools
                                # Format tool_input as YAML-like string
                                formatted_input = format_tool_input(data["tool_input"])
                                tool_call = ToolCall(
                                    tool_name=data["tool_name"],
                                    index=data["index"],
                                    tool_input=formatted_input,
                                    status="pending",
                                )
                                # Create completely new objects to ensure Reflex detects change
                                current_qa = self._chats[self.current_chat][-1]
                                new_qa = {
                                    **current_qa,
                                    "tool_calls": [
                                        *current_qa["tool_calls"],
                                        tool_call,
                                    ],
                                }
                                new_chat_list = [
                                    *self._chats[self.current_chat][:-1],
                                    new_qa,
                                ]
                                self._chats = {
                                    **self._chats,
                                    self.current_chat: new_chat_list,
                                }
                                yield

                            elif event_type == "on_tool_end":
                                # Find the pending tool and mark it complete
                                current_qa = self._chats[self.current_chat][-1]
                                updated_tools = []
                                for tc in current_qa["tool_calls"]:
                                    if tc["status"] == "pending":
                                        updated_tools.append(
                                            {**tc, "status": "complete"}
                                        )
                                    else:
                                        updated_tools.append(dict(tc))
                                new_qa = {**current_qa, "tool_calls": updated_tools}
                                new_chat_list = [
                                    *self._chats[self.current_chat][:-1],
                                    new_qa,
                                ]
                                self._chats = {
                                    **self._chats,
                                    self.current_chat: new_chat_list,
                                }
                                yield

                            elif event_type == "on_chat_model_stream":
                                # First event received - stop showing loading indicator
                                self.awaiting_response = False
                                # First content chunk - collapse tools
                                current_qa = self._chats[self.current_chat][-1]
                                if (
                                    not has_started_streaming
                                    and current_qa["tool_calls"]
                                ):
                                    current_qa = {**current_qa, "tools_collapsed": True}
                                    has_started_streaming = True

                                # Update answer with new text
                                new_qa = {
                                    **current_qa,
                                    "answer": current_qa["answer"] + data["text"],
                                }
                                new_chat_list = [
                                    *self._chats[self.current_chat][:-1],
                                    new_qa,
                                ]
                                self._chats = {
                                    **self._chats,
                                    self.current_chat: new_chat_list,
                                }
                                yield

                            elif event_type == "done":
                                break

        except httpx.ConnectError:
            current_qa = self._chats[self.current_chat][-1]
            new_qa = {
                **current_qa,
                "answer": "Error: Could not connect to Vapor API. Is it running?",
            }
            new_chat_list = [*self._chats[self.current_chat][:-1], new_qa]
            self._chats = {**self._chats, self.current_chat: new_chat_list}
            yield
        except httpx.TimeoutException:
            current_qa = self._chats[self.current_chat][-1]
            new_qa = {
                **current_qa,
                "answer": current_qa["answer"] + "\n\nError: Request timed out.",
            }
            new_chat_list = [*self._chats[self.current_chat][:-1], new_qa]
            self._chats = {**self._chats, self.current_chat: new_chat_list}
            yield

        # Toggle the processing flag.
        self.processing = False
