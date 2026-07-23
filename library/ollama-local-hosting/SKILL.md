---
name: ollama-local-hosting
description: >-
  Use when user asks for installing or configuring Ollama, running LLMs locally for privacy or offline use, selecting models for available VRAM, integrating Ollama with Hermes, or cleaning orphaned local models. NOT for cloud-hosted inference or non-Ollama GGUF runtime setup. Covers native and service installs, model sizing, GPU performance, Snap migration, context settings, troubleshooting, and disk cleanup.
version: 1.2.0
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - ollama
    - local-models
    - self-hosted
    - privacy
    - free
    - hardware
author: Hermes Agent
license: MIT
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['ollama', 'models', 'and', 'ollama-local-hosting', 'installing']
keywords: ['ollama', 'models', 'user', 'asks', 'installing']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['local-ml-hosting', 'deep-model-evaluation', 'local-ai-security-hygiene']
---


# Ollama Local Hosting

Install and configure Ollama for fully local, zero-cost, zero-token LLM
inference. For deep dives see `references/`.

## When to Use This Skill

- User wants to run LLMs locally (privacy, cost, offline)
- User has a GPU with 4+ GB VRAM and asks about model recommendations
- User wants to integrate Ollama with Hermes as fallback provider
- User hits `model not found`, slow inference, or CUDA/Vulkan confusion
- User asks "snap vs native", `OLLAMA_NUM_PARALLEL`, `num_predict`,
  context-length issues
- User wants to migrate from Snap to native install (with model preservation)
- User wants to clean up / delete specific local models to free disk space
- `ollama list` shows only some models but disk usage is much higher — orphaned blobs
- User has multiple Ollama installs (system + user) with overlapping models
- User asks "wie viele ollama modelle habe ich" / "zu viele modelle" / "alles bis auf X löschen"

