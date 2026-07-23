# Hyphenated Module Loader Bridge

> Python kann Module mit Bindestrichen im Dateinamen (`daily-note-health.py`)
> nicht direkt via `import` laden. Lösung: eine Loader-Bridge via
> `importlib.util.spec_from_file_location`.

## Das Problem

```bash
# Dateiname mit Bindestrich
daily-note-health.py

# Test/Import versucht underscore
from daily_note_health import classify_daily_note
# → ModuleNotFoundError: No module named 'daily_note_health'
```

Python's Import-System erlaubt keine Module mit `-` im Namen. Der Bindestrich
wird als Subtraktion interpretiert, nicht als Namensbestandteil.

## Die Lösung: Loader Bridge (5 Zeilen)

```python
"""daily_note_health.py — Loader-Bridge for daily-note-health.py"""

import importlib.util
import sys
from pathlib import Path

_BRIDGE_DIR = Path(__file__).resolve().parent
_IMPL_FILE = _BRIDGE_DIR / "daily-note-health.py"

if not _IMPL_FILE.exists():
    raise ImportError(f"Implementierung nicht gefunden: {_IMPL_FILE}")

_spec = importlib.util.spec_from_file_location("daily_note_health", _IMPL_FILE)
_module = importlib.util.module_from_spec(_spec)
sys.modules["daily_note_health"] = _module
_spec.loader.exec_module(_module)

# Re-Export der öffentlichen Symbole
classify_daily_note = _module.classify_daily_note
HealthStatus = _module.HealthStatus
HealthResult = _module.HealthResult
```

## Wann nötig

- Ein Plan spezifiziert einen Bindestrich-Dateinamen (`daily-note-health.py`)
- ABER die Tests importieren via Understore (`from daily_note_health import …`)
- Die Implementierung soll als `if __name__ == "__main__"`-Skript lauffähig bleiben

## Wann vermeidbar

- Wenn der Dateiname geändert werden kann: `daily_note_health.py` (mit Underscore)
  → kein Bridge nötig, direkt importierbar
- Wenn die Tests das Skript via Subprocess aufrufen (exit code prüfen statt importieren)

## Alternative: Subprocess-Call statt Import

Wenn die zu testende Logik nur via CLI/Exit-Code prüfbar ist, kann der Test
das Skript als Subprocess starten statt es zu importieren:

```python
import subprocess, json

def test_health_check_output():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--json"],
        capture_output=True, text=True
    )
    assert result.returncode == 1  # STUB → exit 1
    data = json.loads(result.stdout)
    assert data["status"] == "STUB"
```

Das umgeht das Import-Problem komplett, ist aber langsamer und prüft nur
CLI-Output, nicht interne Funktionen direkt.

## Empfehlung

Loader Bridge für:
- Projekte, wo der Bindestrich-Dateiname bewusst gewählt wurde (Plan-Vorgabe,
  Namenskonvention)
- Wo Unit-Tests interne Funktionen direkt testen sollen (kein Subprocess)

Subprocess-Ansatz für:
- Smoke-Tests / Integration-Tests
- Wenn nur Exit-Code und CLI-Output relevant sind
- Wenn Import-Setup zu komplex wird (sys.path, venv-Brücken)

## Referenz-Session

- 2026-07-16: `daily-note-health.py` → `daily_note_health.py` Bridge
  im Plan 2026-07-16_230642-daily-report-session-trigger.md
- Plan spezifizierte Bindestrich-Dateinamen + Underscore-Import → Bridge
  als notwendige Abweichung vom Plan dokumentiert
