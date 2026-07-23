# Static-Scan False-Positive Patterns (Bug-Sweep PR #56, 2026-07-07)

Lessons from the Greyhack Bug-Sweep Session — what static scanners misidentify as bugs in GreyScript code.

## Pattern-(d) False-Positive: single-quotes inside outer-DQ strings

Static-Scanner, die naiv nach `'` zählen, schlagen bei Shell-Command-Strings wie `"vim -c ':!/bin/sh'"` an — wo das Single-Quote TEIL der User-Daten ist, nicht Code. Sub-Agent, der blind ersetzt, würde Syntaxfehler erzeugen.

**GreyScript-Spezifikum:** GreyScript hat KEINE String-Escapes (kein `\"`, kein `\\`). Ein `"..."`-String kann keine inneren `"` enthalten ohne `+`-Konkat oder `char(34)`. Single-Quotes IN `"-strings` sind literale Daten, nicht Code.

**Echte Session (Bug-Sweep 2026-07-07, PR #56):**
- Static-Scan zählte 16 single-quote Funde in 6 Files (suid_exploit.src, test_grsa.src, test_decypher.src, test_libcore.src, debugcore.src, launcher.src)
- Sub-Agent-B klassifizierte manuell: **alle 16 FALSE-POSITIVES**
- 0 echte Konvertierungen nötig

**Klassifikations-Heuristik für Pattern-(d) Scanner:**
1. Innerhalb eines `"-strings` (literal user-data) → FALSE-POSITIVE, skippen
2. Innerhalb von `print(... '...')` → FALSE-POSITIVE (user-facing output)
3. In `//`-Kommentaren → FALSE-POSITIVE
4. **Echter Code:** `if x == 'foo'`, `name = 'foo'`, `arr['key']`, `f('arg')`

**Detection-Recipe (Python):**
```python
import re
for f in files:
    for i, line in enumerate(open(f), 1):
        if not re.search(r"'", line): continue
        # Skip if inside outer-DQ-string
        if re.search(r'"[^"]*\'[^"]*"', line): continue
        # Skip if inside print() message
        if re.search(r'print\s*\([^)]*\'[^)]*\)', line): continue
        # Skip if comment
        if line.strip().startswith("//"): continue
        # Real hit
        report(f, i, line)
```

**Lesson:** Static-Scans ohne Kontext-Klassifikation erzeugen False-Positives, die Schwarm-Zeit verschwenden. Sub-Agent-Disziplin "lieber nichts machen als kaputtmachen" ist gut, kostet aber eine Schwarm-Round ohne Output. Immer vorab im Briefing die Klassifikations-Regeln mitgeben.

---

## Pattern-(l) HTTP.Request: pc.wget-Workaround + Hermes-API-Limitation (NEU 2026-07-07)

**HTTP.Request existiert NICHT in GreyScript.** Compiliert clean, crashed aber im echten Game mit `undefined function`.

**Workaround-Rezept (verifiziert 2026-07-07 in bootstrap.src):**

| Use-Case | Fix |
|----------|-----|
| **File-Download** (URL → `/path/to/file`) | `pc.wget(url, dstPath)` + Existenz-Check via `pc.File(dstPath)` |
| **LAN-fileserver probe** (127.0.0.1 oder LAN-IP) | `pc.touch(probePath); f = pc.File(probePath); if f then f.delete end if` dann `pc.wget` |
| **JSON-API endpoint** (z.B. Hermes API auf Port 8333) | **KEIN direkter Workaround möglich!** `pc.wget` erwartet File-URL, scheitert bei JSON-Endpoints. Auskommentieren mit TODO oder via Hermes-Co-Pilot-Workflow (Alt-Tab + hermes-ask CLI). |
| **External HTTP** (z.B. `https://example.com/data`) | TODO-Kommentar + User-Manual-Workaround |

**Wichtig:** `try/catch end try` Blöcke sind in GreyScript **NICHT gültig** (`unexpected keyword 'end try'`). Komplett entfernen und durch `if/then/end if`-Logik ersetzen.

**Bootstrap.src v1.2.0 Fix (Beispiel):**
```greyscript
// VORHER (CRASH + invalid try/catch):
try
    test = HTTP.Request(SOURCE_HOST, "GET")
    if test then
        sourceURL = SOURCE_HOST
    end if
catch e
end try

// NACHHER (sicher + greybel-build-fähig):
shell = get_shell
pc    = shell.host_computer

// Probe-First: pc.touch + File-Existenz-Check statt HTTP-Request
probePath = "/tmp/.bootstrap_probe"
pc.touch(probePath)
probeFile = pc.File(probePath)
if probeFile then
    probeFile.delete
end if
// ... dann pc.wget für echte Downloads
```

**Mock-Env Pitfall:** `pc.wget()` existiert nur im echten GreyHack-Game. `greybel execute` (mock-env) wirft `Path "wget" not found in map`. **Das ist KEIN Bug** — Mock-Env-Limitation. Build mit `greybel build` ist die einzige echte Validierung.

---

## Race-Condition Pattern A ↔ Pattern D (NEU 2026-07-07)

Wenn zwei parallele Fix-Agenten beide dieselbe Source-Datei brauchen (weil sie mehrere Pattern-Klassen enthält), entsteht eine Race-Condition:

**Echte Session:** Pattern-A (one-line-if) und Pattern-D (.strip()/.trim()) brauchten beide `greyhack-tools/password-gen/password_generator.src`:
- Pattern-A: 6 one-line-if-Funde
- Pattern-D: 1 .trim-Fund (Zeile 28, `s = s.trim.upper` — `s.trim` ist method-ref ohne Klammern, crashed im echten Game)
- Agent D hat **bewusst out-of-scope markiert** ("Race-Condition mit Pattern-A-Agents")
- Pattern-A-Agent hat den trim-Bug übersehen
- **Parent musste manuell eingreifen**

**Fix-Pattern für Schwarm-Design:**
1. **Cross-Pattern Files vor Dispatch identifizieren** (welche Files haben ≥ 2 Pattern-Klassen?)
2. **Files mit nur 1 Pattern-Klasse** → geht an den jeweiligen Pattern-Agent
3. **Files mit ≥ 2 Pattern-Klassen** → entweder Parent-Direct Fix oder Sequentialisieren
4. **Sub-Agent-Briefing:** "Wenn du eine Datei siehst die mehrere Pattern-Klassen enthält, fokussiere auf DEINE Klasse. Andere Agenten / Parent fixen den Rest."

Siehe auch: `references/bug-scan-sweep-2026-07-07.md` (im greyhack-tools Repo) für die vollständige Session-Doku inkl. Build-Statistik (41/66 → 47/66 OK).

---

## Validated Scan-Recipe für GreyScript

```bash
# 14-Pattern-Scan über alle aktiven .src-Files (excludes: backups/, build/, bin/, imports/, greybel-vs/test-workspace/, .ci-build/)
cd ~/10-Projekte/10-active/greyhack-tools/
find . -name "*.src" -not -path "./backups/*" -not -path "./build/*" \
  -not -path "./bin/*" -not -path "./imports/*" \
  -not -path "./greybel-vs/test-workspace/*" -not -path "./.ci-build/*" \
  > /tmp/active-src.txt

# 14 Pattern-RegEx anwenden + Build-Verifikation per greybel
for f in $(cat /tmp/active-src.txt); do
  timeout 20 greybel build "$f" /tmp/greybel-test/$(basename $f .src)/build 2>&1 | head -2
done
```

**Speed:** ~2s pro File für Build, ~140ms für kompletter Static-Scan über 78 Files.

**Real-World-Result (Bug-Sweep 2026-07-07, PR #56):**
- 76/78 Files mit statischen Findings (98%)
- 20 Files mit echten Compiler-Bugs (nach Kontext-Klassifikation)
- Build 41/66 → 47/66 OK nach Fixes (+6)
- 16 single-quote "Funde" → 0 echte Fixes (alle false-positive)
- 38 fehlende `//command:` Marker (out-of-scope, separate Aufgabe)