## Quick Start

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull deepseek-r1:8b      # 5.2 GB Q4 — best balance for 8GB VRAM
ollama run deepseek-r1:8b        # interactive test
```

For user-space install (no sudo, survives upgrades) see
`references/snap-to-native-migration.md`.

## Model Selection (Quick)

Choose by VRAM. Larger models on CPU/RAM are slow — see
`references/hardware-vram-guide.md` for why.

| VRAM     | Recommended Models                              | Speed         | Quality           |
|----------|-------------------------------------------------|---------------|-------------------|
| 4-6 GB   | `deepseek-r1:7b`, `llama3.1:8b`, `qwen2.5:7b`   | 🚀 80-100 t/s | ⭐⭐⭐ (GPT-3.5) |
| 8 GB     | `qwythos-9b:latest` (⭐ champion), `ornith-9b-q5:latest`, `qwen-dsv4-q5:latest`, `deepseek-r1:8b`, `qwen3.5:9b` | 🚀 9B Q4 ~16-50, 9B Q5 ~10-20 | ⭐⭐⭐⭐ |
| 8 GB     | **⚠️ 12B Q4 auf 8GB** = 2-5 tok/s (Layer-Split, CPU↔GPU-Transfer)| 🐢 2-5 tok/s | ❌ Nicht produktiv |
| 12 GB    | `qwen2.5:32b` (partial)                         | 🐢 15-30 t/s   | ⭐⭐⭐⭐⭐ (GPT-4) |
| 16+ GB   | `llama3.1:70b`, `qwen2.5:32b` full              | 🐢 8-20 t/s    | ⭐⭐⭐⭐⭐         |

**Sizing rule of thumb (Q4 quantization):** 7-8B ≈ 4-5 GB, 14B ≈ 9 GB,
32B ≈ 19 GB, 70B ≈ 30-40 GB.

**R1 vs Qwen — short version:**

- **R1 (`deepseek-r1:8b`):** Reasoning, structured outputs, JSON, critique.
  Always emits a thinking-trace first → needs `max_tokens >= 2000`.
- **Qwen (`qwen3.5:9b`):** Open generation, tool-use, longer texts.
  Faster, no explicit reasoning trace.

Detailed model recommendations, R1-distill variants, max_tokens test data:
`references/model-recommendations.md`.

## Critical Warnings (TL;DR)

- **Context-Length for Hermes:** Hermes needs ≥64000 tokens context. Ollama
  default is 4096 on <24GB VRAM. **Drei Wege:**

  **A) Systemd drop-in (für direkte `ollama run` Nutzung):**
  ```ini
  Environment=OLLAMA_CONTEXT_LENGTH=64000
  ```
  → `systemctl --user daemon-reload && systemctl --user restart ollama`

  **B) Hermes-side Config (kein Restart nötig):**
  ```yaml
  model:
    ollama_num_ctx: 65536
    context_length: 65536
  ```
  Hermes setzt dann `num_ctx=65536` im Request. Vorteil: kein daemon-reload,
  wirkt nur für Hermes (nicht `ollama run`), überlebt Ollama-Updates da
  kein systemd-drop-in das überschrieben werden kann.

  **C) .bashrc export (einfach, persistent, kein daemon-restart):**
  ```bash
  export OLLAMA_CONTEXT_LENGTH=65536
  ```
  → In `~/.bashrc` setzen. Ollama's OpenAI-compatible endpoint
  (`/v1/chat/completions`) respektiert diese Env-Variable.
  **Hinweis:** Wirkt nur bei API-Calls (was der `providers:` Dict tut),
  nicht bei `ollama run`. Vorteil: kein daemon-restart, keine Modelfile-
  Manipulation, überlebt Ollama-Updates.

  **D) Custom-Modelfile-Tag (f�r Performance-kritische Anwendungen):**
  Erstelle einen dedizierten Tag mit vorallokiertem KV-Cache f�r eine
  bestimmte Context-Gr��e — das beschleunigt Prompt-Eval massiv:
  ```bash
  cat <<'EOF' > /tmp/128k.modelfile
  FROM qwythos-9b-q6:latest
  PARAMETER num_ctx 131072
  EOF
  ollama create qwythos-9b-q6:128k -f /tmp/128k.modelfile
  ```
  **Performance-Impact (RTX 5060 8GB, qwythos-9b-q6):**
  | Tag | Context | VRAM | CPU/GPU Split | Eval t/s | Prompt-Eval t/s |
  |---|---|---|---|---|---|
  | `:latest` | 4096 | 7.6 GB | 0/100% GPU | 28 | 35k+ |
  | `:128k` | 131072 | 13 GB | 49/51% GPU | 10 | 750 (vs ~35 of dynamic!) |

  **Trade-off:** Der `:128k`-Tag ist **22× schneller im Prompt-Eval** bei 64k
  Requests als `:latest` mit per-request `num_ctx=65536` (weil kein dynamischer
  KV-Cache-Alloc). Aber: das Modell läuft auf CPU/GPU-Split (49/51%), was
  **alle Requests verlangsamt** — auch kurze mit nur 1k Context. Die Eval-Speed
  sinkt von ~28 t/s auf ~10 t/s.

  **Empfehlung:** Nutze Custom-Tags nur wenn du **überwiegend gro�e Contexts
  (≥16k)** abfragst. F�r gemischte Nutzung (kurze + lange Prompts) ist
  `:latest` mit per-request `num_ctx` die bessere Wahl — kurze Anfragen
  bleiben schnell.
  ```bash
  # Kurz: latest + num_ctx override
  ollama run qwythos-9b-q6:latest --num-ctx 65536 "<prompt>"
  # Lang: dedicated tag
  ollama run qwythos-9b-q6:128k "<long context prompt>"
  ```

  **Verifizierung:**
  ```bash
  echo $OLLAMA_CONTEXT_LENGTH   # Soll 65536 zeigen
  grep OLLAMA_CONTEXT_LENGTH ~/.bashrc
  ```
- **R1 max_tokens:** R1 reasoning consumes tokens before visible content.
  `max_tokens < ~2000` → empty response, `finish_reason='length'`.
- **`num_predict=128` default breaks thinking models:** Ollama's silent default
  eats the entire budget in the internal `thinking` stream. Fix via Modelfile
  recreation — see `references/qwen-hermes-num-predict-fix.md`.
- **`hermes config set custom_providers '[...]'` saves as YAML string** —
  destroys the list structure. Edit `~/.hermes/config.yaml` directly, or use
  PyYAML script. Details: `references/hermes-config.md`.
- **`model.provider: ollama`** → Ollama Cloud (paid). Use
  **`model.provider: custom:ollama-local`** for local.
- **`ollama ps` empty ≠ Ollama stopped.** Service can run with no model loaded.
  Check `systemctl --user status ollama` + `ss -tlnp | grep 11434`.
- **`ollama list` does NOT show every model on disk.** It only shows models the
  active service knows about. Orphaned manifests/blobs (from `ollama rm`,
  aborted pulls, or another install) sit silently. Always check
  `~/.ollama/models/manifests/` directly before cleanup — see
  `references/model-storage-cleanup.md`.
- **`sudo xargs rm` / `sudo | xargs` from a pipe fails silently.** Sudo needs a
  TTY to prompt for a password; in a pipe it just hangs and fails 3× with
  "3 Fehlversuche bei der Passwort-Eingabe". For destructive sudo loops, write
  a bash script with `set -e` and call `sudo bash /path/to/script.sh` — never
  pipe into `sudo`.
- **Config changes need `/new`** to take effect in active sessions.
- **Qwen3.5-basierte GGUF brauchen RENDERER/PARSER qwen3.5 im Modelfile:**
  Modelle die auf Qwen3.5 basieren (Ornith-1.0-9B, Qwythos-9B-Claude-Mythos-5,
  Qwen3.5-9B-DeepSeek-V4-Flash) benötigen diesen Patch im Modelfile:
  ```dockerfile
  FROM hf.co/<ns>/<model>:Q4_K_M
  RENDERER qwen3.5
  PARSER qwen3.5
  ```
  Ohne diesen Patch produziert Ollama leere Responses oder falsche Tokens.
  Bestätigt: Perplexity-Research-Finding 2026-07-16, live auf RTX 5060
  verifiziert mit Ornith (fix: 836→2598c Reasoning) und Qwythos (1M ctx).
  
  **⚠️ Der Fix allein reicht nicht für das Base Model:** Der `RENDERER qwen3.5` Fix
  behebt die leeren Responses, aber das originale `qwen35-9b` (ohne SFT/RL
  Post-Training) leidet unter einem **Reasoning-Loop**: 14K+ chars Reasoning ohne
  jemals zur Antwort zu kommen. Nur SFT/RL-gefinetune Varianten (Qwythos, Ornith,
  DSV4-Flash) bannen den Loop strukturell. **Das Original `qwen35-9b` ist nicht für
  Production geeignet — auch nicht mit RENDERER Fix.** Siehe
  `research/deep-model-evaluation` → `references/qwen35-family-loop-bug.md`.
- **12B Modelle auf 8GB VRAM = 4-7× LANGSAMER als 9B:** Getestet mit Gemma-4-12B
  Familie (yuxinlu1-coder-v1, yuxin-tau2, xentriom-fable5-v2). Ursache: Ein
  12B Q4_K_M (~7.4 GB) belegt fast den gesamten VRAM, sodass Layer-Split nötig
  wird → ständiger CPU↔GPU-Transfer bei jedem Layer-Wechsel. Resultat: 2-5 tok/s
  vs 16-20 tok/s für vergleichbare 9B. **Auf 8GB VRAM sind 12B Modelle nicht
  produktiv nutzbar — auch nicht Q8_0.** Empfehlung: Bleib bei 9B Q4/Q5-Klasse
  (Qwythos, Ornith, DSV4-Flash) für 8GB. Siehe `references/rtx-5060-benchmarks.md`.

## Hermes Integration (Minimal)

`~/.hermes/config.yaml` — `providers:` dict mit expliziten Modellen:

```yaml
providers:
  local-ollama:
    base_url: http://127.0.0.1:11434/v1
    request_timeout_seconds: 300
    discover_models: false          # ❗ Auto-Discovery ausschalten
    default_model: qwythos-9b-q6:latest
    models:
      qwythos-9b-q6:latest: {}
      qwen-dsv4-q5:latest: {}
      yuxin-tau2:latest: {}
    name: Local Ollama (9B Champions)
