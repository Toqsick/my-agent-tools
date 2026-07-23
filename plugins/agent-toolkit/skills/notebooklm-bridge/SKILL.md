---
name: notebooklm-bridge
description: >-
  Use when user asks for managing NotebookLM notebooks and sources, asking citation-grounded questions over uploaded material, generating audio briefings or artifacts, or troubleshooting nblm authentication. NOT for general Google Drive editing or ungrounded open-web research. Operates NotebookLM through the nblm CLI for source ingestion, cited synthesis, artifact generation, auth refresh, and repo-doc Q&A.
version: 1.0.0
author: Yuno
license: MIT
platforms:
- linux
- macos
metadata:
  hermes:
    tags:
    - notebooklm
    - google
    - rag
    - synthesis
    - audio-overview
    - citation
    - cli-bridge
lane: worker-heavy
reasoning_effort: medium
agent: Researcher
routing_hint: '**Agent-Scope:** Deep-research, fact-checking, paper-search, knowledge-base.
  Off-scope: code-building, visual design, writing — return to Yuno.


  Routing-Spec: `yuno-team-routing`.

  '
---

---

# NotebookLM-Bridge

Drive Google's NotebookLM from Hermes via `notebooklm-py` (offizielles Python-CLI, v0.7.3+). Quellen rein, Gemini-gestützte Antworten mit **Zitaten** raus, plus Artifact-Generation (Audio, Video, Slides, Quiz, Mindmap, Report).

## Setup-Status auf Bastis Box

- **Tool installiert:** `uv tool install "notebooklm-py[browser]"` → v0.7.3
- **Binary:** `/home/bratan/.local/bin/notebooklm`
- **Wrapper:** `/home/bratan/50-System/bin/notebooklm-wrapper.sh`
- **Shortcut:** `~/50-System/bin/nblm` (Symlink)
- **Profile-Storage:** `~/.notebooklm/profiles/default/`
- **Auth-Status:** wechselnd — vor jeder Session `nblm auth check --test --json` verifizieren
- **MCP-Server:** eingebaut (`notebooklm mcp serve`), aber **nicht in Hermes registriert** — siehe [references/registration.md](references/registration.md)

## Wenn `nblm` nicht gefunden wird

Klassische PATH-Falle — `~/.local/bin/` ist nicht in jedem Shell-PATH. Wrapper-Skript setzt das automatisch. Falls auch der Wrapper nicht greift:

```bash
export PATH="$HOME/.local/bin:$PATH"
which notebooklm   # muss was zurückgeben
```

## Befehls-Basis (CLI via `nblm`)

### Auth & Diagnose

```bash
nblm login                              # Browser-Login (1x), triggert Chromium-Download
nblm login --browser-cookies chrome     # Cookies aus Chrome übernehmen
nblm login --master-token --account you@gmail.com   # langlebiges Token, unattended
nblm auth check --test --json           # Health-Check
nblm doctor                             # Voll-Diagnose
```

### Notebooks

```bash
nblm list                               # Alle Notebooks listen
nblm create "Titel"                     # Neues Notebook
nblm create "Titel" --sources url1,url2 # Mit initialen Quellen
nblm use <id>                           # Aktives Notebook setzen
nblm use <partial-id>                   # Eindeutiger Prefix reicht
nblm status                             # Welches Notebook + Conversation aktiv?
nblm clear                              # Kontext zurücksetzen
nblm profile list                       # Multi-Account-Profile
```

### Quellen

```bash
nblm source add <url>                   # Web/YouTube als Quelle
nblm source add <datei.pdf>             # Lokale Datei (PDF, MD, EPUB, Audio, Video, Image)
nblm source add-research "topic"        # Web-Research-Agent (fast/deep)
nblm source add-research "topic" --mode deep   # Tieferes Research
nblm source list                        # Quellen im aktiven Notebook
nblm source get <id>                    # Volltext einer Quelle
nblm source refresh <id>                # Quelle neu laden
```

### Fragen (cited Q&A)

```bash
nblm ask "Frage"                        # Antwort im Markdown
nblm ask "Frage" --json                 # Strukturierte Antwort mit Zitaten
nblm ask "Frage" --save-as-note         # Antwort als Notiz speichern
nblm ask "Frage" --persona "Du bist ein Senior-Architekt"   # Custom-Persona
```

### Artifact-Generation

