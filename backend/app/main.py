import os
from fastapi import FastAPI, HTTPException, status
from google import genai
from google.genai import types

from .config import get_settings
from .prompts import SYSTEM_PROMPT
from .schemas import ChatRequest, ChatResponse, HealthResponse

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI Customer Support Assistant API",
)


def get_genai_client() -> genai.Client:
    api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY is not configured. Please set it in your .env file.",
        )
    return genai.Client(api_key=api_key)


@app.get("/", tags=["General"])
def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        environment=settings.app_env,
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest) -> ChatResponse:
    client = get_genai_client()

    contents = []
    if request.history:
        for msg in request.history:
            role = "user" if msg.role == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.content)],
                )
            )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=request.message)],
        )
    )

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
            ),
        )
        return ChatResponse(
            response=response.text or "",
            model=settings.gemini_model,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM generation failed: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

