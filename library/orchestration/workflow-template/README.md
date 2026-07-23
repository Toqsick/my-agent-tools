# Workflow-Template Skill

Bastis Standard-Workflow für strukturiertes Multi-Agent-Planen über fünf Domänen hinweg.

## Was ist das?

Domain-Adapter für den etablierten `multi-agent-master-workflow`-Skill. Fünf wiederverwendbare Templates für:

- **01-server-hardening** — Linux/Cloud-Server absichern (Homelab, VPS, Cloud)
- **02-repo-cicd** — GitHub-Repo aufräumen + CI/CD aufsetzen (Python, GreyScript, Vault, ...)
- **03-security-cve** — CVE-Analyse mit Quellen-Disziplin
- **04-greyscript** — Grey Hack-Tool-Entwicklung mit allen GreyScript-Specifika
- **05-ollama-llm** — Lokales LLM-Setup auf RTX-basierter Hardware

## Installation

Skill lebt in `~/.hermes/skills/orchestration/workflow-template/` — user-local installiert.
Wird beim nächsten Hermes-Start automatisch geladen (Loader-Cache!).

Aktuelle Session sieht den Skill möglicherweise erst nach `/new`-Befehl.

## Usage

Trigger-Phrasen im Chat:
- "ich brauche einen Plan für [X]"
- "multi-agent master workflow für [Domäne]"
- "systematischer plan für [X]"
- "standard workflow für [X]"

Yuno lädt das passende Template und folgt der Phase-1 → Phase-2-Struktur.

## Architektur

```
SKILL.md                    ← Haupt-Skill (Loader liest das)
├── references/
│   ├── meta/
│   │   ├── color-legend.md       ← 🟥🟧🟨🟩 Standard
│   │   ├── mnemosyne-hooks.md    ← Memory-Disziplin pro Template
│   │   └── changelog.md          ← Versions-Historie
│   └── templates/
│       ├── 00-decision-tree.md   ← Welches Template?
│       ├── 01-server-hardening.md
│       ├── 02-repo-cicd.md
│       ├── 03-security-cve.md
│       ├── 04-greyscript.md
│       └── 05-ollama-llm.md
```

## Maintenance

- Neues Domain-Template: Minor-Version-Bump, File in `references/templates/`
- Breaking Change in Phase-1-Output: Major-Bump
- Pitfall/Fix ergänzt: Patch-Bump + Changelog-Eintrag

## Source-of-Truth

- Original-Material: `~/Dokumente/Perplexity/workflow_templates_verschiedene_themengebiete.md` (v1)
- Master-Workflow-Pattern: `~/.hermes/skills/multi-agent-master-workflow/`
- Konsolidierungsnotiz (Original-Master-Files in `~/Downloads/Github/`): siehe System-Doc
