# Self-Verifier Pattern (Pitfall #5 Workaround)

> **Unabhängige Re-Implementierung von Zähl-/Prüffunktionen zur Cross-Check**
>
> Gelernt aus: `daily-addendum-gate.py` (2026-07-17) — 5 Quality-Gates für
> Obsidian Daily Notes mit Self-Verify Mode.

## Problem

AI-Agenten schreiben oft Zähl- und Prüffunktionen, die **denselben
Denkfehler in mehreren Metriken reproduzieren**. Ein Beispiel:

> Agent schreibt `count_boldface()` mit regex `r'\S\*\*...\*\*'`.
> Regex matcht fälschlich `t** und das auch **` — weil `**`-Paare ohne
> Token-Grenze erfasst werden.
>
> Alle 5 Gates sehen "grün" — weil der Bug konsistent ist.
> Der Output ist trotzdem falsch.

Das ist **Pitfall #5**: Agenten-Code spiegelt Agenten-Bugs. Tests,
die mit demselben Verständnis geschrieben sind, finden diese Bugs nicht.

## Lösung: Self-Verifier

Jede **Zähl-/Prüffunktion bekommt eine zweite, unabhängige Implementierung**
mit einem **anderen Algorithmus**. Eine dritte Meta-Funktion (`run_self_verify`)
vergleicht die Ergebnisse beider Implementierungen.

```
┌─────────────────────────────────────────────────────┐
│  evaluate_gates(text)                               │
│  ├── count_emdashes(text)           ← Regex-Ansatz  │
│  ├── count_boldface(text)           ← Index-Scan    │
│  └── count_wikilinks(text)          ← re.findall    │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  run_self_verify(text)                               │
│  ├── _verify_emdash_independent(text)  ← str.count  │
│  ├── _verify_boldface_independent(text)← re.finditer │
│  └── _verify_wikilink_independent(text)← str.find    │
└─────────────────────────────────────────────────────┘
                        ↓
              orig == indep? → OK
              orig != indep? → WARN (mindestens eine ist falsch)
```

## Implementierungs-Muster

### Grundstruktur

```python
# ===> ORIGINAL-Ansatz (Haupt-Funktion)
def count_wickets(text: str) -> int:
    """Zählt X mittels Regex. Schnell, aber Regex-logik-anfällig."""
    return len(re.findall(r'MUSTER', text))

# ===> UNABHÄNGIGE Re-Implementierung (Self-Verifier)
def _verify_wickets_independent(text: str) -> int:
    """Zählt X mittels str.find / Index-Scan / manuellem Parsing.
    
    Nutzt EINEN ANDEREN Algorithmus als count_wickets.
    Teilt sich nur den definierenden Muster-Begriff (z.B. was ist ein 'Wicket').
    """
    count = 0
    idx = 0
    while True:
        idx = text.find('SUCHSTRING', idx)
        if idx == -1:
            break
        # Zusätzliche Prüfungen (nicht in Regex-Implementierung)
        if _is_not_in_codeblock(text, idx):
            count += 1
        idx += 1
    return count
```

### Wann anwenden?

- **Jede Zählfunktion** in einem Quality-Gate-Script
- **Jede Prüffunktion**, deren Output boolesch oder numerisch ist
- **NICHT** für reine Transformationsfunktionen (Formatter, Renderer)
- **NICHT** für einfache Delegation (Wrapper ohne eigene Logik)

### So findest du die unabhängige Implementierung

| Original | Independent | Warum anders |
|----------|-------------|--------------|
| `re.findall(r'—', text)` | `text.count('—')` | Regex vs std. str-Methode |
| `re.finditer(r'\*\*...\*\*', text)` | Index-Scan mit `text.find('**')` + Balanced-Pair-Logik | Regex erfasst Paare falsch |
| `re.findall(r'\[\[([^\]]+)\]\]', text)` | `str.find('[[')` in Schleife | Regex matcht Codeblocks mit |
| Regex mit Lookbehind `(?<=\S)` | Line-by-Line Scan mit `line.startswith('##')` | Lookbehind bricht auf Multi-`#` |

### Real-World Beispiele aus daily-addendum-gate.py

#### 1. EmDash — Regex ↔ str.count

```python
# ORIGINAL: Regex mit Named Groups
def count_emdashes(text: str) -> dict:
    text = strip_codeblocks(text)
    em = len(re.findall(r'—', text))      # em-dash U+2014
    en = len(re.findall(r'–', text))      # en-dash U+2013
    return {'total': em + en, 'em': em, 'en': en}

# INDEPENDENT: Einfaches str.count (robuster gegen Regex-Nebenwirkungen)
def _verify_emdash_independent(text: str) -> dict:
    text = strip_codeblocks(text)
    em = text.count('—')
    en = text.count('–')
    return {'total': em + en, 'em': em, 'en': en}
```

