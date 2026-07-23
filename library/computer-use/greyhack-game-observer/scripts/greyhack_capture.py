"""
greyhack_capture.py — Observer-Tick für Grey Hack Sessions

Nimmt einen Screenshot des Grey Hack Fensters via cua-driver auf,
extrahiert Text via Tesseract OCR und persistiert das Ergebnis
als Markdown in den Obsidian Vault.

Verwendung:
    python3 greyhack_capture.py [interval_in_seconds]
    # Default: 5.0 Sekunden, Ctrl+C zum Beenden
"""

import os
import sys
import time
import subprocess
import datetime
import argparse
from pathlib import Path


VAULT_CAPTURE_DIR = Path(
    "/home/bratan/Dokumente/Obsidian Vault/99 Capture"
)
TEMP_SCREENSHOT_DIR = Path("/tmp/greyhack_observer")
TESSERACT_LANG = "eng"
TESSERACT_PSM = "6"  # Assume uniform block of text (GreyHack Konsole)


def ensure_dirs() -> None:
    """Stellt sicher, dass Output-Verzeichnisse existieren."""
    VAULT_CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def capture_screenshot(app: str = "steam") -> bytes:
    """Screenshot via cua-driver CLI im Hintergrund ohne Focus-Klau.

    Versucht zuerst cua-driver (mit Display-Env), dann Fallback-Tools.
    """
    import base64
    import json

    # Display-Env-Vars setzen (Xwayland-Verbindung)
    env = os.environ.copy()
    env["DISPLAY"] = ":1"
    env["XAUTHORITY"] = "/run/user/1000/.mutter-Xwaylandauth.L8U0R3"

    # 1. Versuche cua-driver call get_window_state
    try:
        # Finde PID der App
        result = subprocess.run(
            ["pgrep", "-f", app],
            capture_output=True, text=True, timeout=5, env=env
        )
        pids = [p for p in result.stdout.strip().split("\n") if p.isdigit()]

        if pids:
            pid = int(pids[0])
            # Hole Window-State via cua-driver
            cua_result = subprocess.run(
                ["cua-driver", "call", "get_window_state", json.dumps({"pid": pid})],
                capture_output=True, text=True, env=env, timeout=20
            )
            if cua_result.returncode == 0:
                data = json.loads(cua_result.stdout)
                # Suche nach Screenshot (base64-encoded PNG)
                screenshot_b64 = data.get("screenshot_base64") or data.get("screenshot")
                if screenshot_b64:
                    return base64.b64decode(screenshot_b64)
                # Oder: screenshot_file_path (Datei-basiert)
                screenshot_path = data.get("screenshot_file_path")
                if screenshot_path and os.path.exists(screenshot_path):
                    return Path(screenshot_path).read_bytes()
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
        pass

    # 2. Fallback: scrot mit Display-Env
    tmp_path = Path("/tmp/greyhack_observer_fallback.png")
    for cmd in [
        ["scrot", str(tmp_path)],
        ["gnome-screenshot", "-f", str(tmp_path)],
        ["grim", str(tmp_path)],
    ]:
        try:
            subprocess.run(cmd, check=True, timeout=5, env=env)
            if tmp_path.exists():
                return tmp_path.read_bytes()
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    # 3. Letzter Fallback: Klare Fehlermeldung
    raise RuntimeError(
        "Kein Screenshot-Tool verfügbar! Installiere:\n"
        "  sudo apt install scrot        # X11\n"
        "  sudo apt install gnome-screenshot\n"
        "Oder stelle sicher, dass DISPLAY=:1 und XAUTHORITY korrekt gesetzt sind."
    )


def ocr_extract(image_bytes: bytes) -> str:
    """Tesseract-OCR auf ein Bild anwenden."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    image_path = TEMP_SCREENSHOT_DIR / f"capture_{timestamp}.png"
    image_path.write_bytes(image_bytes)

    try:
        result = subprocess.run(
            [
                "tesseract",
                str(image_path),
                "-",
                "-l", TESSERACT_LANG,
                "--psm", TESSERACT_PSM,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        return "[OCR-FEHLER: Tesseract nicht installiert!]"
    except subprocess.TimeoutExpired:
        return "[OCR-FEHLER: Timeout]"


def build_capture_markdown(
    session_id: str,
    timestamp: str,
    screenshot_path: Path,
    ocr_text: str,
) -> str:
    """Baut die Vault-Markdown-Datei für diesen Tick."""
    return f"""---
tags: [capture, greyhack, computer-use]
session-id: {session_id}
captured-at: {timestamp}
stimmung: gameplay-dokumentation
quelle: greyhack-game-observer (Computer Use)
---

# 🎮 GreyHack Capture — {timestamp}

> **Snapshot-Modus:** Observer (passive Mitschrift)
> **Spiel-Fenster:** steam / Grey Hack
> **OCR-Engine:** Tesseract ({TESSERACT_LANG}, psm {TESSERACT_PSM})
> **Session-ID:** {session_id}

## 📺 Screenshot

![GreyHack Snapshot]({screenshot_path})

## 📝 OCR-Extrahierter Text

```
{ocr_text}
```

## 🧠 Kontextuelle Notizen

<!-- Yuno / Orchestrator: Hier können automatische Notizen eingefügt werden -->
- **Erkannte UI-Elemente**: Siehe Screenshot
- **Verbindet zu**: [[GreyHack - Werkzeugkasten & Patterns]], [[Queen-Bee-Lab - GreyHack-Tests]]

## Verbindet zu

- [[MOC - Gaming-Performance]] — Gaming-Hub
- [[System - Skill-Tool-ComputerUse-Strategie]] — Strategie-Dokument
- [[greyhack-smart-macro]] — Nächste Stufe: Aktionen
"""


def capture_session_tick(session_id: str = None) -> str:
    """Einen Observer-Tick ausführen."""
    session_id = session_id or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Schicht 1: Capture
    screenshot_bytes = capture_screenshot(app="steam")
    screenshot_filename = f"greyhack_{session_id}.png"
    screenshot_path = TEMP_SCREENSHOT_DIR / screenshot_filename
    screenshot_path.write_bytes(screenshot_bytes)

    # Schicht 2: OCR
    ocr_text = ocr_extract(screenshot_bytes)

    # Schicht 3: Vault-Persistenz
    capture_file = VAULT_CAPTURE_DIR / f"{timestamp[:10]}_GreyHack_{session_id}.md"
    md_content = build_capture_markdown(
        session_id, timestamp, screenshot_path, ocr_text
    )
    capture_file.write_text(md_content, encoding="utf-8")

    return str(capture_file)


def main():
    parser = argparse.ArgumentParser(description="GreyHack Game Observer")
    parser.add_argument(
        "interval",
        nargs="?",
        type=float,
        default=5.0,
        help="Intervall zwischen Snapshots in Sekunden (default: 5.0)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Nur einen einzelnen Tick ausführen und beenden",
    )
    args = parser.parse_args()

    ensure_dirs()

    if args.once:
        result = capture_session_tick()
        print(f"✅ Einmal-Snapshot: {result}")
        return

    print(f"🔍 Observer startet (Intervall: {args.interval}s, Ctrl+C zum Beenden)")
    try:
        while True:
            tick_result = capture_session_tick()
            print(f"  ✓ Tick: {tick_result}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n🛑 Observer gestoppt.")


if __name__ == "__main__":
    main()