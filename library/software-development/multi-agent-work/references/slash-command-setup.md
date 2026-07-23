# Slash-Command Registrierung

## In Hermes config.yaml

```yaml
slash_commands:
  multi-agent-work:
    description: "Von Research bis Implementierung in einem Durchlauf"
    skill: multi-agent-work
    trigger: "/multi-agent-work"
```

## Oder manuell aufrufen

```
User: /multi-agent-work "Baue mir einen ..."
→ Ich lade Skill `multi-agent-work`
→ Führe 6-Phasen-Workflow aus
→ Liefere lauffähigen Code + Doku
```

## Verwandte Skills

- `multi-agent-research` — Basis-Research (nur Phasen 1-3)
- `ki-murks-verhindern` — Quality Gates für Implementierung
- `rag-pipeline-python` — Für Research mit aktuellem Wissen
- `subagent-driven-development` — 2-Stufen-Review
- `critic-gate` — Deterministisches Quality-Gate mit strukturiertem JSON-Output
- `output-validator` — Syntax-Check vor Handoff an Critic
- `context-pruner` — Kontext-Isolation für Token-Ersparnis