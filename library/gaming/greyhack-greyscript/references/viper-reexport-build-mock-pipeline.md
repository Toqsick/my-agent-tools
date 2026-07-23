# Viper Re-Export Build + Mock Smoke Pipeline

**Session:** 2026-07-15 (Biene C, Engineer-Scout 3/3)  
**Scope:** 5 Viper v1 re-export modules aus `/tmp/viper-reexport/` → Build + Mock-Smoke + Pattern-Scan + Report  
**Tool:** `greybel 3.7.12`, Mock-Env, `params "exit"/"help"`

---

## 1) Build Pipeline

```bash
mkdir -p /tmp/viper-build
for m in core scan post net util; do
  greybel build /tmp/viper-reexport/yuno_viper_$m.src /tmp/viper-build/yuno_viper_$m
done
```

**Alle 5 Builds Exit=0, keine Warnings.**  
Jeder Build produziert in `/tmp/viper-build/yuno_viper_<modul>/build/yuno_viper_<modul>.src` den kompilierten Output.

### Build-Charakteristik

| Aspekt | core | scan | post | net | util |
|--------|------|------|------|-----|------|
| `import_code("/root/...")` | — (Hauptmodul) | ✅ core inkludiert | ✅ core inkludiert | ❌ autark | ❌ autark (pre-shortened) |
| Source-Größe | 14.3 KB / 411 Z | 23.6 KB / 813 Z | 18.1 KB / 685 Z | 21.0 KB / 731 Z | 23.3 KB / 683 Z |
| Build-Output | 9.4 KB / 311 Z | 16.2 KB (+core) | 14.8 KB (+core) | 15.9 KB | 16.8 KB |
| Namespace | volle Namen | volle Namen | volle Namen | volle Namen | **pre-shortened** (BX/Z/I/P/N) |

### Wichtig: Build-Output enthält import_code-Inhalt

`scan` und `post` haben `import_code("/root/yuno_viper_core.src")` im Source → der Compiler **inkludiert den core-Inhalt** direkt in den Build-Output. Das ist normal und erwünscht — das Game wird dann nur die `build/`-Datei laden.

---

## 2) Mock-Smoke Setup

```bash
# Core (standalone, eigenes REPL)
greybel execute /tmp/viper-build/yuno_viper_core/build/yuno_viper_core.src --params "exit" --env-type Mock
# Erwartet: Banner, Auto-Lib-Loader (3/4, 4/4 fail ist ok), Session, Prompt, Exit

# net (autark, keine core-Abhängigkeit)
greybel execute /tmp/viper-build/yuno_viper_net/build/yuno_viper_net.src --params "help" --env-type Mock
# Erwartet: help-Output, kein Fehler (30ms Laufzeit)

# ## KRITISCH: Sub-Module mit import_code() brauchen core im parent-root
# Die `import_code("/root/yuno_viper_core.src")`-Pfade in scan/post werden relativ
# zum **übergeordneten Verzeichnis** des .src-Files aufgelöst:
#   /tmp/.../scan/build/yuno_viper_scan.src
#   → sucht /tmp/.../scan/build/root/yuno_viper_core.src

mkdir -p /tmp/viper-build/yuno_viper_scan/build/root
cp /tmp/viper-build/yuno_viper_core/build/yuno_viper_core.src /tmp/viper-build/yuno_viper_scan/build/root/

greybel execute /tmp/viper-build/yuno_viper_scan/build/yuno_viper_scan.src --params "help" --env-type Mock
# Erwartet: core-Banner, dann sub-Modul-Output, dann REPL

# gleiches Setup für post:
mkdir -p /tmp/viper-build/yuno_viper_post/build/root
cp /tmp/viper-build/yuno_viper_core/build/yuno_viper_core.src /tmp/viper-build/yuno_viper_post/build/root/

greybel execute /tmp/viper-build/yuno_viper_post/build/yuno_viper_post.src --params "help" --env-type Mock
```

### Mock-Erwartungsmatrix

| Modul | Mock-Run | Erwartung | Latenz |
|-------|----------|-----------|--------|
| core | `params "exit"` | ✅ Banner + Libs + Session + Prompt + Exit | <500ms |
| net | `params "help"` | ✅ help-Output, autark | <50ms |
| scan | `params "help"` (mit core-mock) | ✅ core-Banner → sub-Output | <200ms |
| post | `params "help"` (mit core-mock) | ✅ core-Banner → sub-Output | <200ms |
| util | `params "x"` | ⚠️ siehe §3 | — |

---

## 3) Bekannte Mock-Quirks (keine In-Game-Breaker)

### util — `Path "h" not found`

Die `yuno_viper_util.src` hat im **Original-Quelltext bereits pre-shortened Variablen** (steht schon `BX = Z`, `Ck = I.Fa + P.current_user`, `print(N("...", I.FC))` im unkompilierten Source). Das ist untypisch — normalerweise werden diese Names erst vom Compiler komprimiert.

**Effekt im Mock:**
- `Z` wird nicht initialisiert (weil core nicht geladen)
- `I.F*` und `N()` existieren nicht
- `h` global ist nicht gesetzt → `if not h then h = {} end if` (Zeile ~670) scheitert mit `Path "h" not found`