```

**Felder erklärt:**
- `discover_models: false` — verhindert dass Hermes das `/v1/models`-Listing
  von Ollama über die manuelle `models:`-Liste drüberbügelt. **Ohne dieses Flag**
  kann es zu doppelten oder fehlenden Einträgen im Picker kommen.
- `models:` als **Dict** (keyed by model id) — stabiler als eine Liste.
  Werte sind `{}` (Platzhalter). Dict-Format wird von Hermes' `_declared_model_ids`
  Parser korrekt verarbeitet.
- `default_model` — vorausgewähltes Modell im Picker.
- `name` — Anzeigename im Picker (Desktop wie CLI).

**Ohne `models:` → kein Picker-Eintrag.** Hermes kann das Modell dann nur
explizit via `-m <name> --provider custom:local-ollama` erreichen.

### Desktop vs CLI Picker

**Wichtige Entdeckung (2026-07-16):** Custom `providers:` Einträge werden im
**CLI Model-Picker** (`hermes model`) korrekt angezeigt, aber im **Desktop
Model-Picker-Overlay** fehlen sie. Grund: Ein Hermes-Bug — die Backend-Funktion
`list_picker_providers()` wird vom Desktop-API-Endpoint **ohne**
`user_providers=cfg["providers"]` aufgerufen, während die CLI das Argument
korrekt übergibt.

| Layer | Custom providers sichtbar? |
|---|---|
| `hermes model` (CLI-Curses) | ✅ Ja |
| Desktop Model-Picker-Overlay | ❌ Nein (fehlendes Argument) |
| `hermes chat --provider custom:local-ollama -m <model>` | ✅ Ja (direkter Aufruf) |

**Workaround:** Modell über CLI `hermes model` auswählen oder direkt per
`hermes chat -m <modell> --provider custom:local-ollama` starten.

Diagnose & Fix: `references/hermes-provider-discovery.md`

### Nutzer-Präferenz: Manuelle Selektion, kein Auto-Fallback

Basti (2026-07-16) möchte lokale Modelle **manuell** auswählen — nicht
automatisch als Fallback in `fallback_providers:` eingeschleust bekommen.
Das `providers:`-Dict stellt die Modelle nur zur **Auswahl**; es zwingt
keinen Failover auf.

**Per-session switch (bevorzugte Nutzung):**
```bash
hermes chat --provider custom:local-ollama --model qwythos-9b-q6:latest
```

## Systemd Migration (User → System Install)

When Ollama runs as user-service but should switch to system daemon
(for auto-start on boot, cron access, multiple users):

```bash
# Prüfen
systemctl --user status ollama

