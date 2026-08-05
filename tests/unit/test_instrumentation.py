"""Unit-Tests für den @with_tool_logging-Dekorator.

Verifiziert, dass der Dekorator tool_call_start + tool_call_success/error
emittiert, duration_ms nicht-negativ ist und die Fehlerpfad re-raised.
"""

from __future__ import annotations

import logging

import pytest

from mcp_server_basti.instrumentation import with_tool_logging
from mcp_server_basti.logging_setup import LOGGER


@pytest.fixture(autouse=True)
def _capture_logs(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Lenkt den Server-Logger auf caplog um (LOGGER.propagate=False sonst)."""
    LOGGER.addHandler(caplog.handler)
    caplog.set_level(logging.INFO, logger="mcp_server_basti")
    yield caplog
    LOGGER.removeHandler(caplog.handler)


def test_success_logs_start_and_success(caplog: pytest.LogCaptureFixture) -> None:
    """Happy-Path: genau ein start- und ein success-Event."""

    @with_tool_logging()
    def add(a: int, b: int) -> int:
        return a + b

    add(2, 3)
    msgs = [r.getMessage() for r in caplog.records]
    assert "tool_call_start" in msgs
    assert "tool_call_success" in msgs
    assert "tool_call_error" not in msgs


def test_success_duration_is_non_negative(caplog: pytest.LogCaptureFixture) -> None:
    """duration_ms im success-Event ist ein nicht-negativer float."""

    @with_tool_logging()
    def noop() -> None:
        return None

    noop()
    success_records = [r for r in caplog.records if r.getMessage() == "tool_call_success"]
    assert success_records, "Kein tool_call_success-Event"
    duration = success_records[0].duration_ms
    assert isinstance(duration, float)
    assert duration >= 0.0


def test_error_path_reraises_and_logs_error(caplog: pytest.LogCaptureFixture) -> None:
    """Fehler im Tool-Body wird re-raised und als tool_call_error geloggt."""

    class _BoomError(Exception):
        pass

    @with_tool_logging()
    def boom() -> None:
        raise _BoomError("kaputt")

    with pytest.raises(_BoomError):
        boom()
    msgs = [r.getMessage() for r in caplog.records]
    assert "tool_call_start" in msgs
    assert "tool_call_error" in msgs
    assert "tool_call_success" not in msgs
    error_records = [r for r in caplog.records if r.getMessage() == "tool_call_error"]
    assert error_records[0].is_error is True


def test_tool_name_defaults_to_function_name(caplog: pytest.LogCaptureFixture) -> None:
    """Ohne expliziten Namen nutzt der Dekorator fn.__name__."""

    @with_tool_logging()
    def my_special_tool() -> int:
        return 42

    my_special_tool()
    start_records = [r for r in caplog.records if r.getMessage() == "tool_call_start"]
    assert start_records[0].tool_name == "my_special_tool"


def test_explicit_tool_name_overrides(caplog: pytest.LogCaptureFixture) -> None:
    """tool_name= überschreibt den Funktionsnamen im Log-Kontext."""

    @with_tool_logging("custom-name")
    def fn() -> None:
        return None

    fn()
    start_records = [r for r in caplog.records if r.getMessage() == "tool_call_start"]
    assert start_records[0].tool_name == "custom-name"
