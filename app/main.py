"""FastAPI application exposing /health, /chat, and browser chat UI for Nova."""

import logging
from functools import lru_cache
from pathlib import Path
import time
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from google import genai
from google.genai import types

from .config import get_settings
from .prompts import SYSTEM_PROMPT
from .schemas import ChatRequest, ChatResponse, HealthResponse

# ---------------------------------------------------------------------------
# Setup & Configuration
# ---------------------------------------------------------------------------
settings = get_settings()
logger = logging.getLogger("nova.main")

STATIC_INDEX_PATH = Path(__file__).resolve().parent / "static" / "index.html"

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Nova - AI Customer Support Assistant for Delivery & Shipping",
)


# ---------------------------------------------------------------------------
# GenAI Client Factory
# ---------------------------------------------------------------------------
def provider_is_configured() -> bool:
    """Return whether a non-empty provider credential is available."""
    return bool(settings.gemini_api_key.strip())


@lru_cache(maxsize=1)
def get_genai_client() -> genai.Client:
    """Initialize and return the Google GenAI client using configured API key."""
    if not provider_is_configured():
        logger.error("GEMINI_API_KEY is not configured in settings or environment.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The language model provider is not configured.",
        )
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(timeout=settings.gemini_timeout_ms),
    )


def read_static_index() -> str:
    """Read the browser UI and convert filesystem failures into an API error."""
    try:
        return STATIC_INDEX_PATH.read_text(encoding="utf-8")
    except OSError:
        logger.exception("Unable to read browser UI from %s", STATIC_INDEX_PATH)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The browser interface is temporarily unavailable.",
        )


# ---------------------------------------------------------------------------
# UI & General Endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["UI", "General"])
def root(request: Request):
    """Serve the lightweight chat UI for browser testing, or metadata for JSON clients."""
    accept = request.headers.get("accept", "")
    if "application/json" in accept and "text/html" not in accept:
        return JSONResponse(
            {
                "message": f"Welcome to {settings.app_name}",
                "docs": "/docs",
                "health": "/health",
                "chat": "/chat",
                "ui": "/ui",
            }
        )
    if STATIC_INDEX_PATH.is_file():
        return HTMLResponse(content=read_static_index())
    return HTMLResponse(content="<h1>Nova Support AI</h1><p>UI file not found.</p>")


@app.get("/ui", response_class=HTMLResponse, tags=["UI"])
def ui():
    """Explicit endpoint serving Nova's browser chat interface."""
    if STATIC_INDEX_PATH.is_file():
        return HTMLResponse(content=read_static_index())
    return HTMLResponse(content="<h1>Nova Support AI</h1><p>UI file not found.</p>")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """Liveness check that does not require external provider availability."""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.app_env,
    )


@app.get("/ready", response_model=HealthResponse, tags=["Health"])
def readiness_check() -> HealthResponse:
    """Readiness check that verifies the provider is configured."""
    if not provider_is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The language model provider is not configured.",
        )
    return HealthResponse(
        status="ready",
        app_name=settings.app_name,
        environment=settings.app_env,
    )


# ---------------------------------------------------------------------------
# Chat Endpoint
# ---------------------------------------------------------------------------
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
            detail="At least one message is required in 'messages'.",
        )

    # 1. Log incoming request with message count
    logger.info("Received /chat request with %d message(s)", len(messages))

    # 2. Format messages for Google GenAI SDK. The system prompt is supplied
    # separately through GenerateContentConfig.system_instruction.
    contents: list[types.Content] = []
    for msg in messages:
        contents.append(
            types.Content(
                role=msg.role,
                parts=[types.Part.from_text(text=msg.content)],
            )
        )

    # 3. Call LLM API with timing and error handling
    start_time = time.perf_counter()
    logger.info("Calling LLM API using model '%s'...", settings.gemini_model)

    try:
        client = get_genai_client()
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info("LLM call completed successfully in %.2f ms", latency_ms)

        reply_text = (response.text or "").strip()
        if not reply_text:
            logger.error("LLM API returned an empty response after %.2f ms", latency_ms)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="The language model returned an empty response.",
            )
        return ChatResponse(reply=reply_text)

    except HTTPException:
        raise
    except Exception:
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            "LLM API call failed after %.2f ms for model '%s'",
            latency_ms,
            settings.gemini_model,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The language model could not generate a response.",
        )


# ---------------------------------------------------------------------------
# Local Server Execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
