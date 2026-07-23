---
name: nous-multi-lane-routing
version: 1.2
description: >-
  Use when user asks for routing tasks across specialized model lanes, isolating providers by Hermes profile, configuring role-based fallback chains, or assigning planner, coder, researcher, or verifier roles. NOT for choosing one model for a single chat or dispatching one isolated subtask. Defines role-first lane profiles, provider isolation, reasoning settings, delegation rules, schema migration, and Kanban execution.
summary: 'Multi-Lane Worker-Pool mit Token-Plan-Isolation (nous/zai/minimax Provider). NICHT alle Modelle über Nous Portal — jede Marke hat eigenen Provider. Hermes-Profile pro Lane, Auxiliary-Routing, Skill-Lane-Frontmatter, Model-Watchdog gegen ollama-cloud-Auto-Reset, Lane-Health-Cron.

  '
trigger:
- User möchte Tasks nach Modell-Stärken routen
- User hat mehrere Token-Pläne (nous + minimax + zai) und will saubere Trennung
- Multi-Provider-Setup, Provider-Isolation notwendig
- Skill-Zuordnung soll rollenbasiert statt modellbasiert laufen
- model.default resettet sich selbst → Watchdog nötig
- Evaluation/Performance-Check der Lane-Architektur
- Königin/Worker/Gate-Metapher statt konkreter Modellnamen
entrypoints:
- setup_lanes
- provider_isolation
- auxiliary_routing
- skill_lane_mapping
- smoke_test
- evaluation
- documentation
- watchdog_maintenance
author: Hermes Agent
license: MIT
trigger_keywords: ['model', 'one', 'nous-multi-lane-routing', 'routing', 'tasks']
keywords: ['model', 'role', 'user', 'asks', 'routing']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['claude-code-provider-profiles', 'model-selector', 'yuno-team-orchestrator']
---


# Nous Multi-Lane Routing (Token-Plan-Aware)

## ⚠️ KRITISCHE KORREKTUR V1.1 → V1.2
In V1.1 wurde angenommen, dass **alle Modelle über Nous Portal** laufen.
Das ist FALSCH. User-Korrektur aus der 2026-07-02 Session:
- MiniMax M2.7 → `minimax` Provider (eigener Token-Plan, $MINIMAX_API_KEY)
- GLM-5 → `zai` Provider (eigener Token-Plan, $GLM_API_KEY)
- DeepSeek V4 Pro/Flash + StepFun Free → `nous` Provider (Portal-Tokens)

Diese Korrektur durchzieht alle Tabellen und Setup-Schritte.

## Mission
Baut einen **role-first Worker-Pool** auf Basis von Hermes-Profilen mit **korrekter Provider-Isolation**.
Jeder Worker-Typ routet durch seinen eigenen Token-Plan — keine Doppelabrechnung über Nous Portal.
Kein lokales Modell (RAM-Overflow-Risiko). Gratis-Tier via `stepfun/step-3.7-flash:free`.

## Konzept

### Rollen statt Modell-IDs
Routing-Regeln sind an **Rollen** gebunden, nicht an einzelne Modell-IDs. Dadurch überlebt die Pipeline Modellwechsel und Tauschaktionen.

> **⚠️ Single Source of Truth = `config.yaml` → `skill_lanes` (nicht diese Tabelle).** Live-Abgleich 2026-07-21: `koenigin`=**glm-5.2** (zai), `worker-heavy`=**glm-5** (zai), `gate`=**glm-5** (zai), `worker-vision`=**MiniMax-M3** (minimax), `worker-flash`=**stepfun/step-3.7-flash:free** (nous); **Session-`model.default`=MiniMax-M3**, 1. Fallback `zai/glm-5.2`. Frühere Einträge „Königin = deepseek-v4-pro" und „Vision = MiniMax-M2.7" waren **stale** und sind unten korrigiert. Benchmark-Spalten sind historisch/indikativ — bei Zweifel die Live-Config lesen.

