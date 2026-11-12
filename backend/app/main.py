"""FastAPI application exposing /health and /chat endpoints for Nova."""

import logging
import os
import time
from fastapi import FastAPI, HTTPException, status
from google import genai
from google.genai import types

from .config import get_settings
from .prompts import SYSTEM_PROMPT
from .schemas import ChatRequest, ChatResponse, HealthResponse, Message

# ---------------------------------------------------------------------------
# Setup & Configuration
# ---------------------------------------------------------------------------
settings = get_settings()
logger = logging.getLogger("nova.main")

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Nova - AI Customer Support Assistant for Delivery & Shipping",
)


# ---------------------------------------------------------------------------
# GenAI Client Factory
# ---------------------------------------------------------------------------
def get_genai_client() -> genai.Client:
    """Initialize and return the Google GenAI client using configured API key."""
    api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY is not configured in settings or environment.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY is not configured. Please set it in your .env file.",
        )
    return genai.Client(api_key=api_key)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["General"])
def root():
    """Root endpoint welcoming users and providing documentation links."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/health",
        "chat": "/chat",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """Service health check returning app metadata and environment."""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.app_env,
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest) -> ChatResponse:
    """Process incoming chat messages and generate Nova's response.

    Request Flow:
    1. Validate that at least one message is present.
    2. Prepend Nova's system prompt from `prompts.py` to the conversation context.
    3. Format messages into Google GenAI Content objects.
    4. Call the configured Gemini LLM API and measure latency.
    5. Return the generated response in a ChatResponse model.
    """
    messages = request.messages
    if not messages:
        logger.warning("Rejected /chat request: messages list is empty.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one message is required in 'messages' or 'message'.",
        )

    # 1. Log incoming request with message count
    logger.info("Received /chat request with %d message(s)", len(messages))

    # 2. Prepend Nova's system prompt to the incoming messages list
    full_messages: list[Message] = [
        Message(role="system", content=SYSTEM_PROMPT)
    ] + messages

    # 3. Format messages for Google GenAI SDK
    contents: list[types.Content] = []
    for msg in messages:
        role = "user" if msg.role.lower() in ("user", "human") else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg.content)],
            )
        )

    client = get_genai_client()

    # 4. Call LLM API with timing and error handling
    start_time = time.perf_counter()
    logger.info("Calling LLM API using model '%s'...", settings.gemini_model)

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info("LLM call completed successfully in %.2f ms", latency_ms)

        reply_text = response.text or ""
        return ChatResponse(reply=reply_text)

    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            "LLM API call failed after %.2f ms: %s",
            latency_ms,
            str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM generation failed: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Local Server Execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
