"""Type definitions for the Vapor UI state."""

from typing import Literal, TypedDict


class ToolCall(TypedDict):
    """A single tool call with its state."""

    tool_name: str
    index: int
    tool_input: str  # Pre-formatted YAML-like string
    status: Literal["pending", "complete"]


class QA(TypedDict):
    """A question and answer pair with tool calls."""

    question: str
    answer: str
    tool_calls: list[ToolCall]
    tools_collapsed: bool