| Rolle | Zielprofil | Provider | Standardmodell | Kosten/M Input | Coding | Context | Use Case |
|---|---|---|---|---|---|---|---|---|
| **Königin** | main | `zai` (Lane koenigin) | `glm-5.2` — *Session-`model.default` real **MiniMax-M3**; GLM-5.2 = Planer/1. Fallback* | GLM-Token-Plan | — | 1M | Planung, Routing, Decompose, Delegation, Session-Mgmt, Subagent-Spawn |
| **Worker Heavy** | `yuno-coder` | `zai` | `glm-5` | GLM-Token-Plan | **68.8** | 1M | Coding, Refactoring, Security-Audit, Heavy Reasoning, Synthesis |
| **Worker Vision** | `yuno-vision` | `minimax` | `MiniMax-M3` | MiniMax-Token-Plan | — | 1M | Bild/Video/Multimodal, Tool-Use, Creative/Visual |
| **Worker Flash** | `yuno-flash` | `nous` | `stepfun/step-3.7-flash:free` | **$0** | 37.3 | 256k | Bulk-IO, Approval, Routing-Support, einfache Loops, Kuration |
| **Worker Gemini** | `yuno-gemini` | `google-oauth` | `gemini-3.1-pro-preview` | **$0** (Google AI Pro Abo-Kontingent via OAuth) | stark | 1M | Heavy-Reasoning-Alpha wenn GLM-5 ausfällt, 1M-Kontext-Default, Multimodal-Native (Bild/Video/Audio), OAuth-Trennung von Token-Plänen |
| **Gate** | `yuno-coder` | `zai` | `glm-5` | GLM-Token-Plan | **68.8** | 1M | Verifier, Quality Gate, Final Approval, Humanizer, Red-Team-Checks |

---

#### Rollen-Default für Subdelegation
Subdelegation erfolgt rolle-zuerst. Nur wenn Subagent allein laufen soll, landen sie in der Worker-Lane.

---

## Setup-Schritte

### 1. Worker-Profile anlegen

Jedes Profil bekommt eine eigene `~/.hermes/profiles/<name>/config.yaml` mit eigenem `_config_version` und eigenem `model` Block. **NICHT über `hermes config set`** für verschachtelte Blöcke. Nutze direkten YAML-Edit oder `patch`.

Pflicht: `PURPOSE.md` neben `config.yaml` — sonst sind Profile später schlecht unterscheidbar.

```yaml
# ~/.hermes/profiles/yuno-coder/config.yaml
model:
  provider: nous
  model: z-ai/glm-5.2
fallback_providers:
  - provider: nous
    model: deepseek/deepseek-v4-flash
  - provider: nous
    model: minimax/minimax-m3
```

### 2. Main-Config patchen

Änderungen NUR in `~/.hermes/config.yaml`:
- `model.default` auf Orchestrator setzen
- `auxiliary.*` Blöcke nach Stärke zuweisen
- `delegation.model` und `delegation.reasoning_effort` explizit setzen
- `moa.presets` für synchrone Multi-Modell-Aufgaben ergänzen
- `skill_lanes` für rollenbasiertes Skill-Routing ergänzen

**Kritisch:** `hermes config set` kann verschachtelte Keys nicht sauber setzen. Nutze `patch` oder Python-YAML-Schreibzugriff.

### 3. Fallback-Chain in JEDEM Lane-Profil

```yaml
fallback_providers:
  - provider: nous
    model: deepseek/deepseek-v4-flash  # $0.089/M, coding 56.2, 1M ctx
  - provider: nous
    model: minimax/minimax-m3          # $0.30/M, multimodal
```

**Warum:** Gratis/Free-Modelle können 429 liefern. Ohne Fallback → Task failed.

### 4. Auxiliary-Routing im Main

| Auxiliary-Kategorie | Modell | Begründung |
|---|---|---|
| Gratis-Services | approval, title_generation, session_search, monitor, background_review | StepFun Free, keine Sache |
| Vision/Tool | vision, skills_hub, mcp, kanban_decomposer, triage_specifier | MiniMax M3 — einziges Vision-Modell unter Nous |
| Heavy Reasoning | compression, curator, web_extract, profile_describer | GLM 5.2 — höchste Reasoning-Quality in diesem Set |

### 5. Reasoning-Profile je Rolle

| Rolle | `reasoning_effort` | `max_tokens`-Default |
|---|---|---|
| Königin | `xhigh` | 16'384 |
| Worker Heavy | `xhigh` | 16'384 |
| Worker Vision | `xhigh` | 16'384 |
| Worker Flash | `high` | default |
| Gate | `xhigh` | 16'384 |

### 6. Delegation explizit setzen

```yaml
delegation:
  provider: nous
  model: z-ai/glm-5.2        # Worker Heavy als Subagent-Default
  reasoning_effort: xhigh
```

**Warum:** Ein leerer oder fehlender `delegation.model` führt zu Free-Tier-Inheritance oder Modell-Wildwuchs.

### 7. Schema-Migration

