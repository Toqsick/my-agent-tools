# Queen-Bee Orchestration: Configuration & Token-Plan Routing

Die Bienenkönigin (parent) orchestriert einen Schwarm aus Subagenten (Scouts/Workers). Das **Delegation-Modell ist unabhängig vom Parent-Modell** — und das ist der Trick.

Loaded from `multi-agent-orchestration` SKILL.md §"Queen-Bee Orchestration".

## Basis-Konfiguration

```bash
# Scouts/Workers laufen auf einem günstigen/gratis Modell
hermes config set delegation.model "openrouter/owl-alpha"    # 0$/token, 1M ctx
hermes config set delegation.provider "openrouter"

# Optional: Max-Parallelität anpassen
hermes config set delegation.max_concurrent_children 5       # default
hermes config set delegation.max_async_children 3
```

## Rollen-Modell

| Rolle | Modell-Typ | Kosten | Aufgabe |
|-------|-----------|--------|---------|
| **Königin** (parent) | Stark (Claude, Qwen Max) | Höher | Strategie, Synthese, Entscheidungen |
| **Scouts** (Subagenten) | Gratis/Frei (Owl Alpha, Nemotron) | 0$ | Exploration, Datensammlung, Messungen |
| **Arbeiter** (Cron/Script) | Shell-Script (no_agent=True) | 0$ | Wiederkehrende Checks |

## Warum getrennt?

