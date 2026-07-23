---
name: greyhack-mission-orchestrator
description: |
  Use when planning and executing an autonomous GreyHack mission from a written objective, coordinating observation and action loops, or escalating blocked in-game decisions.
  NOT for passive game observation, isolated manual clicks, GreyScript language tutoring, or actions outside the GreyHack game environment.
  Coordinates the Queen-Bee GreyHack pipeline across mission state, computer-use navigation, recovery checkpoints, verification, and user escalation.
version: 1.0.0
author: Yuno (Basti)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - greyhack
    - orchestrator
    - autonomous
    - queen-bee
    - computer-use
    related_skills:
    - computer-use
    - greyhack-game-observer
    - greyhack-smart-macro
trigger_keywords: ['greyhack', 'game', 'mission', 'observation', 'planning']
keywords: ['greyhack', 'game', 'mission', 'observation', 'planning']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['greyhack-smart-macro', 'greyhack-computer-use-suite', 'greyhack-hermes-api']
---


# GreyHack Mission Orchestrator

## Overview
Der **GreyHack Mission Orchestrator** ist die Königin-Stufe unserer Computer-Use-Pipeline — die ultimative Verkörperung der **Queen-Bee-Architektur** für autonomes Gaming. Er kombiniert:

- **Observer** (Screenshot + OCR für visuelle Wahrnehmung)
- **Smart-Macro** (Tastatur/Maus-Aktionen)
- **Vault-Reader** (liest Missions-Ziele aus Obsidian)
- **State-Machine** (Verfolgt Missions-Fortschritt)
- **Kill-Switch** (Sofort-Stopp bei Permission-Dialogen + Telegram-Alert)

Das Ergebnis: Du schreibst eine Mission in deinen Vault, der Orchestrator liest sie, navigiert durch das Spiel, führt Aktionen aus und meldet sich bei dir, wenn er nicht weiterkommt oder eine kritische Entscheidung ansteht.

## When to Use
- **Trigger**: Du willst eine repetitive Mission-Sequenz automatisieren (z.B. "Scan Router → Finde Schwachstelle → Hacke").
- **Trigger**: Du willst Tests im [[Queen-Bee-Lab - GreyHack-Tests]] durchführen, um Multi-Agent-Patterns im Spiel zu validieren.
- **Trigger**: Du willst einen "Erfahrungs-Sammler" bauen, der eigenständig Daten sammelt.
- **Nicht verwenden für**: Missionen, die menschliche Kreativität erfordern (z.B. einmalige Story-Missionen mit Twists) — der Orchestrator ist ein Arbeiter, kein Denker.

## How It Works — Die Queen-Bee-Architektur

```
┌──────────────────────────────────────────────────────────────┐
│              OBSIDIAN VAULT (Basti's Brain)                   │
│  📜 Missions/Mission-Reraldi-IP-154.md                       │
│       - Ziel: Finde Reraldi@adahidomev.net                   │
│       - Steps: [1] Portscan [2] Exploit [3] Daten kopieren    │
└──────────────────────────┬───────────────────────────────────┘
                           │ read
                           ▼
┌──────────────────────────────────────────────────────────────┐
│         ORCHESTRATOR (Queen-Bee Brain in Python)             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  MissionStateMachine                                    │ │
│  │  - Current Step: 1 (Portscan)                           │ │
│  │  - Status: IN_PROGRESS                                  │ │
│  │  - Next Action: Open menu, click "Portscan"             │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Loop:                                                  │ │
│  │  1. OBSERVE: Screenshot + OCR → Current State           │ │
│  │  2. DECIDE: Welche Aktion? (aus Mission-States)        │ │
│  │  3. ACT: Smart-Macro-Befehl                             │ │
│  │  4. VERIFY: Hat es funktioniert?                       │ │
│  │  5. UPDATE: State-Machine weiterschalten                │ │
│  │  6. KILL-SWITCH: Permission-Dialog? → STOPP + Telegram  │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────┘
                           │ computer_use
                           ▼
┌──────────────────────────────────────────────────────────────┐
│           GREY HACK SPIEL-FENSTER                            │
│  (Steuerung komplett im Hintergrund, kein Focus-Klau)       │
└──────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### 1. Mission-Definition im Vault

Erstelle eine Vault-Notiz im Ordner `03 Projekte/Queen-Bee-Lab/Missions/`:

```markdown
---
type: mission
target: Reraldi@adahidomev.net
priority: P0
status: ready-to-run
---

