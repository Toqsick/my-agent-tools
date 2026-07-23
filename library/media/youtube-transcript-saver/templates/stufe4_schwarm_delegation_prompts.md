# Stufe 4 — LLM-Glättung (Single-Worker, nach Stufe 3)

## Wann diesen Workflow nutzen

Stufe 4 ist die Königsdisziplin für **zitierfähige Transcripts**:
- Schulungs-Material das zitiert wird
- Reference-Docs (z.B. Julian-Reihe als Lern-Basis)
- Blog-Beiträge oder Buch-Kapitel

NICHT für:
- Quick-Save-Captures (Stufe 3 reicht)
- Transcripts mit unklarem Inhalt (Stufe 4 würde halluzinieren)

**Wandlungs-Trigger:** "mach phase 4", "stufe 4", "lesbarer machen", "polish das", "zitierfähig machen".

## Voraussetzungen

Vor diesem Workflow MUSS Stufe 3 abgeschlossen sein:
- Final-File in `~/docs/youtube/` mit Header `polishing: Stufe 3 ...`
- Transkript-Block mit 0 Restfehler
- Rest-Ambiguitäten dokumentiert (typisch 2-4)

## Phase-Plan (5 Sub-Phasen)

### Sub-Phase 4.1 — Hochsichere Ambiguitäten deterministisch fixen

**Kritisch: VOR dem LLM-Dispatch durchführen, sonst halluziniert der LLM.**

Bestimme für jede dokumentierte Rest-Ambiguität die Auflösungs-Wahrscheinlichkeit anhand von:
- Video-Description-Kontext (z.B. "KFM2 Plan" + "Hostinger" → KVM 2 mit 85%)
- External Knowledge (z.B. "Resent versendet Emails" → Resend-API mit 90%)
- Hör-Frequenz (1× im Transkript = niedrigere Konfidenz als 3×)
- Wort-Kontext (Welche Wörter stehen drum herum?)

**Fix-Schwelle:** ≥80% Sicherheit → deterministisch fixen.
**Unter 80%:** Im Header als "Rest-Ambiguität bleibt" dokumentieren.

```python
import re
from pathlib import Path

filepath = Path("~/docs/youtube/<existing-file>.md")
content = filepath.read_text()

# Beispiel-Fixes (mit hoher Sicherheit):
fixes = [
    (r"\bKFM2\b", "KVM 2"),         # Hostinger-Standardtarif
    (r"\bResent\b", "Resend"),       # E-Mail-API https://resend.com
    # Weitere Fixes je nach Video-Kontext
]

# Patches auf Transkript-Block anwenden (NICHT auf Header!)
start_idx = content.find("## [00:00]")
end_idx = content.find("<!-- RAW_CAPTION_BLOB")
prefix = content[:start_idx]
transcript = content[start_idx:end_idx]
suffix = content[end_idx:]

for old, new in fixes:
    transcript, n = re.subn(old, new, transcript)
    print(f"  {n}x '{old}' -> '{new}'")

# Header-Update: Stufe 3 → Stufe 4
content_new = prefix + transcript + suffix
content_new = content_new.replace(
    "polishing: Stufe 3 (...)",
    "polishing: Stufe 4 (Multi-Agent + LLM-Glättung) — 5 Worker-Bienen, 2 Ambiguitäts-Fixes deterministisch"
)

# Rest-Ambiguitäten-Liste updaten
content_new = content_new.replace(
    "> - `KFM2 Plan` → vermutlich KVM 2 Plan (Hostinger), aber nicht 100% sicher",
    "> - ~~`KFM2 Plan`~~ → **`KVM 2 Plan`** gefixt (Hostinger-Standardtarif, 85% sicher, gefixt 2026-07-09)"
)
# ... gleiche für Resent/Resend, falls vorhanden

filepath.write_text(content_new)
```

### Sub-Phase 4.2 — Worker 5 (LLM-Glättung) dispatchen

**Single-Worker-Subagent** (`role='leaf'`), Output nach `/tmp/yt_llm_worker/output_worker5_llm.md`.

```python
import urllib.parse

# Input-Files vorbereiten
input_dir = Path("/tmp/yt_llm_worker")
input_dir.mkdir(parents=True, exist_ok=True)

# 1) Polierter Transkript (Stufe-3-Output nach 4.1)
content = filepath.read_text()
start_idx = content.find("## [00:00]")
end_idx = content.find("<!-- RAW_CAPTION_BLOB")
transcript = content[start_idx:end_idx].strip()
(input_dir / "input_stufe3_transcript.md").write_text(transcript)

# 2) Original-Auto-Caption für Cross-Check
import re
raw_match = re.search(r"<!-- RAW_CAPTION_BLOB(.*?)-->", content, re.DOTALL)
raw_blob = raw_match.group(1).strip() if raw_match else ""
(input_dir / "input_raw_caption.txt").write_text(raw_blob)

# 3) Context.md (Video-Hintergrund + Eigenname-Liste + Ambiguitäten)
context = """VIDEO-KONTEXT (für Disambiguierung):

Titel: <VIDEO-TITEL>
Channel: <CHANNEL>
Dauer: HH:MM
Sprache: Deutsch (Auto-Caption, Stufe 3 poliert, jetzt Stufe 4 mit LLM)

WICHTIGE EIGENNAMEN (NICHT ändern, korrekt im Stufe-3-Output):
<LISTE ALLER EIGENNAMEN AUS DEM VIDEO>

REST-AMBIGUITÄTEN (NICHT ändern, sind dokumentiert im Header):
<LISTE DER NOCH UNGEKLÄRTEN AMBIGUITÄTEN>
"""
(input_dir / "context.md").write_text(context)

# 4) Output-Schema
schema = """===START_WORKER5_LLM===
<geglätteter Transkript-Text, NUR Inhalt zwischen Minuten-Markern>
===END_WORKER5_LLM===

===STATUS_WORKER5_LLM===
Wörter: NNNN
Absätze: NN
Minuten-Marker: 23/23 (alle erhalten)
Satzzeichen-Korrekturen: N
Wort-Reparaturen: N
Füllwort-Reduktionen: 0 (Stil erhalten)
Wort-Drift: +/-X%
===END_STATUS_WORKER5_LLM===
"""
(input_dir / "output_schema.md").write_text(schema)
```

