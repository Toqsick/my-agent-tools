# Project README Template

Every active project README should target **180–220 lines** with these mandatory sections.

## Project README Structure

### Project README Template (180-220 lines)

```markdown
# <Project Name>

## 📦 Status-Box

**Status:** 🟢 Active / 🟡 In Progress / 🔴 Blocked
**Last Updated:** YYYY-MM-DD
**Owner:** [Owner Name]

**Summary:** 2-3 sentence description of what this project does and why it exists.

## Quick Facts

| Key | Value |
|---|---|
| **Path** | `~/10-Projekte/10-active/<project-name>/` |
| **Version** | vX.Y.Z |
| **Owner** | [Owner Name] |
| **Created** | YYYY-MM-DD |
| **Language** | Go / Python / Dart / etc. |
| **Build System** | go build / pyproject.toml / flutter build |
| **Test Command** | go test ./... / pytest / flutter test |
| **Main Entry Point** | main.go / app.py / lib/main.dart |

## Architektur-Tree

```
<project-name>/
├── src/               # Source code
├── tests/             # Unit tests
├── docs/              # Documentation
├── config/            # Configuration files
└── README.md          # This file
```

## Setup-Steps

1. **Prerequisites**:
   - [ ] Go 1.21+ / Python 3.11+ / Flutter SDK
   - [ ] Required dependencies listed

2. **Installation**:
   ```bash
   git clone <repo-url>
   cd <project-name>
   # Install dependencies
   ```

3. **Configuration**:
   - [ ] Set environment variables in `.env`
   - [ ] Edit config file as needed

4. **Build**:
   ```bash
   # Build command
   ```

## Tool-Inventar

| Tool | Version | Purpose | Status |
|---|---|---|---|
| Tool Name | vX.Y.Z | Description | ✅ Active / ⚠️ Deprecated |
| Tool Name | vX.Y.Z | Description | ✅ Active |
| Tool Name | vX.Y.Z | Description | 🔴 Missing |

## Bekannte Issues

### 🔴 High Priority

- **[Issue Title]**
  - Description: Brief description
  - Impact: What breaks
  - Workaround: How to work around it
  - Status: In Progress / Open

### 🟡 Medium Priority

- **[Issue Title]**
  - Description: Brief description
  - Impact: What breaks
  - Status: Open

### 📋 Planned

- **[Feature Title]**
  - Description: Brief description
  - Priority: When to implement
  - Status: Planned

## Verwandte Projekte

- [[Related Project 1]] — Description of relationship
- [[Related Project 2]] — Description of relationship
- [[Related Project 3]] — Description of relationship

## Verbindet zu

- [[MOC - Projects]] — Project overview
- [[Glossar]] — Project-specific terminology
- [[Working Agreement - Yuno Basti]] — Development conventions
- [[Project-Name-]] — Related notes

## Glossar

| Akronym | Bedeutung |
|---|---|
| AAA | Authentication, Authorization, Accounting |
| MOC | Map of Content — Navigations-Hub |

## Wartungs-Log

| Date | Änderung | Author |
|---|---|---|
| YYYY-MM-DD | Initial README created | [Name] |
| YYYY-MM-DD | Added section for new feature | [Name] |
```

## Mandatory Sections & Line Counts

| Section | Purpose | ~Lines |
|---|---|---|
| `## 📦 Status-Box` | Status (🟢/🟡/🔴), Zusammenfassung | 5 |
| `## Quick Facts` | Key-value-Tabelle: Pfad, Version, Owner | 12 |
| `## Tool-Inventar` | Tools mit Pfad, Status, Notiz | 20 |
| `## Bekannte Issues` | 🔴 Hoch / 🟡 Mittel / 📋 Geplant | 15 |
| `## Verwandte Projekte` | Sibling-Links | 5 |
| `## Verbindet zu` | 5+ Wiki-Links (MOC, Glossar, …) | 8 |
| `## Glossar` | Projekt-Akronyme | 12 |
| `## Wartungs-Log` | Datum / Änderung | 5 |

## Anti-Halluzination-Verifikations-Workflow

When expanding project READMEs, Cluster 1 must verify EVERY data point against 3+ source types before writing:

1. **Git log** — commits, branches
2. **Package files** — `go.mod`/`pyproject.toml`/`package.json` (versions, licenses)
3. **README.md** — upstream URL, features
4. **Source files** — actual code structure (architecture)

If a repo is missing or locked → write "⚠️ Repository nicht gelesen — manuelle Füllung nötig" instead of guessing.

**Proven 2026-07-05:** 5/5 READMEs filled with verified data, 0 hallucinated details. Typo caught and patched.