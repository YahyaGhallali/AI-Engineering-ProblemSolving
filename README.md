# Nova Support

AI customer support assistant backend built with FastAPI and Google GenAI.

## Project Structure

```text
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
├── README.md
└── backend/
    ├── __init__.py
    └── app/
        ├── __init__.py
        ├── config.py
        ├── main.py
        ├── prompts.py
        └── schemas.py
```

## Getting Started

### 1. Configure Environment Variables
Copy `.env.example` to `.env` and set your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY="your-gemini-api-key"
```

### 2. Run the Server

Using `uv`:

```bash
uv run uvicorn backend.app.main:app --reload
```

The API will be available at:
- **API Base**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **Support Chat**: `POST http://localhost:8000/chat`

