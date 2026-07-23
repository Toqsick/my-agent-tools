---
name: voice-assistant-bots
description: "Use when user asks to architect or deploy a voice-enabled AI assistant, Discord or Telegram voice bot, wake-word pipeline, Docker foundation, Google Cloud speech integration, or autonomous voice cron workflow. NOT for simple TTS conversion or a non-voice chatbot. First checks Hermes built-in voice mode, then covers project structure, deployment, audio, integrations, and model selection."
version: 1.0.0
author: yuno
category: devops
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - discord
    - voice
    - bot
    - docker
    - stt
    - tts
    - google-cloud
    - cron
    - ollama
    - faster-whisper
    - local-ai
    - hermes-gateway
    - minimax-tts
    - telegram-voice
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['voice', 'voice-assistant-bots', 'architect', 'deploy', 'voice-enabled']
keywords: ['voice', 'user', 'asks', 'architect', 'deploy']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['audiobook', 'humanizer']
---


# Voice Assistant Bots

## ⚡ Before building: Hermes built-in voice mode

**Bevor du ein Plugin, einen Standalone-Bot oder irgendeine Voice-Infrastruktur baust:**
**Hermes hat `voice mode` fest eingebaut.** In vielen Fällen reicht ein Slash-Command.

| Command | Was es tut | Wo |
|---|---|---|
| `/voice on` | Voice-Modus an (Spracheingabe, automatische Antwort per TTS bei Voice-Nachrichten) | Hermes CLI, TUI, Telegram, Discord |
| `/voice tts` | **Auto-TTS für ALLE Nachrichten** — jede Antwort wird gesprochen | Telegram, Discord |
| `/voice off` | Voice-Modus aus | alle |
| `/voice status` | Zeigt aktuellen Modus | alle |

### CLI Workflow

```bash
hermes                # CLI starten
/voice on             # Voice-Modus aktivieren
Ctrl+B                # Mikrofon aufnehmen
# sprich, 3s Stille stoppt, Hermes antwortet mit TTS
```

### Config-Toggle für persistente Auto-TTS

```yaml
# ~/.hermes/config.yaml
voice:
  auto_tts: true       # Auto-enable TTS wenn voice mode startet
```

**TL;DR:** Wenn du nur eine Stimme für Antworten willst — `/voice tts` ist der Weg. Komm hierher zurück *nur* wenn du einen platform-externen Bot baust (Discord Voice Channel, eigenständiger Telegram-Bot außerhalb Hermes Gateway).

## Trigger

- Discord Bot mit Spracheingabe (Voice Channel)
- Text-to-Speech Rückgabe
- Docker-Containerisierte Bot-Architektur
- Autonome Cron-Jobs für Morning Briefings

## Projekt-Struktur (Template)

```

set -euo pipefail
~/yuno-voice-bot/
├── main.py                 # Bot-Logik (discord.py)
├── llm_helper.py           # OpenAI-kompatible Nous-/Ollama-Anbindung
├── telegram_helper.py      # stdlib-only Telegram-Fallback
├── stt_helper.py           # lokaler faster-whisper-STT plus Google Cloud STT
├── tts_helper.py           # Google Cloud TTS, Edge TTS, lokaler Piper TTS und Mock-WAV
├── voice_handler.py        # Discord Voice Channel Management
├── morning_cron.py         # Autonomes Briefing-System
├── scripts/                # Hilfs-Skripte, z.B. Invite-Link-/Live-Readiness-Generator und Hermes-Desktop-Config
│   ├── apply_hermes_voice_config.sh
│   ├── discord_invite_url.py
│   └── live_readiness.py
├── tests/                  # Smoke-Tests ohne echte Tokens
├── Dockerfile              # Container mit ffmpeg + libportaudio2
├── docker-compose.yml      # Orchestrierung
├── requirements.txt        # Python-Dep
├── hermes_voice_config.yaml # YAML-Snippet für Hermes Desktop STT/TTS
├── briefing_state.json     # Gedächtnis für Cron-Jobs
├── config.template.env     # sicheres Template ohne Secrets
└── config.env              # lokale Secrets (niemals committen)
```

