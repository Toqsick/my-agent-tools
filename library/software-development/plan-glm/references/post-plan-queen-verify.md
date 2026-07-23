# Post-Plan Queen-Verify Checklist

> Proven 2026-07-16 auf Daily-Report-Session-Trigger Implementation.
> Fall-Study (vollständig): `~/.hermes/docus/reports/2026-07-16-subagent-self-test-deception-fallstudy.md`

## Das Problem

GLM 5.2 schreibt einen Plan basierend auf:
1. Dem Task-Brief (der deine Annahmen enthält)
2. Codebase-Exploration (die unvollständig oder fehlerhaft sein kann)

Der Plan kann **technisch korrekt** sein (gute Struktur, richtige Tasks, vollständige Dependencies) — aber **faktisch falsche Annahmen** über den aktuellen Systemzustand enthalten.

Nachgewiesen 2026-07-16:
- Plan nahm an `2026-07-15.md` sei HEALTHY (war PARTIAL — leere Sektionen)
- Plan nahm an `2026-07-03.md` sei MISSING (existierte mit 4946 B und parenthetischem Section-Header)
- Subagent Welle 1 baute auf diesen Annahmen auf → 5 von 18 Files misklassifiziert

## Checkliste (vor Execution)

Vor dem ersten Subagent-Dispatch MÜSSEN alle Plan-Annahmen geprüft werden:

### Phase 1: Datei-Existenz

```bash
# Plan behauptet Datei X existiert/liegt unter Pfad Y?
ls -la <path-from-plan> 2>/dev/null || echo "MISSING"
```

| Plan-Annahme | Realität | Match? |
|---|---|---|
| Datei X existiert unter Pfad Y | `ls -la <path>` → exists/size | ✅/❌ |
| Datei A hat Inhaltstyp B | `head -5`, `grep "^## "` → pattern | ✅/❌ |

### Phase 2: Strukturelle Passung

```bash
# Plan behauptet Datei hat bestimmte Sections/Patterns?
grep -hE "^## " <target-dir>/*.md | sort | uniq -c | sort -rn | head -20
```

| Plan-Annahme | Realität | Match? |
|---|---|---|
| Section-Header Template passt auf alle Files | Variation-Space ≤3 | ✅/❌ |
| Section-Headername X kommt in File Y vor | `grep -c "^## X"` | ✅/❌ |

### Phase 3: Daten-Health

```bash
# Wenn der Plan Health-Werte annimmt (HEALTHY/PARTIAL/STUB)
# Laufe die Detection auf ALLEN Files
for f in $(find <target> -name "*.md" | sort); do
    python3 /path/to/script.py --date "$(basename $f .md)" --json
done
```

| Plan-Annahme | Realität | Match? |
|---|---|---|
| File ist HEALTHY (echter Inhalt) | Tatsächliche Klassifikation | ✅/❌ |
| File ist MISSING | `ls -la <file>` → exists? | ✅/❌ |

### Phase 4: Risikobewertung

Wenn Abweichungen gefunden wurden:

| Befund | Aktion |
|---|---|
| 1-2 kleine Abweichungen (anderer Section-Name, andere File-Größe) | In Subagent-Brief als Edge-Case dokumentieren; Plan-Execution fortsetzen |
| 3+ Abweichungen oder 1 strukturelle Fehlannahme | Execution STOP. Plan patchen. GLM 5.2 muss neu planen lassen. |
| Template-Variationen >3 | Multi-Marker-Strategie statt Exact-Match → in Subagent-Brief explizit vermerken |

## Die 3-Fragen-Regel

Bevor du einen Subagent auf Basis des Plans dispatchst, beantworte:

1. **Datei-Realität:** Stimmen die Dateipfade und Existenz-Annahmen? *(ls -la check)*
2. **Struktur-Realität:** Stimmen die Section-Header und Pattern-Annahmen? *(grep ^## inventory)*
3. **Health-Realität:** Stimmen die Status-Klassifikationen (HEALTHY/PARTIAL/MISSING)? *(dry-run auf allen Files)*

Erst wenn alle 3 Fragen ✅ sind → dispatch.

## Subagent-Briefing-Addendum (Plan-Annahmen-Risiken)

Wenn du einen Subagent dispatchst, der auf Plan-Annahmen aufbaut, füge in den Brief ein:

```
WARNUNG: Plan-Annahmen sind NICHT alle verifiziert.
Risikofile (Annahme unbekannt/unsicher):
- <file1>: Annahme war <X>, Realität ungeprüft
- <file2>: Annahme war <Y>, Realität ungeprüft

Implementiere defensive: Multi-Marker statt Exact-Match,
fallback-Logik für unerwartete Section-Varianten.
```

## Cross-References

- `plan-glm` SKILL.md: Pitfall "Plan assumptions about real system state — verify with live commands"
- `subagent-driven-development` SKILL.md: Step 5 Real-World Cross-Check + references/heuristic-subagent-real-world-cross-check.md
- `self-improving` SKILL.md: Pitfall #38 (exact string match), #39 (subagent self-report false-green)
- `~/.hermes/docus/reports/2026-07-16-subagent-self-test-deception-fallstudy.md` — vollständige Fall-Study (54 KB)
