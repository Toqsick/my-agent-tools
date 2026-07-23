# Landing Page Multi-Agent Workflow

> Gelernt aus dem Engineer-Run vom 2026-07-08 (Toqsick/yuno-minimax-bundles Landing Page Build).
> Ergänzt das E2E-Delegation-Pattern (`references/e2e-test-pattern.md`) mit **technischen Implementierungs-Details** und **Cross-Agent-Handoff-Friction** für Landing-Page-Builds.

## Das Problem

Ein Multi-Agent-Landing-Page-Build durchläuft Researcher → Designer → Writer → Engineer → Verifier. Die grösste Friction liegt im **Writer→Engineer Handoff**: Der Writer liefert flaches JSON ohne `copy`-Envelope, der Engineer erwartet aber `{{copy.hero.x}}` im Template. Dazu kommen Template-Engine-Design-Entscheidungen (stdlib-only, pass-ordering, Control-Token-Sicherheit) und CI/CD-Konfiguration (GitHub Pages mit Least-Privilege-Permissions).

## Workflow-Phasen

```
Phase 1: Research   → arXiv / Referenz-Pages finden (Researcher)
Phase 2: Design     → Style-Tokens / Farbpalette / Layout (Designer)
Phase 3: Write      → Marketing-Copy als flat JSON (Writer)
Phase 4: Build      → Template-Engine + Makefile + CI/CD (Engineer)
Phase 5: Verify     → html5validator + stdlib-Sanity-Checks (Verifier)
Phase 6: Deploy     → GitHub Actions → GitHub Pages (CI/CD)
```

## Phase 3→4 Handoff: Writer → Engineer Data Shape

### Das Problem

Der Writer liefert naturgemäss flaches JSON, das den Copy-Bereich semantisch strukturiert:

```json
{
  "meta": {
    "title": "Yuno Skills-Bundles",
    "description": "Kuratierte Skills für Hermes Agent."
  },
  "hero": {
    "eyebrow": "MiniMax × Yuno",
    "headline": "Skills-Bundles, die deinen Agenten zum Tool zum Partner machen."
  }
}
```

Der Engineer erwartet im Template aber verschachtelten Zugriff via `copy.`-Pfad:

```html
<title>{{copy.meta.title}}</title>
<span class="eyebrow">{{copy.hero.eyebrow}}</span>
```

### Der Fix: Auto-Wrap in der Build-Funktion

Statt den Writer zu zwingen, einen redundanten `copy`-Envelope zu schreiben, wrappt die Build-Engine die Daten automatisch:

```python
def render(template: str, data: dict) -> str:
    """Apply all template passes.
    
    Auto-wrap flat Writer-JSON in a 'copy' envelope when missing.
    """
    copy_keys = {"meta", "hero", "features", "get_started", "repo", "footer", "cta"}
    if "copy" not in data and copy_keys & data.keys():
        data = {"copy": data}
    
    out = render_each_blocks(template, data)
    out = render_if_blocks(out, data)
    out = render_tokens(out, data)
    return out
```

**Vorteile:**
- Writer kann natürlich strukturiertes JSON liefern (ohne künstlichen Envelope)
- Template bleibt flexibel (kann `copy.`-Pfade referenzieren)
- Kein Breaking Change: wenn `copy`-Key existiert, wird nicht gewrappt

## Phase 4: Template-Engine Design (Stdlib-only Python)

### Warum stdlib-only?

Damit der Build **kein `pip install` in CI** braucht. Python 3.11+ bietet ausreichende Features:
- `re.sub` mit benannter Callback-Funktion
- `functools.reduce` für Deep-Dict-Lookup (`resolve_path`)
- `json.load` für Copy+Style-Tokens

### Pass-Ordnung (kritisch!)

Die 3 Render-Passes müssen **in dieser Reihenfolge** laufen:

