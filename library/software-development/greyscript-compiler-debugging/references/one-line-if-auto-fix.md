# Pattern (a) One-Line-If — Auto-Fix Recipe (2026-07-07)

> Quelle: Session 2026-07-07, Model: MiniMax-M3 (7 .src files in greyhack-tools,
> 37 funde total, 6/7 builds erfolgreich nach Fix).

## The Bug

GreyScript's non-`-u` Parser (greybel ohne `-u`) lehnt one-line `if`-Statements ab:

```greyscript
// ❌ CRASH (parser) — Pattern (a)
if n == 0 then return "0" end if
if s.len == 0 then return [] end if
if cache_file_content == null or cache_file_content == "" then continue end if
```

**Compile-time error signatures** (beide Varianten gesehen):

| Error | Wann |
|---|---|
| `Build error: no matching open if block at <file>:<line>:<col>` | Ältere greybel-Versionen / bestimmte Edge-Cases |
| `Build error: got Keyword[<line>:<col> - <line>:<col>: value = 'end if'] where number, string, or identifier is required` | greybel 3.7.12 (aktuelle Build-Pipeline) |

Beide zeigen auf die Zeile mit dem `if X then BODY end if`.

## The Fix (manuell)

```greyscript
// ✅ WORKING — mehrzeilig
if n == 0 then
    return "0"
end if
if s.len == 0 then
    return []
end if
if cache_file_content == null or cache_file_content == "" then
    continue
end if
```

Body-Indent = Leading-Indent + 1 Tab. Funktioniert für alle Indent-Styles (all-tab, all-spaces, mixed wie `metaxploit.src` mit 4-space outer + tab inner).

## The Auto-Fix (37 funde in 7 Dateien)

Siehe `scripts/expand_one_line_ifs.py`. Aufruf:

```bash
python3 scripts/expand_one_line_ifs.py file1.src file2.src ...
```

**Output:** `<count> fixes` pro Datei + Total. **Detail-Log** unter `/tmp/expansion-log.json` mit `lineno` und `old`-Text pro Match.

### Regex-Constraints (warum das Script NICHT alles umbricht)

Das Script matcht **nur** Pattern (a) und überspringt:

| Pattern | Beispiel | Warum übersprungen |
|---|---|---|
| Statement-chain | `if x then A; B end if` | Semantik ändert sich (zwei statements statt block) — manueller Fix |
| Combined for | `if x then for i in y end for end if` | Würde falsch einrücken |
| Combined if | `if x then if y then z end if end if` | Würde end ifs falsch zuordnen |
| Combined while/function/try | analog | gleicher Grund |
| Empty body | `if x then end if` | defensiv |
| Bereits multi-line | (kein Match — Regex verlangt Single-Line) | idempotent |

### Verified Funde pro Datei (Session 2026-07-07)

| Datei | Funde | Build nach Fix |
|---|---:|---|
| `lzw/encoder.src` | 9 | ✅ OK |
| `list-lib/listLib.src` | 8 | ✅ OK |
| `metaxploit/metaxploit.src` | 7 | ❌ Dependency-Error (NICHT Pattern-a) |
| `password-gen/password_generator.src` | 6 | ✅ OK |
| `htop/htop.src` | 4 | ✅ OK |
| `forcer/forcer.src` | 3 | ✅ OK |
| `bootstrap/bootstrap.src` | 0 (bereits multi-line!) | ✅ OK |
| **TOTAL** | **37** | **6/7 OK** |

**Lesson:** Bootstrap.src wurde in der Aufgaben-Beschreibung mit "1 fund" gelistet, war aber bereits multi-line. **Immer erst grep-check gegen die echte Datei, dann das Fix-Script anwenden.** Die "expected count" aus einem Bug-Report kann veraltet sein.

## Build-Verification (das wichtigste Detail dieser Session)

`greybel build` hat zwei nicht-offensichtliche Gotchas:

### Gotcha 1: `-dbf` Flag ändert Output-Semantik

```bash
# OHNE -dbf: output ist ORDNER, greybel erzeugt <ordner>/build/<file>.src
greybel build input.src /tmp/out          # erzeugt /tmp/out/build/input.src

# MIT -dbf: output ist DATEI, greybel schreibt direkt dort hin
greybel build input.src /tmp/out/build -dbf  # erzeugt /tmp/out/build
```

`No files found!` ohne -dbf heißt normalerweise: Output-Pfad war ein File-Pfad und greybel hat versucht es als Ordner zu interpretieren. Mit `-dbf` muss der Pfad ein File sein, nicht ein Ordner.

### Gotcha 2: Relative Path Resolution

greybel löst Pfade **relativ zum CWD** auf. Im greyhack-tools Repo muss der Pfad `greyhack-tools/<tool>/<file>.src` sein, NICHT `<tool>/<file>.src` (auch wenn man in `greyhack-tools/` ge-`cd`'t ist).

```bash
cd /home/bratan/10-Projekte/10-active/greyhack-tools

# ✅ FUNKTIONIERT
greybel build greyhack-tools/lzw/encoder.src /tmp/out -dbf

# ❌ "No files found!" obwohl die Datei existiert
greybel build lzw/encoder.src /tmp/out -dbf
```

### Gotcha 3: Build-Error Progression als Signal

Wenn `greybel build` einen anderen Error wirft als vorher, ist das ein **gutes Zeichen**:

```
Vorher:  got Keyword[31:55 - 31:61: value = 'end if'] where number, string, or identifier is required  ← Parser-Fehler auf if-Zeile
Nachher: Build error: Dependency /home/Bratan/bin/lib_core does not exist                                     ← Resolution-Fehler, Parser OK!
```

Der Parser hat die if-Statements jetzt akzeptiert. Das neue Problem ist auf einer anderen Layer (dependency resolution) und liegt außerhalb des Pattern-a-Scopes.

## Verifikations-Rezession

```bash
# 1. Backup (mit Timestamp)
TS=$(date +%Y%m%d-%H%M%S)
for f in file1.src file2.src; do cp "$f" "$f.bak-$TS"; done

# 2. Auto-Fix
python3 scripts/expand_one_line_ifs.py file1.src file2.src ...

# 3. Diff prüfen (visuell)
diff file1.src.bak-$TS file1.src

# 4. Build-Verifikation
greybel build file1.src /tmp/out/file1 -dbf  # siehe Gotcha 1
# Erwartet: "Build done. Available in /tmp/out/file1."

# 5. Bei Dependency-Errors: KEIN Pattern-a-Problem, separater Fix nötig
```

## Related

- `references/yuno-tools-pattern-catalog.md` — Broken Pattern #2 (Einzeiler-if)
  dokumentiert das Symptom; dieses File dokumentiert den automatisierten Fix.
- `SKILL.md` "Compiler Error Reference" Tabelle — der `got Keyword[...end if]`
  Error ist hier mit aufzunehmen, falls noch nicht geschehen.