## 1. Docker Fundament

### Voraussetzungen

Docker braucht für Voice-Bots zwingend:
- **ffmpeg** (Audio-Stream Decodierung)
- **libportaudio2** (PortAudio Bindings)

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libportaudio2 \
    portaudio19-dev
```

set -euo pipefail
### Installation (Ubuntu/ZorinOS)

```bash
# Docker GPG Key + Repository
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc

# Docker installieren
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli \
  containerd.io docker-buildx-plugin docker-compose-plugin

# User-Rechte fixen
sudo usermod -aG docker $USER
sudo chmod 666 /var/run/docker.sock

# ffmpeg
sudo apt-get install -y ffmpeg libportaudio2
```

set -euo pipefail
## 2. Discord Bot Setup

### Developer Portal (Browser)

URL: https://discord.com/developers/applications

**Intents (ALLE aktivieren!):**
- ✅ MESSAGE CONTENT INTENT
- ✅ SERVER MEMBERS INTENT
- ✅ VOICE STATE INTENT

**OAuth2 URL Generator:**
- Scopes: `bot`, `applications.commands`
- Permissions: `ViewChannel`, `Send Messages`, `Connect`, `Speak`, `Use Voice Activity`

**Security-Pattern:**
- Runtime-Bot braucht nur `DISCORD_BOT_TOKEN`.
- Invite-Links brauchen nur `DISCORD_CLIENT_ID` plus Scopes/Permissions.
- `DISCORD_CLIENT_SECRET` / Geheimer Client-Schlüssel gehört **nicht** in `config.env`, README, Git, Logs oder Chat.
- Wenn ein Client Secret sichtbar wurde: im Discord Developer Portal sofort rotieren/resetten.
- `DISCORD_PUBLIC_KEY` ist nur für Interactions/Webhooks relevant, nicht für normale Prefix-Commands.
- Invite-Link-Generierung kann als kleines Skript ohne Secrets erfolgen, z.B. `scripts/discord_invite_url.py`.

Details zu Discord-Secrets und OAuth-Invite: `references/discord-security-and-invite.md`.

### Python-Grundgerüst

Siehe `templates/main.py` für ein lauffähiges Skeleton mit:
- Wake-Word Erkennung ("Yuno")
- `!join` / `!leave` Voice Commands
- `!briefing` / `!status` / `!say` Text Commands
- TTS-Integration mit Google Cloud

## 3. Google Cloud APIs

### Aktivierungs-Schritte

1. https://console.cloud.google.com → Projekt wählen
2. **Billing aktivieren** (auch mit kostenlosem Guthaben!)
3. APIs & Dienste → Bibliothek:
   - Cloud Speech-to-Text API
   - Cloud Text-to-Speech API
4. Anmeldedaten → Dienstkontoschlüssel → JSON herunterladen

⚠️ **PITFALL:** Ohne aktiviertes Billing kommt Fehler 403, auch mit Credits!

### 💡 Telegram-Fallback: Bot nützlich machen WÄHREND GCP/Discord blockiert

Solange GCP-Billing / Service-Key / Discord-Token offen sind, läuft der
Voice-Stack nicht. Aber das Morning-Briefing (und Reports) können trotzdem
sofort raus — per Telegram. Telegram braucht nur Bot-Token + Chat-ID, kein
GCP, keine externen Pakete (nur `urllib`).

```python
# morning_cron.py --telegram  → Briefing per Telegram (kein GCP nötig)
from telegram_helper import send_telegram, is_configured
```

set -euo pipefail
`telegram_helper.py` ist stdlib-only und projekt-übergreifend kopierbar
(Voice-Bot UND Cleaner nutzen dieselbe Datei). Vollständiger Code +
graceful-degradation-Prinzipien: `references/telegram-fallback-and-live-testing.md`.

**P0-Bootstrap-Pattern:** Für schnelle End-to-End-Smoke-Tests lohnt sich ein
stdlib-only LLM-Helper (`urllib` gegen OpenAI-kompatible `/chat/completions`)
plus stdlib-only Telegram-Helper. So können `py_compile`,
`python3 -m unittest discover -s tests -v`, `main.py --dry-run` und
`morning_cron.py --dry-run` laufen, bevor Discord/GCP live sind. Details:
`references/stdlib-voice-bot-bootstrap.md`.

### `!ask` — echtes LLM statt Echo (discord.py async-Pitfall)

Das openai-SDK ist synchron, discord.py async. Direkter Call FRIERT den Bot
ein. Immer im Thread aufrufen: `await asyncio.to_thread(ask_llm, question)`,
umschlossen von `async with ctx.typing():`. Antwort als Text senden,
TTS-Vorlesen nur optional wenn im Voice-Channel. Details im selben Reference.

## 4. Wake-Word → Voice Pipeline

```text
User spricht "Yuno!" in Voice-Channel
        ↓
