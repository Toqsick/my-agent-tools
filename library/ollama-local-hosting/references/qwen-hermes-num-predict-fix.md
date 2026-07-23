# Qwen-Hermes num_predict Fix & Single-Slot Queue Hangs

Comprehensive fix for the silent `num_predict=128` Ollama default that breaks
thinking models, plus the related single-slot queue hang on `OLLAMA_NUM_PARALLEL=1`.

## Symptom

Lange Antworten brechen ab oder sind komplett leer, obwohl das Modell
"Output produziert" — der sichtbare Response-String ist `""`,
`done_reason='length'`.

## Ursache

Ollama-Default für `num_predict` ist **128**. Wird beim `ollama pull` nicht
aus dem GGUF mitgezogen, und `ollama show` blendet das Feld aus wenn es dem
Default entspricht — der Bug ist unsichtbar.

Bei Thinking-Modellen (qwen3.5-hermes-Familie) frisst der interne `thinking`-Stream
die 128 Tokens sofort auf, sichtbarer Content kommt nie zustande.

## Fix: Modelfile Recreation

Modell mit Modelfile neu erstellen, `num_predict` explizit setzen:

```bash
cat > /tmp/modelfile << 'EOF'
FROM pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2:hermes
PARAMETER num_ctx 24576
PARAMETER num_predict 16384
# ... rest of params
EOF
ollama create pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2:hermes \
  -f /tmp/modelfile
# "using existing layer sha256:..." bestätigt: GGUF-Blob wird wiederverwendet, kein Re-Download
```

## Sizing-Regel für Thinking-Modelle

Mindestens 50-70% des `num_predict` fürs Thinking reservieren. Bei
`num_ctx=24576` und `num_predict=16384` bleibt realistisch
~5-8k sichtbare Tokens.

### Sizing-Tabelle

| num_ctx  | num_predict | Sichtbarer Content (ca.) |
|----------|-------------|--------------------------|
| 4096     | 2048        | 600-1000 Tokens          |
| 8192     | 4096        | 1.2k-2k Tokens           |
| 16384    | 8192        | 2.5k-4k Tokens           |
| 24576    | 16384       | 5k-8k Tokens             |
| 32768    | 16384       | 5k-8k Tokens             |

## Verifikation

End-to-End-Test mit forciertem Thinking-Prompt, dann Response-Parsing prüfen
(`eval_count == num_predict` + `done_reason='length'` = Cap greift).

## Single-Slot Queue Hangs

Mit `OLLAMA_NUM_PARALLEL=1` (Standard für 8GB VRAM) kann eine einzige
lange Generierung den einzigen Slot blockieren — nachfolgende Requests
hängen in der Queue.

**Diagnose:**

```bash
journalctl --user -u ollama | grep "slot print_timing"
# Wenn n_decoded für eine task_id kontinuierlich wächst → dieser Task hat den Slot
```

**Lösungen:**

1. Warten — der laufende Task ist legitim, abbrechen wäre Datenverlust
2. `curl --max-time 300` — Timeout setzen statt blind killen
3. **Niemals** `kill` auf curl ohne vorher `journalctl` zu prüfen — du
   kaperst eventuell einen echten Job

**Prävention:**

- `OLLAMA_NUM_PARALLEL=2` wenn VRAM es hergibt (z.B. 12+ GB)
- Lange Tasks im Hintergrund mit `timeout` oder explizitem `num_predict`-Cap
- Critic-Gate nutzt kleines `num_predict` und kurze Prompts — kein Hang

## Verwandte Themen

- `references/hardware-vram-guide.md` — VRAM vs DDR5, warum CPU-Offload langsam ist
- `references/hermes-config.md` — Context-Length (64000) Setup für Hermes