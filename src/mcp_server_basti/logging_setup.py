"""Strukturiertes JSON-Logging für den lokalen MCP-Server."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Formatiert jeden LogRecord als eine einzelne JSON-Zeile."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "connection_id": getattr(record, "connection_id", None),
            "tool_name": getattr(record, "tool_name", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "is_error": getattr(record, "is_error", record.levelno >= logging.ERROR),
        }
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_json_logging() -> logging.Logger:
    """Konfiguriert den Server-Logger einmalig auf INFO und stdout."""
    logger = logging.getLogger("mcp_server_basti")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Vorhandene Handler werden ersetzt, damit Reloads keine Duplikate erzeugen.
    logger.handlers.clear()
    # WICHTIG: MCP stdio-Transport nutzt stdout (fd 1) exklusiv für JSON-RPC-Frames.
    # Logging nach stdout würde die Frames verfälschen → stderr (fd 2) verwenden.
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.INFO)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger


LOGGER = setup_json_logging()