#### 2. Boldface — (Balanced-Pair-Index) ↔ Regex

```python
# ORIGINAL: Line-by-line mit Index-Scan auf mid-line-Paaren
def count_boldface(text: str) -> int:
    """Zählt mid-line **...** Paare. Line-Start Labels werden ignoriert."""
    text = strip_codeblocks(text)
    count = 0
    for line in text.split('\n'):
        stripped = line.lstrip()
        if stripped.startswith('**'):
            continue  # Line-Start Label überspringen
        i = 0
        while True:
            start = line.find('**', i)
            if start == -1:
                break
            end = line.find('**', start + 2)
            if end == -1:
                break
            if end > start + 2:  # Leere ** ** ignorieren
                count += 1
            i = end + 2
    return count

# INDEPENDENT: Regex-Ansatz (umgekehrte Logik)
def _verify_boldface_independent(text: str) -> int:
    """Zählt **...** mittels re.finditer.
    
    Nutzt Regex statt Index-Scan — wenn Bugs existieren, sind sie anders.
    """
    text = strip_codeblocks(text)
    count = 0
    for line in text.split('\n'):
        stripped = line.lstrip()
        if stripped.startswith('**'):
            continue
        for m in re.finditer(r'\*\*[^*\n][^*\n]*?\*\*', line):
            count += 1
    return count
```

#### 3. WikiLink — re.findall ↔ str.find

```python
# ORIGINAL: re.findall (fast, aber regex-logik-anfällig)
def count_wikilinks(text: str) -> int:
    text = strip_codeblocks(text)
    return len(re.findall(r'\[\[([^\]]+)\]\]', text))

# INDEPENDENT: str.find (langsamer, aber andere Fehlerklasse)
def _verify_wikilink_independent(text: str) -> int:
    text = strip_codeblocks(text)
    count = 0
    idx = 0
    while True:
        start = text.find('[[', idx)
        if start == -1:
            break
        end = text.find(']]', start + 2)
        if end == -1:
            break
        count += 1
        idx = end + 2
    return count
```

## Integration in CLI

Der Self-Verifier wird als optionales CLI-Flag angeboten (`--verify-self`):

```bash
python3 my-gate.py --verify-self daily-2026-07-16.md
```

Output (JSON):

```json
{
  "ok": true,
  "emdash_match": true,
  "boldface_match": true,
  "wikilink_match": true,
  "details": {
    "emdash": { "orig": 1, "indep": 1 },
    "boldface": { "orig": 0, "indep": 0 },
    "wikilink": { "orig": 14, "indep": 14 }
  }
}
```

### Exit-Codes

| Exit | Bedeutung |
|------|-----------|
| 0 | Alle Metrics stimmen überein |
| 1 | Mindestens eine Metric weicht ab → **WARN: Agent-Code hat einen Bug** |

## Wann der Self-Verifier false alarms schlägt

Der Self-Verifier vergleicht **Algorithmen**, nicht **Wahrheit**. Es ist möglich,
dass beide Implementierungen denselben Bug teilen (z.B. beide codeblocks nicht
strippen). Dagegen hilft:

1. **Codeblock-Stripping VOR dem Vergleich** — beide Implementierungen auf
   demselben Preprocessed-Text laufen lassen (nicht jeder in eigenem Strip)
2. **Drei Implementierungen** bei kritischen Metrics (Majority-Vote)
3. **Manuelles Spot-Checking** bei Diskrepanz — lies die Zeilen im Output

**Wichtig:** Der Self-Verifier findet nur **Konsistenz**, nicht **Korrektheit**.
Ein konsistenter Bug (beide Algorithmen zählen gleich falsch) bleibt unerkannt.
Deshalb trotzdem Tests schreiben.

## Anti-Patterns

1. **Identische Implementierung** — `_verify_x` ruft `count_x` auf → findet nichts
2. **Nicht alle Metrics verifiziert** — die ungeprüfte Metric kann trotzdem Bugs haben
3. **Self-Verifier als Ersatz für Tests** — nein, Tests + Self-Verifier sind komplementär
4. **Self-Verifier als Production-Feature** — nein, `--verify-self` ist ein Dev/Debug-Tool
5. **Zu viele unabhängige Implems** — 3 parallel reichen, mehr erhöht nur Wartungskosten

## Verwandte Patterns

- `ki-murks-verhindern` §"Verifying Fix-Plan / Artifact Claims" — gleiche Grundidee
  (Claim gegen unabhängige Quelle prüfen), andere Domäne
- `output-validator` — Syntax-Prüfung (Self-Verifier prüft Semantik der Zählung)
- `critic-gate` — Semantic Check (Self-Verifier ist deterministisch, Critic ist LLM-basiert)
