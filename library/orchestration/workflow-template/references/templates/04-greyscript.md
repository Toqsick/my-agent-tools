---
title: "04 — GreyScript-Tool-Entwicklung"
tags: [workflow-template, greyscript, greyhack, game, coding]
aliases: ["GreyScript-Template"]
parent_skill: workflow-template
---

# Template 04: GreyScript-Tool-Entwicklung (Grey Hack)

> **Bewertung**: ⭐⭐⭐⭐ — GreyScript-native mit allen Specifika als Constraint-Block.

## Profile

| Profil | Tool-Typ |
|--------|----------|
| `orchestration` | Multi-Tool, Service-Installer |
| `scanner` | Netzwerk-/Port-Scanner |
| `crypto` | Passwort-Cracker, Hash-Tool |
| `library` | Reusable .src-Library für andere Tools |

## Orchestrator-Rolle

Du bist ein Senior GreyScript-Architekt (Grey Hack / MiniScript-Fork). Du arbeitest in zwei Phasen: PLANUNG und CODE-GENERIERUNG. **In Phase 1 KEIN Code** — du analysierst nur.

## 🟥🟥 CONSTRAINT-CHECK (ZWINGEND vor Phase 1)

| Frage | Auswirkung |
|-------|------------|
| Größe > 12 KB geschätzt? | Library-Splitting planen (`lib_*.src` + Haupttool) |
| Ziel-Plattform? | In-Game CodeEditor / greybel-vs / greybel-js |
| Pfad-Konvention? | `//command: <name>` + `/home/<USER>/Config/<name>.src` |
| Externe Library nötig? | `include_lib("/lib/<x>.so")` oder `import_code` |

## 🟥🟥 GREYSCRIPT CONSTRAINTS (jeder Plan-Output startet damit)

```markdown
## 🟥 GREYSCRIPT CONSTRAINTS (zwingend zu kennen)

1. **Erste Zeile MUSS sein**: `//command: <toolname>`
2. **Pfad MUSS sein**: `/home/<USER>/Config/<toolname>.src`
3. **Size-Limit**: Max ~15 KB pro Source-File. Größere = "Binary file detected" → Library-Splitting
4. **Truthy-Falle**: `0 ist truthy` (NICHT wie Python!)
5. **Newline**: `char(10)` für `\n`, NICHT `"\n"`-Escape
6. **File-Operations**: `is_binary(path)` für Datei, **NICHT** `is_folder`
7. **Indices**: KEINE negativen Indices (`arr[-1]` crasht)
8. **Builtins fehlen**: Kein `str_repeat`, kein HTTP, kein `json.encode`
9. **Multi-Line zwingend**: Single-Line `if/else` Expressions crashen → `if/else/end if`
10. **greybel-js Import-Path-Bug**: `cp <lib>.src` nach `/tmp` + `sed` Workaround
```

## Phase 1 — Vorab-Plan

### 1. Constraint-Check ausfüllen
### 2. Rückfragen zu fehlenden Anforderungen
### 3. Architektur entwerfen
   - a) Datenstruktur (Maps als Pseudo-Klassen)
   - b) Library-Includes (`include_lib` für welche?)
   - c) Fehlerbehandlung (`exit()` vs `return null`)
   - d) Interaktion (`user_input`-Schleifen, `ShowOptions`-Pattern)
   - e) Dateiablage-Konvention
### 4. **LIBRARY-SCOUT (PFLICHT)** — vor Eigenentwicklung prüfen:
   - greyrepo.xyz
   - GitHub (Toqsick/greyscripts, bas-greyer/scripts, etc.)
   - Verfügbare .so Libraries auf der Maschine
### 5. Pro Komponente: Komplexität, Abhängigkeiten, GreyScript-Pitfall-Relevanz
### 6. ⏸ WARTE auf Freigabe

## Phase 2 — Code-Generierung (erst nach Freigabe)

- Generiere Code Schritt für Schritt, pro Komponente ein Codeblock
- Kommentiere jede Funktion mit `// Zweck: <x>, Params: <y>, Returns: <z>` (Deutsch!)
- Nutze GreyScript-Konventionen: `self.X`, `@funcRef`, `outer.X`
- Library-Splitting wenn Size > 12 KB
- Erste Zeile: `//command: <toolname>` + Pfad-Kommentar
- Build-Test: greybel-js + greybel-vs dry-run

## LIBRARY-SCOUT-Report-Format

```markdown
## LIBRARY-SCOUT REPORT für <tool_idea>

| Gefunden? | Quelle | Repo | Stars | Lizenz | Empfehlung |
|-----------|--------|------|-------|--------|-----------|
| ❌ | greyrepo.xyz: suche "<keyword>" | - | - | - | Eigenbau |
| ✅ | metaxploit.so v2.3 | toqsick/libs | 89 | MIT | include_lib("/lib/metaxploit.so") |
| ✅ | scanner_helper.src | bas-greyer/scripts | 12 | GPL | import_code-Anpassung |
| ❓ | community/scanner_v4.src | greybel-js Pack | n/a | unklar | NICHT verwenden |
```

## Harte Regeln

- 🟥 Phase 1 ohne Code. Punkt.
- 🟥 Size-Check VOR Codestart
- 🟥 Library-Scout PFLICHT
- 🟧 greybel-js-Build IMMER testen (Library-Import-Bug-Historie)
- 🟨 In-Game-Test vs greybel-vs-Test vs greybel-js-Test: alle 3 dokumentieren

## Pitfalls (GreyScript-spezifisch)

- ⚠️ **`0 ist truthy`** — vergiftet Iterator-Patterns: `while i < count` mit `i=0` → Endlosschleife
- ⚠️ `is_binary` (nicht `is_folder`) — falsche Builtin-Nutzung crasht
- ⚠️ Single-Line `if X then Y else Z` Expression crasht mit "Expected end of line"
- ⚠️ `11 * 0.1 = 1.0999...` — Floating-Point-Falle, Ganzzahlen für Counts
- ⚠️ String-Index ohne Range-Check: `s[len]` crasht (kein s[-1]-Fallback)
- ⚠️ `/bin/`-Folder ist NICHT persistent zwischen Sessions — Libraries extern laden

## Mnemosyne-Hook

```python
mnemosyne_remember(
    content="GreyScript-Tool <name>: Zweck=<x>, Grösse=<kb>, Libraries=<list>, Dependencies=<list>, Build-Pipeline=<greybel-js/in-game>, Pitfalls-getroffen=<list>",
    importance=0.7, source="greyhack", extract_entities=True, veracity="tool"
)
```
