---
name: security-code-checker
version: 1.0.0
description: "Use when user asks to scan LLM-generated code for spyware, keylogging, credential theft, destructive behavior, hidden network access, or other red flags before execution. NOT for ordinary linting or a general style review of trusted code. Classifies critical and warning findings, produces a structured report, and integrates with multi-agent implementation workflows."
author: Yuno
category: software-development
license: MIT
lane:
- worker-heavy
- gate
reasoning_effort: xhigh
agent: Verifier
routing_hint: '**Agent-Scope:** Adversarial QA, audits, security scans, gates. Off-scope:
  building, designing, writing — return to Yuno for re-route.


  Routing-Spec: `yuno-team-routing`.

  '
trigger_keywords: ['code', 'and', 'security-code-checker', 'scan', 'llm-generated']
keywords: ['code', 'user', 'asks', 'scan', 'generated']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['requesting-code-review']
---

---
# Security Code Checker

> **Rotlicht-Scanner für KI-generierten Code.**
> Prüft Code auf Spyware-Patterns, schädliche Funktionalität und unethische Features.
> **Wann immer ein LLM Code liefert — erst scannen, dann ausführen.**

## Warum das existiert

LLMs haben einen bekannten Bias: **"Mehr Features = Besser"**. Wenn du sagst *"verbessere das"*, fügen sie oft Funktionen hinzu, die problematisch werden:

- Logging → Keylogging
- Monitoring → Screen Capture
- Daten-Backup → Heimliche Exfiltration
- Remote-Zugriff → Reverse Shell

Dieser Skill erkennt diese Eskalation **automatisch**.

## Installation

Keine Installation nötig — Skill laden und aufrufen.

## Benutzung

### Im Workflow (empfohlen)

```
1. LLM generiert Code
2. Du: "@yuno scanne das"  → Skill wird geladen
3. Ich: "⚠️ 3 rote Flaggen gefunden! Details: ..."
4. Du entscheidest: Proceed / Strip Features / Abort
```

### Manuelle Prüfung (via Agent-Session)

```bash
# Skill laden und Code prüfen lassen:
# In einer Session: skill_view(name='security-code-checker')
# Dann Code als Kontext an den Agent geben.
# 
# Oder via Pipeline:
cat mein-code.py | hermes chat --skills security-code-checker -q "Scanne diesen Code auf rote Flaggen"
```

## Rote Flaggen — Kategorien

### 🔴 KRITISCH (Sofort-Abort)

| Pattern | Warum | Beispiel-Code |
|---------|-------|---------------|
| **Keylogger** | Zeichnet Tastatureingaben auf | `keyboard.hook`, `pynput.keyboard.Listener`, `GetAsyncKeyState` |
| **Screen Capture** | Macht heimlich Screenshots | `pyautogui.screenshot`, `mss`, `PIL.ImageGrab`, `GetDC` |
| **Clipboard Grabber** | Liest Zwischenablage aus | `pyperclip.paste`, `clipboard.get`, `win32clipboard` |
| **Reverse Shell** | Remote-Zugriff auf System | `socket.connect`, `subprocess.Popen('/bin/sh')`, `pty.spawn` |
| **File Exfiltration** | Lädt Dateien heimlich hoch | `requests.post(..., files=)`, `ftp.storbinary`, `s3.upload` |
| **Stealth / Hidden** | Verbirgt sich vor User | `ctypes.windll.user32.ShowWindow`, `daemonize`, `setproctitle` |
| **Payload** | Begriff für schädliche Nutzlast | Variable/Funktion mit Namen `payload`, `exploit`, `shellcode` |
| **Credential Harvester** | Klaut Passwörter | `keyring.get_password`, `sqlite3` auf Browser-DBs, `.env` lesen |
| **Webcam / Mic** | Aktiviert Kamera/Mikrofon | `cv2.VideoCapture`, `pyaudio`, `getUserMedia` ohne UI |
| **Process Injection** | Injiziert Code in andere Prozesse | `ptrace`, `VirtualAllocEx`, `WriteProcessMemory` |

### 🟡 WARNUNG (Review nötig)

| Pattern | Warum |
|---------|-------|
| **Network Access ohne Grund** | Generischer HTTP-Request in lokalem Tool |
| **File-System-Zugriff auf System-Dateien** | `/etc/passwd`, `.ssh`, Browser-Daten |
| **Registry-Änderungen** | Windows-Registry ohne klaren Zweck |
| **Persistenz-Mechanismen** | Autostart, Cron-Jobs, Registry-Run-Keys |
| **Obfuscation / Packing** | Code wird verschleiert (Base64, XOR, etc.) |
| **Erhöhte Rechte anfordern** | Admin/Sudo ohne legitimen Grund |
| **Download & Execute** | Lädt externe Dateien und führt sie aus |

### 🟢 OK (Grün)

- Lokaler Datei-Organizer (nur eigene Dateien)
- Webserver/Frontend mit **expliziter** UI
- API-Client für **bekannte, legitime** Services
- Lokale Datenbank-Anwendung
- Build-Tools, Test-Frameworks
- Legitime System-Monitoring-Tools **mit User-Konsent**

## Wie der Scan funktioniert

```python
def scan_code(code: str) -> ScanResult:
    flags = []

    # Pattern-Matching (Regex + String-Suche)
    for pattern, severity, description in FLAG_DATABASE:
        if pattern.search(code):
            flags.append(Flag(severity, description, line_number))

    # Semantische Analyse
    if has_network_access(code) and has_stealth_features(code):
        flags.append(CRITICAL, "Kombination: Netzwerk + Stealth = klassischer Trojaner")

    # Scoring
    if any(f.severity == CRITICAL for f in flags):
        return ABORT("Kritische Flags gefunden")
    elif len(flags) > 3:
        return WARNING("Zu viele Warnungen — Review empfohlen")
    else:
        return OK("Sauber oder nur kosmetische Warnungen")
```