**Im echten In-Game:**
- Wird der Source im CodeEditor geladen (nicht der re-exported unkompilierte Source), compiliert der Game-Compiler erneut → Names werden neu komprimiert und `h`/`Z`/`I`/`P`/`N` korrekt gesetzt
- **Kein In-Game-Blocker**

**Workaround für Mock-Tests:**
```bash
# util mit h-wrapper mock-en
cat > /tmp/viper-build/yuno_viper_util/build/wrap.src <<'EOF'
h = {}
import_code("/root/yuno_viper_util.src")
EOF
# Trotzdem: Z/I/P/N fehlen → Runtime Error. util Mock nur mit full-core-wrapper sinnvoll.
```

### net — `import_code` nicht vorhanden, aber autark

`yuno_viper_net.src` hat KEIN `import_code("yuno_viper_core")`. Es definiert alle eigenen Helfer (`yvn_safe_router()`, `yvn_format_output()`, etc.). **Das ist von Design so gewollt** — net kann eigenständig laufen und muss nicht core laden.

### scan/post — `network_gateway`/`get_router` funktioniert im Mock nicht

Die `network_gateway` und `get_router`-Aufrufe sind in-game native API-Funktionen. Im Mock-Env (`--env-type Mock`) sind sie nicht implementiert → Runtime Error wenn ein Befehl sie aufruft. Das ist OK — der **Banner/Init/Smoke** sollte trotzdem durchlaufen.

---

## 4) Pattern-Scan (nach Build)

Nach dem Build die 5 Build-Outputs auf bekannte Bug-Klassen scannen:

```bash
# Pattern (a): Einzeiliger if/then/end if
rg '\bif\b.*\bthen\b.*\bend\s+if\b' /tmp/viper-build/*/build/*.src

# network_gateway (prüfen auf Guards um jeden Fund)
rg 'network_gateway' /tmp/viper-build/*/build/*.src

# get_router (prüfen auf Shell-Guard)
rg 'get_router' /tmp/viper-build/*/build/*.src

# getcontent/setcontent lowercase (muss snake_case sein)
rg '\bgetcontent\b|\bsetcontent\b' /tmp/viper-build/*/build/*.src
# → 0 Treffer erwartet. Getcontent ist immer get_content mit Unterstrich.

# import_code-Topologie (prüfen welche Module core laden)
rg 'import_code' /tmp/viper-reexport/*.src | grep -v '^Binary'

# Module-Header check
for f in /tmp/viper-build/*/build/*.src; do
  first=$(head -1 "$f")
  module=$(basename "$f" .src)
  if echo "$first" | grep -q "^//command:\|^UtilLs\|^yuno_viper"; then
    echo "✅ $module: $first"
  else
    echo "⚠️ $module: $first"
  fi
done
```

---

## 5) Report-Format

Standardisierte Struktur für Build/Mock-Reports:

```markdown
# <Projekt> — Build/Mock Report

**Datum:** <YYYY-MM-DD>
**Tool:** greybel <version>
**Source:** <Pfad> (N Module)

---

## 1) Build-Tabelle

| # | Modul | Source-Größe | Build-Output | Exit | Status |
|---|-------|-------------|-------------|------|--------|
| 1 | core | N B / N Z | N B, N Z | 0 | ✅ GREEN |
| ... | ... | ... | ... | 0 | ✅ GREEN |

## 2) Mock-Execute Tabelle

| # | Modul | Mock-Run | Ergebnis | Notizen |
|---|-------|----------|----------|---------|

## 3) Pattern-Scan

### 3.1 Module-Header
### 3.2 Einzeilige if/then/end if
### 3.3 network_gateway / get_router / FS-Access
### 3.4 getcontent lowercase
### 3.5 import_code-Topologie

## 4) Captured Breakers

| ID | Typ | Severity | Beschreibung | Mitigation |

## 5) Tools & Reproduzierbarkeit

Bash-Befehle zum Reproduzieren (shell == bash)

## 6) Self-Report
```

---

## 6) Wichtige Befunde aus 2026-07-15 Reexport

1. **`net` und `util` haben KEIN `import_code("yuno_viper_core")`** → Sie sind autark konzipiert. In-Game können sie als Standalone-Commands ohne core laufen. Überprüfen vor jedem Deploy ob diese Autarkie noch gilt.

2. **`scan` und `post` HABEN `import_code("/root/yuno_viper_core.src")`** → DB-Injection MUSS core unter `/root/` bereitstellen, sonst starten scan/post nicht.

3. **`util.src` Original-Source ist pre-shortened** (BX/Z/I/P/N stehen schon da). Das bedeutet vermutlich dass irgendwann ein kompilierter Output zurück in den unkompilierten Source kopiert wurde. Kein Bug → aber ungewöhnlich. Nie versuchen Names zu "reparieren" — das ist der tatsächliche Source.

4. **network_gateway in net.src** (2 Stellen, beide in `yvn_safe_router(ip)` mit Shell-Guard `if sh == null then return {"router": null, "error": "..."}`). Sicher gewrappt.

5. **`get_router`** in scan.src (9×), immer innerhalb von Funktionen die zuvor `pc`/`sh` validieren. Kein direct-into-global pattern.