Discord → Bot empfängt Audio (PCM)
        ↓
PCM/WAV-Puffer für STT
        ↓
faster-whisper lokal ODER Google Cloud STT → Transkription
        ↓
Ollama lokal ODER Hermes/Nous API (LLM) → Antwort generieren
        ↓
Google Cloud TTS / Edge TTS / lokaler Piper TTS / NeuTTS → Audio generieren
        ↓
Bot spielt Audio im Voice-Channel ab
```

set -euo pipefail
**Wichtig:** Ollama ist für LLM/Text, nicht für STT. Für Speech-to-Text nutzt man `faster-whisper`, Whisper.cpp oder Cloud-STT. Details: `references/local-llm-stt-architecture.md`.

## 5. Autonome Cron-Jobs

### ⚠️ KRITISCHER PITFALL: `cronjob` Tool vs. CLI

**Das `cronjob` tool in Hermes hat Limitierungen!**

Bei wiederholten Fehlversuchen mit `cronjob action=create` → **Nutze stattdessen die CLI:**

```bash
hermes cron create "0 8 * * *" \
  "Dein Self-Contained Prompt hier..." \
  --name job-name \
  --skill model-selector \
  --workdir /home/bratan/yuno-voice-bot
```

set -euo pipefail
**Wichtige CLI-Parameter:**
- `schedule` als erstes positional arg (z.B. `0 8 * * *`, `30m`, `every 2h`)
- `prompt` als zweites positional arg (self-contained!)
- `--skill` für Skill-Loading
- `--workdir` für Projekt-Kontext

### Briefing-State Pattern

Cron-Jobs laufen in **isolierten Sessions** — sie kennen den Chat nicht!
Lösung: `briefing_state.json` als externes Gedächtnis.

```python
# morning_cron.py
import json

def load_briefing_state(path="briefing_state.json"):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "Gedächtnisdatei nicht gefunden."}

def generate_briefing(state):
    # Yuno-Persona: kawaii, deutsch, nicht archaisch
    greeting = state["persona"]["preferred_greeting"]
    # ... Formatierung mit Prioritäten, Tickets, Mood