Dann `delegate_task` mit strikten Constraints — siehe `templates/stufe4_worker5_prompt.md` für den vollständigen Briefing-Text.

### Sub-Phase 4.3 — Polling-Loop (Wall-Clock 30-60s)

```python
import time
worker_file = input_dir / "output_worker5_llm.md"
start = time.time()
timeout = 360  # 6 Min

while time.time() - start < timeout:
    if worker_file.exists():
        elapsed = int(time.time() - start)
        print(f"  [{elapsed:3d}s] Worker 5 geliefert ({worker_file.stat().st_size:,} bytes)")
        break
    time.sleep(10)
else:
    print("TIMEOUT — Worker 5 hat nicht geliefert")
```

### Sub-Phase 4.4 — Integration + Header-Update

```python
output_text = worker_file.read_text()
parts = output_text.split("===START_WORKER5_LLM===")
worker5_transcript = parts[1].split("===END_WORKER5_LLM===")[0].strip()

# In Original-Markdown einbauen
content = filepath.read_text()
start_idx = content.find("## [00:00]")
end_idx = content.find("<!-- RAW_CAPTION_BLOB")
prefix = content[:start_idx]
raw_blob_section = content[end_idx:]

new_content = prefix + worker5_transcript + "\n\n" + raw_blob_section

# Header-Warnhinweis-Block: Worker 5 dokumentieren
old_hinweis = "- **Worker 4 (Merger)**: ... Wort-Drift +1.14%"
new_hinweis = old_hinweis + "\n> - **Worker 5 (LLM-Glättung, Stufe 4)**: Sprachliche Politur — <N> Satzzeichen-Korrekturen, <N> Wort-Reparaturen, 0 Füllwort-Reduktionen, Drift +/-X%"

new_content = new_content.replace(old_hinweis, new_hinweis)

filepath.write_text(new_content)
```

### Sub-Phase 4.5 — Verifikation

```python
import re

content = filepath.read_text()
start_idx = content.find("## [00:00]")
end_idx = content.find("<!-- RAW_CAPTION_BLOB")
transcript = content[start_idx:end_idx]

# 1. Restfehler-Check (sollte immer noch NULL sein)
RESTFEHLER = [r"\bClaudee\b", r"\bTmax\b", r"\bTMAX\b", r"\bT-Max\b", r"\bSL\w+\b", r"\bRustinger\b", ...]
clean = all(len(re.findall(p, transcript)) == 0 for p in RESTFEHLER)
print(f"  Restfehler: {'NULL' if clean else 'KRITISCH'}")

# 2. Eigennamen-Counts (sollten UNVERÄNDERT sein)
for name in ["Claude Code", "tmux", "/loop", "/goal", "/compact", "/clear"]:
    count = transcript.count(name)
    print(f"  {count:3d}x '{name}'")

# 3. Minuten-Marker
marker_re = r'^## \[\d{2}:00\]$'
marker_count = len(re.findall(marker_re, content, re.MULTILINE))
print(f"  Marker: {marker_count}/23")

# 4. Wort-Drift (sollte ±2% sein)
raw_count = 4870  # Original Auto-Caption
current_count = len(transcript.split())
drift = (current_count - raw_count) / raw_count * 100
print(f"  Drift: {drift:+.2f}%")
```

## Gemessene Performance (Session 2026-07-09, pvhphecd70Y)

| Sub-Phase | Dauer | Output |
|-----------|-------|--------|
| 4.1 Ambiguitäts-Fixes | ~1 Min | 2 Patches (KVM 2, Resend) |
| 4.2 Input vorbereiten + Dispatch | ~2 Min | Worker 5 gestartet |
| 4.3 LLM wartet | ~50s | 4901 Wörter Transkript |
| 4.4 Integration | ~1 Min | Header auf Stufe 4 aktualisiert |
| 4.5 Verifikation | ~30s | 0 Restfehler, 23/23 Marker |
| **Gesamt** | **~5 Min** | Stufe-4-File |

## Lessons Learned (Session 2026-07-09)

1. **KÖNIGIN MUSS AMBIGUITÄTEN VOR LLM FIXEN** — sonst halluziniert der LLM
2. **Strikte Constraints funktionieren** — Worker 5 hat "Julians Stil erhalten" + "0 Füllwort-Reduktionen" respektiert (14× natürlich, 6× eigentlich erhalten)
3. **Stufe 4 = Polishing-only** — Single-Worker reicht, kein Merger nötig bei guter Disziplin
4. **Empfehlung** — Stufe 4 nur für zitierfähige Transcripts, NICHT für Quick-Save

## Siehe auch

- `templates/stufe4_worker5_prompt.md` — Vollständiger Worker-5-Briefing-Text
- `templates/stufe3_schwarm_delegation_prompts.md` — Stufe 3 (Multi-Agent) zum Vergleich
- `references/merger-methodology.md` — Stufe-3-Merger-Methodik (verwandte Disziplin)
- `references/known-hearing-errors.md` — Heuristik-Liste für Ambiguitäts-Bewertung