Nach Profil-Erstellung: `hermes config check` → zeigt `Config version: X → X+1 (update available)` an. Hermes migriert beim nächsten Start automatisch. Kein manueller Schritt nötig.

---

## Nutzung

### Sync
```bash
hermes chat --profile yuno-coder -q "Refactor..."
hermes chat --profile yuno-vision --image screenshot.png -q "Beschreibe..."
hermes chat --profile yuno-flash -q "Parse diese Logs..."
hermes chat --profile yuno-coder --synthesizer -q "Verifiziere..."
```

### Async via Kanban
```bash
hermes kanban swarm "Ziel" \
  --worker yuno-coder:"Code-Audit":coding \
  --worker yuno-vision:"Screenshot-Analyse":vision \
  --worker yuno-flash:"Bulk-Parse":file \
  --verifier yuno-coder \
  --synthesizer yuno-coder
```

---

## Skill-Routing — Rollen statt Modellnamen

Skills werden **rollenbasiert** zugewiesen, nicht modellbasiert. Es gibt zwei Quellen:

### 1. Zentrale Registry: `config.yaml → skill_lanes`
```yaml
skill_lanes:
  koenigin:
    profile: yuno
    model: z-ai/glm-5.2        # live (2026-07-21); Session-model.default = MiniMax-M3
    reasoning_effort: xhigh    # GLM-5.2: löst effektiv zu `max` auf (nur 2 Stufen)
    skills:
      - writing-plans
      - multi-agent-research

  worker-heavy:
    profile: yuno-coder
    model: z-ai/glm-5.2
    reasoning_effort: xhigh
    skills:
      - simplify-code
      - security-code-checker
      - github-code-review

  worker-vision:
    profile: yuno-vision
    model: minimax/minimax-m3
    reasoning_effort: xhigh
    skills:
      - architecture-diagram
      - pixel-art
      - html-artifact

  worker-flash:
    profile: yuno-flash
    model: stepfun/step-3.7-flash:free
    reasoning_effort: high
    skills:
      - codebase-inspection
      - research-tools
      - ocr-and-documents

  gate:
    profile: yuno-coder
    model: z-ai/glm-5.2
    reasoning_effort: xhigh
    skills:
      - security-code-checker
      - requesting-code-review
      - humanizer
```

### 2. Per-Skill Frontmatter
```yaml
---
lane:
- worker-heavy
- gate
reasoning_effort: xhigh
---
```

Multi-Lane-Skills sind erlaubt. Trage sie in `skill_lanes` **unter beiden Rollen** ein.

### Warum 2-schichtig?
Zentrale Registry istRouting. Skill-Frontmatter ist Self-Description; robust gegenüber Skill-Moves/Updates. Beide müssen konsistent sein.

## Mapping: Rolle → Hermes-Aufruf

| Aufgaben-Lane | Rolle | Beispielkommando |
|---|---|---|
| Planung/Routing/Delegation/Spawn | Königin | `hermes chat -q "Plane..."` |
| Code/Refactoring/Security/Synthese | Worker Heavy | `hermes chat --profile yuno-coder -s simplify-code -q "Refactor..."` |
| Bild/Video/UI/Visual | Worker Vision | `hermes chat --profile yuno-vision -s architecture-diagram -q "Mach..."` |
| IO-Parsing/Approval/Gratis | Worker Flash | `hermes chat --profile yuno-flash -q "Parse..."` |
| Review/Verify/Humanizer | Gate | `hermes chat --profile yuno-coder -s requesting-code-review -q "Check..."` |

## Entscheidungsmatrix

| Lane/Rolle | Delegations-Hinweis | Begründung |
|---|---|---|
| Königin | Selber entscheiden, delegieren, synchronisieren | Planungskosten sparen, Kontext erhalten |
| Worker Heavy | Subagent oder explizites `--profile yuno-coder` | Höchste Coding/Reasoning Quality |
| Worker Vision | Nur bei Bild/Video/Creative/Artefakt | Einziges Vision-Modell unter Nous Portal |
| Worker Flash | Bulk IO, einfache Prüfungen, Free-Tier | $0, ausreichend |
| Gate | Nach Worker-Runs, vor Merge/Release | Quality Gate, Fact-Check |

## 3-Job-Smoke-Test für Lane-Profile (nach Änderung Pflicht)

```
Job 1: File-Scan
Job 2: Tool-Validation mit Exit-Code
Job 3: Doc-Generation mit File-Write
```

Akzeptanzkriterien:
- Alle 3 liefern Output in <60s
- Alle liefern `##DEPPS_DONE##`
- File-Writes via `read_file` verifiziert
- Exit-Codes sind 0