```python
# ✅ RICHTIG
out = render_each_blocks(template, data)  # 1. {{#each ...}} Blöcke expandieren
out = render_if_blocks(out, data)         # 2. {{#if ...}} Blöcke expandieren
out = render_tokens(out, data)            # 3. {{simple.tokens}} ersetzen
```

**Warum:** `render_each_blocks` produziert neue `{{copy.hero.x}}`-Tokens für jedes wiederholte Item. `render_tokens` muss **danach** laufen, damit diese neuen Tokens auch ersetzt werden.

### TOKEN_RE: Control-Token-Sicherheit

Der Regex für Simple-Tokens muss **Control-Tokens ausschliessen**:

```python
# ❌ FALSCH: matscht auch {{#each}} und {{/each}}
TOKEN_RE = re.compile(r'\{\{([^{}]+?)\}\}')

# ✅ RICHTIG: Lookahead blockiert # und / nach {{
TOKEN_RE = re.compile(r'\{\{(?![#/])([^{}]+?)\}\}')
```

Ohne den `(?![#/])`-Lookahead würde `re.sub` `{{/each}}` zu `{{each}}` korrumpieren — das schliesst den Block nie, und der Container-String wird zerstört.

### {{#each}}-Block-Expansion

```python
def render_each_blocks(template: str, data: dict) -> str:
    """Expand {{#each path}}...{{/each}} blocks recursively."""
    EACH_RE = re.compile(r'\{\{#each ([^{}]+?)\}\}(.*?)\{\{/each\}\}', re.DOTALL)
    
    def _expand(match):
        items_path = match.group(1).strip()
        block_template = match.group(2)
        items = resolve_path(data, items_path)
        if not isinstance(items, list):
            return match.group(0)  # unverändert bei Fehler
            
        parts = []
        for item in items:
            # Rekursive Expansion: neue Tokens aus dem Listen-Item
            item_data = dict(data)  # shallow copy
            parts.append(render_each_blocks(block_template, {**data, items_path.rpartition('.')[2]: item}))
        return ''.join(parts)
    
    return EACH_RE.sub(_expand, template)
```

**Pitfall:** Der zweite `render_each_blocks`-Call innerhalb der List-Expansion ist **rekursiv**. Wenn ein `{{#each}}`-Block in einem anderen `{{#each}}`-Block liegt, muss die Engine das mehrfach auflösen können. Ein einfacher `re.sub` ohne Rekursion bricht bei nested Lists.

### {{#if}}-Conditional-Blöcke (v2, 2026-07-08)

Die Template-Engine unterstützt optionalen Content via `{{#if path}}...{{/if}}`:

```python
def render_if_blocks(template: str, data: dict) -> str:
    """Expand {{#if path}}...{{/if}} — removes block when path value is falsy."""
    IF_RE = re.compile(r'\\{\\{#if ([^{}]+?)\\}\\}(.*?)\\{\\{/if\\}\\}', re.DOTALL)

    def _resolve(match):
        condition_path = match.group(1).strip()
        block_content = match.group(2)
        value = resolve_path(data, condition_path)
        if value and value not in (None, '', [], {}, 0, False):
            return block_content
        return ''

    return IF_RE.sub(_resolve, template)
```

**Nutzung:** Alternativtexte, Sonder-Features, A/B-Testing:
```html
{{#if hero.show_eyebrow}}<span class="eyebrow">{{copy.hero.eyebrow}}</span>{{/if}}
```

### `this.X`-Property-Zugriff im Loop

Innerhalb eines `{{#each}}`-Blocks referenziert `{{this.property}}` das aktuelle Iterations-Item:

```html
{{#each bundles}}
<h3>{{this.display_name}}</h3>
<p>{{this.description}}</p>
{{/each}}
```

**Implementierung:** `resolve_path` muss `this.`-Prefix als Sonderfall erkennen:

```python
def resolve_path(data: dict, path: str):
    if path.startswith('this.'):
        key = path[5:]  # strip 'this.' — direktes Item-Property
        return data.get(key) if isinstance(data, dict) else None
    # normaler Dot-Notation-Lookup
    for part in path.split('.'):
        if isinstance(data, dict):
            data = data.get(part)
        else:
            return None
    return data
```