# User-mode stoppen
systemctl --user stop ollama
systemctl --user disable ollama

# System-mode aktivieren (Unit liegt seit install.sh in /etc/systemd/system/)
sudo systemctl enable ollama
sudo systemctl start ollama
```

**Gilt nicht, wenn user in `ollama` group:** Dann geht `systemctl enable ollama`
(auch ohne sudo) — der Service läuft als `User=ollama` mit PID in system-space.
`loginctl enable-linger` muss gesetzt sein damit user-Services nach Logout leben.

**🪤 Models-Pfad wechselt bei System-Install:**
- User mode: `~/.ollama/models/` (OLLAMA_MODELS default = `$HOME/.ollama`)
- System mode: `/usr/share/ollama/.ollama/models/`

Bei Migration existierende Modelle entweder neu pullen oder manuell kopieren.
Blobs sind SHA256-content-addressed und zwischen beiden roots portabel —
nur Manifeste unterscheiden sich.

**🪤 OLLAMA_KEEP_ALIVE per drop-in (system mode):**
```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d/
sudo tee /etc/systemd/system/ollama.service.d/keepalive.conf <<'EOF'
[Service]
Environment="OLLAMA_KEEP_ALIVE=15m"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Verify: `systemctl show ollama -p Environment | tr ' ' '\n' | grep KEEP_ALIVE`

