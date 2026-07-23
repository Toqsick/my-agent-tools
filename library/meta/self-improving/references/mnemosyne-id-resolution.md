# Mnemosyne ID Resolution — recall → export → resolve

> **Added 2026-07-15** aus ID-Discovery über 3 Self-Improving-Lessons.
> **Problem:** Einem semantischen Lesson-Titel die korrekte Mnemosyne-ID zuordnen.
> **Workflow:** `mnemosyne recall` (Text-Suche) → `mnemosyne export` (Metadata) → `summary_of`-Chain auflösen.

## Workflow

### Phase 1: Keyword-Recall (Text-Matching)

`mnemosyne recall` ist der **schnellste Einstieg**, aber liefert **nur**: ID, Content, Score.
Keine Metadaten (importance, veracity, tier, status, tags).

```bash
# Batch unabhängige Queries parallel (session_start)
mnemosyne recall "keyword1 keyword2" 5
mnemosyne recall "keyword3 OR keyword4" 5
```

**Score-Interpretation:**
| Score | Bedeutung |
|-------|-----------|
| ≥ 0.5 | starkes semantisches Match |
| 0.3–0.5 | mögliches Match, prüfen |
| < 0.3 | Rauschen, ignorieren |

**FTS5-Pitfall:** Lange Phrasen (>4 Wörter) liefern oft 0 Treffer. Auf 2–3 Kernbegriffe reduzieren.

### Phase 2: Metadata-Export (Deep-Inspect)

Wenn Recall-Kandidaten gefunden sind, aber die **Metadata** (importance, tier, veracity, Tags) fehlen:

```bash
mnemosyne export /tmp/mnemosyne-export.json
```

Dann per Python/JSON die Kandidaten inspizieren. Die Export-JSON hat diese Buckets:

| Bucket | Inhalt | Feld-Schema |
|--------|--------|-------------|
| `working_memory` | Stabile, dauerhafte Einträge | `id, content, importance, veracity, source, metadata_json, recall_count, superseded_by, ...` |
| `episodic_memory` | Konsolidierte Zusammenfassungen | `id, content, importance, summary_of, source, metadata_json, recall_count, ...` |
| `legacy_memories` | Alte/ersetzte Einträge | Ähnlich working |
| `scratchpad` | Temporäre Notizen | Variables Schema |

**Wichtige Schema-Unterschiede:**

| Feature | working_memory | episodic_memory |
|---------|---------------|-----------------|
| `veracity` | Vorhanden (`verified`, `stated`, `unknown`, `inferred`) | **Nicht vorhanden** (None) |
| `metadata_json` | Reichhaltig: `tier`, `tags`, `category`, `status` | Schlicht: `original_count`, `source`, `llm_used` |
| `summary_of` | Nicht vorhanden | **Vorhanden** — komma-separierte IDs der Originals |
| `importance` | Eigene Bewertung | Geerbt/konsolidiert (meist ≤ 0.7) |
| `superseded_by` | Vorhanden | Nicht vorhanden |

### Phase 3: Episodic → Working resolution (summary_of-Chain)

**Episodic memories** sind `sleep_consolidation`-Zusammenfassungen. Sie sind **nicht** die Quelle der Wahrheit – das sind die Working-Tier-Originals, auf die `summary_of` zeigt.

```python
# Nach mnemosyne export:
episodic_entry = {"id": "e1ab871de07e6527", "summary_of": "8756923629f9f8eb", ...}
# summary_of kann auch mehrere IDs enthalten:
episodic_entry = {"id": "f0577226b849aed2", "summary_of": "797bdf34985cd42d,63d4c331169e97f4", ...}
```

**Resolution-Regeln:**
1. Der Episodic-Eintrag ist **read-only** – nie als canonical ID verwenden
2. Die `summary_of`-IDs sind die **wirklichen** Working-Tier-Originals
3. Ein Episodic kann mehrere Originals konsolidieren → alle prüfen
4. Die Originals haben eigene `importance` und `veracity` – die Episodic-Werte sind nur Annäherungen

### Phase 4: Confidence Assessment

Aus den Metadata-Feldern der **Working-Tier-Originals** die Confidence ableiten:

| Kriterium | High | Medium | Low |
|-----------|------|--------|-----|
| `importance` | ≥ 0.85 | 0.70–0.84 | < 0.70 |
| `veracity` | `verified` | `stated` / `inferred` | `unknown` |
| `metadata_json.status` | `verified` | `hypothese` | fehlt |
| `recall_count` | ≥ 3 | 2 | 1 |
| `source` | `user` / `self-improving` | `inferred` | `sleep_consolidation` |

**Harte Grenze:** Wenn `importance` < 0.85 oder `veracity == unknown`, ist die Confidence **maximal medium** – auch wenn der Content perfekt matcht.

### Phase 5: Output

```markdown
| Lesson | Mnemosyne-ID | Importance | Tier | Veracity | Confidence |
|--------|-------------|------------|------|----------|------------|
| ... | `xxxxxxxxxxxxxxxx` | 0.85 | working | verified | **high** |
```

**Cross-Reference:** Wenn die ID in einer `references/`-Datei erwähnt wird (z.B. `references/subagent-self-test-deception.md`), die ID dort aktiv auf den Working-Tier-Original aktualisieren, nicht auf den Episodic-Summary.

## Typische Fallstricke

| Falle | Symptom | Fix |
|-------|---------|-----|
| Episodic-ID als canonical verwenden | Falsche Importance/Veracity | `summary_of` auflösen → Working-Original |
| Recall auf Export-Daten | `mnemosyne recall` sucht nur im Content | Export für Metadata, Recall für Text |
| `summary_of` übersehen | Glaubt, Episodic sei die Lesson | Jeden Episodic-Eintrag auf `summary_of` prüfen |
| `metadata_json` nicht parsen | JSON-String im Feld übersehen | `json.loads()` aufrufen |
| Confidence aus Episodic-Daten | Zu niedrige/hohe Einschätzung | Nur Working-Tier-Metadata zählt |

## Python-Cheatsheet für Export-Abfragen

```python
import json
with open('/tmp/mnemosyne-export.json') as f:
    data = json.load(f)

working = data['working_memory']
episodic = data['episodic_memory']

# Index aufbauen
idx = {item['id']: item for item in working}

# summary_of-Chain auflösen
for e in episodic:
    summary_of = e.get('summary_of', '')
    if summary_of:
        originals = summary_of.split(',')
        for oid in originals:
            orig = idx.get(oid)
            if orig:
                print(f'{e["id"]} → {oid} (importance={orig["importance"]})')

# Metadata parsen
for item in working:
    meta_raw = item.get('metadata_json')
    meta = json.loads(meta_raw) if isinstance(meta_raw, str) else (meta_raw or {})
    print(f'{item["id"]}: tier={meta.get("tier")}, status={meta.get("status")}, tags={meta.get("tags")}')
```

## Siehe auch

- `self-improving` SKILL.md → "Dedupe — Vor dem Schreiben suchen" (Mnemosyne-Recall vor dem Speichern)
- `references/cross-session-consolidation.md` → FTS5-Query-Pitfalls, Session-Discovery
- `references/health-check-testing-methodology.md` → Mnemosyne-Cron-Health-Check