**Pitfall:** Ohne diesen Check parst `resolve_path(data, 'this.display_name')` den Pfad als drei Dot-Segmente (`this` → `display` → `name`) und returned `None`, weil `data['this']` nicht existiert.

### Featurse
- **`make all`** = clean + build + verify (Default-Target)
- **`make build`** = ruft `build.py --template ... --copy ... --output ...` auf
- **`make serve`** = lokaler HTTP-Server auf `:8000`
- **`make verify`** = Validierung mit Graceful-Fallback
- **`make clean`** = dist/ + __pycache__ entfernen

### Python-Version-Check

```makefile
PYTHON_OK := $(shell $(PYTHON) -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null && echo yes || echo no)
```

Der Check ist wichtig weil `build.py` stdlib-Features nutzt die Python <3.11 nicht hat (z.B. tomllib in der ursprünglichen Spec).

### Graceful Verify-Fallback

```makefile
verify: build  ## Validate dist/index.html with html5validator (or fallback)
ifeq ($(shell which html5validator 2>/dev/null),)
	@echo "⚠️  html5validator not installed. Running stdlib sanity checks..."
	$(PYTHON) -c "
import sys
sys.path.insert(0, '.')
from build import _check_output
rc = _check_output('dist/index.html')
sys.exit(0 if rc else 1)
"
else
	html5validator dist/index.html --skip-non-html
endif
```

**Vorteil:** CI kann ohne Vorbedingungen laufen — installierte Tools werden genutzt, fehlende Tools führen zu einem internen Fallback statt zu einem Fehlschlag.

## Phase 4: GitHub Actions Deploy-Pipeline

### Workflow-Struktur

```yaml
name: Deploy Landing Page
on:
  push:
    branches: [main]
    paths:
      - 'scripts/**'
      - 'copy.json'
      - 'Makefile'
      - '.github/workflows/deploy-landing.yml'
  workflow_dispatch:  # Manuelle Auslösung

# EIN Job mit 3 Steps, kein matrix/parallel
# → minimales Permission-Modell
permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build-and-deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: make build           # ← stdlib-only, keine pip-Installs
      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist/
      - id: deployment
        uses: actions/deploy-pages@v4
```

### Design-Entscheidungen

| Entscheidung | Begründung |
|---|---|
| **1 Job, 3 Steps** | Kein Build→Deploy-Split nötig — die Page ist <10 KB, Build in <5s |
| **`contents: read`** | Read-only Checkout. Pages-Deploy braucht nur `pages: write` + `id-token: write` |
| **`actions/upload-pages-artifact@v3`** | Offizielles GitHub-Actions-Pages-Plugin mit Retention-Management |
| **`actions/deploy-pages@v4`** | Aktuelle Version (2026-07). Nutzt OIDC statt deploy-keys |
| **`actions/setup-python@v5` mit cache** | Erste Installation: ~30s. Cached für Folge-Builds: ~5s |
| **Nur `scripts/**` + `copy.json` + `style-tokens.json` + `requirements.txt` als Path-Trigger** | Kein Re-Deploy bei `.gitignore`- oder `README`-Änderungen. **v2 wichtig:** `style-tokens.json` + `requirements.txt` MÜSSEN in `paths:` sein, sonst triggern Designer- und Cache-Updates keinen CI-Run |
| **`workflow_dispatch`** | Manuelles Re-Deploy bei CI-Config-Änderungen |
| **Concurrency `pages`** | Kein paralleler Deploy auf Pages — in-flight wird gecancelled |

### Warum kein `pip install` im CI?

Das Build-Script (`build.py`) ist **stdlib-only** (Python 3.11+): `re`, `json`, `sys`, `pathlib`. Der einzige externe Dependency-Wunsch wäre `html5validator` für das `verify`-Target — und selbst das hat einen stdlib-Fallback. Kein `requirements.txt`, kein `pip install`, kein Caching-Schmerz.

