# Pattern 1: Read→Patch-Retry bei Sibling-Konflikten

## Symptom
Das `patch`-Tool gibt eine `_warning` im Ergebnis-Objekt zurück — genau dieses Format:

```json
{
  "_warning": "... was modified by sibling subagent 'sa-0-7f1728e2' at 18:33:47 — after this agent's last read at 18:30:39. Re-read the file before writing."
}
```

Tritt auf bei parallelen Subagents, die dieselbe Datei anfassen, obwohl disjunktes File-Scope vereinbart wurde — oder wenn zwei Cluster-Wellen überlappen.

## Lösung

```python
if result.get("_warning") and "sibling" in result["_warning"]:
    fresh_content = read_file(path)        # frischen Stand holen
    # Prüfen ob old_string noch im frischen Content existiert
    if old_string not in fresh_content:
        # WARNING: Sibling hat old_string bereits entfernt → Patch ungueltig
        # → neuen Stand analysieren, ggf. alternative old_string finden
        # oder den Patch komplett neu aufsetzen
    else:
        patch(path, old_string, new_string)  # 1× retry
    # bei 2× Fehlschlag: read erneut, dann ein letztes Mal retry
    # bei 3× Fehlschlag: im Final-Report als "Sibling-Konflikt nicht loesbar" dokumentieren
```

## Wichtige Nuance
Der `_warning` sagt dir NICHT, ob der Patch fehlschlug — er sagt nur "dein read ist stale". Du MUSST re-read + re-patch. Einfach den selben Patch nochmal zu schicken (ohne re-read) funktioniert nicht, weil `patch` die Datei nach dem letzten bekannten Read-Stand vergleicht.

## Nicht verwechseln mit
`success: false` im `patch`-Resultat. Das ist ein echter Patch-Fehler (old_string nicht gefunden o. ä.) — andere Behandlung.

## Verifikation
Patch muss `success: true` liefern ODER der Inhalt muss nach erfolgreichem re-read + patch dem gewünschten Ergebnis entsprechen. Vor Final-Report das ganze File kurz nochmal lesen per `read_file`.