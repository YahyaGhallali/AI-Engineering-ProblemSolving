"""Pydantic schemas and models for Nova Support AI."""

from typing import List, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_MESSAGES = 20
MAX_MESSAGE_LENGTH = 4_000
MessageRole = Literal["user", "model"]


class Message(BaseModel):
    """A single chat message with a role and text content."""

    role: MessageRole = Field(..., description="Role of the sender ('user' or 'model')")
    content: str = Field(
        ...,
        min_length=1,
        max_length=MAX_MESSAGE_LENGTH,
        description="Text content of the message",
    )

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value: object) -> str:
        """Normalize and validate the sender role."""
        if not isinstance(value, str):
            raise ValueError("role must be a string")
        normalized = value.strip().lower()
        if normalized not in ("user", "model"):
            raise ValueError("role must be user or model")
        return normalized

    @field_validator("content", mode="before")
    @classmethod
    def normalize_content(cls, value: object) -> str:
        """Reject blank content and normalize surrounding whitespace."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("content must be a non-empty string")
        return value.strip()


# Backward-compatibility alias
ChatMessage = Message


class ChatRequest(BaseModel):
    """Request payload for the /chat endpoint.

    Accepts a chronological list of user and model messages.
    """

    model_config = ConfigDict(extra="forbid")

    messages: List[Message] = Field(
        ...,
        min_length=1,
        max_length=MAX_MESSAGES,
        description="Chronological list of conversation messages",
    )


class ChatResponse(BaseModel):
    """Response payload for the /chat endpoint."""

    reply: str = Field(..., description="Nova's generated response")


class HealthResponse(BaseModel):
    """Response payload for the /health status check endpoint."""

    status: str = Field(default="ok", description="Service status indicator")
    app_name: str = Field(..., description="Application name")
    environment: str = Field(..., description="Deployment environment")
