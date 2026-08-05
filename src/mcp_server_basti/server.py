"""Privater FastMCP-Server für lokale Werkzeuge.

Architektur:
- Transport: stdio (fd 0/1), Logging nach stderr (fd 2) — niemals stdout.
- Standalone FastMCP (>=3.0) statt des mcp[cli]-Shims: nur standalone bietet
  ``tags``, ``output_schema``, ``timeout`` und ``run_in_thread``. Tools sind
  sync ``def``; FastMCP lagert sie via ``run_in_thread=True`` in einen
  Threadpool aus, sodass ``asyncio.to_thread`` entfällt.
- Tool-Errors: werden via ``ToolError``-Exception signalisiert.
  Hintergrund: der mcp-lowlevel-Pfad baut Wire-Antworten in
  ``mcp/server/lowlevel/server.py`` — nur Exceptions werden zu
  ``CallToolResult(isError=True)``. Return-Werte werden pauschal mit
  ``isError=False`` gewrappt. Daher raise statt return.
- Pro-Aufruf-Logging ist im ``@with_tool_logging``-Dekorator
  (``instrumentation.py``) gekapselt; die Tool-Body selbst sind reine Logik.
- Alle Tools advertise ``readOnlyHint=True`` und ``tags={"system","read-only"}``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from mcp_server_basti.instrumentation import with_tool_logging
from mcp_server_basti.schemas import (
    BlameEntry,
    BootTiming,
    DiskStatus,
    FailedUnits,
    Filesystem,
    FirewallState,
    GpuStatus,
    MemoryStatus,
    PowerProfile,
    RepoInfo,
    SystemStatus,
)

# Standard-Repository für get_repo_info — wird relativ zu dieser Datei bestimmt.
# (Portabel; kein Env-Override notwendig, da der Server immer im Repo läuft.)
DEFAULT_REPO_PATH = Path(__file__).resolve().parent.parent.parent

mcp = FastMCP("mcp-server-basti")

# Gemeinsame Annotations/Tags für alle read-only-System-Tools.
_READ_ONLY = ToolAnnotations(
    title="Read-only System-Tool",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)
_SYSTEM_TAGS = {"system", "read-only"}
_TOOL_TIMEOUT = 15.0
_SUBPROC_TIMEOUT = 10


def _run(
    argv: list[str],
    *,
    cwd: str | None = None,
    check: bool = True,
    timeout: int = _SUBPROC_TIMEOUT,
) -> subprocess.CompletedProcess[str]:
    """Führt ein Kommando aus; übersetzt Subprocess-Fehler in ToolError.

    Zentraler Helfer, damit die Tool-Body reine Parsing-Logik bleiben.
    """
    try:
        return subprocess.run(
            argv,
            check=check,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
        cmd = " ".join(argv)
        raise ToolError(f"Kommando '{cmd}' fehlgeschlagen: {exc}") from exc


@mcp.tool(
    tags=_SYSTEM_TAGS,
    annotations=_READ_ONLY,
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def get_system_status() -> SystemStatus:
    """Gibt den aktuellen Systemstatus aus dem Programm ``uptime`` zurück."""
    try:
        result = subprocess.run(
            ["uptime"],
            check=True,
            capture_output=True,
            text=True,
            timeout=_SUBPROC_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
        raise ToolError(f"Systemstatus konnte nicht ermittelt werden: {exc}") from exc
    return SystemStatus(uptime=result.stdout)


@mcp.tool(
    tags={"system", "smoke-test"},
    annotations=ToolAnnotations(
        title="Echo (Smoke-Test)",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def echo_tool(text: str) -> str:
    """Gibt den übergebenen Text unverändert zurück.

    Nützlich als Health-Check und zum Testen der stdio-Verbindung.
    """
    # Bewusst roher str (kein Schema) — Health-Check muss beliebigen Text
    # inkl. Leer/Unicode unverändert round-tripen.
    return text


@mcp.tool(
    tags=_SYSTEM_TAGS,
    annotations=_READ_ONLY,
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def get_repo_info() -> RepoInfo:
    """Gibt den aktuellen Git-Branch und den letzten Commit des Server-Repos zurück."""
    try:
        # symbolic-ref --short gibt im detached-HEAD-State non-zero zurück,
        # sodass wir die echte Detached-Branch erkennen können.
        branch_proc = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=_SUBPROC_TIMEOUT,
            cwd=str(DEFAULT_REPO_PATH),
        )
        detached = branch_proc.returncode != 0
        if not detached:
            branch = branch_proc.stdout.strip()
        else:
            # Detached HEAD — symbolic-ref schlägt fehl, fallback auf rev-parse.
            short_sha = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                timeout=_SUBPROC_TIMEOUT,
                cwd=str(DEFAULT_REPO_PATH),
            ).stdout.strip()
            branch = f"detached@{short_sha}"

        last_commit = subprocess.run(
            ["git", "log", "-1", "--oneline"],
            check=True,
            capture_output=True,
            text=True,
            timeout=_SUBPROC_TIMEOUT,
            cwd=str(DEFAULT_REPO_PATH),
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
        raise ToolError(
            f"Repository-Informationen konnten nicht ermittelt werden: {exc}"
        ) from exc

    return RepoInfo(branch=branch, last_commit=last_commit, detached=detached)


@mcp.tool(
    tags=_SYSTEM_TAGS,
    annotations=_READ_ONLY,
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def get_disk_status() -> DiskStatus:
    """Liefert Belegung aller Dateisysteme (``df -h``).

    /mnt/DATA ist auf dieser Workstation kritisch (95%+); das Tool macht keine
    teure ``du``-Analyse der Home-Consumer (zu langsam für ein MCP-Tool) — dafür
    gibt es ``yuno-cleaner scan``.
    """
    proc = _run(
        ["df", "-h", "--output=source,fstype,size,used,avail,pcent,target"],
        check=False,
    )
    filesystems: list[Filesystem] = []
    lines = proc.stdout.splitlines()
    # Erste Zeile ist der Header von df --output.
    for line in lines[1:]:
        parts = line.split()
        if len(parts) != 7:
            continue
        filesystems.append(
            Filesystem(
                source=parts[0],
                fstype=parts[1],
                size=parts[2],
                used=parts[3],
                avail=parts[4],
                pcent=parts[5],
                target=parts[6],
            )
        )
    return DiskStatus(filesystems=filesystems)


@mcp.tool(
    tags=_SYSTEM_TAGS,
    annotations=_READ_ONLY,
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def get_gpu_status() -> GpuStatus:
    """Liefert NVIDIA GPU-Status (Treiber, Temp, Auslastung, VRAM, Power-Limits).

    Verwendet ``nvidia-smi`` (NVML-Pfad, funktioniert unter Wayland). power_limit/
    power_default/power_max sind ``None`` falls der POWER-Abschnitt nicht auslesbar ist.
    """
    proc = _run(
        [
            "nvidia-smi",
            (
                "--query-gpu=driver_version,name,temperature.gpu,"
                "utilization.gpu,memory.used,memory.total,pstate"
            ),
            "--format=csv,noheader,nounits",
        ],
    )
    fields = [f.strip() for f in proc.stdout.strip().split(",")]
    if len(fields) < 7:
        raise ToolError(
            f"nvidia-smi lieferte unerwartetes Format: {proc.stdout!r}"
        )

    power_limit = power_default = power_max = None
    power_proc = _run(["nvidia-smi", "-q", "-d", "POWER"], check=False)
    for line in power_proc.stdout.splitlines():
        stripped = line.strip()
        # nvidia-smi listet pro GPU einen Abschnitt; bei mehreren GPUs gewinnt
        # der erste Abschnitt (GPU 0) — später Abschnitte (iGPU, oft N/A) nicht
        # überschreiben. "Current Power Limit" ist der Live-Wert.
        value = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
        if stripped.startswith("Current Power Limit") and power_limit is None:
            power_limit = value
        elif stripped.startswith("Default Power Limit") and power_default is None:
            power_default = value
        elif stripped.startswith("Max Power Limit") and power_max is None:
            power_max = value

    return GpuStatus(
        driver_version=fields[0],
        name=fields[1],
        temperature_gpu=fields[2],
        utilization_gpu=fields[3],
        memory_used=fields[4],
        memory_total=fields[5],
        pstate=fields[6],
        power_limit=power_limit,
        power_default=power_default,
        power_max=power_max,
    )


@mcp.tool(
    tags=_SYSTEM_TAGS,
    annotations=_READ_ONLY,
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def get_memory_status() -> MemoryStatus:
    """Liefert RAM/Swap-Belegung (``free -h``), zram und Swaps als rohe Text-Blöcke."""
    free = _run(["free", "-h"]).stdout
    zram = _run(["zramctl"], check=False).stdout
    swaps = _run(["swapon", "--show"], check=False).stdout
    return MemoryStatus(free=free, zram=zram, swaps=swaps)


@mcp.tool(
    tags=_SYSTEM_TAGS,
    annotations=_READ_ONLY,
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def get_failed_units() -> FailedUnits:
    """Liefert fehlgeschlagene systemd-Units (``systemctl --failed``).

    systemctl beendet non-zero, falls Units fehlgeschlagen sind — das ist für
    uns kein Fehler, sondern genau der zu reportende Zustand.
    """
    proc = _run(["systemctl", "--failed", "--no-pager"], check=False)
    failed: list[str] = []
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("UNIT"):
            continue
        # Überspringe die Summary-Zeile ("N loaded units listed.") — echte
        # Unit-Namen enthalten immer ein Suffix wie .service/.mount/.timer.
        first = stripped.split()[0]
        if "." in first:
            failed.append(first)
    return FailedUnits(failed=failed, raw=proc.stdout)


@mcp.tool(
    tags=_SYSTEM_TAGS,
    annotations=_READ_ONLY,
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def get_kernel_warnings() -> str:
    """Liefert Kernel-Warning-Logs des aktuellen Boot (``journalctl -b -p warning``).

    Bewusst roher Text — journalctl parsen ist fragil (Timestamps, multiline
    Stack-Traces, PAM-Rauschen). Clients filtern selbst.
    """
    proc = _run(["journalctl", "-b", "-p", "warning", "--no-pager"], check=False)
    return proc.stdout


@mcp.tool(
    tags=_SYSTEM_TAGS,
    annotations=_READ_ONLY,
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def get_boot_timing() -> BootTiming:
    """Liefert Boot-Timing (``systemd-analyze blame`` + ``critical-chain``)."""
    blame_proc = _run(["systemd-analyze", "blame", "--no-pager"], check=False)
    blame: list[BlameEntry] = []
    for line in blame_proc.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=1)
        if len(parts) == 2:
            blame.append(BlameEntry(time=parts[0], unit=parts[1]))

    chain_proc = _run(
        ["systemd-analyze", "critical-chain", "--no-pager"], check=False
    )
    return BootTiming(blame=blame, critical_chain=chain_proc.stdout)


@mcp.tool(
    tags=_SYSTEM_TAGS,
    annotations=_READ_ONLY,
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def get_power_profile() -> PowerProfile:
    """Liefert den aktiven power-profiles-daemon Modus (``powerprofilesctl get``)."""
    proc = _run(["powerprofilesctl", "get"])
    return PowerProfile(profile=proc.stdout.strip())


# Absolute Pfade für die sudoers-geschützten Firewall-Kommandos.
# sudoers matcht auf argv[0]; Pfade sind host-verifiziert (command -v ufw ss).
_UFW_BIN = "/usr/sbin/ufw"
_SS_BIN = "/usr/bin/ss"


@mcp.tool(
    tags={"security", "read-only"},
    annotations=ToolAnnotations(
        title="Firewall-Status (UFW + lauschende Ports)",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def get_firewall_state() -> FirewallState:
    """Liefert UFW-Status und lauschende TCP-Ports.

    Erfordert eine NOPASSWD-sudoers-Regel für ``ufw status verbose`` und
    ``ss -tlnp`` (root-only). Ohne die Regel degradiert der Tool sauber zu
    einem ToolError, der auf ``docs/mcp-server/SUDOERS_SETUP.md`` verweist —
    kein stiller Partial-Result. Siehe SUDOERS_SETUP.md für die Installation.
    """
    out: dict[str, str] = {}
    commands: dict[str, list[str]] = {
        "ufw": ["sudo", "-n", "--", _UFW_BIN, "status", "verbose"],
        "listening_ports": ["sudo", "-n", "--", _SS_BIN, "-tlnp"],
    }
    for key, argv in commands.items():
        try:
            proc = subprocess.run(
                argv,
                check=True,
                capture_output=True,
                text=True,
                timeout=_SUBPROC_TIMEOUT,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").lower()
            # sudo -n scheitert non-zero, wenn ein Passwort nötig wäre.
            if "password" in stderr or "a password is needed" in stderr:
                raise ToolError(
                    "get_firewall_state benötigt eine NOPASSWD-sudoers-Regel "
                    "(siehe docs/mcp-server/SUDOERS_SETUP.md). "
                    f"Kommando: {' '.join(argv)}"
                ) from exc
            raise ToolError(
                f"Firewall-Status konnte nicht ermittelt werden "
                f"({' '.join(argv)}): {exc.stderr or exc}"
            ) from exc
        except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
            raise ToolError(
                f"Firewall-Status konnte nicht ermittelt werden: {exc}"
            ) from exc
        out[key] = proc.stdout
    return FirewallState(ufw=out["ufw"], listening_ports=out["listening_ports"])


def main() -> None:
    """Startet den lokalen MCP-Server über den stdio-Transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