```

set -euo pipefail
### 6. Modell-Auswahl für Voice-Bots

| Aufgabe | Empfohlenes Modell | Grund |
|---------|-------------------|-------|
| Alltags-Chat | qwen/qwen3.6-35b-a3b | Kostenlos, schnell |
| Bot-Architektur | qwen/qwen3.7-max | Agent-Frontier, Tool-Support |
| Input-Heavy | moonshotai/kimi-k2.6 | $0.684/M Input, Open-Weight |
| Persona-Text | anthropic/claude-sonnet-4.6 | Nuance, natürliche Sprache |

Siehe `references/model-selection-for-bots.md` für Details.

### Hermes Desktop voice config

Hermes Desktop uses the same `~/.hermes/config.yaml` settings as the Hermes CLI. For the Yuno voice stack, the recommended STT backend is **`faster-whisper`** (CTranslate2 INT8, ~5-10× faster than vanilla whisper) with the `large-v3` model for best German accuracy. Die Python-Deps müssen im Hermes-Venv installiert sein (siehe `references/hermes-desktop-voice-config.md` für den vollständigen Dep-Install + Config-Setup-Workflow). A small host-run script such as `scripts/apply_hermes_voice_config.sh` plus `hermes_voice_config.yaml` is the safest project artifact; apply it on the host and restart Hermes Desktop.

**KEY INSIGHT — built-in voice mode existiert:** Bevor du ein Plugin baust: Hermes hat `/voice on` (CLI, Telegram, Discord) und `/voice tts` (Auto-TTS für alle Antworten) **fest eingebaut**. Kein Plugin nötig. Aus Hermes CLI/TUI:

```text
/voice on       # Voice-Modus aktivieren
/voice tts      # Auto-TTS für ALLE Nachrichten
/voice status   # Status prüfen
```

**Persistentes Auto-TTS in config.yaml:**

```yaml
voice:
  auto_tts: true       # Automatische TTS-Wiedergabe
  record_key: "ctrl+b" # Aufnahme-Hotkey
```

Das TTS-Provider-Setup (minimax, edge, elevenlabs) ist separat in `tts.provider:` konfiguriert.

**Minimal local voice stack (base — works immediately):**

```env
LOCAL_STT_MODEL=base
TTS_PROVIDER=edge
EDGE_TTS_VOICE=de-DE-KatjaNeural
```

**Upgrade to faster-whisper large-v3 (95%+ German accuracy):**

```env
LOCAL_STT_MODEL=large-v3
STT_BACKEND=faster-whisper
TTS_PROVIDER=edge
EDGE_TTS_VOICE=de-DE-KatjaNeural
```

Siehe `references/hermes-desktop-stt-smoke-test.md` für das vollständige Upgrade-Pattern inkl. ensurepip, Pre-Load und Fallback-Chain.

set -euo pipefail
**Host-only apply pattern:**

```bash
./scripts/apply_hermes_voice_config.sh --dry-run
./scripts/apply_hermes_voice_config.sh
hermes config path
```

set -euo pipefail
Expected config:

```yaml
stt:
  enabled: true
  provider: local
  local:
    model: base

tts:
  provider: edge
  edge:
    voice: de-DE-KatjaNeural
```

set -euo pipefail
After applying, restart Hermes Desktop. If the agent is running in a Docker backend, do **not** assume files written under `~/...` exist on the user's desktop host. Either run the Hermes CLI on the host, provide a copy-paste host bootstrap, or use explicit bind mounts. Approval mode is not the cause of a missing host-side script; it is a filesystem boundary. Full recipe: `references/hermes-desktop-voice-config.md`.

### Testing

```bash
cd ~/yuno-voice-bot

# Dependencies lokal installieren (optional)
pip install -r requirements.txt

