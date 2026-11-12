# Nova Support

Nova Support is a FastAPI customer-support assistant for delivery, shipping,
tracking, and refund questions. The current implementation is **v0.1**:
Google GenAI inference, a system prompt with a static micro-FAQ, request
validation, structured backend logging, and a browser chat UI are implemented.
RAG, MCP tools, RBAC, semantic routing/caching, and evaluation workflows are
planned.

## System Design

```mermaid
flowchart TD
    UI["Browser chat UI (app/static/index.html)"] --> API["FastAPI app (/ and /ui)"]
    Client["API client"] --> CHAT["FastAPI /chat"]
    API --> CHAT
    CHAT --> Schema["Request validation (app/schemas.py)"]
    Schema --> Prompt["Prompt and guardrails (app/prompts.py)"]
    Prompt --> Boundary["Provider boundary (timeout and safe errors)"]
    Boundary --> LLM["Google GenAI Gemini"]
    LLM --> CHAT
    CHAT --> UI
    Config["Settings and logging (app/config.py)"] --> API
```

```mermaid
sequenceDiagram
    participant U as User
    participant UI as Browser UI
    participant API as FastAPI /chat
    participant S as Schemas
    participant P as System prompt
    participant B as Provider boundary
    participant L as Gemini
    U->>UI: Enter delivery question
    UI->>API: POST /chat with messages
    API->>S: Validate and normalize payload
    S-->>API: ChatRequest
    API->>P: Assemble system instruction
    API->>B: Apply timeout and call provider
    B->>L: Generate content
    L-->>API: Generated reply
    API-->>UI: ChatResponse
    UI-->>U: Render reply
```

## Project Structure

```text
├── .env.example
├── .github/
│   └── copilot-instructions.md
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── prompts.py
│   ├── schemas.py
│   └── static/
│       └── index.html
├── tests/
│   ├── test_main.py
│   └── test_nova.py
├── pyproject.toml
├── README.md
└── uv.lock
```

- `app/config.py`: Loads environment settings and configures logging.
- `app/main.py`: Defines the FastAPI application, UI, liveness `/health`,
  provider-readiness `/ready`, and bounded `/chat` endpoints.
- `app/prompts.py`: Defines Nova's scope, loyalty rule, policies, and guardrails.
- `app/schemas.py`: Defines and normalizes chat and health request/response
  models.
- `app/static/index.html`: Browser chat client for the local API.
  Assistant responses render `**bold**` segments as bold text while keeping
  message content safely text-based.
- `tests/test_main.py`: Focused request validation and provider error tests.
- `tests/test_nova.py`: Optional live FAQ and guardrail regression checks.
- `.github/copilot-instructions.md`: Repository guidance; the only application
  package is the root `app/` directory. Do not recreate `backend/`.

## Local Setup and Runbook

Use `uv` for environment and dependency management:

```bash
cp .env.example .env
# Set GEMINI_API_KEY in .env
uv sync
uv run uvicorn app.main:app --reload
```

Open `http://localhost:8000` for the browser chat UI. Swagger documentation is
available at `http://localhost:8000/docs`.

Run the test suite with:

```bash
uv run pytest
```

Run the live FAQ and guardrail regression checks against a running server with:

```bash
uv run python tests/test_nova.py
```

## API Contract and Design Decisions

- `GET /`: Serves the browser UI for HTML clients or service metadata for JSON
  clients.
- `GET /ui`: Serves the browser UI explicitly.
- `GET /health`: Returns `status`, `app_name`, and `environment`.
- `GET /ready`: Returns `200` only when the Gemini credential is configured;
  otherwise returns `503`.
- `POST /chat`: Accepts `{"messages": [{"role": "user", "content": "..."}]}`.
  `messages` is required; legacy `message` and `history` fields are not
  supported. Roles are limited to `user`/`model`, requests contain at most 20
  messages, and each message is at most 4,000 characters. Responses are
  `{"reply": "..."}`.
- The system prompt limits answers to delivery and shipping support, prevents
  competitor promotion, and enforces the static shipping, operating-hours,
  damaged-parcel, and lost-parcel policies.
- Startup configuration, request counts, LLM latency, and failures are logged
  without logging API keys or returning provider exception details. Provider
  calls have a 30-second timeout, and missing configuration/provider failures
  return explicit safe HTTP errors.
- The browser UI supports lightweight bold formatting using `**text**`.

## Advancements

### 2026-11-12

- **What changed:** Consolidated the implementation and browser UI into the
  root `app/` package, removed the duplicate `backend/` tree, and updated
  startup documentation and the module execution target.
- **Why it changed:** Ensures imports, static assets, and the documented
  `uv run uvicorn app.main:app --reload` command all use one application
  location.
- **Next planned layer:** Add retrieval-backed knowledge and tool integrations
  without introducing a second application package.

- **What changed:** Added strict message roles and limits, bounded Gemini
  requests, safe provider errors, `/ready`, and a credential-free
  `.env.example`, plus focused pytest coverage and root-package test
  configuration with clean imports and diagnostics under the declared Python
  environment.
- **Why it changed:** Prevents prompt-context abuse and cost spikes, avoids
  leaking provider internals, and makes deployment readiness observable.
- **Next planned layer:** Add authenticated server-side conversation state so
  assistant history cannot be forged by clients.

- **What changed:** Added safe bold formatting for assistant messages in
  `app/static/index.html`.
- **Why it changed:** Prevents Markdown markers such as `**Standard Shipping:**`
  from appearing literally in the chat UI.
- **Next planned layer:** Expand formatting only if the response contract
  formally adopts a broader Markdown subset.
