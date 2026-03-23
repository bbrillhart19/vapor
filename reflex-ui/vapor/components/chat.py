import reflex as rx
from reflex.constants.colors import ColorType

from vapor._types import QA, ToolCall
from vapor.state import State


def message_content(text: str, color: ColorType) -> rx.Component:
    """Create a message content component.

    Args:
        text: The text to display.
        color: The color of the message.

    Returns:
        A component displaying the message.
    """
    return rx.markdown(
        text,
        background_color=rx.color(color, 4),
        color=rx.color(color, 12),
        display="inline-block",
        padding_inline="1em",
        border_radius="8px",
    )


def tool_call_item_active(tool_call: ToolCall) -> rx.Component:
    """Display a tool call in the active (pre-streaming) state.

    Shows completed tools with checkmark only, pending tools with spinner and input.

    Args:
        tool_call: The tool call to display.

    Returns:
        A component with status icon, tool name, and input if pending.
    """
    status_icon = rx.cond(
        tool_call["status"] == "pending",
        rx.spinner(size="1"),
        rx.icon("check", size=16, color=rx.color("green", 9)),
    )

    header = rx.hstack(
        status_icon,
        rx.text(
            tool_call["tool_name"],
            font_weight="bold",
            font_size="0.9em",
        ),
        spacing="2",
        align="center",
    )

    # Show input only for pending tools
    return rx.cond(
        tool_call["status"] == "pending",
        rx.vstack(
            header,
            rx.box(
                rx.text(
                    tool_call["tool_input"],
                    style={
                        "margin": "0",
                        "font-family": "monospace",
                        "font-size": "0.85em",
                        "white-space": "pre-wrap",
                    },
                ),
                padding="8px",
                background=rx.color("gray", 3),
                border_radius="4px",
                width="100%",
            ),
            align="start",
            spacing="2",
            width="100%",
        ),
        header,
    )


def active_tool_box(tool_calls: list[ToolCall]) -> rx.Component:
    """Display all tool calls during execution.

    Shows completed tools with checkmark, pending tool with spinner and input.
    The box expands as more tools are added.

    Args:
        tool_calls: List of tool calls for the current QA.

    Returns:
        A nested box component showing all tool calls.
    """
    return rx.box(
        rx.vstack(
            rx.foreach(tool_calls, tool_call_item_active),
            align="start",
            spacing="2",
            width="100%",
        ),
        padding="12px",
        border=f"1px solid {rx.color('gray', 6)}",
        border_radius="8px",
        background_color=rx.color("gray", 2),
        margin_bottom="8px",
    )


def tool_history_item(tool_call: ToolCall) -> rx.Component:
    """Display a single tool in the collapsed history view.

    Args:
        tool_call: The tool call to display.

    Returns:
        A compact tool display with checkmark.
    """
    return rx.hstack(
        rx.icon("check", size=14, color=rx.color("green", 9)),
        rx.text(tool_call["tool_name"], font_size="0.85em"),
        spacing="2",
    )


def tool_history_accordion(
    tool_calls: list[ToolCall],
    is_collapsed: bool,
    qa_index: int,
) -> rx.Component:
    """Expandable/collapsible tool call history after streaming begins.

    Args:
        tool_calls: List of tool calls to display.
        is_collapsed: Whether the tool history is collapsed.
        qa_index: Index of the QA pair for the toggle handler.

    Returns:
        A collapsible component showing tool call history.
    """
    return rx.box(
        rx.hstack(
            rx.cond(
                is_collapsed,
                rx.icon("chevron-right", size=16),
                rx.icon("chevron-down", size=16),
            ),
            rx.text(
                "Tool calls (",
                tool_calls.length(),
                ")",
                font_size="0.85em",
                color=rx.color("gray", 11),
            ),
            spacing="1",
            align="center",
            cursor="pointer",
            on_click=lambda: State.toggle_tools_collapsed(qa_index),
            padding="4px",
            _hover={"background": rx.color("gray", 3)},
            border_radius="4px",
        ),
        rx.cond(
            ~is_collapsed,
            rx.vstack(
                rx.foreach(tool_calls, tool_history_item),
                spacing="1",
                padding_left="24px",
                padding_top="4px",
            ),
            rx.fragment(),
        ),
        padding="8px",
        border=f"1px solid {rx.color('gray', 5)}",
        border_radius="6px",
        background_color=rx.color("gray", 2),
        margin_bottom="8px",
    )