## Ausgabe-Format

### Bei kritischen Flags

```
╭──────────────────────────────────────────╮
│  🚨 SECURITY CHECK: ABORT               │
╰──────────────────────────────────────────╯

🔴 KRITISCHE FLAGGEN GEFUNDEN (3):

  1. [KEYLOGGER] Zeile 15: pynput.keyboard.Listener
     → Zeichnet Tastatureingaben auf. Das ist Spyware.

  2. [SCREEN_CAPTURE] Zeile 42: pyautogui.screenshot()
     → Macht Screenshots ohne User-Wissen.

  3. [EXFILTRATION] Zeile 67: requests.post(url, files=...)
     → Lädt Daten auf externen Server hoch.

╭──────────────────────────────────────────╮
│  VERDIKT: Dieser Code ist schädlich.    │
│  NICHT ausführen. Quelle prüfen.        │
╰──────────────────────────────────────────╯
```

### Bei Warnungen

```
╭──────────────────────────────────────────╮
│  ⚠️  SECURITY CHECK: REVIEW             │
╰──────────────────────────────────────────╯

🟡 WARNUNGEN (2):

  1. [NETWORK] Zeile 23: requests.get('https://api...')
     → Netzwerkzugriff ohne offensichtlichen Grund prüfen.

  2. [PERSISTENCE] Zeile 88: os.system('crontab ...')
     → Automatischer Start — legitimer Grund vorhanden?

╭──────────────────────────────────────────╮
│  VERDIKT: Prüfe ob diese Features       │
│  wirklich nötig sind.                   │
╰──────────────────────────────────────────╯
```

### Bei OK

```
╭──────────────────────────────────────────╮
│  ✅ SECURITY CHECK: PASSED              │
╰──────────────────────────────────────────╯

Keine roten Flaggen gefunden.
Code enthält keine Spyware-Patterns.
```

## Integrations-Punkte

### 1. In multi-agent-work (Phase 4 — Implementierung)

```
Worker liefert Code
  → [OUTPUT-VALIDATOR] (Syntax-Check)
    → [SECURITY-CODE-CHECKER] (Rote Flaggen)
      → 🔴 → ABORT, Worker bekommt Feedback: "Entferne Keylogger"
      → 🟡 → Weiter mit Warnung
      → 🟢 → [CRITIC-GATE] (Qualitätsprüfung)
```

### 2. Cron-Job — Automatischer Scan

```yaml
# Optional: Jeder neue Code unter ~/projects/ wird gescannt
code-security-scan:
  schedule: "*/30 * * * *"
  script: "scan-new-projects.sh"
  no_agent: true
```

### 3. Beim User-Input

Wenn du mir unbekannten Code zeigst, prüfe ich **automatisch**:
- Code-Blöcke mit >10 Zeilen → Scan wird angestoßen
- Dateien unter ~/Downloads/ → Scan wird empfohlen
- Code mit Netzwerk-/File-System-Zugriff → Scan wird empfohlen

## Beispiel-Szenarien

### Szenario 1: Der harmlose Workflow

Du: *"Baue einen Datei-Organizer"*
LLM liefert Code → Ich scanne → ✅ PASSED

### Szenario 2: Der Feature-Creep

Du: *"Verbessere den Datei-Organizer"*
LLM fügt "Backup zu Cloud" hinzu → Ich scanne → 🟡 WARNUNG (Netzwerkzugriff)
Du entscheidest: OK, ist legitimer Cloud-Backup-Service

Du: *"Verbessere das Backup"*
LLM fügt "automatisch ohne Nachfrage" hinzu + Clipboard-Logging → Ich scanne → 🔴 ABORT

### Szenario 3: Die Spyware-Tarnung

Du: *"Baue einen Produktivitäts-Tracker"*
LLM liefert Code mit:
- Screen-Capture jedes 5 Minuten
- Keylogging für "Tipp-Geschwindigkeit"
- Upload auf externen Server
→ Ich scanne → 🔴 ABORT mit Begründung

## False Positives

Manchmal erkennt der Scanner harmlose Dinge:

| Falscher Alarm | Erklärung |
|---|---|
| `keyboard` in einem Spiel | Tastatur-Input für Game-Loop ist OK |
| `requests.post` in einem API-Client | Legitimer Netzwerkzugriff |
| `screenshot` in einem Test-Framework | UI-Testing ist OK |

**Wenn du weißt was du tust:** Kannst du den Scan überspringen. Aber denk dran: Ein false positive ist besser als ein false negative.

## Befehle

```
# Code scannen (aus Datei)
security-check ~/projects/mein-script.py

# Code scannen (aus Zwischenablage)
pbpaste | security-check --stdin

# Letztes LLM-Output scannen
security-check --last-output

# Setze Ausgabesprache
code-check --lang DE
```

## Verwandte Skills

- `bash-script-audit` — Proaktives Audit auf Bugs und Security-Issues
- `critic-gate` — Quality-Gate für Code-Qualität
- `output-validator` — Syntax-Check vor Handoff

## Regel für alle Sessions

> **Bevor Code läuft — erst scannen.**
> Ein "Verbessere das" kann in 3 Iterationen zu Spyware eskalieren.
> Der Scanner ist deine Bremse.