# Mission: Reraldi@adahidomev.net (IP 154.19.190.206)

## Ziel
Hole die geheimen Daten von der Mailbox des Ziels.

## Steps (vom Orchestrator auszuführen)
1. **Connect** zur Ziel-IP
2. **Portscan** auf Standard-Ports
3. **SMTP-Enum** um offene Mailbox zu finden
4. **Brute-Force** mit der suid_exploit Datenbank
5. **Daten extrahieren** und in `~/Missions/Reraldi/output.txt` speichern

## Expected Output
- Mailbox-Login-Daten
- Liste der extrahierten Mails
- IP-Bestätigung
```

### 2. Orchestrator-Skript starten

```python
from pathlib import Path
from hermes_tools import computer_use
from hermes_skills.computer_use.greyhack_game_observer import capture_session_tick
from hermes_skills.computer_use.greyhack_smart_macro import type_greyscript, click_with_retry

VAULT = Path("/home/bratan/Dokumente/Obsidian Vault")
MISSION_FILE = VAULT / "03 Projekte/Queen-Bee-Lab/Missions/Mission-Reraldi-IP-154.md"

class MissionOrchestrator:
    def __init__(self, mission_file: Path):
        self.mission_file = mission_file
        self.mission_data = self._parse_mission()
        self.current_step = 0
        self.state = "INIT"
        
    def _parse_mission(self) -> dict:
        \"\"\"Parst die Vault-Mission-Datei.\"\"\"
        content = self.mission_file.read_text(encoding="utf-8")
        # Sehr einfach gehalten: Wir parsen nur die Steps
        steps = []
        in_steps = False
        for line in content.splitlines():
            if line.startswith("## Steps"):
                in_steps = True
                continue
            if line.startswith("## ") and in_steps:
                break
            if in_steps and line.strip().startswith(tuple("123456789")):
                steps.append(line.strip())
        return {
            "target": self._extract_frontmatter(content, "target"),
            "priority": self._extract_frontmatter(content, "priority"),
            "steps": steps,
            "raw": content,
        }
    
    def _extract_frontmatter(self, content: str, key: str) -> str:
        \"\"\"Extrahiert einen YAML-Wert aus dem Frontmatter.\"\"\"
        if not content.startswith("---"):
            return ""
        parts = content.split("---", 2)
        if len(parts) < 3:
            return ""
        for line in parts[1].splitlines():
            if line.startswith(f"{key}:"):
                return line.split(":", 1)[1].strip()
        return ""
    
    def check_kill_switch(self):
        \"\"\"Prüft, ob ein Permission-Dialog aufgetaucht ist.\"\"\"
        try:
            capture = computer_use(action="capture", mode="ax", app="steam", background_only=True)
            forbidden = ["permission", "allow", "deny", "sudo", "password prompt"]
            for elem in capture if isinstance(capture, list) else []:
                label = str(elem.get("label", "")).lower()
                if any(kw in label for kw in forbidden):
                    self._send_telegram_alert(
                        f"🚨 KILL-SWITCH!\\nMission: {self.mission_file.name}\\n"
                        f"Permission-Dialog: {elem.get('label')}"
                    )
                    raise RuntimeError(f"Permission-Dialog: Auto-Stopp!")
        except ImportError:
            pass
    
    def _send_telegram_alert(self, message: str):
        \"\"\"Sendet eine Telegram-Nachricht an Basti.\"\"\"
        # ... (Telegram-Versand wie in Working Agreement §7)
        print(f"📨 TELEGRAM: {message}")
    
    def run(self):
        \"\"\"Haupt-Loop: Observer → Decide → Act → Verify.\"\"\"
        print(f"🎮 Starte Mission: {self.mission_data.get('target')}")
        print(f"   Steps: {len(self.mission_data['steps'])}")
        
        for i, step in enumerate(self.mission_data["steps"]):
            self.current_step = i + 1
            self.state = f"STEP_{self.current_step}"
            print(f"\\n--- Step {self.current_step}/{len(self.mission_data['steps'])} ---")
            print(f"   {step}")
            
            # Kill-Switch vor jeder Aktion
            self.check_kill_switch()
            
            # Observer: Screenshot machen
            try:
                capture_result = capture_session_tick(session_id=f"mission-{self.current_step}")
                print(f"   📸 Snapshot: {capture_result}")
            except Exception as e:
                print(f"   ⚠️ Snapshot fehlgeschlagen: {e}")
            
            # Hier würde die konkrete Aktion stehen (step-spezifisch)
            # In einer echten Mission hätten wir eine Mapping-Logik:
            # step.startswith("1.") → type_greyscript(portscan.src)
            # step.startswith("2.") → click_with_retry(...)
            # usw.
            
            # Vereinfacht für Demo:
            print(f"   ▶️ Aktion würde jetzt ausgeführt...")
            
            # State persistieren
            self._save_state()
        
        self.state = "COMPLETE"
        self._save_state()
        print("\\n✅ Mission abgeschlossen!")
    
    def _save_state(self):
        \"\"\"Speichert den aktuellen State in den Vault.\"\"\"
        state_file = VAULT / "03 Projekte/Queen-Bee-Lab/Mission-State.md"
        state_file.write_text(
            f"\\"\\"\\"\\n# Mission State\\n\\n- File: {self.mission_file.name}\\n"
            f"- Step: {self.current_step}/{len(self.mission_data['steps'])}\\n"
            f"- State: {self.state}\\n- Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n\\\"\\"\\"\\",
            encoding=\"utf-8\",
        )

