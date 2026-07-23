# GreyScript-Sandbox-Befehle

## 1. Tool ausführen (Sandbox-Mode)

```bash
set -euo pipefail
# Einfach ausführen (params ohne Programmnamen, ab Index 0!)
greybel execute tools/password-gen/password-gen.src

# Mit Parametern
greybel execute tools/password-gen/password-gen.src -p "--help"
greybel execute tools/password-gen/password-gen.src -p "--length" -p "32"
greybel execute tools/password-gen/password-gen.src -p "--count" -p "5" -p "--readable"

# Im Mock-Mode (simuliert GreyHack-Umgebung)
greybel execute tools/portscan.src -et Mock

# Debug: was als params ankommt
echo 'print(params.len); while i < params.len do print("p["+i+"]="+params[i]); i=i+1; end while' > /tmp/debug.src
greybel execute /tmp/debug.src -p "arg1" -p "arg2"
```

**Kritisch: params-Offset.** Greybel execute übergibt PARAMS OHNE Programmnamen — params[0] ist das erste Argument. Im GreyHack-Spiel ist params[0] der Programmname und params[1] das erste Argument. Tools, die für GreyHack geschrieben wurden, starten bei i=1 und müssen ggf. auf i=0 angepasst werden.

## 2. Tool kompilieren

```bash
set -euo pipefail
# Einzelne Datei
greybel build tools/password-gen/password-gen.src /tmp/build/

# Alle Tools im Repo (via ci-build.sh)
bash scripts/ci-build.sh --out-dir .ci-build
```

## 3. Interaktive REPL

```bash
set -euo pipefail
greybel repl
# Dann: print("hello"); params = ["--help"]
# Einzeiler:
echo 'print("Hello GreyScript!")' | timeout 3 greybel repl
```

## 4. In-Game Import (später)

```bash
set -euo pipefail
greybel import tools/ --port 8332
```

## 5. Interactive Shell Testing via stdin (NEU 2026-07-04)

Bei Scripts mit while-loop + user_input (z.B. interaktive Shells wie YUNO VIPER) funktioniert `echo` oder `printf` für stdin — der Mock-Env liest zeichenweise und verarbeitet Trennungen:

```bash
# Test interactive shell commands via heredoc (stdin an greybel execute)
FILE="/home/bratan/greyhack-tools/yuno_viper/modules/yuno_viper_core.src"
printf 'help\nversion\nexit\n' | timeout 5 greybel execute "$FILE" -et Mock --silent 2>&1 | tail -30
```

**Wichtig:** Mock-Env liest stdin ZEICHENWEISE (char-by-char, nicht zeilenweise). Das bedeutet jedes Zeichen wird einzeln an `user_input()` weitergegeben. Der prompt-Echo (Eingabe-Bestätigung) erscheint im Output — filtere mit `grep` nach den gewünschten Ausgabezeilen:

```bash
# Filtere nur die Ausgabezeilen, ignoriere prompt-echo
printf 'help\nexit\n' | timeout 5 greybel execute "$FILE" -et Mock --silent 2>&1 | grep -E '^[\[ ]'
```

**Problem: command-mode Scripts.** Scripts die `params` auswerten (Command-Tools ohne user_input) können NICHT via stdin getestet werden — sie brauchen `-p` Flags:
```bash
# Für command-mode (kein user_input):
greybel execute tool.src -p "arg1" -p "arg2" -et Mock --silent
```