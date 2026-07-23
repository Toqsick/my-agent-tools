# Run-Log: kanban-video-orchestrator 1.0.2 → 1.0.3

Vollständige Reproduktion des Patches. Quell-ZIP lag auf
`/home/bratan/.hermes/kanban/kanban-video-orchestrator-ALL-IN-ONE-v1.0.2.zip`.

## Quell-Material

- **Source-ZIP:** `/home/bratan/.hermes/kanban/kanban-video-orchestrator-ALL-IN-ONE-v1.0.2.zip`
- **SHA-256:** `773c9bf2597873f6bed9b612d51184fc2b198e8cbe02ab1ec29a6460ff3f5e94`
- **Inhalt:** 37 Einträge in 3 Layern: ZIP-Layout (Flatten) + nested `release-package/` + Beispiel-ZIPs. Kanonische Release-Version ist `kanban-video-orchestrator-release-v1.0.2.zip` (24 906 B, SHA-256 `b05a12bb9906d1ed0e2aa169dbdbca1dec56325b94ff3f298463a3a7e92ad507`) mit 14 Files (Flat-Layout, ohne nested `release-package/`).
- **Autor (laut SKILL.md frontmatter):** `[SHL0MS, alt-glitch]`
- **Hermes auf Workstation:** aktive Default-Profile `default / yuno / yuno-coder / yuno-vision / yuno-flash`, Modell `minimax/MiniMax-M3`.

## Befunde (CRITICAL/HIGH/MED/LOW, priorisiert)

| # | Sev | Datei | Symptom | Fix |
|---|-----|-------|---------|-----|
| 1 | **CRITICAL** | `scripts/bootstrap_pipeline.py:368/383` | `cp: reguläre Datei '$WORKSPACE/audio/track.mp3' kann nicht angelegt werden` — single-quoted Zielpfade blockieren `$VAR`-Expansion, Setup crasht vor Director-Task. | Neuer Helper `shell_double_quote_expand_vars()` für generator-eigene Zielpfade. |
| 2 | HIGH | `assets/setup.sh.tmpl` | Profile-Config-Patch schreibt nur `toolsets` + `skills.always_load`. Dispatcher liest aber `platform_toolsets.cli` → Worker spawnt mit falscher/leerer Tool-Liste, Director zerlegt blind. | Patch schreibt zusätzlich `platform_toolsets.cli` + Assertion. |
| 3 | HIGH | `scripts/monitor.py` | Enrich-Loop las Felder (`heartbeat_at`, `max_runtime_s`, `retries`) die `kanban list --json` nicht liefert. STUCK/OVERTIME-Detection war effektiv tot. Timestamp-Parser nahm ISO, Hermes liefert epoch. | Komplett neues `enrich()` mit `kanban show --json` → `runs[-1]`, neue `parse_ts()` für epoch+ISO, UTC-aware, retries via `len(runs)-1`. |
| 4 | MED | `bootstrap_pipeline.py` (Profile-Create) | `hermes profile create foo --clone 2>/dev/null \|\| true` maskiert Konflikte — überschreibt fremde Profile ohne Warnung. | Neue `create_profile()`-Shell-Funktion mit Owner-Marker `$HOME/.hermes/profiles/<name>/.kanban-video-orchestrator-owner`. |
| 5 | MED | Setup | Profile-Descriptions fehlen → Kanban-Decomposer routet blind (Description-basierte Decomposition). | `profile_description()`-Generator + `hermes profile describe --text` für jedes Profil. |
| 6 | MED | `assets/setup.sh.tmpl` (Director-Body) + `assets/soul.md.tmpl` | Workspace-Regel im Director-Body war Python-Pseudocode (`workspace_kind="dir"`), nicht echte CLI-Flags. SOUL.md erwähnte Heartbeats ohne Tool. | Echte Flags (`--workspace dir:<path> --tenant <slug>`), konkretes `hermes kanban heartbeat` mit `--note` in SOUL. |
| 7 | LOW | `README.md` / `docs/dry-run-checklist.md` / `SKILL.md` | Doku zeigte `hermes kanban stats --tenant` (existiert nicht — nur `--board`), `workspace_kind=`-Pseudocode, `toolsets`-only-Setup. | Doku überall an aktuelle CLI-Form angepasst. |

## Reproduktions-Befehle (1:1 zum Smoke-Run)

### Extraktion mit Zip-Slip-Schutz
```python
from zipfile import ZipFile
from pathlib import Path
import shutil
src = Path('/home/bratan/.hermes/kanban/kanban-video-orchestrator-ALL-IN-ONE-v1.0.2.zip')
out = Path('/home/bratan/20-Workspace/kanban-video-orchestrator-v1.0.2-analysis')
if out.exists(): shutil.rmtree(out)
out.mkdir(parents=True, exist_ok=True)
with ZipFile(src) as z:
    for info in z.infolist():
        target = (out / info.filename).resolve()
        if not str(target).startswith(str(out.resolve()) + '/'):
            raise RuntimeError(f'unsicherer ZIP-Pfad: {info.filename}')
    z.extractall(out)
```