if __name__ == \"__main__\":
    orchestrator = MissionOrchestrator(MISSION_FILE)
    orchestrator.run()
```

### 3. Sicherheits-Framework: 4 Hard Rules

| # | Regel | Implementation |
|---|-------|----------------|
| 1 | **Niemals auf Permission-Dialoge klicken** | `check_kill_switch()` vor jeder Aktion |
| 2 | **Bei Fehler: Telegram-Alert + Stopp** | `_send_telegram_alert()` + `raise RuntimeError` |
| 3 | **Max 10 Versuche pro Step** | Counter + Escalation |
| 4 | **Audit-Log: Alle Aktionen persistent** | Jeder State-Change → Vault-Markdown |

## Common Pitfalls
1. **Race-Conditions bei Multi-Step-Missionen**: Wenn das Spiel langsamer als erwartet lädt, kann der nächste Schritt ins Leere gehen. IMMER `time.sleep()` + `capture_after=True`!
2. **Mission-State-Vergessen**: Wenn der Orchestrator abstürzt, muss er beim Neustart wissen, wo er war. State-File nach JEDEM Step schreiben!
3. **OCR-Fehler bei Spieler-Namen**: "Reraldi" könnte als "Rera1di" (mit Eins statt l) gelesen werden. Pre-Build einer bekannten Korrektur-Map!
4. **Steam-Overlay blockiert Sicht**: Das Steam-Overlay (Shift+Tab) kann das Sichtfeld blockieren. Vor Orchestrator-Start: `Shift+Tab` drücken, um Overlay zu schließen.
5. **In-Game-Manual mit XSendEvent-Blockade**: Die meisten Spiele (Grey Hack, Genshin, etc.) blockieren XSendEvent-basierte Klicks. Assisted Reconnaissance (User klickt, Agent OCR'd) ist die einzige funktionierende Strategie für In-Game-Dokumentation. Siehe `desktop-window-reconnaissance` → `references/greyhack-manual-reading-2026-07-06.md` für das volle Pattern.
6. **WID-Drift zwischen Sessions**: Grey Hack vergibt bei jedem Start neue Window-IDs (12582935 → 12582985 zwischen Sessions). Niemals hardcoden — bei jedem Run mit `xdotool search --name "Grey Hack"` re-discoveren.
7. **Subprocess-Env nicht gesetzt**: `cua-driver`, `xwd`, `xdotool` brauchen `DISPLAY=:1` + `XAUTHORITY=...` in der Subprocess-Env. Setze `env = os.environ.copy()` und exportiere die Vars explizit.

## Verification Checklist
- [ ] Mission-Datei existiert im Vault mit korrekten Frontmatter (`target`, `priority`, `status`)
- [ ] Orchestrator-Skript kann gestartet werden ohne Fehler
- [ ] Kill-Switch funktioniert (teste mit Dummy-Permission-Dialog)
- [ ] State-File wird nach jedem Step aktualisiert
- [ ] Telegram-Alerts werden bei Kill-Switch ausgelöst (teste mit `--dry-run`)
- [ ] Alle Aktionen laufen `background_only=True` (kein Focus-Klau)

## Step-Handler-Pattern: Assisted Reconnaissance (NEW 2026-07-06)

Für Spiele mit XSendEvent-Blockade kann der Orchestrator **Assisted Reconnaissance** für In-Game-Dokumentation orchestrieren: User klickt manuell durch, Agent OCR'd + extrahiert.

```python
# In orchestrator.py, add to _execute_step():
elif "manual" in step_lower or "tutorial" in step_lower or "doku" in step_lower:
    self._action_manual_page(step_description)

