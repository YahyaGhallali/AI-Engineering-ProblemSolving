from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the sender ('user' or 'model')")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Current user query")
    history: Optional[List[ChatMessage]] = Field(
        default_factory=list,
        description="Previous messages in the conversation",
    )


class ChatResponse(BaseModel):
    response: str = Field(..., description="Generated assistant response")
    model: str = Field(..., description="LLM model identifier used for generation")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status indicator")
    app_name: str = Field(..., description="Application name")
    environment: str = Field(..., description="Deployment environment")

