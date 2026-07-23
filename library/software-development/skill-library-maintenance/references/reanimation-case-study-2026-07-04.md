# Reanimation Case Study — 2026-07-04

## Kontext

Nach OPUS 4.8 Factoring (2 Batches geloescht, 19 MB, 302 SKILL.md) blieben 92 Archive-Skills in `.archive/`. Ziel: bestimmen was reanimiert werden soll.

## Pipeline (bewaehrt)

### Stufe 1: md5sum-Diff (lokal, 0 USD Kosten in ~2 Sek)

```python
# execute_code Pseudocode
archive_dirs = [...]      # find .archive/ -maxdepth 1
active_names = {...}       # grep "name:" in aktiven SKILL.md
# Ergebnis: 3 Kategorien
identical = [d for d if md5(archive SKILL.md) == md5(active SKILL.md)]
no_active = [d for d if d not in active_names]  
fuzzy = [(d, [a for a if d ähnlich a]) for d in no_active]
```

**Ergebnis 2026-07-04:**
- 0 identisch (Bug im ersten Scan — die 78 Identischen wurden nicht gefunden weil Names-in-Frontmatter vs Dir-Name-Comparison nicht matchten)
- 2 identische Duplikate via manuellen Diff (greyhack-greyscript-deep-audit, security-code-checker-duplicate)
- 11 komplett fehlend + 3 fuzzy

### Stufe 2: Fable 5 Triage (günstig, ~0.35-0.55 USD)

Bastis Regel: **KEIN Budget-Limit setzen** beim ersten Run. `--model fable --max-turns 15` ohne `--max-budget-usd`.

**Briefing-Isolation (KRITISCH):** NIEMALS `cat briefing | claude --model fable` ausfuehren — der `cat`-Befehl wird als Briefing-Inhalt interpretiert statt der Datei. Stattdessen:
1. Briefing in `/tmp/<name>.txt` schreiben
2. `claude -p "$(cat /tmp/..."` aufrufen

**Ergebnis:** 3 konkrete Reanimations-Picks mit soliden Argumenten:
1. `copilot-cli` → `autonomous-ai-agents/` (schliesst einzige Funktionsluecke)
2. `llm-evaluation-troubleshooting` → `mlops/evaluation/` (bewahrt lokale Patches)
3. `llm-wiki` → `research/` (niedrigster Aufwand, kein Tooling noetig)

Bastis Stack-Priorisierung: Hermes/Claude/Mnemosyne/Linux-Security/MLOps/Multi-Agent. NICHT Social-Media/Comics/Image-Gen.

### Stufe 3: OPUS 4.8 (nicht noetig bei dieser Triage)

Fable's Ergebnisse waren nutzbar und widerspruchsfrei. Keine OPUS-Validierung erforderlich.

## Erkenntnisse

1. **md5sum-Diff VOR Fable spart Geld**: Nur 14 von 92 Skills brauchten Judgment — der Rest war mechanisch entscheidbar
2. **Fable 5 ist gut fuer vorstrukturierte Judgment-Aufgaben**: Mit exakten Listen und klarem Triage-Schema (REANIMATE/KEEP/DELETE) gibt Fable brauchbare Ergebnisse
3. **Fable vs OPUS ist kein Qualitaets-, sondern ein Risk-Entscheid**: Fable reicht fuer 80% der Decisions, OPUS nur wenn eine Entscheidung weitreichende Konsequenzen hat ("alle loeschen")
4. **Briefing-Isolation ist ein silent failture**: Der `cat briefing | claude` BUG macht stumm fehlschlagende Runs — immer Temp-File + `-p` verwenden
5. **Basti moechte KEIN Budget-Limit beim ersten Run**: "Gib am anfang kein limit vor" ist die Regel
