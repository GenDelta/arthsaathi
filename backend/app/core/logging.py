"""Structured (JSON) logging configuration for ArthSaathi.

Usage: call ``configure_logging()`` once at application startup (done in main.py).
All modules obtain a logger via ``logging.getLogger(__name__)``.

PII policy (AGENT_INSTRUCTIONS.md §2):
- Do NOT log: name, phone_number, extracted_text, document raw content.
- Acceptable at INFO: transaction amount (not PII), user_id, document_id.
- Agent graph transitions: logged at DEBUG level only.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        log_object: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_object, ensure_ascii=False)


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger with JSON output to stdout."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Suppress noisy third-party loggers at WARNING
    for noisy in ("uvicorn.access", "httpx", "httpcore", "lancedb"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