def message(qa: QA, index: int) -> rx.Component:
    """A single question/answer message with tool call handling.

    Args:
        qa: The question/answer pair.
        index: The index of this QA in the chat for toggle handler.

    Returns:
        A component displaying the question/answer pair with tool calls.
    """
    return rx.box(
        # Question - right aligned
        rx.box(
            message_content(qa["question"], "mauve"),
            text_align="right",
            margin_bottom="8px",
        ),
        # Answer section - left aligned
        rx.box(
            # Tool calls display - conditional on state
            rx.cond(
                qa["tool_calls"].length() > 0,
                rx.cond(
                    qa["answer"].length() > 0,
                    # After streaming starts: collapsible history
                    tool_history_accordion(
                        qa["tool_calls"], qa["tools_collapsed"], index
                    ),
                    # Before streaming: active tool box with loading ellipsis
                    rx.vstack(
                        active_tool_box(qa["tool_calls"]),
                        rx.cond(
                            State.awaiting_response,
                            loading_ellipsis(),
                            rx.fragment(),
                        ),
                        align="start",
                        spacing="0",
                        width="100%",
                    ),
                ),
                # No tool calls - show loading ellipsis if awaiting
                rx.cond(
                    State.awaiting_response & (qa["answer"].length() == 0),
                    loading_ellipsis(),
                    rx.fragment(),
                ),
            ),
            # Answer content
            rx.cond(
                qa["answer"].length() > 0,
                message_content(qa["answer"], "accent"),
                rx.fragment(),
            ),
            text_align="left",
            margin_bottom="8px",
        ),
        max_width="50em",
    )


def loading_ellipsis() -> rx.Component:
    """Animated ellipsis loading indicator."""
    return rx.text(
        "...",
        color=rx.color("accent", 9),
        font_size="2.5em",
        line_height="1",
        style={
            "animation": "pulse 1.5s ease-in-out infinite",
            "@keyframes pulse": {
                "0%, 100%": {"opacity": "0.4"},
                "50%": {"opacity": "1"},
            },
        },
    )


def chat() -> rx.Component:
    """List all the messages in a single conversation."""
    return rx.auto_scroll(
        rx.vstack(
            rx.foreach(
                State.selected_chat,
                lambda qa, index: message(qa, index),
            ),
            width="100%",
            max_width="50em",
            margin="0 auto",
            align="stretch",
        ),
        flex="1",
        padding="8px",
        width="100%",
    )


def action_bar() -> rx.Component:
    """The action bar to send a new message."""
    return rx.center(
        rx.vstack(
            rx.form(
                rx.hstack(
                    rx.input(
                        rx.input.slot(
                            rx.tooltip(
                                rx.icon("info", size=18),
                                content="Enter a question to get a response.",
                            )
                        ),
                        placeholder="Ask Vapor...",
                        id="question",
                        flex="3",
                        size="3",
                    ),
                    rx.button(
                        "Send",
                        loading=State.processing,
                        disabled=State.processing,
                        type="submit",
                    ),
                    max_width="50em",
                    margin="0 auto",
                    align_items="center",
                ),
                reset_on_submit=True,
                on_submit=State.process_question,
            ),
            width="100%",
            padding_x="16px",
            align="stretch",
        ),
        position="sticky",
        bottom="0",
        left="0",
        padding_y="16px",
        backdrop_filter="auto",
        backdrop_blur="lg",
        border_top=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
        align="stretch",
        width="100%",
    )
