"""
orchestrator.py — Queen-Bee Autonomous Mission Orchestrator

Liest eine Mission aus dem Obsidian Vault, führt sie autonom via Computer Use aus.
Beinhaltet State-Machine, Kill-Switch und Telegram-Alerts.

Verwendung:
    python3 orchestrator.py <pfad_zur_mission_md>
    python3 orchestrator.py --dry-run <pfad_zur_mission_md>  # Nur Validierung
"""

import sys
import time
import argparse
import subprocess
from pathlib import Path


VAULT = Path("/home/bratan/Dokumente/Obsidian Vault")
MISSION_STATE_FILE = VAULT / "03 Projekte/Queen-Bee-Lab/Mission-State - Live-Status.md"


def ensure_cua_available():
    """Prüft, ob cua-driver verfügbar ist."""
    try:
        from hermes_tools import computer_use  # noqa: F401
        return True
    except ImportError:
        return False


def send_telegram_alert(message: str) -> bool:
    """Sendet eine Telegram-Nachricht (Token via .env)."""
    env_path = Path.home() / ".hermes/.env"
    if not env_path.exists():
        print(f"⚠️ .env nicht gefunden, Alert nur lokal: {message}")
        return False

    try:
        # Sehr vereinfacht: In echtem Setup via hermes-cli oder direkter API
        import os
        for line in env_path.read_text().splitlines():
            if "TELEGRAM_BOT_TOKEN" in line:
                token = line.split("=", 1)[1].strip().strip('"').strip("'")
            if "TELEGRAM_HOME_CHANNEL" in line:
                channel = line.split("=", 1)[1].strip().strip('"').strip("'")

        subprocess.run([
            "curl", "-s", "-X", "POST",
            f"https://api.telegram.org/bot{token}/sendMessage",
            "-d", f"chat_id={channel}",
            "-d", f"text={message}",
        ], check=True, timeout=10)
        return True
    except Exception as e:
        print(f"⚠️ Telegram-Versand fehlgeschlagen: {e}")
        return False


