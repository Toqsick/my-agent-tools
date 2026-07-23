# Pre-Existing-Errors Baseline — Build/Compile Verification

## Wann

Du modifizierst Code in einem Projekt mit einer getypten/kompilierten Sprache (TypeScript, Rust, Go, ...) und willst beweisen, dass deine Änderungen **keine neuen Fehler einführen**.

Ohne Baseline siehst du nach deiner Änderung N TypeScript-Fehler — sind das alles alte, oder hast du neue gemacht? Das Verfahren trennt beides.

## Technik 1: Stash & Isolate (uncommittete Änderungen vorhanden)

```bash
# 1. Uncommittete Änderungen weglegen
git stash push -m "pre-baseline-$(date +%s)"

# 2. Build/Type-Check auf sauberem Stand
npx tsc --noEmit 2>&1 | head -60
# → "Found NN errors" notieren

# 3. Änderungen zurückholen
git stash pop

# 4. Selben Check mit deinen Änderungen
npx tsc --noEmit 2>&1 | head -60

# 5. Vergleichen
# Gleiche N? → Keine neuen Fehler
# Mehr? → Neue Fehler lokalisieren und fixen
```

## Technik 2: Git-Referenz (keine uncommitteten Änderungen)

```bash
# Baseline aufnehmen
git rev-parse HEAD > /tmp/baseline-sha
npx tsc --noEmit > /tmp/baseline-errors.txt 2>&1
echo "Pre-existing: $(wc -l < /tmp/baseline-errors.txt) lines of errors"

# ... Arbeit erledigen ...

# Diff gegen Baseline
npx tsc --noEmit 2>&1 | diff - /tmp/baseline-errors.txt
# Leer = keine Regression
```

## Warum

- Projekte akkumulieren mit der Zeit vorbestehende Type-/Build-Fehler
- Eine Behauptung "kompiliert sauber" ist falsch, wenn sie vorbestehende Fehler ignoriert
- Die Technik isoliert dein Signal vom Rauschen alter Fehler
- Fängt auch Seiteneffekte: hat dein Refaktor eine unabhängige Datei kaputt gemacht?

## Sprachspezifische Varianten

| Sprache | Check-Befehl |
|---------|-------------|
| TypeScript | `npx tsc --noEmit` |
| Rust | `cargo check` |
| Go | `go build ./...` |
| Java | `mvn compile` oder `gradle compileJava` |
| C++ | `make -j$(nproc)` (mit geeignetem Target) |

## Fallstricke

- **`git stash` ignoriert neue (ungetrackte) Dateien** — `git stash -u` inkludiert sie, aber can alle neuen Dateien. Wenn du *und* neue Dateien erwartest, check lieber per `git stash -u`.
- **Unterschiedliche Node-Version** → gleiches Projekt, gleiche `node --version` nutzen
- **Unterschiedliche Compiler-Version** → bei `npx tsc` wird die Lockfile-Version genutzt (stabil), bei `npm run build` könnte es anders sein
- **Metrische Fehlerzahlen** ≠ semantisch gleiche Fehler. Der Diff-Check (Technik 2, `diff`) ist präziser als reiner Zahlenvergleich.
