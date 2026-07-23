# Context-Dependent Entity Mappings

Manche Auto-Caption-Hörfehler sind **Channel-spezifisch** — derselbe akustische Input kann je nach Creator ein anderes Tool/System meinen. Hier dokumentiert: bekannte Channel und ihre spezifischen Entitäten.

## Julian Ivanov (KI-Automatisierung, youtube.com/@julianivanov)

### Agentische Systeme — die Trinität

Julian nennt in seinen Videos regelmäßig drei agentische Systeme als seine **Haupt-Toolchain**:

| Aussprache / Auto-Caption | Gemeint | Häufigkeit |
|--------------------------|---------|-----------|
| Claude Code | Claude Code (Anthropic) | Jedes Video, durchgängig |
| Codex | Codex (OpenAI) | Jedes Video, 2-5x |
| **OpenCla** (ohne w) | **OpenClaw** (Julians eigenes Tool, published auf GitHub) | Jedes Video, 2-5x |
| Hermes | Hermes Agent (Nous Research) | Nur Compilation-Video |

**Wichtig:** `OpenCla` heißt in Julian-Videos **NIE** `OpenCode` (wie ich in Video 1 fälschlich annahm). Es ist sein **eigenes Tool** `OpenClaw`, das er in der Trinität `Claude Code, Codex, OpenClaw, Hermes` aufzählt.

### Julian-Spezifische Korrekturen

| Auto-Caption | Korrekt | Channel-Besonderheit |
|-------------|---------|---------------------|
| `OpenCla` (ohne -w) | `OpenClaw` | **NUR bei Julian** — nicht generic! Siehe Agentische-Systeme-Trinität oben |
| `OpenClaw` | `OpenClaw` (korrekt, nicht patchen) | Bereits korrekt, ist sein Tool-Name |
| `Claudian` | `Claudian` (Obsidian-Plugin, korrekt) | Name des Plugins, nicht "Claude"(n) zu patchen |
| `JULIANIVANOV` (Rabattcode) | `JULIANIVANOV` | Hostinger-Rabattcode, großgeschrieben |
| `Jurian Ivanov` / `Jorian` | `JULIANIVANOV` | Hörfehler die den Rabattcode verhunzen |

### Julian-Use-Cases (wiederkehrend)

Die 5 Use Cases aus Video 1 + 10 Skills aus Video 4 sind permanente Referenzen:
- **1. Morgen-Briefing**: Notion/Google Tasks + Claude Code → Daily Plan
- **2. Journal**: Claude Code → Obsidian Eintrag 1x/Woche
- **3. Konkurrenz-Research**: Topics → Recherche → Claude.Vibes → Notion
- **4. Claude Code 30-Tage-Challenge**: Geschützte Feature-Dev-Umgebung
- **5. 6-Monats-Review**: Periodische Analyse aller Claude-Code-Sessions

Top-10-Plugins-Reihenfolge (Video 4):
1. Obsidian-Skills (MCP-Server für Vault-Zugriff)
2. Excalidraw (Whiteboard-Diagramme)
3. NotebookLM (Google Podcasts from Notes)
4. Remotion (Code-zu-Video-Rendering)
5. Context7 (GitHub-Issue-Kontext)
6. Firecrawl (Webscraping)
7. Playwright (Browser Automation)
8. Feature Dev (Anthropic Feature-Dev-Plugin)
9. Superpowers (Tool-Integrationen)
10. CLAUDE.md Management

### OpenClaw-Spezifisches Vokabular

Julian verwendet in Video 1 spezifische OpenClaw-Features die für Auto-Captions schwer sind:

| Auto-Caption | Korrekt | Kontext |
|-------------|---------|---------|
| Heartbeat | Heartbeat | Feature: Pausen-Überwachung |
| Outlayer | Outlier | Statistische Abweichungsanalyse |
| Kanboard | Kanban-Board | Visual Dashboard |
| Tasksow / Tagessow | Tagesthemen | News-Integration |
| N8N-Integration | n8n | Workflow-Automation |

## Generic (alle anderen KI-Coding-Channels)

Wenn der Channel **nicht** Julian Ivanov ist:

| Auto-Caption | Korrekt | Grund |
|-------------|---------|-------|
| `OpenCla` | **Context-abhängig** | Unbekanntes Tool → im Original belassen und im Header markieren. Nicht raten! |
| `Claude Code`, `Cloud Code` | `Claude Code` | Standard-Korrektur |
| `Hermes` | `Hermes` | Nous-Research-Tool |

## Disambiguierungs-Regel

1. **Channel identifizieren** (aus Description/Metadaten)
2. **Channel-spezifische Entity-Map laden** (diese Datei)
3. **Generic-Fallback**: Wenn Channel unbekannt → Standard-Korrektur aus `known-hearing-errors.md`, `OpenCla` unverändert lassen

## Siehe auch

- `known-hearing-errors.md` — Alle generic Patterns
- `youtube-transcript-saver/SKILL.md` — 5c Heuristik-Liste mit Channel-Hinweis
