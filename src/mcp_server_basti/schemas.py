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


class Filesystem(TypedDict):
    """Eine Zeile aus ``df -h --output=...``."""

    source: str
    fstype: str
    size: str
    used: str
    avail: str
    pcent: str
    target: str


class DiskStatus(TypedDict):
    """Ergebnis von ``get_disk_status``."""

    filesystems: list[Filesystem]


class GpuStatus(TypedDict):
    """Ergebnis von ``get_gpu_status`` (eine GPU)."""

    driver_version: str
    name: str
    temperature_gpu: str
    utilization_gpu: str
    memory_used: str
    memory_total: str
    pstate: str
    power_limit: str | None
    power_default: str | None
    power_max: str | None


class MemoryStatus(TypedDict):
    """Ergebnis von ``get_memory_status`` (rohe Text-Blöcke, unflexible Formate)."""

    free: str
    zram: str
    swaps: str


class FailedUnits(TypedDict):
    """Ergebnis von ``get_failed_units``."""

    failed: list[str]
    raw: str


class BlameEntry(TypedDict):
    """Eine Zeile aus ``systemd-analyze blame``."""

    unit: str
    time: str


class BootTiming(TypedDict):
    """Ergebnis von ``get_boot_timing``."""

    blame: list[BlameEntry]
    critical_chain: str


class PowerProfile(TypedDict):
    """Ergebnis von ``get_power_profile``."""

    profile: str


class FirewallState(TypedDict):
    """Ergebnis von ``get_firewall_state`` (rohe Text-Blöcke).

    Beide Felder sind rohe Kommando-Outputs (UFW-Status, lauschende Ports).
    Erfordert eine NOPASSWD-sudoers-Regel — siehe
    ``docs/mcp-server/SUDOERS_SETUP.md``.
    """

    ufw: str
    listening_ports: str