# New handler:
def _action_manual_page(self, step_description: str) -> None:
    """Capture and OCR an in-game Manual page the user opened."""
    import subprocess
    # 1. Screenshot via cua-driver
    png_data = self._capture_greyhack_window()
    # 2. OCR with German language pack (Grey Hack is bilingual)
    ocr = subprocess.run(
        ["tesseract", "/tmp/gh_manual.png", "-", "-l", "eng+deu", "--psm", "6"],
        capture_output=True, text=True, timeout=30
    )
    # 3. Save as vault note
    safe_name = re.sub(r'[^a-z0-9]+', '-', step_description.lower())[:50]
    note_path = VAULT / f"05 Ressourcen/greyhack-manual-{safe_name}.md"
    note = f"""# Grey Hack Manual: {step_description}

> **Quelle**: In-Game Manual (extracted via cua-driver + Tesseract)
> **Datum**: {time.strftime('%Y-%m-%d %H:%M')}

{ocr.stdout}
"""
    note_path.write_text(note, encoding="utf-8")
    print(f"   📖 Manual page extracted: {note_path}")
```

**Voraussetzung**: User hat die Manual-Seite im Spiel geöffnet, bevor der Step-Handler triggert. Orchestrator erkennt am Step-Text (z.B. "Lies Manual: Libraries & Exploits") und führt den OCR-Extract automatisch durch.

## Verbindet zu
- [[Queen-Bee-Lab - GreyHack-Tests]] — Testlabor für diese Architektur
- [[greyhack-game-observer]] — Schicht 1: Beobachten
- [[greyhack-smart-macro]] — Schicht 2: Agieren
- [[MOC - Gaming-Performance]] — Gaming-Hub
- [[System - Skill-Tool-ComputerUse-Strategie]] — Strategischer Kontext
- [[Yuno - Mobile MaxClaw-Setup]] — GreyHack-Inventar-Referenz
- [[Subagent-Patterns - Delegation & Routing]] — Subagent-Orchestrierungs-Logik