### CI-Cache-Gotcha: `cache-dependency-path` braucht ein existierendes File

**Symptom:** `actions/setup-python@v5` mit `cache: 'pip'` und `cache-dependency-path: requirements.txt` schlägt CI mit `FileNotFoundError` fehl, wenn `requirements.txt` nicht existiert — auch wenn stdlib-only kein `pip install` braucht.

**Symptom (still):** Wenn `requirements.txt` existiert aber leer ist, cacht `setup-python` erfolgreich einen leeren Cache → `pip install` skippt → kein Timeout → CI pass.

**Fix:** Eine leere (oder minimale) `requirements.txt` im Repo:
```bash
echo "# stdlib-only — exists for cache-dependency-path key" > requirements.txt
```

**Warum das passiert:** `actions/setup-python@v5` erwartet einen gültigen File-Pfad für `cache-dependency-path`. Bei `stdlib-only`-Builds vergisst man leicht, dass trotzdem eine existierende Datei angegeben werden muss.

**Nicht-Fix:** `cache-dependency-path` weglassen → der Cache-Key fällt auf den Default, der alle `requirements*.txt` und `pyproject.toml` matched. Wenn KEINE dieser Dateien existiert, schlägt der Action-Step trotzdem fehl.

**Verified 2026-07-08:** Das v1-Bundle-Repo-Deploy scheiterte mit `FileNotFoundError: requirements.txt`. Nach Anlegen einer leeren `requirements.txt` lief der CI-Durchlauf erfolgreich durch.

## Phase 5: Verifier-Quality-Gate

### Sanity-Checks im Build-Script

```python
def _check_output(output_path: str) -> bool:
    """Built-in quality checks: file exists, non-empty, no unresolved tokens."""
    content = Path(output_path).read_text()
    checks = [
        ("Datei existiert", content),
        ("Nicht leer", len(content) > 100),
        ("Keine unresolved Tokens", not re.search(r'\{\{[^}]+\}', content)),
        ("Doctype vorhanden", '<!doctype html>' in content.lower()),
    ]
    ok = True
    for name, cond in checks:
        if cond:
            print(f"  ✅ {name}")
        else:
            print(f"  ❌ {name}")
            ok = False
    return ok
```

### Multi-Agent-Verifier-Schritte

| Was | Wer prüft | Wie |
|---|---|---|
| Copy-Content stimmt | Verifier | `grep` auf gerenderter HTML nach Headline/Description |
| CI-Workflow valid | Verifier | YAML-Syntax + Action-Versionen (`@v4`, `@v5`) |
| Template kompiliert | Engineer | `python3 scripts/build.py` + Sanity-Check |
| `make all` grün | Engineer | `cd /tmp/project && make all` |
| Design-Konsistenz | Designer | Vision-Analyse der gerenderten Seite |
| Writer-Facts korrekt | Researcher | Cross-Check der Copy gegen arxiv/Quellen |

## Bekannte Pitfalls

### 1. Writer liefert anderes JSON-Schema als erwartet
**Symptom:** `resolve_path` returned `None` für `copy.hero.headline` — aber die Datei hat `hero.headline` ohne `copy`-Envelope.
**Fix:** Auto-Wrap in der Pipeline (siehe Phase 3→4).

### 2. Template-Tokens werden nicht ersetzt nach {{#each}}
**Symptom:** Gerenderte HTML hat `{{features.items.0.title}}` anstatt echten Werten.
**Fix:** Render-Pass-Ordnung: erst `render_each_blocks`, dann `render_tokens`. Der `render_each_blocks`-Pass produziert neue Tokens, die erst im zweiten Pass ersetzt werden.

