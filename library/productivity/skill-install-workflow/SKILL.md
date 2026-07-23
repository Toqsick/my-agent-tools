---
name: skill-install-workflow
description: >-
  Use when user asks for installing a skill from a GitHub repository, copying an external skill into Hermes, documenting an installed skill, or handling a repository that contains multiple skills. NOT for authoring a new skill from scratch or installing ordinary application packages. Uses a three-step import, Hermes placement, description-documentation, structure, security review, and multi-skill repository workflow.
version: 1.0.0
lane: worker-flash
reasoning_effort: high
author: Hermes Agent
license: MIT
trigger_keywords: ['skill', 'repository', 'installing', 'hermes', 'user']
keywords: ['skill', 'repository', 'installing', 'hermes', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['course-repo-builder', 'hermes-agent-skill-authoring', 'skill-creator']
---


# Skill-Install-Workflow

Standard-Workflow zum Installieren von skills.sh-Skills als Hermes-Skill.

## Voraussetzungen

- `npx` ist nicht im globalen PATH. Nutze:
  ```bash

set -euo pipefail
  export PATH="$HOME/.hermes/runtime/node/bin:$PATH"
  # Oder direkt:
  ~/.hermes/runtime/node/bin/npx skills <command>
  ```

## 3-Schritt-Workflow

### Schritt 1: OpenCode-Installation
```bash

set -euo pipefail
# Skill aus GitHub-Repo installieren
npx skills add <owner/repo> --skill <skill-name> --agent opencode --yes

# Beispiel:
npx skills add vercel-labs/agent-skills --skill web-design-guidelines --agent opencode --yes
```
→ Kopiert die Skill-Dateien nach `~/.hermes/.agents/skills/<skill-name>/`

### Schritt 2: Als Hermes-Skill kopieren

1. Verzeichnis erstellen: `mkdir -p ~/.hermes/skills/<skill-name>`
2. `SKILL.md` von `~/.hermes/.agents/skills/<skill-name>/SKILL.md` kopieren
3. **Frontmatter anpassen:**
   - `description` auf Deutsch übersetzen
   - In der Body-Sprache Englisch belassen (Skills sind international)
4. **Body auf Deutsch übersetzen** wenn der Skill primär für Hermes gedacht ist
5. Support-Dateien (references/, templates/, scripts/) mitkopieren

### Schritt 3: DESCRIPTION.md erstellen

Erstelle `~/.hermes/skills/<skill-name>/DESCRIPTION.md` mit:

```markdown
# <skill-name> — Skill-Beschreibung

**Name:** <skill-name>
**Version:** x.x.x
**Autor:** <author>
**Quelle:** https://github.com/<owner>/<repo>
**Installs:** xxx (skills.sh)
**Lizenz:** MIT/Apache/Proprietary

## Was ist das?
[< 3 Sätze: Was, Wann, Output]

## Wann nutzen?
[Bullet-Points]

## Wie funktioniert's?
[Kurze Anleitung]

## Important Notes
[Hinweise für Hermes-spezifische Anpassungen]

## Sicherheit
[Gen + Socket + Snyk wenn relevant]
```

set -euo pipefail
## Verzeichnis-Struktur nach Installation

```
~/.hermes/skills/<skill-name>/
├── SKILL.md          # YAML Frontmatter + Markdown Body (Deutsch Beschreibung)
├── DESCRIPTION.md    # Metadaten + Kurzreferenz
├── references/       # Optional: Referenz-Dateien
│   └── *.md
├── templates/        # Optional: Templates
│   └── *.*
└── scripts/          # Optional: Skripte
    └── *.py
```

set -euo pipefail
## Multi-Skill-Repos

Einige Repos enthalten mehrere Skills (z.B. `anthropics/skills` mit pdf, docx, xlsx, pptx):

```bash
# Einzelnes Skill installieren
npx skills add anthropics/skills --skill pdf --agent opencode --yes

# Dann einzeln als Hermes-Skill kopieren
mkdir -p ~/.hermes/skills/pdf
cp ~/.hermes/.agents/skills/pdf/SKILL.md ~/.hermes/skills/pdf/SKILL.md
# Frontmatter + Body anpassen
```

## Pitfalls

1. **npx nicht gefunden**: `~/.hermes/runtime/node/bin/npx` statt `npx`
2. **Skill-Name ≠ Repo-Name**: Prüfe verfügbare Skills mit `npx skills add <repo> --list`
3. **Allowed-tools Feld**: skills.sh Skills nutzen `allowed-tools`, Hermes nutzt `toolsets` — nicht kompatibel, ignorieren
4. **WebFetch → web_extract**: skills.sh Skills referenzieren `WebFetch`, Hermes nutzt `web_extract` — im Body anpassen

## Beispiele

Skills die nach diesem Workflow installiert wurden:
- `find-skills` aus vercel-labs/skills (1.5M installs)
- `web-design-guidelines` aus vercel-labs/agent-skills (420K installs)
- `vercel-react-best-practices` vercel-labs/agent-skills (390K installs)
- `pdf` aus anthropics/skills (100K installs)
- `context-mode` aus mksglu/claude-context-mode (trending)
- `firecrawl-web` aus BexTuychiev/firecrawl-claude-code-skill
- `model-selector` (eigener Skill, wird regelmäßig aktualisiert)
