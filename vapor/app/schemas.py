"""Pydantic schemas for the Vapor REST API."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for the /chat endpoint."""

    message: str = Field(
        ...,
        description="The user's chat message to send to the agent.",
        min_length=1,
    )
