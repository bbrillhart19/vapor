import json
import os
from typing import Any, TypedDict

import httpx
import reflex as rx


def get_vapor_api_url() -> str:
    """Get the Vapor API URL from environment."""
    port = os.getenv("APP_PORT", "8000")
    host = os.getenv("VAPOR_API_HOST", "localhost")
    return f"http://{host}:{port}"


class QA(TypedDict):
    """A question and answer pair."""

    question: str
    answer: str


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
    async def vapor_process_question(self, question: str):
        """Get the response from the Vapor API.

        Args:
            question: The user's question.
        """
        # Add the question to the list of questions.
        qa = QA(question=question, answer="")
        self._chats[self.current_chat].append(qa)

        # Clear the input and start the processing.
        self.processing = True
        yield

        api_url = get_vapor_api_url()
        event_type = None

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

                            if event_type == "content":
                                self._chats[self.current_chat][-1]["answer"] += data[
                                    "text"
                                ]
                                self._chats = self._chats
                                yield

                            elif event_type == "tool_call":
                                tool_info = (
                                    f"\n\n*Using tool: {data['tool_name']}...*\n\n"
                                )
                                self._chats[self.current_chat][-1][
                                    "answer"
                                ] += tool_info
                                self._chats = self._chats
                                yield

                            elif event_type == "done":
                                break

        except httpx.ConnectError:
            self._chats[self.current_chat][-1][
                "answer"
            ] = "Error: Could not connect to Vapor API. Is it running?"
            self._chats = self._chats
            yield
        except httpx.TimeoutException:
            self._chats[self.current_chat][-1][
                "answer"
            ] += "\n\nError: Request timed out."
            self._chats = self._chats
            yield

        # Toggle the processing flag.
        self.processing = False