# Setup validieren
python3 -m py_compile *.py scripts/*.py
python3 -m unittest discover -s tests -v
python3 main.py --dry-run
python3 morning_cron.py --dry-run

# Discord-Invite und Live-Readiness prüfen
python3 scripts/discord_invite_url.py
python3 scripts/live_readiness.py

# Hermes-Desktop-Config anwenden (nur auf dem Host!)
./scripts/apply_hermes_voice_config.sh --dry-run
./scripts/apply_hermes_voice_config.sh
hermes config path

# Lokales LLM/STT vorbereiten (optional)
# Ollama:
NOUS_API_BASE_URL=http://127.0.0.1:11434/v1
LOCAL_LLM_MODEL=deepseek-r1:8b
LOCAL_LLM_MODEL=deepseek-r1:8b
# STT:\nSTT_PROVIDER=local\nLOCAL_STT_MODEL=base        # base (quick) or large-v3 (95%+ DE, via faster-whisper)
# TTS:
TTS_PROVIDER=local        # Piper, wenn LOCAL_TTS_MODEL gesetzt ist
# oder:
TTS_PROVIDER=edge         # einfachster Start ohne API-Key, aber Cloud
EDGE_TTS_VOICE=de-DE-KatjaNeural

# Docker-Build testen
docker compose up --build
```

⚠️ **PITFALL:** Für kurze Discord-Antworten ist GPU bei TTS meist nicht nötig. STT und LLM profitieren deutlich stärker von GPU; Piper TTS ist häufig auch auf CPU flüssig genug.

⚠️ **PITFALL:** `py_compile` beweist nicht, dass Live-Features funktionieren.**
Es zeigt nur, dass Python-Dateien syntaktisch laden. Echte Live-Tests brauchen echte Tokens/Credentials oder sauber gemockte Integrationstests.

⚠️ **PITFALL: Discord Client Secret gehört nicht in Runtime-Configs.** Für einen laufenden Bot werden `DISCORD_BOT_TOKEN`, optional `DISCORD_CLIENT_ID`, LLM-Key und optionale Fallback-Tokens gebraucht — aber kein `DISCORD_CLIENT_SECRET`. Wenn ein Client Secret sichtbar gepostet wurde, im Developer Portal rotieren und in der Doku nur den Security-Hinweis ohne Secret-Wert festhalten. Siehe `references/discord-invite-and-live-readiness.md`.

**Discord-Secret-Hygiene:** Client Secret, Bot-Token und Telegram-Token gehören
nie in README, Git, Chat oder Doku. Wenn ein Client Secret sichtbar gepostet wurde, rotieren
und nur `DISCORD_BOT_TOKEN` plus optional `DISCORD_CLIENT_ID` für Runtime/Invite
verwenden. Details: `references/discord-invite-and-live-readiness.md`.

**Host-vs-Docker-Grenze:** Wenn der Agent in einem Docker-Backend arbeitet,
existieren geschriebene Dateien nicht automatisch auf dem Desktop-Host. Wenn der
User ein Script nicht findet, nicht Approval Mode beschuldigen — zuerst prüfen,
ob `hermes` CLI im aktuellen Environment verfügbar ist, dann Config mit
`hermes config set ...` setzen, `hermes config path` verifizieren und Hermes
Desktop neu starten lassen. Wenn die CLI nur im Container läuft, Host-Copy-Paste
oder ein Host-Script bereitstellen. Details:
`references/hermes-desktop-voice-config.md`.

## 6. Hermes Gateway Telegram Voice Integration

### STT (Whisper) → Telegram Adapter Plugin

Statt eines standalone Discord Bots kann Voice direkt **im Hermes Gateway Telegram-Adapter** integriert werden.

**Architektur:**
```
User sendet Telegram Voice Message (.ogg)
        ↓
Telegram Adapter → cache_audio_from_bytes() → /tmp/.hermes_voice_*.ogg
        ↓
stt_helper.py (Whisper base Modell) → Transkription
        ↓
Transkription als Textnachricht injected → Agent antwortet
        ↓
text_to_speech Tool → MiniMax German_SweetLady → OGG Voice-Bubble
```

### Setup-Workflow

1. **STT Helper anlegen:** `plugins/platforms/telegram/stt_helper.py`
   - Whisper `base` Modell (142 MB, einmaliger Download)
   - Dekodiert OGG/Opus via pydub + ffmpeg
   - Cold Start ~4s (Modell-Load), Folgetranskription ~0.5s pro 10s Audio

2. **Telegram Adapter patchen:** `plugins/platforms/telegram/__init__.py`
   - Nach `cache_audio_from_bytes()` STT-Aufruf einhängen
   - Transkription per `on_text_message()` mit Feature `is_voice_transcription` injecten

3. **Config** in `config.yaml`:
   ```yaml
   telegram:
     extra:
       voice_stt:
         enabled: true
         model: base
         language: de
   tts:
     provider: minimax
     minimax:
       voice_id: German_SweetLady
   ```
   MiniMax braucht `MINIMAX_API_KEY` in `.env`. Config-Änderungen via Python/sed (patch()-Tool blockt config.yaml).

### P0 Pitfalls

- **Gateway Restart:** `hermes gateway restart` blockt in Sandbox. Nutze:
  ```bash
  systemctl --user stop hermes-gateway.service && sleep 3 && systemctl --user start hermes-gateway.service
  ```
- **Multi-Platform Conflict:** Discord mit totem Token verursacht Polling-Konflikte. Entferne aus `platforms:`-Liste und clean `gateway_state.json`.
- **MiniMax Emotion Tags:** `emotion=happy|sad|angry|surprised|fearful|disgusted|neutral` im `text_to_speech` Tool.
- **TTS Auto-Delivery:** Telegram zeigt MiniMax-Audio automatisch als runde Voice-Bubble (kein manuelles Media-Handling).

## Verknüpfte Skills

- `discord-voice` — **Lokaler Voice-Bot (ohne Docker):** discord.py + Edge-TTS + faster-whisper + Nous Portal LLM. Kein Google Cloud nötig, kein Docker. Plug-and-Play auf dem Host.
- `model-selector` — Modell-Vergleiche für Bot-Tasks
- `hermes-agent` — Hermes Konfiguration (protected)
- `messaging-gateway-setup` — Discord/Telegram Gateway

## Plugin-Entwicklung (Hermes)

Bevor du ein Hermes-Plugin für Voice baust: **/voice tts ist built-in und kein Plugin nötig.**