### 3. RACE beim Verifier-Output
**Symptom:** Verifier und Engineer widersprechen sich (z.B. "12 Copy-Felder" vs "22 Copy-Felder").
**Fix:** Beide haben vom selben Source-Output gearbeitet — das Problem war, dass der eine die Pre-Build-Version und der andere die Post-Build-Version sah. **Synchronisiere den Snapshot bevor Verifier läuft.** Nutze `/tmp` als gemeinsamen Stage-Ordner.

### 4. MCP-Token-Race beim Multi-Repo-Push
**Symptom:** `mcp__github__create_or_update_file` sagt "already exists" obwohl das File nicht existiert.
**Fix:** Nach jedem Write curl-verifizieren. Bei Konflikt auf `gh api -X PUT` mit aktueller SHA umsteigen.

### 5. CI-Cache-Key delegiert an nicht-existierendes File
**Symptom:** `actions/setup-python@v5` bricht ab mit `FileNotFoundError: requirements.txt` — trotz stdlib-only Build.
**Fix:** Immer eine `requirements.txt` im Repo anlegen (auch wenn leer). Siehe "CI-Cache-Gotcha" Abschnitt oben.

### 6. Inline CSS-Class-Concat → Boolean Conditional (featured_class-Fix, 2026-07-08)

**Symptom:** copy.json enthält `"featured_class": " bundle--featured"` und das Template nutzt `class="bundle {{this.featured_class}}"`. Die Klasse wird als Leerzeichen-Prefix-String im JSON gehalten, was fragil ist (falsches Leerzeichen bricht die HTML-Klasse) und semantisch unehrlich (CSS ist View-Layer, nicht Data-Layer).

**Fix — Migration zu boolean Conditional:**

```json
// copy.json — VORHER (string-concat)
{
  "name": "Code",
  "featured_class": " bundle--featured",
  "count": 91
}

// copy.json — NACHHER (boolean conditional)
{
  "name": "Code",
  "featured": true,
  "count": 91
}
```

```html
{{#if this.featured}}<div class="bundle bundle--featured">
{{else}}<div class="bundle">{{/if}}
  <h3>{{this.name}}</h3>
</div>
```

Das `{{#if}}`-Conditional zieht die CSS-Klasse inline statt per JSON-String. Vorteile:
- **Semantisch korrekt:** `featured` ist ein boolesches Merkmal im Data-Layer, kein CSS-Fragment
- **Kein Leerzeichen-Risiko:** Der HTML-Code kontrolliert die Klasse, nicht ein unsichtbarer Prefix-Char im JSON
- **Einfacher zu erweitern:** Aus `{{#if featured}}` kann man später `{{#if featured}}featured{{/if}} {{#if archived}}archived{{/if}}` machen — keine String-Konkatenation im Template

**Verifizierung nach Migration:**
```bash
# Vorher: grep "featured_class" copy.json → existiert
# Nachher: grep "featured_class" copy.json → leer (keine false positives)
# Template: grep -c "bundle--featured" dist/index.html → korrekte Anzahl (z.B. 12)
```

**Wann nicht anwenden:**
- Wenn die CSS-Klasse **dynamisch** ist (vom User gewählt, nicht systemisch): z.B. `status_class: "error"` → String ist korrekt, das ist Data-Layer
- Wenn mehrere CSS-Klassen **exklusiv** sind (genau eine von N): Array + `join(" ")` ist pragmatischer als N `{{#if}}`-Blöcke

### 7. Path-Trigger-Mismatch: `style-tokens.json` fehlt in `paths:`
**Symptom:** Designer updatet die Style-Tokens → Push auf main → CI läuft NICHT → alte Page deployed.
**Fix:** Alle Build-Input-Files in `paths:` aufnehmen: `copy.json`, `style-tokens.json`, `index.html.template`, `scripts/**`, `Makefile`, `requirements.txt`, `.github/workflows/deploy-landing.yml`.

## Makefile-Verify-Gates (v2, 2026-07-08)

Das `make verify`-Target prüft Output-Qualität vor Deploy mit konkreten Schwellen:

