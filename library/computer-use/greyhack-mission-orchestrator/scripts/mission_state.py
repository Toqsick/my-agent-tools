"""
mission_state.py — State-Machine und Hilfsfunktionen für GreyHack-Missionen

Definiert Mission-Phasen, Step-Transitionen und Validierungs-Logik.
Wird vom Orchestrator verwendet, um den aktuellen Spielzustand zu erkennen.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class GameState(Enum):
    """Mögliche Grey-Hack-Spielzustände."""
    UNKNOWN = "unknown"
    LOGIN_SCREEN = "login_screen"
    CITY_MAP = "city_map"
    ROUTER_VIEW = "router_view"
    MAILBOX_VIEW = "mailbox_view"
    FILE_BROWSER = "file_browser"
    TERMINAL = "terminal"
    DIALOG_OPEN = "dialog_open"
    PERMISSION_DIALOG = "permission_dialog"
    LOADING = "loading"
    ERROR_SCREEN = "error_screen"


class MissionStatus(Enum):
    """Status einer Mission im Orchestrator."""
    INIT = "init"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETE = "complete"
    FAILED = "failed"
    KILLED = "killed"


@dataclass
class MissionStep:
    """Ein einzelner Schritt in einer Mission."""
    index: int
    description: str
    expected_state: GameState
    action_type: str  # "type_greyhack", "click", "wait", "verify"
    action_params: dict = field(default_factory=dict)
    max_attempts: int = 3
    timeout_seconds: float = 30.0
    post_condition: Optional[str] = None


@dataclass
class Mission:
    """Eine vollständige GreyHack-Mission."""
    name: str
    target: str
    priority: str
    steps: list[MissionStep]
    status: MissionStatus = MissionStatus.READY
    current_step_index: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def advance(self) -> bool:
        """Setzt die Mission einen Schritt weiter. Returns True wenn fertig."""
        self.current_step_index += 1
        return self.current_step_index >= len(self.steps)

    @property
    def current_step(self) -> Optional[MissionStep]:
        """Gibt den aktuellen Schritt zurück, oder None wenn fertig."""
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def progress_percent(self) -> float:
        """Fortschritt in Prozent (0-100)."""
        if not self.steps:
            return 100.0
        return (self.current_step_index / len(self.steps)) * 100


def detect_state_from_ocr(ocr_text: str) -> GameState:
    """Versucht, aus OCR-Text den aktuellen Spielzustand zu erkennen.

    Priorisiert spezifische States vor generischen (z.B. Permission-Dialog
    vor Login-Screen, da "password" in beiden vorkommen kann).
    """
    text_lower = ocr_text.lower()

    # Priorisierte Reihenfolge: SPECIFIC → GENERIC
    state_indicators = [
        (GameState.PERMISSION_DIALOG, ["allow", "deny", "permission", "sudo", "authentication required"]),
        (GameState.LOADING, ["loading", "please wait"]),
        (GameState.ERROR_SCREEN, ["error", "failed", "crash"]),
        (GameState.ROUTER_VIEW, ["router", "ssid", "wifi password", "network"]),
        (GameState.MAILBOX_VIEW, ["inbox", "compose", "subject:", "from:"]),
        (GameState.FILE_BROWSER, ["folder", "directory", "/home/", "/usr/"]),
        (GameState.TERMINAL, ["shell.build", "command:", "$ "]),
        (GameState.CITY_MAP, ["city map", "location:", "travel to", "bank", "shop"]),
        (GameState.LOGIN_SCREEN, ["username", "login", "sign in"]),  # "password" entfernt — zu generisch
        (GameState.DIALOG_OPEN, ["[ok]", "[cancel]", "[yes]", "[no]"]),
    ]

    for state, indicators in state_indicators:
        if any(ind in text_lower for ind in indicators):
            return state

    return GameState.UNKNOWN


def create_sample_mission(target: str = "Reraldi@adahidomev.net") -> Mission:
    """Erstellt eine Beispiel-Mission für Tests."""
    return Mission(
        name=f"Mission: {target}",
        target=target,
        priority="P0",
        steps=[
            MissionStep(
                index=1,
                description="Connect zur Ziel-IP",
                expected_state=GameState.TERMINAL,
                action_type="type_greyhack",
                action_params={"file": "/home/bratan/10-Projekte/10-active/greyhack-tools/src/tools/portscan.src"},
            ),
            MissionStep(
                index=2,
                description="Portscan auf Standard-Ports",
                expected_state=GameState.ROUTER_VIEW,
                action_type="wait",
                action_params={"seconds": 5.0},
            ),
            MissionStep(
                index=3,
                description="SMTP-Enum um offene Mailbox zu finden",
                expected_state=GameState.MAILBOX_VIEW,
                action_type="click_and_verify",
                action_params={"element_index": 0, "expected_text": "smtp"},
            ),
            MissionStep(
                index=4,
                description="Daten extrahieren",
                expected_state=GameState.FILE_BROWSER,
                action_type="type_greyhack",
                action_params={"file": "/path/to/extract_tool.src"},
            ),
        ],
    )