```bash
nblm generate audio                     # Audio Overview (Podcast, MP3)
nblm generate audio --format deep-dive --length long --language de
nblm generate video                     # Video Overview (MP4)
nblm generate slide-deck                # Slides (PDF/PPTX)
nblm generate mind-map                  # Mindmap als JSON
nblm generate quiz                      # Quiz (JSON/MD/HTML)
nblm generate flashcards                # Karteikarten
nblm generate report                    # Bericht (briefing-doc/study-guide/blog-post)
nblm download audio                     # Generiertes MP3 herunterladen
nblm download report                    # Report als Markdown
nblm download mind-map --kind note-backed   # alternative Mindmap-Variante
```

## Typische Workflows

### 1. Master-Brain-Notebook

Persistent cross-session memory. Jede Session schreibt wichtige Entscheidungen als Notiz, neue Sessions fragen das Brain kurz ab.

```bash
nblm use <master-brain-id>
nblm ask "Was waren die wichtigsten Entscheidungen der letzten 7 Tage?"
# Antwort mit Zitaten auf vorherige Notizen
```

### 2. Source-Synthese-Briefing

Mehrere Quellen in ein Notebook, daraus einen kompakten Briefing-Doc ziehen.

```bash
nblm create "Briefing: Topic"
nblm source add https://example.com/spec.pdf
nblm source add https://github.com/owner/repo
nblm source add ~/docs/whitepaper.pdf
nblm generate report --format briefing-doc --wait
nblm download report --output ~/briefings/topic-$(date +%F).md
```

### 3. Audio-Briefing (cron-fähig)

```bash
nblm use <daily-brief-id>
nblm generate audio --format brief --language de
nblm download audio --output ~/podcasts/brief-$(date +%F).mp3
```

Kombinierbar mit `nblm login --master-token` für unbeaufsichtigten Refresh.

### 4. Grounded Q&A über Repo-Docs

Coding-Fragen aus deinen eigenen Docs beantwortet bekommen — mit Zitaten, ohne Halluzinationen.

```bash
nblm create "Projekt-Brain"
nblm source add ~/docs/system/*.md      # deine Docs als Quellen
nblm ask "Wie ist die NVIDIA-Power-Management-Konvention auf dieser Box?"
# Antwort zitiert ~/docs/system/nvidia-...md
```

## Auth & Refresh

**Cookie-Lebensdauer:** typischerweise einige Wochen. Symptom des Ablaufs: 401/403 bei `nblm ask`.

- **Manuell:** `nblm login` (Browser-Login wiederholen)
- **Automatisch (cron-tauglich):** `nblm login --master-token --account you@gmail.com` mintet on-demand frische Cookies
- **Auth-Healthcheck** vor jeder längeren Workflow-Kette: `nblm auth check --test --json`

## Pitfalls

- **Cookies laufen ab** → alle paar Wochen Refresh, oder Master-Token-Mode
- **Rate Limits** — Google throttelt bei Heavy Use. Aufteilung auf mehrere Notebooks hilft
- **Erste `nblm login` braucht Browser** — Playwright-Chromium wird automatisch gedownloaded (~170 MB)
- **Linux + Playwright:** bei `TypeError: onExit is not a function` siehe Library-Troubleshooting
- **`~/.hermes/` Sandbox-Schutz:** Auth-State NICHT dort ablegen, sondern in `~/.notebooklm/`
- **Web-Tools-Offline:** wenn Firecrawl nicht konfiguriert, `web_extract` schlägt fehl → direkt `curl` nutzen (z.B. `curl -sL https://raw.githubusercontent.com/<owner>/<repo>/main/README.md`)

## MCP-Bridge-Modus (auf Freigabe warten)

Die Library bringt einen eingebauten MCP-Server mit (`notebooklm mcp serve`). Registrierung in `~/.hermes/config.yaml` macht NotebookLM direkt aus Yuno-Sessions aufrufbar — als `mcp__notebooklm__*` Tools.

**Status:** nicht registriert (Sandbox-Schutz). Basti muss explizit Freigabe für `config.yaml`-Edit geben. Siehe [references/registration.md](references/registration.md) für Setup-Snippet, Verifikation und Pitfalls.

## Weitere Doku

- Repo: <https://github.com/teng-lin/notebooklm-py>
- PyPI: <https://pypi.org/project/notebooklm-py/>
- CLI-Reference: `https://github.com/teng-lin/notebooklm-py/blob/main/docs/cli-reference.md`
- MCP-Guide: `https://github.com/teng-lin/notebooklm-py/blob/main/docs/mcp-guide.md`
- Lokale Projekt-Kopie: `~/10-Projekte/10-active/notebooklm-bridge/SKILL.md`