### Statischer Pass — Schema vs Generator
```bash
cd /home/bratan/20-Workspace/kanban-video-orchestrator-v1.0.2-analysis/release-package
python3 -m py_compile scripts/bootstrap_pipeline.py scripts/monitor.py
python3 scripts/bootstrap_pipeline.py --schema-out /tmp/kvo-102-schema.json
diff -u plan.schema.json /tmp/kvo-102-schema.json
# → leer = OK
```

### Statischer Pass — Live-CLI-Form verifizieren
```bash
hermes kanban create --help    # zeigt --workspace / --tenant / --max-runtime etc.
hermes kanban list --help       # zeigt nur --tenant, KEIN --status ready (initial-status)
hermes kanban list --json       # FLAT shape, KEIN heartbeat_at / max_runtime_s / retries
hermes kanban show <task-id> --json
                                # { task, runs:[...], events:[...], ... }
                                # runs[-1] hat last_heartbeat_at / max_runtime_seconds
```

### Reproduktiver Smoke-Run (Fake-Hermes)

```bash
set -euo pipefail
FIX=/home/bratan/20-Workspace/kanban-video-orchestrator-v1.0.3-yuno-fix
SMOKE=/tmp/kvo-103-smoke-$(date +%s)
mkdir -p "$SMOKE"
cd "$FIX"

# Plan mit realen Dummy-Asset-Pfaden
python3 - <<'PY' "$FIX" "$SMOKE"
from pathlib import Path
import json, sys
base = Path(sys.argv[1]); smoke = Path(sys.argv[2])
plan = json.loads((base/'examples/example-plan-product-teaser.json').read_text())
assets = smoke/'dummy-assets'; assets.mkdir(parents=True, exist_ok=True)
files = {'track.mp3': b'dummy', 'logo.svg': b'<svg/>',
         'Inter-Regular.ttf': b'font', 'demo-capture.mp4': b'vid',
         'ref-frame-01.png': b'png'}
for n, d in files.items(): (assets/n).write_bytes(d)
plan['assets'] = {
    'audio_track': str(assets/'track.mp3'),
    'logos': [str(assets/'logo.svg')],
    'fonts': [str(assets/'Inter-Regular.ttf')],
    'existing_footage': [str(assets/'demo-capture.mp4')],
    'style_frames': [str(assets/'ref-frame-01.png')],
}
(smoke/'plan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')
PY

# Generieren
python3 scripts/bootstrap_pipeline.py "$SMOKE/plan.json" \
  --out "$SMOKE/setup.sh" --brief-out "$SMOKE/brief.md" --team-out "$SMOKE/TEAM.md"
bash -n "$SMOKE/setup.sh"

# Fake-Hermes bauen
FAKEBIN="$SMOKE/bin"; mkdir -p "$FAKEBIN"
cat > "$FAKEBIN/hermes" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
log="${HERMES_FAKE_LOG:?}"
echo "hermes $*" >> "$log"
case "${1:-} ${2:-}" in
  "profile create"*) mkdir -p "$HOME/.hermes/profiles/${3}"; printf '{}\n' > "$HOME/.hermes/profiles/${3}/config.yaml"; exit 0;;
  "profile describe"*) exit 0;;
  "kanban init"|"kanban stats") exit 0;;
  "kanban create"*) echo "t_fake_103"; exit 0;;
  "kanban list"*) echo "[]"; exit 0;;
  "kanban watch"*) sleep 60;;
esac
exit 0
SH
chmod +x "$FAKEBIN/hermes"

FAKEHOME="$SMOKE/fakehome"; mkdir -p "$FAKEHOME/.hermes"
printf 'ELEVENLABS_API_KEY=dummy\nOPENROUTER_API_KEY=dummy\n' > "$FAKEHOME/.hermes/.env"
export HERMES_FAKE_LOG="$SMOKE/hermes-calls.log"

set +e
HOME="$FAKEHOME" PATH="$FAKEBIN:$PATH" HERMES_HOME="$FAKEHOME/.hermes" \
  bash "$SMOKE/setup.sh" > "$SMOKE/setup.stdout" 2> "$SMOKE/setup.stderr"
rc=$?
set -e
echo "=== setup_rc=$rc ==="
```

**Erwartete Evidenz nach dem Patch (alle Punkte müssen grün sein):**
- `setup_rc=0`
- stdout enthält `✓ copied track.mp3 -> .../audio/track.mp3` (5 Zeilen)
- `✓ SOUL.md for <profile>` × 10 Profile
- `✓ director / copywriter / concept-artist / ...` × 10 Profile-Configs
- `t_fake_103` (Director-Task gefeuert)
- `hermes-calls.log` enthält `profile create ... --clone`, `profile describe ...`, `kanban create ...`
- `$FAKEHOME/.hermes/profiles/<name>/.kanban-video-orchestrator-owner` enthält `q3-product-teaser`
- `$FAKEHOME/.hermes/profiles/<name>/config.yaml` enthält
  `toolsets: [...]`, `platform_toolsets.cli: [...]`, `skills.always_load: [...]`

