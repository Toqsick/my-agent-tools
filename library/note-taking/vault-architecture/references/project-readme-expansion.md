# Project README Expansion — Verification Workflow

> Worked example from 2026-07-05: 5 Project-READMEs expanded to 174–236 lines with Status-Box, Quick-Facts, Architektur-Tree, Setup, Tool-Liste, Bekannte Issues, Glossar, and Wiki-Links. Anti-Halluzinations-Tripwire strikt eingehalten.

## Structure Template

Every expanded Project README should contain these sections in order:

```
# 🎮/🐧/💻 Projekt: <Name>

> Kurzbeschreibung (1 Satz)

## 📦 Status-Box
→ 🟢 AKTIV / 🟡 PAUSE / 🔴 BLOCKIERT / ✅ DONE
→ 1–2 Sätze: Was ist das Projekt, was wurde erreicht, was ist offen

## Quick Facts
| Feld | Wert |
|---|---|
| Status | 🟢 aktiv |
| Priorität | P0–P3 |
| Start-Datum | YYYY-MM-DD |
| Owner | Basti + Yuno |
| Repo / Pfad | ~/10-Projekte/... |
| Version | (git tag, Version-File) |
| Letzter Stand | YYYY-MM-DD |

## <Projekt-spezifische Sektionen>
Architektur, Setup, Installation, etc.

## Tool-Inventar / Tool-Liste
| Tool | Pfad / Paket | Status | Notiz |
|---|---|---|---|

## Bekannte Issues / Offene Findings
### 🔴 Hoch
### 🟡 Mittel
### 📋 Geplant

## Verwandte Projekte
→ [[Sibling-Links]] zu anderen Projekten im Vault

## Verbindet zu
→ [[MOC - Projekte]], [[Glossar]], [[MOC - <Domäne>]], …

## Glossar (Projekt-spezifische Akronyme)
Siehe [[Glossar]] für Vault-weite Akronyme.

## Wartungs-Log
| Datum | Änderung |
|---|---|

## Referenzen (zu anderen Notes)
```

## Anti-Halluzinations-Tripwire — Project README Verification

**Rule:** Before writing ANY content to a Project README, verify EVERY data point against real source files. Follow this checklist:

### 1. Project Directory Verification

```bash
ls <project-dir>/              # Struktur lesen
ls <project-dir>/*/             # Subdirs checken
```

**Was prüfen:** Existiert das Projekt? Liegt es am erwarteten Pfad? Welche Subdirs gibt es?

### 2. Git Check

```bash
cd <project-dir> && git log --oneline -5 2>&1 | head -10
cd <project-dir> && git describe --tags --always 2>&1
```

**Was prüfen:** Gibt es einen Git-History? Letzter Commit? Tag? Branch? Falls kein Git: "kein Git-Repo" im README vermerken, nicht "main/latest" erfinden.

### 3. Language-Specific Source Check

| Sprache | Quellen | Was extrahieren |
|---|---|---|
| **Python** | `pyproject.toml`, `requirements.txt`, `setup.py`, `setup.cfg` | Paketname, Version, Dependencies |
| **Node** | `package.json` | Projektname, Version, npm-Dependencies |
| **Go** | `go.mod` | Modul-Pfad, Go-Version, Dependencies |
| **Shell** | `head -30 <script.sh>` | Shebang, Kommentar-Header, CLI-Args |
| **Rust** | `Cargo.toml` | Paketname, Version, Dependencies |
| **Config/Env** | `*.env`, `*.env.template`, `*.template.env`, `config.yaml` | Config-Struktur, Secrets-Bedarf |

**Konkretes Vorgehen:**

```bash
# Für Python-Projekte
head -30 <project>/pyproject.toml     # name, version, deps
head -30 <project>/requirements.txt   # pip dependencies
cat <project>/setup.cfg               # setup metadata

# Für Shell-Skript-Projekte
head -30 <project>/<script>.sh        # header comments, CLI args

# Für Config-Projekte
cat <project>/<config>.template.env   # env var names ohne Secrets
cat <project>/config.yaml             # yaml config structure
```

**Resultat:** `--category SYSTEM BROWSER GAMING DUPLICATES LARGE ALL` — echte Werte aus dem Code, nicht geraten.

### 4. Tool/Core-File Verification

