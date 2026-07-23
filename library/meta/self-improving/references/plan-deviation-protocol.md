# Plan Deviation Documentation Protocol

> Gelernt aus 2026-07-16 TDD-Session: Ein Plan hatte 3 Bugs (falscher
> Test-Pfad, unterschwellige Threshold-Größe, fehlende Loader-Bridge).
> Statt den Plan still zu korrigieren → transparent dokumentiert als
> Abweichungen. Dieses Protokoll codiert, wie und wann.

Das Problem: Du führst einen Plan aus (z.B. aus `.hermes/plans/`), und
der Plan hat Bugs. Falsche Pfade, unterschwellige Schwellwerte, fehlende
Abstraktionen. **Was tust du?**

Die falsche Antwort: "Stur nach Plan" (Tests werden nie grün) oder
"Still korrigieren" (der Plan-Autor kriegt nie Feedback).

Die richtige Antwort: **Transparent dokumentieren.**

## Wann Abweichen

**Deviate direkt (danach dokumentieren) bei:**
- Mechanischen Fehlern: falscher Pfad, falscher Threshold, falsche Konstante
- Offensichtlichem Fix: Plan sagt `tmpdir/file.md`, Code sucht `tmpdir/subdir/file.md`
  → Subdir im Test-Helper anlegen, nicht den Code umbauen
- Testdaten passen nicht zu Production: Testfixture zu klein für Threshold
  → Fixture enlargement manifest (nicht Heimlich)
- Vergessener Abstraktion: Plan spezifiziert Bindestrich-Dateiname + Underscore-Import
  → Loader-Bridge hinzufügen, dokumentieren warum

**Stop and ask bei:**
- Kern-Architektur ist falsch (Ansatz funktioniert garnicht)
- Zwei Tasks im Plan widersprechen sich
- Plan setzt Dependency/Tool/API voraus, das nicht existiert
- Abweichung ändert >30% eines Tasks
- Unsicher ob Abweichung die Plan-Intention ändert

## Dokumentationsformat

Jede Abweichung bekommt im Code (Docstring/Bridge-File) und in der
Session-Summary drei Felder:

```
ABWEICHUNG VOM PLAN: <eine Zeile was der Plan sagte>
- Warum: <warum die Realität einen anderen Weg erforderte>
- Fix: <was stattdessen gemacht wurde>
```

### Beispiel aus der Session

Plan: `_write_daily()` schreibt nach `tmpdir/today.md`.
Reality: `classify_daily_note(tmpdir)` sucht unter `tmpdir/06 Daily Notes/today.md`.

```python
def _write_daily(self, content: str) -> Path:
    """Schreibt eine Test-Daily in das Temp-Verzeichnis.

    ABWEICHUNG VOM PLAN: Der Plan schrieb nach tmpdir/today.md,
    aber classify_daily_note() erwartet tmpdir/06 Daily Notes/today.md.
    - Warum: Test-Helper und Implementierung hatten unterschiedliche
      Vault-Pfad-Annahmen
    - Fix: _write_daily() erstellt jetzt das Subdir und schreibt dorthin
    """
    daily_dir = Path(self.tmpdir) / "06 Daily Notes"
    daily_dir.mkdir(parents=True, exist_ok=True)
    ...
```

### Commit/Summary-Format

Nach Abschluss aller Tasks:

```
1. Was der Plan richtig hatte (Autor weiß was funktioniert)
2. Jede Abweichung mit was/warum/fix
3. Was NICHT getan wurde (Tasks bewusst ausgelassen)
4. Hinweise für den Plan-Autor — was genau gefixt werden sollte
```

## Typische Plan-Bugs (aus der Praxis)

| Bug | Plan sagt | Reality | Fix |
|-----|-----------|---------|-----|
| **Falscher Test-Pfad** | `tmpdir/file.md` | Code sucht `tmpdir/subdir/file.md` | Subdir im Test-Helper |
| **Unterschwelliger Threshold** | 85 Bytes Addendum → PARTIAL erwartet | 825 < 1000 Bytes → STUB | Addendum auf >1000 Bytes vergrößert |
| **Fehlende Loader Bridge** | `daily-note-health.py` + `from daily_note_health import` | Python importiert keine Bindestrich-Module | `importlib.util` Bridge-Datei |
| **Falscher Dateiname** | `daily_note_health`-Import | Datei heißt `daily-note-health.py` | s.o. |
| **Vergessenes Chmod** | Skript ausführbar | 644 Permissions → kein +x | `chmod +x` |
| **Falscher Exit-Code** | `sys.exit(0)` | Exit-Code-Map nicht definiert | `exit_map` in main() |

## Warum nicht still korrigieren?

1. **Der Plan-Autor kriegt nie Feedback** → nächster Plan hat denselben Bug
2. **Der nächste Agent trifft auf dieselbe Falle** → doppelte Arbeit
3. **Die Abweichung im Code ist die beste Doku** — sie lebt mit dem Code,
   nicht in einem separaten "lessons learned"-Dokument
4. **Es baut Vertrauen** — der User sieht dass du denkst, nicht blind folgst

## Verwandt

- `self-improving` — Lessons aus Fehlern, aber Plan-Abweichungen sind keine
  Fehler, sondern bewusste Design-Entscheidungen während der Ausführung.
  Dieses Protokoll ergänzt `self-improving` um den "execution-time quality
  feedback"-Aspekt.
- `python-tooling/references/hyphenated-module-bridge.md` — Die Loader-Bridge
  als konkrete Technik