Wenn du trotzdem ein Plugin schreiben willst (z. B. für benutzerdefinierte Hooks):

1. Dein Hook-Name MUSS in `VALID_HOOKS` sein (siehe `references/valid-hooks.md`)
2. `post_response` / `on_response` / `response_complete` sind **keine gültigen Hooks**
3. Debug: `HERMES_PLUGINS_DEBUG=1 hermes`
4. Plugin-Verzeichnis: `~/.hermes/plugins/<name>/` mit `plugin.yaml` + `__init__.py`

## Referenzen

- `references/valid-hooks.md` — Komplette Liste der gültigen Hermes Plugin Hooks (VALID_HOOKS)
- `references/cron-pitfalls.md` — Detaillierte Cron-Erstellung & Debugging
- `references/model-selection-for-bots.md` — Modell-Tabelle für Voice-Bot-Tasks
- `references/telegram-fallback-and-live-testing.md` — Stdlib-Telegram-Sender, !ask LLM-Pattern (async-Thread), Live-Test-Methodik, synthetische Fixtures
- `references/discord-invite-and-live-readiness.md` — Discord-Invite-Link, Client-Secret-Safety und Live-Readiness-Check für Voice-Bots
- `references/stdlib-voice-bot-bootstrap.md` — P0-Bootstrap mit stdlib-only LLM/Telegram-Helfern und Smoke-Tests
- `references/discord-security-and-invite.md` — Discord Runtime-Secrets, Client Secret Rotation, OAuth-Invite ohne Secrets
- `references/local-llm-stt-architecture.md` — Ollama als lokales LLM, `faster-whisper` für STT, Modell-/VRAM-Empfehlungen und Test-Patterns
- `references/hermes-desktop-voice-config.md` — Hermes-Desktop-STT/TTS-Config, Host-vs-Docker-Grenze und Yuno-Minimalstack
- `references/hermes-desktop-stt-smoke-test.md` — STT-Smoke-Test: lokales Whisper via arecord+Script, Venv-Pfad-Pitfall (.venv vs venv/), Pre-Load-Pattern, Mikro-Diagnose
- `references/hermes-gateway-telegram-voice.md` — Hermes Gateway Telegram Voice Integration: Whisper STT + MiniMax TTS Plugin-Pattern

## Skripte

- `scripts/voice-stt-smoke.sh` — Wiederausführbarer STT-Smoke-Test für Hermes Desktop. Capture (arecord) + faster-whisper large-v3 (primär, CTranslate2 INT8) mit Fallback auf vanilla whisper base + automatische Venv-Detection + Pre-Load. Kopieren nach `~/.hermes/scripts/` und ausführen: `bash ~/.hermes/scripts/voice-stt-smoke.sh`.
