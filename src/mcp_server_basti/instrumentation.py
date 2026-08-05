"""Strukturierte pro-Aufruf-Instrumentierung für die basti-Tools.

Kapselt das Logging-Boilerplate (request_id, started_at, tool_call_start,
tool_call_success/error), das zuvor in jedem Tool inline stand. Die Tools
selbst bleiben reine Business-Logik und heben nur noch ``ToolError``.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar
from uuid import uuid4

from mcp_server_basti.logging_setup import LOGGER

if TYPE_CHECKING:
    from collections.abc import Mapping

CONNECTION_ID = "local-stdio"

P = ParamSpec("P")
R = TypeVar("R")


def _log_context(
    tool_name: str,
    request_id: str,
    **extra: Any,
) -> dict[str, Any]:
    """Erzeugt die gemeinsamen strukturierten Felder für einen Tool-Aufruf."""
    return {
        "request_id": request_id,
        "connection_id": CONNECTION_ID,
        "tool_name": tool_name,
        **extra,
    }


def _log_completion(
    tool_name: str,
    request_id: str,
    started_at: float,
    is_error: bool,
) -> float:
    """Loggt tool_call_success/error mit Duration und gibt duration_ms zurück."""
    duration_ms = round((time.perf_counter() - started_at) * 1000, 3)
    log_method = LOGGER.error if is_error else LOGGER.info
    log_method(
        "tool_call_error" if is_error else "tool_call_success",
        extra=_log_context(
            tool_name,
            request_id,
            duration_ms=duration_ms,
            is_error=is_error,
        ),
    )
    return duration_ms


def with_tool_logging(
    tool_name: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Dekorator: emit tool_call_start/success/error um einen (sync) Tool-Body.

    Die gewrappte Funktion darf ``ToolError`` raisen — der Dekorator loggt die
    Fehler-Duration und re-raised (damit die FastMCP-Schicht es zu isError macht).
    """

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        name = tool_name or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            request_id = str(uuid4())
            started_at = time.perf_counter()
            LOGGER.info("tool_call_start", extra=_log_context(name, request_id))
            try:
                result = fn(*args, **kwargs)
            except BaseException:
                _log_completion(name, request_id, started_at, is_error=True)
                raise
            _log_completion(name, request_id, started_at, is_error=False)
            return result

        return wrapper

    return decorator


def log_context(tool_name: str, request_id: str, **extra: Any) -> Mapping[str, Any]:
    """Öffentlicher Alias für ``_log_context`` (für externe Aufrufer)."""
    return _log_context(tool_name, request_id, **extra)
