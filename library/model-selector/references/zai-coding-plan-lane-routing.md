# z.ai Coding-Plan Lane Routing (2026-07-16)

**Gilt für:** Modell-Allokation auf Hermes Skill-Lanes unter z.ai Coding-Plan (Lite/Pro/Max).

---

## 1. z.ai GLM Modell-Familie

| Modell | Input $/M | Output $/M | Cached Input | Context | Release |
|---|---|---|---|---|---|
| **GLM-5** (Original) | $1.00 | $3.20 | $0.20 | 128K | 2025 |
| **GLM-5.1** | $1.40 | $4.40 | $0.26 | 128K | ~2026 H1 |
| **GLM-5.2** | $1.40 | $4.40 | $0.26 | **1M** | 2026-06-16 |
| GLM-5-Turbo | $1.20 | $4.00 | $0.24 | — | — |

**Pro 1M Tokens: GLM-5.2 = +40% teurer als GLM-5, dafür 10× Context.**

### Performance (Terminal-Bench 2.1)
- GLM-5.1: 63.5 → **GLM-5.2: 81.0** (+27 Punkte)
- Vergleich: Opus 4.8: 85.0

### Neu in GLM-5.2
- **IndexShare**: 2.9× weniger per-token FLOPs bei 1M Context (arXiv 2603.12201)
- **Effort-Level**: low/med/high/**max** — Capability↔Latency trade-off
- **FrontierSWE**: nur 1% hinter Opus 4.8, bestes open-source Long-Horizon Modell

---

## 2. Coding-Plan Tiers

| Tier | Preis/Mo | Volumen | Priority Access | Ideal für |
|---|---|---|---|---|
| **Lite** | $18 | Base | ❌ Kein Priority | "lightweight iteration on small repo" |
| **Pro** | $72 | 5× Lite | ✅ Priority Access, MCP inklusive | "day-to-day development, mid-sized repo" |
| **Max** | $160 | 20× Lite | ✅ Dedicated Resources | "advanced users, mid-to-large repo" |

Alle Tiers inkludieren: Vision Analysis, Web Search, Web Reader, Zread MCP, Claude Code.

---

## 3. Skill-Lane Allokation (Lite-Plan)

**Faustregel:** Jede Lane × Häufigkeit × Kosten = Impact auf dein Volumen.

| Lane | Frequenz | Modell | Effort | Grund |
|---|---|---|---|---|
| **koenigin** ⭐ | Selten (Plan-Phase, Decompose) | **GLM-5.2** | max | Bestes Modell für Planung — läuft wenig, also Volumen-schonend |
| **gate** | Mittel (Quality Gate) | **GLM-5** | xhigh | Qualität wichtig, aber häufiger → 5.2 würde Volumen fressen |
| **worker-heavy** | Häufig (Coding, Refactoring) | **GLM-5** | xhigh | Fleißarbeit, keine 1M Context nötig |
| **worker-light** | Sehr häufig (Scout, Suchen) | **MiniMax M2.7/M3** | — | Kostenlos / Flatrate, unbegrenzt |
| **coding (MoA)** | Häufig | **MiniMax M3** | — | Mixture-of-Agents, braucht Token-Volumen |

### Lite-Plan Risiken bei GLM-5.2
- ❌ Kein Priority Access → **HTTP 429** in Peak-Zeiten sobald Volumen-Grenze erreicht
- ❌ Output-Tokens durch Effort=max: **+50-120%** vs GLM-5 gleichem Task
- ❌ 1M Context wird selten gebraucht — bei kurzen Prompts zahlt man 5.2-Preis für 5-Performance
- ✅ Kein Risiko wenn Lane selten läuft (wie koenigin)

---

## 4. CLI-Befehle (gesperrte Config)

**`~/.hermes/config.yaml` ist agent-protected — direktes patchen wird geblockt!**

```bash
# ✅ Richtig: via hermes config CLI
hermes config set skill_lanes.koenigin.model glm-5.2

# ❌ Falsch: direktes editieren / patchen der yaml
# → "Refusing to write to Hermes config file"
```

Weitere Konfigurationen:

```bash
# Modell abfragen
hermes config get skill_lanes.koenigin.model

# Reasoning-Effort setzen
hermes config set skill_lanes.koenigin.reasoning_effort max

# Subagent-Dispatch Modell (kostensparend)
hermes config set delegation.model "deepseek/deepseek-v4-flash"
hermes config set delegation.provider "nous"
```

---

## 5. Bastis Ist-Stand (2026-07-16)

```
Coding-Plan:                      Lite ($18/mo)
claude-zai Opus-Modell:           glm-5.2[1m]
claude-zai Sonnet-Modell:         glm-5
claude-zai Haiku-Modell:          glm-4.7-flash
claude-zai effortLevel:           max

Hermes skill_lanes koenigin:      glm-5.2  ← NEU (war glm-5)
Hermes skill_lanes gate:          glm-5
Hermes skill_lanes worker-heavy:  glm-5
```

---

## 6. Empfehlungen nach Plan-Tier

### Lite ($18/mo) — aktuell
- Nur koenigin auf GLM-5.2 (seltene, wichtige Calls)
- Rest auf GLM-5 oder MiniMax M3
- Bei 429-Frust: claude-zai Opus auf glm-5 zurückdrehen

### Pro ($72/mo) — wenn budget mitspielt
- koenigin + gate auf GLM-5.2
- Effort=max für Plan-Phase, xhigh für Gate
- 5× Volumen → selten Rate-Limits

### Max ($160/mo) — wenn's drauf ankommt
- Alle Skill-Lanes auf GLM-5.2
- Effort=max überall
- Dedicated Resources → keine Spitzenauswirkungen

---

## Referenzen

- `~/00-Meta/navigation.md` — Cluster-Map
- `~/.hermes/docus/runbooks/glm-5-vs-5.2-coding-plan.md` — Ausführliches Spec-Doc mit Benchmarks
- `references/basti-cost-routing.md` — Nous-Budget-Regelung (älter, ergänzt durch dieses File)
- https://z.ai/blog/glm-5.2 — Offizielles Release-Blog
- https://docs.z.ai/guides/overview/pricing — Live-Preise
- https://z.ai/subscribe — Coding-Plan Abos

---

*Yuno ʕ•ᴥ•ʔ — Stand 2026-07-16, vor Preisentscheidungen immer live auf z.ai prüfen*