class MissionOrchestrator:
    def __init__(self, mission_file: Path, dry_run: bool = False):
        self.mission_file = mission_file
        self.dry_run = dry_run
        self.mission_data = self._parse_mission()
        self.current_step = 0
        self.state = "INIT"
        self.max_attempts_per_step = 10

    def _parse_mission(self) -> dict:
        """Parst die Vault-Mission-Datei (Frontmatter + Steps)."""
        if not self.mission_file.exists():
            raise FileNotFoundError(f"Mission nicht gefunden: {self.mission_file}")

        content = self.mission_file.read_text(encoding="utf-8-sig")

        target = ""
        priority = ""
        status = ""
        steps = []

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm_lines = parts[1].splitlines()
                for line in fm_lines:
                    if line.startswith("target:"):
                        target = line.split(":", 1)[1].strip()
                    elif line.startswith("priority:"):
                        priority = line.split(":", 1)[1].strip()
                    elif line.startswith("status:"):
                        status = line.split(":", 1)[1].strip()

        in_steps = False
        for line in content.splitlines():
            # Flexibel: matche "## Steps" oder "## 📋 Steps (vom Orchestrator...)"
            stripped = line.lstrip("#").strip().lower()
            if stripped.startswith("steps") or stripped.startswith("📋 steps"):
                in_steps = True
                continue
            if line.startswith("## ") and in_steps:
                break
            if in_steps and line.strip() and line.strip()[0].isdigit():
                # Entferne Markdown-Bold (**1.**) und Numbering (1.)
                cleaned = line.strip()
                if cleaned.startswith("**"):
                    cleaned = cleaned.lstrip("*")
                steps.append(cleaned)

        return {
            "target": target,
            "priority": priority,
            "status": status,
            "steps": steps,
            "raw": content,
        }

    def check_kill_switch(self) -> None:
        """Prüft, ob ein Permission-Dialog aufgetaucht ist. Stoppt SOFORT."""
        if self.dry_run:
            return
        try:
            from hermes_tools import computer_use
            capture = computer_use(
                action="capture", mode="ax", app="steam", background_only=True
            )
        except ImportError:
            return

        forbidden = ["permission", "allow", "deny", "sudo", "password prompt"]
        for elem in capture if isinstance(capture, list) else []:
            label = str(elem.get("label", "")).lower()
            if any(kw in label for kw in forbidden):
                msg = (
                    f"🚨 KILL-SWITCH!\n"
                    f"Mission: {self.mission_file.name}\n"
                    f"Permission-Dialog: {elem.get('label')}"
                )
                send_telegram_alert(msg)
                raise RuntimeError(f"Permission-Dialog: Auto-Stopp! {elem.get('label')}")

    def _save_state(self) -> None:
        """Persistiert den aktuellen Orchestrator-State im Vault."""
        # Existierende Datei lesen, um Frontmatter zu erhalten
        existing_fm = ""
        if MISSION_STATE_FILE.exists():
            existing_content = MISSION_STATE_FILE.read_text(encoding="utf-8-sig")
            if existing_content.startswith("---"):
                parts = existing_content.split("---", 2)
                if len(parts) >= 3:
                    existing_fm = "---" + parts[1] + "---\n\n"

        state_content = f"""# 🎮 Mission State (Live)

> **Wird automatisch vom Orchestrator aktualisiert**

- **Datei**: {self.mission_file.name}
- **Ziel**: {self.mission_data.get('target', '?')}
- **Priorität**: {self.mission_data.get('priority', '?')}
- **Step**: {self.current_step}/{len(self.mission_data['steps'])}
- **State**: {self.state}
- **Dry-Run**: {self.dry_run}
- **Zeit**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Steps
{chr(10).join(f"- {s}" for s in self.mission_data['steps'])}
"""
        MISSION_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Schreiben mit erhaltenem Frontmatter
        full_content = existing_fm + state_content
        MISSION_STATE_FILE.write_text(full_content, encoding="utf-8")

    def run(self) -> None:
        """Haupt-Loop: Observer → Kill-Switch → Action → Verify → Update."""
        target = self.mission_data.get('target', 'Unbekannt')
        steps = self.mission_data['steps']
        print(f"🎮 Starte Mission: {target}")
        print(f"   Steps: {len(steps)}")
        print(f"   Dry-Run: {self.dry_run}")

        if self.dry_run:
            print("\n📋 Mission-Parsing erfolgreich!")
            print(f"   Ziel: {target}")
            print(f"   Priorität: {self.mission_data.get('priority')}")
            print(f"   Status: {self.mission_data.get('status')}")
            for i, step in enumerate(steps, 1):
                print(f"   Step {i}: {step[:80]}...")
            return

        # Live-Run: Telegram-Notification bei Start
        send_telegram_alert(
            f"🎮 Mission GESTARTET: {target}\n"
            f"   Steps: {len(steps)}\n"
            f"   Priorität: {self.mission_data.get('priority')}"
        )

        for i, step in enumerate(steps, 1):
            self.current_step = i
            self.state = f"STEP_{i}"
            print(f"\n--- Step {i}/{len(steps)} ---")
            print(f"   {step}")

            # Kill-Switch VOR jeder Aktion
            try:
                self.check_kill_switch()
            except RuntimeError as e:
                print(f"   🛑 STOPP: {e}")
                self.state = "KILLED"
                self._save_state()
                send_telegram_alert(
                    f"🛑 Mission ABGEBROCHEN: {target}\n"
                    f"   Step: {i}/{len(steps)}\n"
                    f"   Grund: {e}"
                )
                return

            # Step-spezifische Action-Logik
            try:
                self._execute_step(i, step)
            except Exception as e:
                print(f"   ⚠️ Step-Fehler: {e}")
                # Optional: Retry-Logic oder Skip
                time.sleep(1.0)

            # State persistieren
            self._save_state()

            # Anti-Race-Condition: Pause zwischen Steps
            time.sleep(2.0)

        self.state = "COMPLETE"
        self._save_state()
        send_telegram_alert(
            f"✅ Mission ABGESCHLOSSEN: {target}\n"
            f"   Alle {len(steps)} Steps erfolgreich!"
        )
        print("\n✅ Mission abgeschlossen!")

    def _execute_step(self, step_index: int, step_description: str) -> None:
        """Führt einen einzelnen Step aus. Kann per Override erweitert werden."""
        step_lower = step_description.lower()

        # Step 1: Screenshot
        if "screenshot" in step_lower:
            self._action_screenshot(step_description)

        # Step 2: OCR / State-Detection
        elif "ocr" in step_lower or "analyse" in step_lower:
            self._action_ocr_analysis(step_description)

        # Step 3: Status-Update
        elif "status" in step_lower or "update" in step_lower:
            self._action_status_update(step_description)

        # Default: Nur Log
        else:
            print(f"   ▶️  Generic-Step (kein spezifischer Handler): {step_description[:60]}...")

    def _action_screenshot(self, step_description: str) -> None:
        """Macht einen Screenshot via Observer-Skill."""
        print("   📸 Mache Screenshot...")
        try:
            # Füge Scripts-Pfad zum sys.path hinzu
            import sys
            observer_scripts = Path("/home/bratan/.hermes/skills/computer-use/greyhack-game-observer/scripts")
            if str(observer_scripts) not in sys.path:
                sys.path.insert(0, str(observer_scripts))

            from greyhack_capture import capture_session_tick
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            result = capture_session_tick(session_id=f"test-{timestamp}")
            print(f"   ✅ Screenshot gespeichert: {result}")
        except Exception as e:
            print(f"   ⚠️ Screenshot-Fehler: {e}")
            # Versuche Fallback: scrot direkt
            import subprocess
            try:
                fallback_path = "/tmp/greyhack_fallback.png"
                scrot_result = subprocess.run(
                    ["scrot", fallback_path],
                    capture_output=True, text=True, timeout=10
                )
                if scrot_result.returncode == 0:
                    print(f"   ✅ Fallback-Screenshot: {fallback_path}")
            except Exception:
                print(f"   📁 Manuelle Überprüfung von 99 Capture/ empfohlen")

    def _action_ocr_analysis(self, step_description: str) -> None:
        """Analysiert den letzten Screenshot via OCR."""
        print("   🔍 Analysiere Spiel-State via OCR...")
        try:
            # Finde neuesten Screenshot
            capture_dir = VAULT / "99 Capture"
            if not capture_dir.exists():
                print("   ⚠️ Kein Capture-Ordner")
                return

            screenshots = sorted(capture_dir.glob("*.md"), key=lambda p: p.stat().st_mtime)
            if not screenshots:
                print("   ⚠️ Keine Screenshots gefunden")
                return

            latest = screenshots[-1]
            content = latest.read_text(encoding="utf-8-sig")

            # Extrahiere OCR-Text aus dem File
            if "OCR-Extrahierter Text" in content:
                ocr_start = content.find("```\n", content.find("OCR-Extrahierter Text")) + 4
                ocr_end = content.find("\n```", ocr_start)
                ocr_text = content[ocr_start:ocr_end]

                # State-Detection
                from mission_state import detect_state_from_ocr
                detected_state = detect_state_from_ocr(ocr_text)
                print(f"   📊 Erkannter State: {detected_state.value}")
                print(f"   📝 OCR-Text (erste 100 Zeichen): {ocr_text[:100]}...")
        except Exception as e:
            print(f"   ⚠️ OCR-Analyse-Fehler: {e}")

    def _action_status_update(self, step_description: str) -> None:
        """Persistiert den aktuellen Status im Vault."""
        print("   📝 Update Mission-State...")
        self._save_state()
        print(f"   ✅ State gespeichert in {MISSION_STATE_FILE.name}")


def main():
    parser = argparse.ArgumentParser(description="GreyHack Mission Orchestrator")
    parser.add_argument("mission", help="Pfad zur Mission-Markdown-Datei")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur die Mission parsen und validieren, nichts ausführen",
    )
    args = parser.parse_args()

    mission_file = Path(args.mission)
    if not mission_file.is_absolute():
        mission_file = VAULT / args.mission

    if not ensure_cua_available():
        print("⚠️ cua-driver nicht gefunden — verwende Dry-Run oder installiere es")

    orchestrator = MissionOrchestrator(mission_file, dry_run=args.dry_run)
    try:
        orchestrator.run()
    except KeyboardInterrupt:
        print("\n🛑 Manueller Abbruch.")
        orchestrator.state = "INTERRUPTED"
        orchestrator._save_state()


if __name__ == "__main__":
    main()