## Performance Settings (8GB VRAM)

System-mode drop-in (`/etc/systemd/system/ollama.service.d/performance.conf`)
oder user-mode (`~/.config/systemd/user/ollama.service`):

```ini
Environment="OLLAMA_VULKAN=false"        # CUDA on NVIDIA (faster)
Environment="OLLAMA_FLASH_ATTENTION=true"
Environment="OLLAMA_MAX_LOADED_MODELS=1" # critical for 8GB
Environment="OLLAMA_KEEP_ALIVE=15m"
Environment="OLLAMA_NUM_PARALLEL=1"      # save VRAM
```

**🪤 OLLAMA_IGPU_ENABLE=1: iGPU wird ignoriert by default.** Auf
NVIDIA PRIME/Optimus Laptops (NVIDIA + Intel iGPU) aktiviert Ollama
standardmäßig **nur** die NVIDIA GPU — die Intel iGPU wird komplett
übersprungen, auch wenn sie Vulkan-compute-capable ist. Ollama-Log:
```
dropping integrated GPU; to enable, set OLLAMA_IGPU_ENABLE=true
```
Setze `Environment="OLLAMA_IGPU_ENABLE=1"` um die iGPU als Compute-Backend
zu listen. Allein aktiviert bringt es keinen Speed-Vorteil — die iGPU ist
deutlich langsamer. Nur sinnvoll bei Tensor-Split über beide GPUs
(siehe `deep-model-evaluation` → Dual-GPU Compute Detection).

Verify CUDA picked (nicht Vulkan/iGPU):
```bash
# System-mode:
journalctl -u ollama --since="1 minute ago" --no-pager | grep "library="
# User-mode:
journalctl --user -u ollama --since="1 minute ago" --no-pager | grep "library="
# Expect: library=CUDA compute=12.0 name="NVIDIA GeForce RTX ..."
```

## Selective Model Cleanup (Free Disk Space)

When the user wants to delete specific models but keep others, **always
dry-run first** — manifests reference shared layer blobs, and a naive
`rm -rf ~/.ollama` kills blobs the kept models still need.

**Storage anatomy** — Ollama stores two layers per model:
- `~/.ollama/models/manifests/<ns>/<model>/<tag>` — JSON with `layers[].digest`
- `~/.ollama/models/blobs/sha256-<digest>` — content-addressed file

Same digest = same file (hardlinked or shared). Deleting a model whose
manifest overlaps with a kept model's manifest removes a shared blob too.
Therefore: classify manifests (KEEP vs DEL), then compute KEEP blobs as the
union of all KEEP-manifest layer digests, then DEL = all blobs − KEEP blobs.

**Multi-install trap.** `ollama list` shows only what the *running* service
sees. `~/.ollama/` (user, `OLLAMA_MODELS=$HOME/.ollama` default) and
`/usr/share/ollama/.ollama` (system install) can coexist with overlapping
model names and zero shared blobs. **Always identify both roots** with
`ps -ef | grep ollama` + `systemctl status ollama` before touching anything.

**Procedure (full recipe in `references/model-storage-cleanup.md`):**

