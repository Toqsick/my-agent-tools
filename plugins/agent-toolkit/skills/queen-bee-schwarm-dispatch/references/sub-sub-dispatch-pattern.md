# Sub-Sub Dispatch Pattern — Validated 2026-07-14

## Ergebnis der Validierung

**3 Parent-Bienen mit `role='orchestrator'` haben alle erfolgreich 1 Sub-Sub gespawnt.**
sub_call_count=1 in allen 3 Self-Reports. 6/6 Side-Effect-Files existieren.

## Kernerkenntnis

Der **Toolset-Strip in `tools/delegate_tool.py:705`** verwendet ein AND-Gate:
- `role != 'orchestrator'` **AND** `max_spawn_depth < 2`
- Nur wenn BEIDE Bedingungen wahr sind, wird `delegate_task` entfernt
- Heißt: EIN `role='leaf'` genügt, um delegate_task zu killen — max_spawn_depth ist egal
- Heißt auch: `max_spawn_depth=1` mit `role='orchestrator'` KILLT delegate_task NICHT
  (weil Bedingung 2 nicht erfüllt)

## Config-Änderung (einmalig)

```bash
# Backup + Setzen
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%Y%m%d-%H%M%S)
hermes config set delegation.max_spawn_depth 2
hermes config check
grep max_spawn_depth ~/.hermes/config.yaml
```

## Dispatch-Template für 3 Parent + je 1 Sub-Sub

```python
# Parent-Call (im Queen-Kontext):
delegate_task(
    role='orchestrator',           # KRITISCH — NICHT leaf!
    tasks=[
        {
            "goal": "...",
            "context": "...\n\nDu MUSST Sub-Sub X aktiv spawnen unter Y.\n\nSelf-Report MUSS enthalten:\n- sub_call_count\n- ...",
            "role": "orchestrator"  # explizit auf Parent-Ebene
        },
        # ... 2 weitere
    ]
)
```

Jeder Parent bekommt: Haupt-Task (was Parent selbst macht) + explizite Sub-Sub-Anweisung
(was Parent via delegate_task an eine Sub-Biene delegiert).

## Side-Effect-Beweis-Schema

Jeder Parent muss **2 eindeutige Side-Effect-Files** erzeugen:

| File | Wer erzeugt | Existenz beweist |
|------|-------------|------------------|
| `/tmp/gh-test-<name>/<ts>.json` (oder .md) | Parent selbst | Parent hat gearbeitet |
| `/tmp/gh-test-<name>/<ts>-sub.json` (oder .md/.txt) | Sub-Sub | Sub-Sub wurde gespawnt |

Wahl der Pfade:
- Unterschiedlicher `<name>` pro Parent (z.B. alpaca, bumble, cicada)
- Gleiches `<ts>` pro Parent-Sub-Paar (z.B. 1784062446)
- Format-Endung verschieden pro Level: Parent `.json`/`.md`, Sub-Sub `-sub.<ext>`
- Pfade MÜSSEN im Briefing festgelegt sein — sonst erfindet jede Biene eigene

## Verifikations-Befehle (nach Dispatch)

```bash
# Alle 6 Side-Effect-Files checken
for sub in alpaca bumble cicada; do
  echo "--- $sub ---"
  ls -la "/tmp/gh-test-$sub/" | grep -v 'total '
done

# SHA256-Cross-Check (für Hash-basierte Tasks)
while read hash file; do
  fresh=$(sha256sum "$file" 2>/dev/null | awk '{print $1}')
  if [ "$hash" = "$fresh" ]; then echo "✓ MATCH: $file"; else echo "✗ MISMATCH: $file"; fi
done < /tmp/gh-test-cicada/1784062446-sub.txt
```

## Erwartete Self-Report-Felder

```yaml
sub_call_count: 1        # Wie oft delegate_task aufgerufen
main_file: "/tmp/...json"  # Pfad + Größe
sub_file: "/tmp/...sub.md" # Pfad + Größe
verdict: "ja/nein"         # Hat sich Sub-Sub gelohnt?
reasoning: "..."           # Begründung
```

## Parallel-Math

`max_concurrent_children=6` limitiert gleichzeitige Subagents.
- 3 Parent + 3 Sub-Sub = 6 → exakt am Limit (funktioniert, aber kein Puffer)
- 2 Parent + je 1 Sub-Sub = 4 → komfortabel
- Vor Sub-Sub-Dispatch: `process(action='list')` checken ob andere background-Jobs
  laufen (Cron, Server, etc.)

## Faustregel: Lohnt sich Sub-Sub?

| Kriterium | Lohnt sich | Lohnt nicht |
|-----------|-----------|-------------|
| Sub-Task Reasoning | ✅ Klassifikation, Diagnose | ❌ sha256sum, grep, ls |
| API-Calls Sub vs Parent | ✅ Sub > 20 Calls (Bumble: 41) | ❌ Sub < 5 Calls |
| Context-Entlastung | ✅ Sub-Output > 10 KB | ❌ Sub-Output < 1 KB |
| Side-Effekt | ✅ Sub findet Insight (Alias-Mismatch) | ❌ Reine Mechanik |