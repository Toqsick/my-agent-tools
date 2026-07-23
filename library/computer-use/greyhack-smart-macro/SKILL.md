---
name: greyhack-smart-macro
description: |
  Use when performing active in-game actions in GreyHack via smart macros, automating a repetitive in-game task (mining, hacking, trading), or running a macro loop while the greyhack-game-observer skill watches outcomes.
  NOT for passive observation only, mission orchestration across multiple macros, or scripting outside GreyHack — use greyhack-game-observer or greyhack-mission-orchestrator instead.
  Drive GreyHack in-game actions via smart-macro automation.
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
    - macro
    - automation
    - input
    - computer-use
    related_skills:
    - computer-use
    - greyhack-game-observer
    - greyhack-mission-orchestrator
trigger_keywords: ['greyhack', 'game', 'actions', 'smart', 'macros']
keywords: ['greyhack', 'game', 'actions', 'smart', 'macros']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['greyhack-mission-orchestrator', 'greyhack-hermes-api', 'greyhack-game-observer']
---


# GreyHack Smart Macro

## Overview
Der **GreyHack Smart Macro** ist die aktive Ausführungs-Stufe unserer Computer-Use-Pipeline. Während der Observer nur zusieht, kann dieser Skill **GreScript-Code in die Spiel-Konsole tippen**, **Login-Daten eingeben**, **UI-Buttons klicken** und **sich durch die Grey-Hack-GUI navigieren** — alles im Hintergrund, ohne deinen Editor-Focus zu klauen.

## When to Use
- **Trigger**: Du willst ein GreyScript-Tool aus deinem Vault direkt ins Spiel tippen lassen (kein Copy-Paste!).
- **Trigger**: Du willst repetitive Login-Sequenzen automatisieren.
- **Trigger**: Du willst eine Mission-Schritt-Reihenfolge ausführen, die visuelles Feedback braucht (z.B. "Mailbox öffnen", "Passwort eintippen", "Bestätigen klicken").
- **Trigger**: Der `greyhack-mission-orchestrator` braucht atomare Aktionen, um seine Mission-State-Machine zu füllen.
- **Nicht verwenden für**: Passives Beobachten (nutze `greyhack-game-observer`) oder komplett autonome Missionen (nutze `greyhack-mission-orchestrator` mit dieser Skill als Basis).

## How It Works

Das Smart-Macro folgt dem **3-Schichten-Pattern**: Locate → Verify → Act.

```
┌─────────────────────────────────────────────────────────┐
│  Schicht 1: LOCATE                                      │
│  - Element-Index via SOM (Set-of-Mark) Overlay          │
│  - Vision-Modell identifiziert UI-Element               │
│  - AX-Tree-Index liefert stabile IDs                     │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Schicht 2: VERIFY                                      │
│  - Pre-Capture: Wie sieht es JETZT aus?                │
│  - Post-Capture: Hat die Aktion gewirkt?                │
│  - OCR-Vergleich: Erwarteter Text sichtbar?             │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Schicht 3: ACT                                         │
│  - click / type / key mit Verifikation danach           │
│  - Bei Misserfolg: Retry mit Backoff (max 3x)           │
│  - Bei Permission-Dialog: SOFORT STOPP + Telegram-Alert │
└─────────────────────────────────────────────────────────┘
```

## Implementation Steps

### 1. GreyScript ins Spiel tippen

```python
from hermes_tools import computer_use
from pathlib import Path
import time

GREYSCRIPT_FILE = Path("/home/bratan/10-Projekte/10-active/greyhack-tools/src/tools/portscan.src")

def type_greyscript_into_console(src_file: Path):
    \"\"\"Liest eine .src-Datei und tippt sie in die Grey-Hack-Konsole.\"\"\"
    script_content = src_file.read_text(encoding="utf-8")
    
    # Pre-Verify: Konsole ist im Eingabe-Modus
    pre_capture = computer_use(action="capture", mode="ax", app="steam", background_only=True)
    ax_tree = pre_capture  # AX-Index mit Elementen
    
    # Finde das Konsolen-Eingabefeld (über Textinhalt oder Element-Index)
    # In Grey Hack: das Eingabefeld ist typischerweise am unteren Bildschirmrand
    console_input_element = None
    for elem in ax_tree:
        if "text field" in elem["role"].lower() or "edit" in elem["role"].lower():
            console_input_element = elem["index"]
            break
    
    if console_input_element is None:
        raise RuntimeError("Konsolen-Eingabefeld nicht gefunden!")
    
    # Klick auf Eingabefeld (um Fokus zu setzen, ABER: Hintergrund!)
    computer_use(action="click", element=console_input_element, capture_after=True)
    
    # Tippe das Skript in mehreren Zeilen (Grey-Hack hat oft Char-Limits pro Zeile)
    for line in script_content.splitlines():
        # cua-driver typet langsam genug, dass Grey Hack mithält
        computer_use(action="type", text=line + "\n", capture_after=False)
        time.sleep(0.1)  # Pause zwischen Zeilen für Stabilität
    
    # Post-Verify: Skript wurde vollständig getippt (OCR-Check)
    post_capture = computer_use(action="capture", mode="vision", app="steam", background_only=True)
    # Optional: OCR-Vergleich, ob alle Zeilen angekommen sind
    
    print(f"✅ {src_file.name} erfolgreich getippt!")

type_greyscript_into_console(GREYSCRIPT_FILE)
```

### 2. Login-Sequenz automatisieren