1. Identify KEEP set (friendly names: `library/<model>:<tag>` or
   `<ns>/<model>:<tag>` or `hf.co/<ns>/<model>:<tag>`).
2. Walk all manifests, classify into KEEP/DEL.
3. KEEP blobs = union of layer digests from KEEP manifests.
4. DEL blobs = all blob files − KEEP blobs.
5. Show user exact `rm -rf` commands + expected before/after `du -sh`.
6. Wait for explicit OK, then stop service, run cleanup, restart, verify.

**Path-parsing pitfall (recurring bug).** Manifest paths split differently
depending on namespace:
- `registry.ollama.ai/library/<model>/<tag>` → 4 parts after the root
- `registry.ollama.ai/<ns>/<model>/<tag>` → 5 parts after the root
- `hf.co/<ns>/<model>/<tag>` → 4 parts

A naive `parts[2]/parts[3]:parts[4]` parser misses everything in `library/`.
Use explicit branch-by-prefix parsing. Reference implementation lives in
`references/model-storage-cleanup.md#dry-run-script`.

## Troubleshooting (Quick)

- **Slow inference:** Model is swapping to RAM. Use a smaller model that fits
  VRAM. See `references/hardware-vram-guide.md`.
- **"model not found":** Run `ollama pull <model>` first.
- **Ollama not accessible:** `systemctl --user status ollama`,
  `ss -tlnp | grep 11434`.
- **Empty response with R1 model:** `max_tokens >= 2000`. See
  `references/model-recommendations.md#r1-reasoning-models-max_tokens-fallstrick`.
- **Curl hangs with 0% CPU:** Single-slot queue (a previous long gen owns the
  slot). Check `journalctl --user -u ollama | grep "slot print_timing"`. Wait
  it out or `--max-time 300`. **Don't `kill` blindly** — you may cancel a
  real job. See `references/qwen-hermes-num-predict-fix.md#single-slot-queue-hangs`.
- **Model stuck in endless Reasoning-Loop (>5 Min, >0% CPU):** Ein Reasoning-
  Modell (DSV4-Flash, R1, Qwythos) produziert endlos interne Reasoning-Tokens
  und kommt nie zur Antwort. `ollama ps` zeigt den Slot aktiv, `top` zeigt
  >10% CPU auf dem llama-server. **Recovery:** `ollama stop <model>` —
  das entlädt das Modell sauber (killt den Slot, lässt den Service laufen).
  Danach mit `num_predict: 256` oder `--max-tokens 100` erneut testen.
  Siehe auch die Critical Warning zu RENDERER/PARSER qwen3.5 — das Base-Modell
  ohne SFT/RL hat diesen Bug strukturell.
- **Port 11434 already in use:** Often an old Snap or global install.
  `sudo lsof -i :11434`. See `references/snap-to-native-migration.md`.
- **`ollama pull` hängt bei 80-95% (Partial-Blob stoppt Fortschritt):**
  Reproduzierbarer Bug auf Ollama v0.30.x (2026-07-15/16 bestätigt). Tritt bei
  großen Modellen (≥5 GB) auf, besonders wenn mehrere Pulls parallel liefen.
  Der Pull-Prozess lebt, aber der Partial-Blob wächst nicht mehr. Fix:
  ```bash
  # Resume via API — setzt vom Partial-Blob fort, kein Neu-Download
  curl -X POST http://127.0.0.1:11434/api/pull \
    -H "Content-Type: application/json" \
    -d '{"model": "hf.co/ns/model:tag"}'
  # Oder: anderen Quant pullen (Q5_K_M statt Q4_K_M) — umgeht den Bug komplett
  ollama pull hf.co/ns/model:Q5_K_M
  ```
  **🪤 Prävention:** Große Pulls (>4 GB) einzeln ausführen, nicht parallel.
  Resume-Strategie erfolgreich getestet für yuxinlu1 12B Q4_K_M (7.4 GB),
  DSV4-Flash Q4_K_M (5.6 GB). Siehe `references/ollama-pull-hang-workaround.md`.
