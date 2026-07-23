# Model Recommendations (Detailed)

Long-form model recommendations, benchmarks, and DeepSeek R1 Distill
variant comparisons.

## Quick Selection by VRAM

| VRAM     | Recommended Models                                    | Speed          | Quality           |
|----------|-------------------------------------------------------|----------------|-------------------|
| 4-6 GB   | `deepseek-r1:7b`, `llama3.1:8b`, `qwen2.5:7b`         | 🚀 ~80-100+ t/s | ⭐⭐⭐ (GPT-3.5)  |
| 8 GB     | `deepseek-r1:8b`, `qwen3.5:9b`, `qwen2.5:14b`        | 🚀 8B ~30-50, 14B ~4-7 | ⭐⭐⭐⭐ |
| 12 GB    | `qwen2.5:32b` (partial), `llama3.1:70b` (heavy swap)  | 🐢 ~15-30 t/s    | ⭐⭐⭐⭐⭐ (GPT-4) |
| 16+ GB   | `llama3.1:70b`, `qwen2.5:32b` full                    | 🐢 ~8-20 t/s     | ⭐⭐⭐⭐⭐         |

## DeepSeek R1 Distill Variants

Diese sind destilliert von DeepSeek R1 (685B) auf kleinere Base-Modelle.
Verfügbar via Ollama:

- **`deepseek-r1:7b`** (Qwen-7B base, 4.7 GB Q4) — passt komplett in 6GB+ VRAM
- **`deepseek-r1:8b`** (Llama-8B base, 5.2 GB Q4) — passt komplett in 8GB VRAM,
  leicht besser als 7B
- **`deepseek-r1:14b`** (Qwen-14B base, 9.0 GB Q4) — braucht CPU-Offload auf
  8GB-Karten (~4-7 tok/s), merklich besseres Reasoning als 8B
- **`deepseek-r1:32b`** (Qwen-32B base) — nur für 24+ GB VRAM
- **`deepseek-r1:70b`** (Llama-70B base) — nur für Multi-GPU-Setups

## R1 vs Qwen — Wann welches Modell?

| Anwendungsfall                        | Empfehlung                  |
|---------------------------------------|-----------------------------|
| Strukturierte Outputs (PASS/FAIL, JSON) | `deepseek-r1:8b`           |
| Critique-Tasks (Critic-Gate)          | `deepseek-r1:8b`           |
| Reasoning-intensive Prompts           | `deepseek-r1:8b` (oder 14b wenn VRAM) |
| Offene Generierung, längere Texte     | `qwen3.5:9b`                |
| Tool-Use, Function-Calling            | `qwen3.5:9b`                |
| Multilingual (Deutsch, Europäisch)    | `qwen2.5:7b` / `qwen3.5:9b` |
| Code-Generation                       | `qwen2.5-coder:7b`         |

## R1 Reasoning Models: max_tokens Fallstrick

**Symptom:** `hermes chat --provider custom:ollama-local --model deepseek-r1:8b`
antwortet mit leerem Content und `finish_reason='length'`, obwohl Ollama
erreichbar ist.

**Ursache:** R1-Modelle (deepseek-r1, qwen-r1 etc.) produzieren **immer
zuerst einen Reasoning-Trace**, bevor der eigentliche Content kommt. Bei
`max_tokens < ~1000` wird das gesamte Token-Budget vom Reasoning
verschlungen, der Content bleibt leer.

**Messung (RTX 5060 8GB, 2026-06-08):**

- Prompt: "Antworte in EXAKT einem Wort: Hallo oder Hi"
- `max_tokens=2000` → Antwort "Hi", 354 Completion-Tokens (davon ~330 Reasoning),
  20.2s, 17.5 TPS, `finish_reason='stop'` ✓
- `max_tokens=30` → `content=''`, 30 Tokens nur Reasoning, `finish_reason='length'` ✗
- `max_tokens=50` → `content=''`, 50 Tokens nur Reasoning, `finish_reason='length'` ✗

**Fix:** `max_tokens >= 1000` für R1-Calls. Konkret:

- Bei direktem Ollama-API-Call: `max_tokens=2000` als sichere Untergrenze
- Hermes-Profile: siehe `hermes-local-9b-setup.md` (`max_tokens: 4096` für
  Thinking-Modelle)
- Critic-Gate Script: setzt `max_tokens` nicht explizit, vertraut auf
  Ollama-Default (meist ausreichend, da Output klein)

## Ollama Model Commands

```bash
ollama list                          # installierte Modelle
ollama pull <model>                  # Download (siehe Background-Pattern unten)
ollama rm <model>                    # Modell entfernen
ollama show <model>                  # Modelfile + Parameter anzeigen
ollama ps                            # aktuell geladene Modelle (≠ laufender Service!)
ollama cp <src> <dst>                # Modell kopieren (z.B. mit anderem num_ctx)
```

## Background Download Pattern (Large Models >4 GB)

Foreground downloads können timeouten (max 600s). Nutze background mode mit
notification:

```bash
terminal(command="ollama pull deepseek-r1:14b", background=True, notify_on_complete=True, timeout=900)
```

Download läuft im Hintergrund; Notification bei Fertigstellung. Progress
jederzeit mit `process(action='poll', session_id='...')`.

**Resuming interrupted downloads:** Wenn ein Download mittendrin abbricht
(z.B. 74% von 9 GB), bleiben die Partial-Daten erhalten. Ein erneuter
`ollama pull <model>` resumed von der letzten Position — verifiziert den
cached Blob und lädt nur die restlichen Bytes. Kein Neustart nötig.

**Space requirements:** Genug freien Speicher vorher prüfen. Ollama speichert
unter `/var/snap/ollama/common/models/blobs/` (Snap) oder `~/.ollama/models/blobs/`
(manual). Check `df -h /` zuerst.

## Model Storage Locations

| Installation | Model Path                              | Check                    |
|--------------|------------------------------------------|--------------------------|
| Snap         | `/var/snap/ollama/common/models/blobs/`  | `snap list ollama`       |
| Manual       | `/usr/share/ollama/.ollama/models/blobs/` | `which ollama`          |
| User         | `~/.ollama/models/blobs/`                 | `ls ~/.ollama/`          |

Models können zwischen Locations symlinked werden. Größe checken mit
`du -sh <path>`.