Wenn 1/3 failt: Retry mit halbiertem Scope oder Tier auf `deepseek-v4-flash` hochsetzen.

## Pitfalls

1. **KEIN lokales Modell für Worker-Pool** — 12B-Modelle brauchen ~12GB RAM → RAM-Overflow.
2. **`hermes config set` kann verschachtelte Keys nicht sauber setzen** — sibling-Keys gehen verloren. Nutze `patch` oder Python-YAML.
3. **Free-Modelle brauchen Fallback-Chain** — 429 nach Bursts möglich, sonst Task lost.
4. **Main-Orchestrator nicht GLM** — $0.93/M für jede Approval-Frage ist nicht sinnvoll.
5. **StepFun Free ist in Benchmarks niedrig** — $0 ist $0. Für Bulk-Tasks reicht es.
6. **Modell-Wechsel braucht Hermes-Neustart** — neue Config greift erst nach `/reset`.
7. **Subagent-Self-Reports sind keine Facts** — immer verifizieren.
8. **Lane-Profiles brauchen `PURPOSE.md`** — sonst verwechselst du sie irgendwann.
9. **Skill-Duplikate im Bundle** — `security-code-checker` existierte doppelt; Duplikat aufräumen.
10. **Rollen zuerst** — ändert man das Modell in einer Rolle, müssen nur die Profile aktualisiert werden; Skills, Registry und Calling-Patterne bleiben unverändert.
11. **Kanban-Spawn skill-loader bug** — Lokale Skills (`firecrawl-web`, `software-development/...`) werden in Kanban-Worker-Spawn nicht aufgelöst. Workaround: in Swarm-Templates nur builtin Skills nutzen. Langfristig: Hermes-Issue tracen.
12. **Lane-Profile brauchen `reasoning_effort` + Fallbacks + Modell** — Fehlt einer der 3 Keys, ist das Profil nicht produktiv tauglich. Health-Checks müssen diese 3 Keys prüfen.
13. **Skill-Lane-Frontmatter-Coverage muss 100% sein** — sonst rutscht ein Skill in die falsche Lane oder wird gar nicht geroutet. Nach jedem Skill-Install/Curator-Lauf Coverage prüfen.
14. **Stress-Test ist Pflicht, nicht optional** — Nur Single-Spawn-Tests reichen nicht. 3 parallele Swarms decken Rate-Limits, Fallback-Ketten und Daemon-Dispatching erst auf.
15. **Daemon + Watchdog sind Produktiv-Pflicht** — Ohne persistenten Daemon und Health-Cron ist Swarm-Betrieb nach Reboot tot.
16. **Gemini-CLI als 5. Free-Lane (ab 2026-07-05)** — `npm i -g @google/gemini-cli`, OAuth-Login mit Google-Account → zieht Kontingent aus **Google AI Pro Abo** (kein API-Billing). Setup: `~/.gemini/settings.json` → `selectedType: "oauth-personal"`, OAuth-Client-Credentials in `~/.gemini/.env` (mode 600). **NICHT gleichzeitig GEMINI_API_KEY setzen** — der priorisiert vor OAuth und bricht den Abo-Pfad. **Pitfall:** OAuth-URL darf NICHT durch Hermes-Background-Terminal gerendert werden (URL-Mangling, Google: "Request malformed"). Immer im User-Terminal ausführen oder manuell per Browser-Schritt. Siehe `autonomous-ai-agents/coding-agents/references/gemini-cli.md`.

## Datenbank/Persistenz

Migrationen werden **nicht manuell ausgeführt**. Updates per Schema-Migration bei Config-Änderungen.

## Files in diesem Skill

| Pfad | Zweck |
|---|---|
| `references/nous-multi-lane-setup-2026-07-02.md` | Setup-Details + Änderungslog |
| `references/nous-skill-lane-registry-2026-07-02.md` | 5-Rollen-Skill-Registry, Lane-Frontmatter-Map, Duplikate |
| `references/kanban-operator-reference-2026-07-02.md` | Daemon/Health/Swarm-Templates/Stress-Test-Operator-Reference |

## Verbundene Skills

- `orchestration/hermes-orchestration` — Queen+Worker Pattern
- `model-selector` — Modell-Vergleiche
- `kanban-codex-lane` — async Multi-Lane via Kanban-Boards
- `autonomous-ai-agents/coding-agents` — Coding-Agent-CLIs (Claude/Codex/Copilot/OpenCode/**Gemini**)
