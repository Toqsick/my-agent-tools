# Biene-X Code-Trace: Hypothesis Falsification — Worked Example

**Session:** System-Audit 2026-07-16 (Königin + 4 Bienen, 48 Min)
**Biene:** Biene-X (Mnemosyne-LLM-Drift Diagnose)
**Wall-Time:** ~87s (6 tool calls)
**Queen-Hypothese:** "Mnemosyne will API-Provider X, .env hat falschen Key → AAAK-Fallback"

## Ausgangslage

Mnemosyne-Sleep-Runs zeigten seit 2026-07-10 `llm_used: 0`. Memory-Summaries fehlten.
Meine erste Annahme: "Mnemosyne ruft einen API-Provider auf (MiniMax-M3), der Token ist abgelaufen oder falsch."

Hätte ich diese Route genommen: 3-5 Min Queen-Arbeit (.env prüfen, config.yaml prüfen, API-Test mit curl, logs wälzen) — und am Ende immer noch keine Antwort.

## Dispatched Briefing

```
Du bist Biene-X (Code-Trace) in Yunos Diagnose-Schwarm.

KONTEXT:
- Hermes-Mnemosyne-LLM funktioniert nicht → vermutlich API-Provider / Key
- Datei: ~/.hermes/mnemosyne/core/local_llm.py

DEINE TASKS (ALLES READ-ONLY):
1. Lies local_llm.py — wie lädt Mnemosyne den LLM? Welcher Provider?
2. Prüfe die Import-Kette — wird etwas benötigt was fehlt?
3. Prüfe ob GGUF-Modelle vorhanden sind
4. Führe Test-Import aus: python3 -c "from llama_cpp import Llama"
5. FALSIFIZIERE oder BESTÄTIGE die Queen-Hypothese "API-Key fehlt"

MAX 8 tool-calls.
```

## Biene-Output (gekürzt)

```
Queen-Hypothese 'API-Key fehlt' wird FALSIFIZIERT.

Befund:
1. local_llm.py:91 — _load_llm() versucht `from llama_cpp import Llama`
   → ImportError: No module named 'llama_cpp'
   → silent fallback: `except ImportError: return None`
   → KEIN API-Call! Mnemosyne ruft keinen Remote-Provider auf.

2. local_llm.py:48-52 — wenn Host-LLM-Provider aktiv:
   `MNEMOSYNE_HOST_LLM_ENABLED` + `MNEMOSYNE_HOST_LLM_PROVIDER`
   → beide NICHT gesetzt → lokaler GGUF-Pfad aktiv

3. GGUF-Modell vorhanden:
   ~/.hermes/mnemosyne/models/openbmb/MiniCPM5-1B-Q4_K_M.gguf (656 MB)

4. LLM_ENABLED=True in config.env

5. Test-Import: python3 -c "from llama_cpp import Llama"
   → ModuleNotFoundError: No module named 'llama_cpp'

ECHTER FEHLER (P1):
llama-cpp-python und ctransformers sind NICHT im hermes-agent-venv installiert.
Import schlägt still fehl → MNEMOSYNE_LLM_AVAILABLE=False → AAAK-Fallback.

SEIT: mind. 2026-07-10 (erster Log-Eintrag mit llm_used: 0)

FIX: pip install llama-cpp-python

Self-Report: 6 tool-calls, 87s, 3 findings
```

## Was gelernt wurde

1. **Erste Hypothese ist oft falsch.** Statt selbst zu raten: dispatche Code-Trace Bee.
2. **Code-Tracing in <90s** ist schneller als 3-5 Min Queen-Rate-Versuche.
3. **Import-Kette prüfen** ist der effektivste Debug-Schritt für silent-fail-Probleme.
4. **GGUF-Modelle sind lokal** — kein API-Key involviert. Hätte ich vor Dispatch wissen können, aber die Queen hatte die falsche Architektur im Kopf.

## Vergleich: Queen-Direct vs Code-Trace Bee

| Aspekt | Queen ratet selbst | Code-Trace Bee |
|--------|-------------------|----------------|
| Zeit | 3-5 Min (env prüfen, curl, logs) | 87s |
| Hypothese | Bestätigt (falsch) oder ratlos | FALSIFIZIERT mit Ersatz |
| Ergebnis | "Kein Plan" | "pip install fehlt" |
| Lerneffekt | 0 | source-code-Architektur verstanden |
| Wiederholbarkeit | Neu raten | Nächstes Mal sofort dispatch |

## Nutze dieses Referenz-Beispiel

Für jedes "warum funktioniert X nicht?" mit interner Code-Basis:
1. Identifiziere den Code-Pfad (local_llm.py, config_loader.py, ...)
2. Dispatche Code-Trace Bee mit genauem File-Pfad + Zeilen
3. Sag der Biene: "Prüfe Import, nicht API"
4. Die Hypothese wird falsifiziert → echter Fehler gefunden
