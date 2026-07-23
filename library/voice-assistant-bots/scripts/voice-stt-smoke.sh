#!/usr/bin/env bash
# STT-Smoke-Test v2.1 — faster-whisper large-v3 mit Fallback auf vanilla-whisper base
# Nutzt korrektes Venv (venv/ ohne Punkt), Pre-Load und ENTER-Trigger.
# Ablage: ~/.hermes/scripts/voice-stt-smoke.sh
#
# Modell-Upgrade-Pfad:
#   Vanilla whisper base  → faster-whisper large-v3 (CTranslate2 INT8, cpu)
#   - 10× weniger RAM als vanilla large-v3
#   - 5–10× schnellere Inference (CTranslate2 INT8)
#   - language="de" erzwungen → kein Englisch-Drift bei kurzen deutschen Phrasen
#   - Fallback: vanilla whisper base bei ImportError (z.B. faster-whisper nicht installiert)

set -euo pipefail

WAV="/tmp/hermes-stt-smoke.wav"
TEXT_OUT="/tmp/hermes-stt-smoke.txt"
LOG="/tmp/hermes-stt-smoke.log"

echo "=== STT SMOKE v2.1 $(date -Iseconds) ===" > "$LOG"

echo "════════════════════════════════════════════"
echo "  STT SMOKE TEST — Hermes × lokales Whisper"
echo "════════════════════════════════════════════"
echo ""

# Venv-Detection: venv/ ohne Punkt, Fallback system python3
# !!! WICHTIG: ~/.hermes/hermes-agent/.venv/ EXISTIERT NICHT — es ist venv/ ohne Punkt !!!
HERMES_VENV=~/.hermes/hermes-agent/venv
HERMES_PY="$HERMES_VENV/bin/python"
[ -x "$HERMES_PY" ] || HERMES_PY="$(command -v python3)"

# Falls pip fehlt (PEP 668 / ensurepip nicht gelaufen):
#   $HERMES_PY -m ensurepip --upgrade
#   Das installiert pip 24.x OHNE System-Mutation.

echo "  Venv-Pfad: $HERMES_VENV"
echo "  Python:    $HERMES_PY"
echo ""

# Mikrofon anzeigen
echo "  Verfügbare Input-Quellen:"
pactl list short sources 2>/dev/null | grep input || arecord -l 2>/dev/null | head -n 5
echo ""

echo "  Capture: plughw:1,0 · 16 kHz · mono · S16_LE · 3 Sek"
echo "  >>> Drück ENTER, sobald du bereit bist <<<"
echo "      (direkt nach Enter läuft die Aufnahme)"
echo ""
read -r -p "  ENTER zum Starten…"
echo ""

echo "Stage 1: Audio-Capture (sprich JETZT!)…"
arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 3 -q "$WAV" 2>> "$LOG"
WAV_BYTES=$(stat -c %s "$WAV")
echo "  ✓ WAV: $WAV_BYTES Bytes" | tee -a "$LOG"

if [ "$WAV_BYTES" -lt 1000 ]; then
  echo "  ⚠ WAV sehr klein — Mikrofon gemutet oder keine Sprache?"
fi

echo ""
echo "Stage 1.5: faster-whisper large-v3 Pre-Load"
echo "  (beim ersten Mal ~1,5 GB Download + ~30 Sek Modell-Lade)"
echo "  Backend: CTranslate2 INT8, device=cpu"
$HERMES_PY - <<'PYEOF' 2>> "$LOG"
try:
    from faster_whisper import WhisperModel
    print("  Loading faster_whisper large-v3 (cpu, int8)…", flush=True)
    m = WhisperModel("large-v3", device="cpu", compute_type="int8")
    print("  ✓ large-v3 ready (CTranslate2 INT8)", flush=True)
except Exception as e:
    print(f"  ⚠ Preload fehlgeschlagen: {e}", flush=True)
    print("  → Stage 2 lädt dann inline", flush=True)
PYEOF

echo ""
echo "Stage 2: faster-whisper Transkription"
echo "  (Fallback: vanilla whisper base bei ImportError)"
$HERMES_PY - <<'PYEOF' 2>> "$LOG"
from pathlib import Path

wav = Path("/tmp/hermes-stt-smoke.wav")
seg_lines = []
final_text = ""

# Primär: faster_whisper (CTranslate2 large-v3, int8, Deutsch erzwungen)
# Fallback: vanilla whisper base (falls faster-whisper nicht installiert)
try:
    from faster_whisper import WhisperModel
    backend = "faster_whisper (large-v3)"
    print("  Loading faster_whisper large-v3 (cpu, int8)…", flush=True)
    model = WhisperModel("large-v3", device="cpu", compute_type="int8")
    print("  Transcribing (de, beam_size=5, vad_filter=True)…", flush=True)
    segments, info = model.transcribe(str(wav), language="de",
                                      beam_size=5, vad_filter=True)
    print(f"  ✓ Transkription abgeschlossen ({info.language}, "
          f"Wahrscheinlichkeit {info.language_probability:.2f}):", flush=True)
    for seg in segments:
        line = f"    [{seg.start:.2f}s - {seg.end:.2f}s] {seg.text.strip()}"
        print(line, flush=True)
        seg_lines.append(line)
        final_text += seg.text.strip() + " "
except ImportError as e:
    print(f"  ⚠ faster_whisper ImportError: {e}", flush=True)
    print("  → Fallback: vanilla whisper 'base'", flush=True)
    import whisper
    backend = "vanilla whisper (base)"
    model = whisper.load_model("base")
    result = model.transcribe(str(wav), language="de", fp16=False)
    for seg in result["segments"]:
        line = f"    [{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text'].strip()}"
        print(line, flush=True)
        seg_lines.append(line)
        final_text += seg["text"].strip() + " "

final_text = final_text.strip()
Path("/tmp/hermes-stt-smoke.txt").write_text(final_text + "\n")
print(f"\n  → FINAL ({backend}): '{final_text}'", flush=True)
PYEOF

echo ""
echo "Stage 3: Cleanup…"
rm -f "$WAV"
echo "  ✓ WAV entfernt" | tee -a "$LOG"

echo ""
echo "════════════════════════════════════════════"
echo "  Transkript aus $TEXT_OUT:"
echo "════════════════════════════════════════════"
cat "$TEXT_OUT" 2>/dev/null
echo "════════════════════════════════════════════"
echo ""
echo "Fertig. Log: $LOG"
