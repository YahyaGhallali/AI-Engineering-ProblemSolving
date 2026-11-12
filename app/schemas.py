"""Pydantic schemas and models for Nova Support AI."""

from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class Message(BaseModel):
    """A single chat message with a role and text content."""

    role: str = Field(..., description="Role of the sender ('user', 'model', or 'system')")
    content: str = Field(..., description="Text content of the message")


# Backward-compatibility alias
ChatMessage = Message


class ChatRequest(BaseModel):
    """Request payload for the /chat endpoint.

    Supports `messages: list[Message]` as the primary schema, while gracefully
    accepting legacy `message` + `history` payloads.
    """

    messages: List[Message] = Field(
        default_factory=list,
        description="Chronological list of conversation messages",
    )
    # Legacy fields for backward compatibility
    message: Optional[str] = Field(
        default=None,
        description="Legacy single message string",
    )
    history: Optional[List[Message]] = Field(
        default=None,
        description="Legacy conversation history",
    )

    @model_validator(mode="after")
    def unify_messages(self) -> "ChatRequest":
        """Consolidate legacy message and history fields into messages list."""
        if not self.messages:
            unified: List[Message] = []
            if self.history:
                unified.extend(self.history)
            if self.message and self.message.strip():
                unified.append(Message(role="user", content=self.message.strip()))
            self.messages = unified
        return self


class ChatResponse(BaseModel):
    """Response payload for the /chat endpoint."""

    reply: str = Field(..., description="Nova's generated response")


class HealthResponse(BaseModel):
    """Response payload for the /health status check endpoint."""

    status: str = Field(default="ok", description="Service status indicator")
    app_name: str = Field(..., description="Application name")
    environment: str = Field(..., description="Deployment environment")