```makefile
verify: build
	size_threshold=35000  # Bytes — fängt Mini-Output-Bug ab
	@if [ $$(stat -c %s dist/index.html) -lt $$size_threshold ]; then ...
	@grep -q "{{" dist/index.html && echo "UNRESOLVED TOKENS" && exit 1 || true
	@grep -c "<section" dist/index.html | awk '{if($$1<5) exit 1}'  # ≥5 Sections
	@grep -c "bundle--" dist/index.html | awk '{if($$1<10) exit 1}'  # ≥10 bundle-classes
	@grep -c "<details" dist/index.html | awk '{if($$1<4) exit 1}'   # ≥4 FAQ Items
```

| Gate | Schwelle | Fängt ab |
|------|----------|----------|
| Dateigröße | ≥ 35 KB | Mini-Output (v1-Bug: 6 KB statt 47 KB) |
| Unresolved Tokens | 0 | Template-Engine-Fehler |
| `<section>` Count | ≥ 5 | Missing Content-Sections |
| `bundle--` classes | ≥ 10 | Bundle-Cards nicht gerendert |
| `<details>` Count | ≥ 4 | FAQ nicht gerendert |

## Session-Referenz

### v1 (2026-07-08, initial)

| Feld | Wert |
|---|---|
| Datum | 2026-07-08 |
| Projekt | Toqsick/yuno-minimax-bundles |
| Artefakte | `scripts/build.py`, `scripts/index.html.template`, `Makefile`, `.github/workflows/deploy-landing.yml`, `README-DEPLOY.md` |
| Agenten | Researcher (arxiv), Designer (style-tokens.json), Writer (copy.json), Engineer (Pipeline), Verifier (Gate) |
| Repo | `Toqsick/yuno-minimax-bundles`, Branch `landing` |
| Build-Check | `make all` ✅: 4 Feature-Cards geloopt, Hero+Footer mit Copy gefüllt, 0 unresolved Tokens, 6055 Bytes |
| Token-Fix | `(?![#/])` Lookahead in TOKEN_RE |
| Data-Shape-Fix | Auto-wrap flaches Writer-JSON in `copy`-Envelope |

### v2 (2026-07-08, Fix-Iteration)

| Feld | Wert |
|---|---|
| Auslöser | v1 Verifier → NEEDS-FIX (Designer-HTML vs Pipeline-Output incompatible) |
| Fix-Strategie | Chained-Sequential Pipeline: Designer fertig → Writer nutzt Designer-Output → Engineer nutzt beide |
| Designer-Output | `index.html.template` (36 KB, mit `{{copy.X}}`-Tokens) + `copy.json` (9 KB, spec-konform mit allen 7 Sections) |
| Style-Tokens | Neu: `style-tokens.json` (2.5 KB, colors, typography, spacing) |
| Build-Script | `build.py` (10.7 KB, 302 Zeilen) mit `{{#each}}`-Loop + `{{#if}}`-Conditional + `this.X`-Support |
| Cache-Fix | Leeres `requirements.txt` angelegt für `setup-python@v5` `cache-dependency-path` |
| Path-Filter | 8 paths in `deploy-landing.yml` inkl. `style-tokens.json` + `scripts/**` + `README-DEPLOY.md` |
| Makefile | Neu: `make verify`-Target mit Größen/Sections/Bundles/FAQ-Gates |
| Build-Test | `make all` ✅: 47.836 Bytes, 5 Sections, 22 bundle-- classes, 6 FAQ `<details>`, 0 unresolved tokens |
| Verifier-Verdict | Expected: PASS (alle 5 v1-Issues gefixt)

## Siehe auch

- `references/e2e-test-pattern.md` — Pre-Preparation, Context-Injection-Matrix, Verifier-Gate vor Dispatch
- `references/fix-loop-pattern.md` — Engineer→Verifier→Fix→Re-Audit→PASS (für Production-Ready)
- Haupt-SKILL.md — Multi-Persona Fix-Loop Pattern, Anti-Patterns
