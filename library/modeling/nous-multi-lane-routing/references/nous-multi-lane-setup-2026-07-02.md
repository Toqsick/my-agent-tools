# Nous Multi-Lane Routing — Session-Verlauf 2026-07-02

## Ausgangslage
Basti wünschte ein klares, strukturiertes Multi-Modell-Routing über **ausschließlich Nous Portal**.
Wichtig: Kein lokales Modell (RAM-Schutz), Kosten-Grenzen beachten, Stärken-optimiert.

## Modell-Benchmarks (aus Hermes-Modellliste)

| Modell | Coding | Context | Preis/M prompt |
|---|---|---|---|
| `deepseek/deepseek-v4-pro` | 59.4 | 1M | $0.44 |
| `z-ai/glm-5.2` | **68.8** | 1M | $0.93 |
| `minimax/minimax-m3` | 58.6 | 1M | $0.30 |
| `deepseek/deepseek-v4-flash` | 56.2 | 1M | $0.089 |
| `stepfun/step-3.7-flash:free` | 37.3 | 256k | **$0.000** |

## Korrekturen während Setup

1. **Keine lokale Bottleneck** — `ollama-launch` wird nicht im `yuno-bulk` Profil vererbt.
   Ursache: Profile haben eigenständige `providers`-Blöcke ohne Überschneidung zum `default` Profil.
2. **StepFun Free als Primary** — Basti hat `stepfun/step-3.7-flash:free` als Gratis-Modell gewählt.
3. **MoA-Presets erfordern `aggregator` + `reference_models`** — Fehlte bei initialer Anlage.

## Smoketest
Alle 3 Lanes identifiziert Modell korrekt. Flash antwortet in 14s.

## Geänderte Files
- `~/.hermes/config.yaml`
- `~/.hermes/profiles/yuno-coder/`, `yuno-vision/`, `yuno-flash/` — neu
- `~/.hermes/profiles/yuno-bulk/` — gelöscht
- `~/docs/system/multi-lane-routing-2026-07-02.md`