- **`ollama create` hängt bei 0% CPU >5 Min (Create-Race):** Reproduzierbarer Bug
  auf Ollama v0.30.x (2026-07-15/16 bestätigt). Wenn ein `ollama create` während
  eines laufenden Pulls oder parallel zu einem anderen Create gestartet wird,
  blockiert der Create-Prozess stumm (0% CPU, Partial-Blob unverändert). Fix:
  ```bash
  pkill -f "ollama create"          # Alle Create-Prozesse killen
  ollama list                        # Prüfen ob was fehlt
  sleep 3 && ollama create <name> -f <modelfile>  # Neu starten (einzeln!)
  ```
  **🪤 Prävention:** Nie `ollama create` parallel zu einem laufenden Pull
  starten. Es reicht ein `ollama pull` im Hintergrund + `ollama create` davor.

## Complete Uninstallation

```bash
systemctl --user stop ollama && systemctl --user disable ollama
rm -f ~/.config/systemd/user/ollama.service
rm -rf ~/.ollama ~/.local/bin/ollama ~/.local/lib/ollama
sudo rm -f /usr/local/bin/ollama /etc/systemd/system/ollama.service
sudo snap remove --purge ollama 2>/dev/null
systemctl --user daemon-reload
```

Verify: `which ollama` (empty), `ss -tlnp | grep 11434` (empty),
`systemctl --user status ollama` ("could not be found").

## References

- **`references/model-recommendations.md`** — Detailed model picks, R1 distill
  variants, R1 max_tokens test data, model storage paths, background download
  pattern for models >4GB.
- **`references/hardware-vram-guide.md`** — Why VRAM >> DDR5 for LLMs,
  CPU-offload performance math, quantization trade-offs, MoE models.
- **`references/rtx-5060-benchmarks.md`** — Concrete RTX 5060 Laptop (8GB)
  benchmarks, CUDA vs Vulkan, context-length overhead.
- **`references/hermes-provider-discovery.md`** — Hermes Desktop vs CLI
  Provider-Picker Diskrepanz: Root-Cause (fehlendes `user_providers` Argument),
  Diagnose-Script, Workarounds, Upstream-Fix-Beschreibung.
  Verwende wenn Custom Provider im Desktop-Picker fehlen aber im CLI da sind.
- **`references/hermes-config.md`** — Both config formats, fallback chains,
  Critic-Gate setup, runtime verification, context-length, multi-install
  conflicts.
- **`references/snap-to-native-migration.md`** — Full Snap → native migration
  with model preservation, CUDA-optimized user-systemd service recipe.
- **`references/qwen-hermes-num-predict-fix.md`** — num_predict=128 silent
  default fix, Modelfile recreation recipe, num_predict sizing table, single-
  slot queue hang diagnosis.
- **`references/offline-fallback-strategy.md`** — Strategies for Ollama as
  offline fallback (manual switch, pre-flight script, Hermes fallback chain).
- **`references/model-storage-cleanup.md`** — Storage anatomy, multi-install
  detection, dry-run script that classifies manifests/blobs by KEEP set,
  path-parsing pitfalls, safe `rm` recipe (bash script, not `sudo xargs`).
  Load when user wants to delete specific models or asks "zu viele modelle".
- **`references/ollama-pull-hang-workaround.md`** — Resume-Strategie für
  hängende Ollama-Pulls (80-95% stuck), curl-POST /api/pull Workaround,
  Quant-Wechsel-Alternative, Prävention.

> **Note:** PodTalk/TheCommunity P2P chat integration (WebRTC, local AI
> provider setup) ist nicht Teil dieses Skills — wurde beim Slim-Down
> entfernt, da keine Reference-Datei existierte. Inhalt kann bei Bedarf
> nachgereicht werden, ist aber nicht kritisch für den Hauptworkflow.