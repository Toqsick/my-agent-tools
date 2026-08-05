"""Strukturierte Rückgabe-Schemata (TypedDicts) für die basti-Tools.

Alle Tools, die mehr als einen freien Text-String zurückgeben, nutzen hier
definierte TypedDicts. FastMCP leitet das JSON-Schema automatisch vom
Rückgabe-Typ ab; explizites ``output_schema=`` wird nur gesetzt, wo ein
strikteres ``additionalProperties: False`` gewünscht ist.
"""

from __future__ import annotations

from typing import TypedDict


class SystemStatus(TypedDict):
    """Ergebnis von ``get_system_status`` (``uptime``-Output)."""

    uptime: str


class RepoInfo(TypedDict):
    """Ergebnis von ``get_repo_info``."""

    branch: str
    last_commit: str
    detached: bool