- `delegate_task()` ignoriert den `model`-Parameter **stillschweigend** (Pitfall #10/#28 in pitfalls-cheatsheet)
- Die einzige Steuerung ist `delegation.model` in der Config
- Gratis-Modelle (Owl Alpha: 1M Context, 0$/token) sind ideal für parallele Scouts, weil:
  - Hoher Context für komplexe Aufgaben
  - Keine Kostenexplosion bei 5 parallelen Subagenten
  - Rate-Limits (20 req/min, 200/day) reichen für Explorations-Runden
- Bei erschöpften Rate-Limits → Parent übernimmt direkt (Fallback aus Phase 2)

## Empfohlene Free-Modelle für Scouts

| Modell | ID | Context | Besonderheit |
|--------|-----|---------|-------------|
| **Owl Alpha** | `openrouter/owl-alpha` | ~1M | Beste Quality unter Free (Rank #5 OR) |
| **NVIDIA Nemotron 3 Super** | `nvidia/nemotron-3-super-120b-a12b:free` | 1M | Solide Allrounder |
| **Qwen3 Coder** | `qwen/qwen3-coder:free` | 1M | Stärkster Free-Coder |
| **Free Router** | `openrouter/free` | 200K | Auto-Routing falls eins ausfällt |

**Wichtig:** Nach Modell-Wechsel in Session beachten — die Config lebt in `config.yaml`, aber die aktuelle Session liest sie nur beim Start. Für sofortige Wirkung: Session beenden und neu starten. Subagenten in der aktuellen Session verwenden noch das alte Modell bis zum nächsten `/reset`.

## ▶︎ Token-Plan-Aware Multi-Provider Routing (PROVEN 2026-07-02)

**Grundproblem:** Jedes Modell läuft über einen spezifischen Provider → eigenen Token-Plan/Abrechnung.
Wenn alle Worker über `delegation.provider=nous` laufen, werden **alle Token-Pläne falsch abgerechnet**.
Dieser Bug wurde 2026-07-02 live gefunden und gefixt — siehe `hermes-subagent-bridge.md` Pitfall #7.

**Korrekte Architektur:** Jeder Worker-Role bekommt sein eigenes Provider/Model-Paar,
entweder via **Profile** (für async delegation) oder via **MoA-Presets** (für sync routing).

### Async: Profile-basiertes Routing

```yaml
# ~/.hermes/profiles/yuno-coder/config.yaml
_config_version: 33
provider: zai                       # GLM Token-Plan
model:
  default: glm-5
  auxiliary:
    vision:
      provider: minimax             # MiniMax Token-Plan
      model: MiniMax-M3             # MiniMax Token-Plan
    flash:
      provider: nous                # Nous Portal (StepFun Free = $0)
      model: stepfun/step-3.7-flash:free

# Profile-übergreifende skill_lanes Registry (in main config.yaml):
skill_lanes:
  registry:
    worker-heavy: yuno-coder        # → zai/glm-5
    worker-vision: yuno-vision      # → minimax/MiniMax-M3
    worker-flash: yuno-flash        # → nous/stepfun-3.7-flash:free
    gate: yuno-coder                # → zai/glm-5
```

**Token-Plan-Dreieck (Bastis Setup, 2026-07-02, optimiert für 44€ Budget):**

| Profil | Provider | Modell | Abrechnung über |
|--------|----------|--------|-----------------|
| `yuno` (Königin) | **`zai`** | **GLM-5** | **Eigener GLM-Plan** (0€ Nous!) |
| `yuno-coder` (Worker Heavy) | `zai` | GLM-5 | **Eigener GLM-Plan** |
| `yuno-vision` (Worker Vision) | `minimax` | MiniMax-M3 | **Eigener MiniMax-Plan** |
| `yuno-flash` (Worker Flash) | `nous` | StepFun Free | Nous Portal ($0) |

Profil wechseln via `hermes chat --profile NAME` oder via `skill_lanes`-Registry.

### Sync: MoA-Preset-basiertes Routing (Synchronous Multi-Model Voting)

Für **synchronous Voting** (nicht async delegation) nutzt Hermes' MoA-System.
MoA-Presets definieren wer votet (reference_models) und wer synthetisiert (aggregator).

```yaml
# ~/.hermes/config.yaml → moa.presets
coding:                           # 2 Voter → 1 Aggregator
  reference_models:
    - { provider: zai, model: glm-5 }
    - { provider: nous, model: deepseek/deepseek-v4-pro }
  aggregator: { provider: zai, model: glm-5 }

workflow:                         # 3 Voter → 1 Aggregator (alle Token-Pläne!)
  reference_models:
    - { provider: zai, model: glm-5 }
    - { provider: minimax, model: MiniMax-M3 }
    - { provider: nous, model: deepseek/deepseek-v4-flash }
  aggregator: { provider: zai, model: glm-5 }
```

**Usage:**
```bash
/moa coding        # Chat-Befehl: wechselt zu GLM+DeepSeek Dual-MoA
/moa workflow      # Alle 3 Token-Pläne parallel
/moa balanced      # Zurück zum Default (GLM-5 allein, 0 Nous-Kosten)
```

### Wann async (delegate_task) vs. sync (MoA)?

| Kriterium | Async (delegate_task) | Sync (MoA) |
|-----------|----------------------|------------|
| Timing | Background, kein Wait | Blockiert bis Ergebnis da |
| Ergebnis | Subagent-Summary (text) | Komplett synthetisiert |
| Nutzung | Research, Bulk, lange Tasks | Schnelle Antwort mit Multi-Perspective |
| Provider | Profile-gesteuert (`--profile`) | MoA-Preset-gesteuert (`/moa`) |
| Token-Kosten | Parallel, schwerer kontrollierbar | Sequenziell, vorhersagbarer |

### Known Pitfall (2026-07-02)

**`--profile` Flag in Hermes v0.18 ignoriert manchmal die Profile-Config.**
Langfristig: `hermes config set model.default glm-5` + `hermes config set provider zai` im Profile.

### Anti-Pattern (Live gefixt 2026-07-02)

❌ **Modelle über falschen Provider routen** — z.B. `{ provider: nous, model: z-ai/glm-5.2 }`
→ Wird über Nous Portal abgerechnet, nicht über eigenen GLM-Plan.
→ **Korrekter Provider** ist `zai` für GLM, `minimax` für MiniMax, `nous` für DeepSeek.

❌ **Nur ein Provider für alle Worker** — z.B. alle Worker auf `nous` → doppelte Abrechnung
→ Jeder Token-Plan braucht seinen eigenen Provider-String.

✅ **Token-Plan-Check vor Deployment:**
```bash
# Prüfe welcher Provider aktiv ist (je Profil):
grep -E "provider:|model:" ~/.hermes/profiles/*/config.yaml

# Prüfe ob ein Modell über den falschen Provider läuft:
hermes chat -m glm-5 --provider zai -p "Wer bin ich?"
# Output muss "glm-5" zeigen, nicht "deepseek"!
```

## Workflow: Queen-Bee mit Owl Alpha Scouts

```
1. Königin (starkes Modell) analysiert Problem
2. Split in 3-5 unabhängige Aufgaben
3. Scouts spawnen auf openrouter/owl-alpha (gratis, parallel)
4. Jeder Scout liefert Messungen, keine Schätzungen (mit terminal+file tools)
5. Königin sammelt Ergebnisse, dedupliziert, synthetisiert
6. Falls Scouts 429 (Rate-Limit): Königin übernimmt direkt
7. Königin priorisiert und führt P0-Fixes aus
```