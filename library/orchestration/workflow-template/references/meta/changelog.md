# Changelog: workflow-template

Versions- und Inhalts-Historie dieses Skills.

## [1.0.1] — 2026-07-05 — Post-Release Patch

### Geändert

- Pitfall #6 (Loader-Cache) korrigiert: `skill_view` funktioniert SOFORT, kein Session-Neustart nötig (live bewiesen in Build-Session)
- Changelog "Bekannte Limitierungen" aktualisiert (Loader-Cache-Irrtum entfernt)

### Hinzugefügt

- `references/consolidation-pattern.md` — wiederverwendbare Technik zur Konsolidierung mehrerer Derivativ-Quellen in einen Skill
- Querverweis auf Consolidation-Pattern im SKILL.md Overview

## [1.0.0] — 2026-07-05 — Initial Release

### Hinzugefügt

- Haupt-Skill `SKILL.md` mit Trigger-Phrasen, Decision-Tree, Farb-Legende, Mnemosyne-Disziplin
- 5 Domain-Templates als separate References:
  - `01-server-hardening.md` — Linux/Cloud-Hardening mit 7 Sub-Agenten
  - `02-repo-cicd.md` — GitHub-Repo-Hygiene mit 6-Profil-Decision-Tree
  - `03-security-cve.md` — CVE-Analyse mit Sources-First + CVSS-Regeln
  - `04-greyscript.md` — GreyScript-Entwicklung mit 10 Constraint-Items
  - `05-ollama-llm.md` — Ollama-Setup mit Quant-Tabelle + num_gpu-Formel
- Meta-References:
  - `color-legend.md` — 🟥🟧🟨🟩 Standard-Doku
  - `mnemosyne-hooks.md` — Hooks pro Template mit importance/source Mapping
- Decision-Tree `00-decision-tree.md` mit Profilen pro Template
- README im Skill-Root für Maintenance-Instruktionen
- `combinations.md` — Multi-Domain-Patterns

### Quellen

- v1 Original: `~/Dokumente/Perplexity/workflow_templates_verschiedene_themengebiete.md`
- Master-Pattern: `~/.hermes/skills/multi-agent-master-workflow/`
- Konsolidierungsnotiz: System-Doc `~/docs/system/workflow-templates-standard-2026-07-05.md`

### Bekannte Limitierungen (v1.0.0)

- 5 Profile pro Domain-Template ist initial abdeckend, weitere Profile ad-hoc erweiterbar
- Konflikt-Resolution mit `multi-agent-master-workflow` braucht Re-Test in Production
- Kombinations-Templates als Stub (`combinations.md`); v1.1 füllt sie mit Leben

### Lessons Learned (für v1.1)

- Test-Plan pro Template weiter vereinheitlichen
- Shell-Wrapper-Script (`bin/workflow-template`) für Headless-Aufruf
- Weitere Domain-Templates: Obsidian-Vault-Cleanup, Docker-Compose-Setup, Discord-Bot-Architektur
