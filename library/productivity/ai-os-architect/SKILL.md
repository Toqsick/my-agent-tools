---
name: ai-os-architect
description: >-
  Use when user asks for designing a personal AI operating system, connecting Obsidian with coding agents, planning reusable skills, routines, and integrations, or setting up remote AI-assistant access. NOT for installing one isolated tool or enterprise operating-system administration. Organizes knowledge, connections, skills, routines, remote access, and cost controls into a practical personal-assistant architecture.
version: 1.0.0
author: Yuno (für Basti)
license: MIT
platforms:
- linux
- macos
- windows
tags:
- claude-code
- obsidian
- ai-orchestration
- pkm
- productivity
- skills
metadata:
  hermes:
    tags:
    - claude-code
    - obsidian
    - ai-orchestration
    - pkm
trigger_keywords: ['personal', 'operating', 'system', 'skills', 'routines']
keywords: ['personal', 'operating', 'system', 'skills', 'routines']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---


# AI Operating System Architect

Hilft beim **schrittweisen Aufbau** eines persönlichen KI-Betriebssystems basierend auf Julian Ivanovs Tutorial-Architektur.

## Wann nutzen

- Du willst Claude Code als persönlichen Assistenten aufsetzen
- Du brauchst eine Struktur für Obsidian + Claude Code Zusammenarbeit
- Du willst dein eigenes System auf einem VPS für Mobile-Zugriff
- Du suchst Inspiration für Skills, Routinen, Verbindungen

## Die 4 Bausteine

### Baustein 1: Wissen (Obsidian + CLAUDE.md)

**Setup-Schritte:**
1. Obsidian herunterladen (obsidian.md)
2. Vault erstellen (= leerer Ordner)
3. Claudian-Plugin installieren (Claude Desktop + Obsidian Brücke)
4. Obsidian-Skill via `/install <repo>` in Claude Code laden
5. CLAUDE.md Onboarding-Vorlage aus Download-Hub holen
6. In Vault-Root legen, Claude Code mit "Mach das Onboarding" starten

**8-Ordner-Struktur:**
```
Kontext/     # Über dich, Branding, Schreibstil
Inbox/       # Tägliche Gedanken, Brain-Dump
Projekte/    # Aktive Aufgaben mit Deadline
Bereiche/    # Laufende Verantwortlichkeiten
Ressourcen/  # Allgemeines Wissen, Tool-Dokumentationen
Daily Notes/ # Tagesprotokolle
Archiv/      # Abgeschlossene Projekte
Anhänge/     # Bilder, PDFs
```

Für Zorin/Ubuntu-Systeme heißt es `Kontext` und `Inbox` (nicht `01 Kontext`), wenn du deutsche Ordnernamen ohne Nummern-Präfix willst. Wenn du das Julian-Ivanov-Original mit numerischem Präfix (`01 Kontext/`, `02 Inbox/` …) bevorzugst, hilft `scripts/scaffold-julian-ivanov-vault.sh` — es legt die Ordner an und schreibt eine MOC-Hub-Seite in Vault-Root (idempotent, Backup alter MOC). Für Vault-Pfad-Edge-Cases (Env-Variable leer + Fallback existiert nicht) siehe `references/obsidian-vault-scaffold.md`. Für das Per-Projekt-4-Notizen-Split (README/Plan/CHANGELOG/Troubleshooting) ist die gleiche Referenzdatei die Vorlage.

### Baustein 2: Verbindungen (Skills + MCP + CLIs)

**Strategie:** CLI > MCP (token-effizienter)

**Top-Plugins die Julian empfiehlt:**
1. Excalidraw Skill (Cole Medin)
2. NotebookLM-py (Google NotebookLM)
3. Remotion Skill (Video-Animationen)
4. Context7 CLI (Upstash)
5. Firecrawl CLI + Skill (Web-Scraping)
6. Playwright CLI (Browser-Automation)
7. Obsidian Skills (kepano)
8. Feature Dev Plugin (Anthropic)
9. Superpowers Plugin (obra)
10. CLAUDE.md Management Plugin (Anthropic)

**Installation:** Link kopieren, in Claude Code einfügen, "Installiere das" sagen.

### Baustein 3: Skills

**Skill = Markdown-Datei mit Anweisungen, lädt on-demand in Context.**

**Plugin = Skill + zusätzliche Dateien** (Referenzen, Scripts, MCP)

**Faustregel:** Alles was du Claude mehr als 2× erklärst → Skill werden

**Workflow:**
1. Skill-Idee: Was soll Claude können?
2. SKILL.md schreiben mit YAML-Frontmatter + Anweisungen
3. In `.claude/skills/<skill-name>/` legen
4. Testen mit `/skills` reload
5. Bei Bedarf: zusätzliche Referenzen + Scripts → Plugin

### Baustein 4: Routinen

**Scheduled Tasks + Automation für wiederkehrende Abläufe.**

**Beispiele:**
- Tägliche Backups via cron
- Wöchentliche Reports aus Daily Notes
- Memory-Flush Sessions
- Auto-Sync Vault via Git

## Remote-Zugriff (Bonus-Kapitel)

**Stack:**
1. **GitHub** — Versionskontrolle für Vault + CLAUDE.md + Skills
2. **VPS** — bei Hostinger mit Code `JULIANIVANOV` für 10% Rabatt
3. **SSH** — vom Terminal/VS Code zum Server
4. **Git-Sync** — Obsidian ↔ Server via Git Plugin
5. **SSH-App auf Mobile** — Claude Code vom Handy aus

**Dashboard (Bonus):** Übersicht über alle laufenden Tasks + Verbindungen.

## Kosten-Reduktion

**Modell-Strategie:**
- **Opus 4.6** → nur für komplexe Coding-Tasks
- **Sonnet 4.5** → Standard (Best Balance)
- **Haiku** → Schnelle Klassifizierung
- **Kimi K2.5** (Moonshot, Open-Source) → günstige Alternative
- **Gemini 2.0 Flash** → ultra-billig

**Bis zu 80% Kostenersparnis.**

## Pitfalls

1. **CLAUDE.md zu lang** → Performance sinkt. <200 Zeilen halten (ETH-Studie)
2. **Globale Installation** von Skills → frisst Context in jedem Projekt. IMMER auf Projektebene
3. **MCP-Server mit vielen Tools** → 10%+ Context-Verbrauch allein für Tool-Definitions
4. **"Cloud" vs "Claude" verwechselt** → Auto-Caption-Hörfehler, in Transcripts prüfen
5. **Slash-Initiate generierte CLAUDE.md** → oft schlechter als manuell geschrieben (ETH-Studie)

## Erste-Schritte-Checkliste

- [ ] Obsidian heruntergeladen
- [ ] Vault erstellt
- [ ] Claudian-Plugin installiert
- [ ] CLAUDE.md Onboarding-Vorlage geholt
- [ ] 15-20 Min Onboarding durchgeführt
- [ ] 3 wichtigste Skills installiert (Context7, Excalidraw, Obsidian-Skill)
- [ ] Erste Daily Note geschrieben
- [ ] (Optional) Git-Repo für Vault erstellt
- [ ] (Optional) VPS gebucht + SSH-Setup

## Siehe auch

- `youtube-transcript-saver` — für die Source-Transkripte
- `references/obsidian-vault-scaffold.md` — Vault-Pfad-Edge-Cases + Per-Projekt-4-Notizen-Split-Vorlagen
- `scripts/scaffold-julian-ivanov-vault.sh` — legt 8 Ordner + MOC in Vault-Root an (idempotent)
- `claude-code-setup` (geplant) — für initiale Claude Code Konfiguration