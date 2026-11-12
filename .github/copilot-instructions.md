# Workspace & Documentation Instructions — Nova Support

## 1. Core Engineering Constraints
- **Package Manager:** Use `uv` exclusively (`uv init`, `uv add`, `uv run`, `uv sync`). Never generate `requirements.txt`, `Dockerfile`, or `docker-compose.yml` unless explicitly requested.
- **Code Style:** Write straightforward, readable, well-commented code without obscure abstractions or premature overengineering.
- **Observability:** Include clean, structured Python `logging` (timestamps, levels, latency, request/error context) in all backend and UI entry points. Never log secret API keys.
- **Ambiguity Rule:** If requirements, schemas, or provider choices are unclear, stop and ask before making assumptions.
- **Application layout:** Keep the single FastAPI package at the project root in `app/`. Never create or restore a `backend/` directory.
- **Server command:** Run the server from the project root with `uv run uvicorn app.main:app --reload`.

---

## 2. Mandatory Technical `README.md` Sync Rule
**Every time you create, modify, refactor, or delete code, prompts, endpoints, or dependencies, you MUST create or update `README.md` at the project root in the same turn.**

Never leave `README.md` out of sync with the actual codebase. Treat `README.md` as a living technical architecture document.

### Required Sections in `README.md`
1. **Project Overview & Current Architecture Stage**
   - Summarize what Nova currently does and clearly state which system layer is **Implemented** vs. **Planned** (e.g., *v0.1: Model + System Prompt + Static Micro-FAQ* vs. upcoming *RAG, MCP Tools, RBAC, Guardrails, Semantic Cache/Router, Observability & Evals*).
2. **System Design & Mermaid Diagrams**
   - Include at least two up-to-date Mermaid diagrams reflecting the **current** code (update nodes and flows whenever new components are added):
     - **System Architecture (`flowchart TD` or `flowchart LR`):** Show the UI/client, FastAPI backend, prompt/guardrail layer, LLM provider, and any connected tools or data stores.
     - **Request Lifecycle (`sequenceDiagram`):** Trace a user message step-by-step from input validation and logging through prompt assembly, LLM inference, error handling, and response delivery.
   - *Mermaid Syntax Rule:* Always wrap node labels containing spaces, parentheses, or slashes in double quotes (e.g., `API["FastAPI (/chat)"]`) so diagrams render cleanly on GitHub and in IDE previews.
3. **Codebase Structure & Module Responsibilities**
   - Provide an up-to-date directory tree and a concise table or bullet list explaining the role of every file (`main.py`, `config.py`, `prompts.py`, `schemas.py`, UI files, tests).
4. **Local Setup & Runbook (`uv`)**
   - Document exact commands to copy `.env.example` to `.env`, install dependencies (`uv sync`), start the FastAPI backend (`uv run uvicorn ...`), launch the chat UI, and run tests (`uv run pytest ...`).
5. **API Contract & Design Decisions**
   - Document active endpoints (e.g., `GET /health`, `POST /chat`), request/response payloads, prompt guardrails (scope, loyalty rule, micro-FAQ), and logging/error-handling behavior.
6. **Advancements & Architectural Changelog**
   - Maintain a chronological log (`### Advancements`) recording each meaningful code or architectural change:
     - **What changed** (files/modules added or updated)
     - **Why it changed** (problem solved or capability unlocked)
     - **Next planned layer** (e.g., moving from static FAQ to RAG or adding MCP tool calling)

### Documentation Integrity Rules
- **Truthfulness:** Never document unbuilt features as active. Clearly badge or separate `[Implemented]` capabilities from `[Roadmap / Planned]` upgrades.
- **Incremental Updates:** When modifying existing code, update only the impacted sections, diagrams, and the **Advancements** log rather than wiping valid technical details.