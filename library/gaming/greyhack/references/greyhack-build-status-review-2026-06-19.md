# GreyHack Build Status Review — 2026-06-19

**Zweck:** Session-spezifische, aber wiederverwendbare Prüfrezepte für den `greyscripts`-Repo- und Build-Status.

## Ausgangsfrage

User fragte nach Modellwechsel, ob der aktuelle Status „gut so“ sei. Ziel war keine Featurearbeit, sondern ein echter Statuscheck gegen Docs, Git und Build.

## Repo-Status

```bash
cd /home/bratan/greyscripts
git status --short --branch
git branch --show-current
git rev-parse --short HEAD
git remote -v
```

Ergebnis:

```text
## develop...origin/develop
?? .hermes/plans/2026-06-19_001500-greyscripts-todo-scan.md
?? .hermes/plans/2026-06-19_011200-awesome-hacking-greyhack-research.md
?? .hermes/plans/2026-06-19_013000-awesome-hacking-top20-plan.md
?? docs/security-research/
?? suid_exploit.src

develop
b2a4396
origin  https://github.com/Toqsick/greyscripts.git (fetch)
origin  https://github.com/Toqsick/greyscripts.git (push)
```

Interpretation:

- `develop` ist der aktive Branch.
- Keine committed Änderungen auf `develop`.
- Research-/Plan-Dateien und `docs/security-research/` sind untracked; nicht automatisch entfernen.
- Root-`suid_exploit.src` ist untracked und muss separat geprüft werden.

## Build-Script-Hilfe

Falscher Versuch:

```bash
./scripts/ci-build.sh --out-dir /tmp/greybel-build all
```

Ergebnis:

```text
ERROR: source not found for 'all'
exit_code=2
```

Korrekte Hilfe:

```bash
./scripts/ci-build.sh --help
```

Ergebnis:

```text
Usage: ./scripts/ci-build.sh [--out-dir DIR] [FILE_OR_TOOL ...]

Options:
  --out-dir DIR               Directory for generated build outputs (default: .ci-build)
  --include-greyhack-tools    Also build imported/stale greyhack-tools/ sources
  --help                      Show help message

Arguments:
  If FILE_OR_TOOL is omitted, all .src files under src/ and tools/ are built.
```

Lesson: Bei unbekannter Script-Syntax zuerst `--help` prüfen. `all` ist kein gültiges Argument.

## Full Build

Korrekter Befehl:

```bash
./scripts/ci-build.sh --out-dir /tmp/greybel-build
```

Ergebnis:

```text
Building 19 GreyScript file(s) into /tmp/greybel-build
...
Build complete: 19 file(s) ok
```

Status: Full Build grün.

## Fileserver-Check

Start:

```bash
python3 ~/bin/temp_fileserver.py
```

Health-Check:

```bash
sleep 1
curl -fsS http://localhost:8765/lib_core/lib_core.src >/tmp/lib_core_check.src
wc -c /tmp/lib_core_check.src
```

Ergebnis:

```text
8310 /tmp/lib_core_check.src
```

Status: Fileserver erreichbar, `lib_core.src` verfügbar.

## Untracked Artefakt prüfen

```bash
test -f suid_exploit.src && wc -c suid_exploit.src
test -f src/tools/suid_exploit.src && wc -c src/tools/suid_exploit.src
cmp -s suid_exploit.src src/tools/suid_exploit.src; echo cmp_exit=$?
git ls-files src/tools/suid_exploit.src suid_exploit.src
```

Ergebnis:

```text
6430 suid_exploit.src
11052 src/tools/suid_exploit.src
cmp_exit=1
src/tools/suid_exploit.src
```

Interpretation:

- Root-`suid_exploit.src` ist kein gepflegtes Repo-File.
- Es ist nicht identisch mit `src/tools/suid_exploit.src`.
- Nicht blind löschen; als Artefakt behandeln und im Statusbericht erwähnen.

## Research-Docs geprüft

Vorhandene Research-Docs:

```text
docs/security-research/README.md
docs/security-research/awesome-hacking-top20.md
docs/security-research/tool-candidates-review.md
docs/security-research/specs/recon-lite.md
docs/security-research/specs/cli_core.md
docs/security-research/specs/mission_report.md
```

Interpretation: Research- und Mini-Spec-Lage ist dokumentiert; keine neue Umsetzung wurde begonnen.

## Reusable Checkliste

Für künftige Session-Starts:

1. `git status --short --branch` lesen.
2. Branch und Commit nennen.
3. `ci-build.sh --help` prüfen, wenn Syntax unklar.
4. Full Build ohne `all` ausführen, wenn keine Datei ausgewählt wurde.
5. Fileserver mit `curl` und `wc -c` prüfen.
6. Untracked Root-`.src`-Dateien mit gepflegten Dateien unter `src/` oder `tools/` vergleichen.
7. Keine untracked Research-/Plan-Docs automatisch entfernen.
8. Ergebnis knapp auf Deutsch zusammenfassen.