```bash
head -100 <project>/<tool>.py        # argparse/CLI-Konfiguration
grep -c "def " <project>/<tool>.py   # Anzahl Funktionen/Methoden
grep "import " <project>/<tool>.py   # Dependencies
```

**Was prüfen:** CLI-Arguments, Hauptfunktionen, tatsächliche Modul-Struktur.

### 5. Stale-Data Marking Protocol

When facts come from a pre-existing document that is known to be stale (pre-Reset, pre-Restructure, superseded by later changes):

**Do NOT:** ❌
- Silently copy stale data → perpetuates errors
- Silently drop stale data → destroys potentially useful info
- Mark as certain → lies to the reader

**Do:** ✅
```markdown
> Laut [Quelle] wurden 444 LITE-Mods aus dem 1195-Mod-Heavy-Set geparst.
> **⚠️ Achtung: diese Angaben stammen aus [Quelle] und sind pre-Reset/Stand [Datum] — vor Nutzung neu verifizieren.**
```

**Rechtfertigung:** Der Leser bekommt (a) die nützliche Info, (b) die Warnung dass sie veraltet sein könnte, und (c) den Ankerpunkt für die Verifikation. Das ist besser als Blindkopie (Fehler fortpflanzen) oder Stillschweigen (Wissen verlieren).

### Concrete Execution Pattern (2026-07-05)

Applied to 5 projects in order:

1. **CP77-Modding**: `ls ~/10-Projekte/10-active/cp77-modding/` → 8 scripts, downloads/, cod-research/ → kein Git → alle Source-Files gelesen → Stale-Data aus STATUS-COD-LITE.md explizit markiert
2. **Yuno-Cleaner**: Python-Projekt → `pyproject.toml` (name, version), `yuno_cleaner.py` (argparse, 5 Scanner-Module), `requirements.txt` (rich, psutil)
3. **Yuno-Voice-Bot**: Python-Projekt → `main.py`, `requirements.txt` (discord.py, faster-whisper, edge-tts), `config.template.env`
4. **Perf-Tuning RTX5060**: Fix-Script-Verzeichnis → `head` auf jedem der 5 Skripte → Größen/Zweck aus Datei-Headern → concurrent-modification mit Sibling-Agent erkannt und retry
5. **Linux-Assistant**: Git vorhanden → `git log --oneline -5` (Commit 80d2ec0), `git describe --tags --always` (v0.6.2), version-File, pyproject.toml

## Sibling Conflict Recovery (Applied 2026-07-05)

During Phase 6 Cluster 2, file `Perf-Tuning RTX5060/README.md` was concurrently modified by Sub-Agent B (this session) and a sibling from Cluster 1.

**Detection:** `patch` returned `success: true` with `_warning: file was modified by sibling subagent 'sa-...'`

**Recovery steps performed:**
1. Re-read the full file (`read_file`) — bekommt den aktuellen Stand
2. Re-identify the edit target — feststellen was der Sibling hinzugefügt hat
3. Re-patch mit neuem old_string (der Sibling hatte die Sektion bereits erweitert)
4. **Decision: Was tun wenn das Ziel nie erreicht wird?** → Wenn der Sibling den geplanten Patch bereits gemacht hat, nur noch die eigenständigen Sektionen (Fix-Skript-Tool-Liste) hinzufügen — nicht die Arbeit des Siblings duplizieren

**Pattern summary:**
- Sibling hat `Status-Box` + `Quick Facts` + `Phasen-Plan` + `Bekannte Issues` + `Fix-Bereitschaft` + `Verifikations-Plan` bereits hinzugefügt → dieser Cluster skippt diese Sektionen und patcht nur `Fix-Skripte (Tool-Liste)` als neuen Content
- **Kein Konflikt** weil die additive Tool-Liste eine disjunkte Sektion ist

## Werkzeuge zur Verifikation

```bash
# Projekt-Struktur
ls -la <project-dir>/

# Git-Status
cd <project-dir> && git log --oneline -3 2>/dev/null || echo "KEIN GIT"

# Python-Metadaten
head -40 <project>/pyproject.toml 2>/dev/null
head -40 <project>/requirements.txt 2>/dev/null

# Tool-Signatur (argparse)
head -100 <project>/<tool>.py 2>/dev/null | grep -A 5 'add_argument\|argparse\|click\.'

# Dateigrößen (sinnvoll für Downloads-Verzeichnisse)
du -sh <project-dir>/*/
```
