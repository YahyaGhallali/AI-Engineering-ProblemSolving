"""Root-level entrypoint forwarding to backend.app.main."""
from backend.app.main import app, chat, health_check, root

__all__ = ["app", "chat", "health_check", "root"]