## Release-Bau

```bash
cd /home/bratan/20-Workspace/kanban-video-orchestrator-v1.0.3-yuno-fix
rm -rf scripts/__pycache__                       # NICHT in die ZIP

# Flat release-package/ neu aufbauen
python3 -c "
import shutil
from pathlib import Path
src=Path('.')
dst=Path('release-package')
if dst.exists():
    for child in dst.iterdir():
        if child.is_dir(): shutil.rmtree(child)
        else: child.unlink()
for name in ['README.md','SKILL.md','CHANGELOG.md','VERSION','plan.schema.json','assets','docs','scripts','examples']:
    s=src/name
    if s.is_dir(): shutil.copytree(s, dst/name)
    else: shutil.copy2(s, dst/name)
"

cd release-package
python3 - <<'PY' > release-manifest-v1.0.3.csv
import hashlib, csv, sys
from pathlib import Path
root=Path('.')
files=sorted(p for p in root.rglob('*') if p.is_file() and p.name != 'release-manifest-v1.0.3.csv')
w=csv.writer(sys.stdout)
w.writerow(['release_path','bytes','sha256'])
for f in files:
    data=f.read_bytes()
    w.writerow([str(f.as_posix()), len(data), hashlib.sha256(data).hexdigest()])
PY

# ZIP bauen (Manifest NICHT im ZIP — Original 1.0.2 hat es auch nicht im ZIP)
cd ..
python3 - <<'PY'
import zipfile
from pathlib import Path
src=Path('release-package')
dst=Path('kanban-video-orchestrator-release-v1.0.3.zip')
with zipfile.ZipFile(dst,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(src.rglob('*')):
        if p.is_file():
            z.write(p, str(p.relative_to(src).as_posix()))
PY
sha256sum kanban-video-orchestrator-release-v1.0.3.zip
```

**Output:**
- ZIP: 28 165 B
- SHA-256: `5fd62b67b355e7643f25e87d236d9755495946e14109c137ffadfa30deae3467`
- 15 Files (inkl. Manifest im ZIP — siehe Pitfall zur ZIP-Variante)

### Final-Verify nach Build
```bash
mkdir -p /tmp/kvo-103-final-verify
cd /tmp/kvo-103-final-verify
unzip -q /home/bratan/.hermes/kanban/kanban-video-orchestrator-release-v1.0.3.zip
python3 scripts/bootstrap_pipeline.py --schema-out /tmp/final-schema.json
diff -u plan.schema.json /tmp/final-schema.json      # → leer
for p in examples/*.json; do
  python3 scripts/bootstrap_pipeline.py "$p" --validate-only
done                                                # → alle 3 grün
bash -n assets/setup.sh.tmpl                          # → SETUP_TEMPLATE_BASH_OK
```

## Deliverables

| Datei | Pfad | Hash / Größe |
|------|------|------|
| ZIP | `/home/bratan/.hermes/kanban/kanban-video-orchestrator-release-v1.0.3.zip` | 28 165 B, `5fd62b67…3467` |
| Manifest | `/home/bratan/.hermes/kanban/release-manifest-v1.0.3.csv` | 14 Files, 86 635 B uncompressed |
| Working-Copy | `/home/bratan/20-Workspace/kanban-video-orchestrator-v1.0.3-yuno-fix/` | mit `release-package/`-Flat-Tree |
| PR-Draft | `/home/bratan/20-Workspace/kanban-video-orchestrator-v1.0.3-yuno-fix/PR-DRAFT.md` | copy-paste-ready |
| Source-ZIP-Analysis | `/home/bratan/20-Workspace/kanban-video-orchestrator-v1.0.2-analysis/` | Original-Diagnostik |

## Lessons Learned (für nächste Session)

1. **Generator-controlled shell paths mit `$VAR` brauchen double-quote, NICHT single-quote.** Das ist der häufigste Bug in Templates, die ein Helferlein wie `shell_single_quote(s)` zu eifrig anwenden.
2. **Hermes-CLI-Flag-Snapshots in Templates veralten schnell.** Immer gegen `hermes <subcmd> --help` validieren, bevor ein Bundle gegen Live-Hermes läuft.
3. **Hermes-Kanban-Daten leben in `show --json` → `runs[-1]`, nicht in `list --json`.** Wer Monitor-Scripts schreibt muss das wissen, sonst sieht er leere Detections.
4. **Profile-Conflict-Masking ist still.** `2>/dev/null || true` überdeckt, dass `hermes profile create foo --clone` keinen Konfliktfehler wirft, wenn `foo` schon existiert. Owner-Marker sind die einzige sichere Abhilfe.
5. **Fake-Hermes in einem PATH-prepended Bin-Dir ist die schnellste reproduzierbare Smoke-Test-Methode.** Kein Live-Hermes nötig, kein Risiko für `~/.hermes/`, schneller Loop.