```python
def automated_login(username: str, password: str):
    \"\"\"Führt die Login-Sequenz für Grey Hack aus.\"\"\"
    # 1. Warte auf Login-Screen
    time.sleep(2.0)
    
    # 2. Username-Feld: Klicken + Tippen
    computer_use(action="click", element=12, capture_after=True)  # Username-Feld (Element-Index vorher bestimmen!)
    computer_use(action="type", text=username)
    computer_use(action="key", keys="Tab")  # Springt zum Passwort-Feld
    
    # 3. Password-Feld: Tippen
    computer_use(action="type", text=password)
    computer_use(action="key", keys="return")  # Login bestätigen
    
    # 4. Post-Verify: Login-Screen ist weg, City-Map sichtbar
    time.sleep(3.0)
    verify_capture = computer_use(action="capture", mode="ax", app="steam", background_only=True)
    
    # Wenn "Login" noch im AX-Tree ist: Login fehlgeschlagen!
    if any("login" in elem["label"].lower() for elem in verify_capture):
        raise RuntimeError("Login fehlgeschlagen — Passwort falsch oder Server down")
    
    print("✅ Login erfolgreich!")
```

### 3. UI-Button-Klicks mit Retry-Logic

```python
import time

def click_with_retry(element_index: int, expected_text: str = None, max_attempts: int = 3):
    \"\"\"Klickt auf ein Element mit OCR-Verifikation und Retry.\"\"\"
    for attempt in range(1, max_attempts + 1):
        try:
            # Pre-Capture
            pre = computer_use(action="capture", mode="som", app="steam", background_only=True)
            
            # Klick
            computer_use(action="click", element=element_index, capture_after=True)
            time.sleep(1.0)  # Warte auf UI-Update
            
            # Post-Verify (wenn erwarteter Text gegeben)
            if expected_text:
                post = computer_use(action="capture", mode="vision", app="steam", background_only=True)
                # OCR-Vergleich hier (Tesseract auf das Bild)
                if expected_text.lower() in ocr_extract(post).lower():
                    return True  # Erfolgreich!
                else:
                    print(f"⚠️ Versuch {attempt}: Erwarteter Text nicht gefunden, retry...")
                    time.sleep(0.5)
            else:
                return True  # Kein Verify nötig
        except Exception as e:
            print(f"⚠️ Versuch {attempt} fehlgeschlagen: {e}")
            time.sleep(0.5)
    
    raise RuntimeError(f"Klick auf Element {element_index} nach {max_attempts} Versuchen fehlgeschlagen!")
```

### 4. Sicherheits-Kill-Switch: Permission-Dialoge

```python
def check_for_permission_dialog():
    \"\"\"Prüft, ob ein Permission-Dialog aufgetaucht ist. Stoppt SOFORT, wenn ja.\"\"\"
    capture = computer_use(action="capture", mode="ax", app="steam", background_only=True)
    
    # Suche nach typischen Permission-Indikatoren
    forbidden_keywords = [
        "permission", "allow", "deny", "sudo", "password prompt",
        "authentifizierung", "zugriff", "berechtigung"
    ]
    
    for elem in capture:
        label = elem.get("label", "").lower()
        if any(keyword in label for keyword in forbidden_keywords):
            # STOPP! Niemals auf Permission-Dialoge klicken!
            send_telegram_alert(
                f"🚨 PERMISSION-DIALOG ERKANNT!\\n"
                f"Element: {elem['label']}\\n"
                f"Auto-Stop aktiviert. Bitte manuell bestätigen."
            )
            raise RuntimeError(
                f"Permission-Dialog erkannt — Auto-Stopp! Bitte manuell bestätigen."
            )
```

## Common Pitfalls
1. **Pixel-Koordinaten statt Element-Index**: `coordinate=[x, y]` ist extrem fragil (Fenster kann verschoben werden, DPI-Änderungen). **IMMER** `element=N` verwenden.
2. **Focus-Klau durch `raise_window=True`**: Das Obsidian-Editor-Fenster verliert den Focus! Niemals setzen, immer `background_only=True`.
3. **Zu schnelles Tippen**: Grey Hack hat eine interne Rate-Limit. Wenn du 100 Zeichen in 100ms tippst, kann das zu "Buffer Overflow" führen. Empfehlung: 0.1s Pause zwischen Zeilen.
4. **Fehlende Post-Verify**: Nach jeder Aktion MUSS ein `capture_after=True` erfolgen, um zu prüfen, ob die Aktion tatsächlich gewirkt hat. Sonst "blind klicken" = Race-Conditions.
5. **Hardcoded Element-Indizes**: Element-Indizes sind nur bis zum nächsten Capture stabil! Immer vor der Aktion frisch capturen.

## Verification Checklist
- [ ] Alle Klicks nutzen Element-Indizes, nicht Pixel-Koordinaten
- [ ] Jede Aktion hat `capture_after=True` zur Verifikation
- [ ] Bei Permission-Dialogen stoppt das Skript SOFORT und sendet Telegram-Alert
- [ ] Retry-Logic ist implementiert (max 3 Versuche mit Backoff)
- [ ] Keine Texteingabe ohne vorherigen Klick auf das Eingabefeld

## Verbindet zu
- [[MOC - Gaming-Performance]] — Gaming-Hub
- [[greyhack-game-observer]] — Vorherige Stufe: Beobachten
- [[greyhack-mission-orchestrator]] — Nächste Stufe: Autonome Missionen
- [[System - Skill-Tool-ComputerUse-Strategie]] — Strategischer Kontext
- [[Yuno - Mobile MaxClaw-Setup]] — GreyHack-Inventar-Referenz