# Basti Tool-Cost Routing Rules (2026-07-15)

**Gilt für:** ALLE Tool-Calls + Subagent-Dispatch im Kontext von Bastis 44€ Nous-Budget.

## Strikte Priorität

| Priority | Provider/Modell | Wann |
|----------|----------------|------|
| **1** | **Lokal** (Ollama, lokal gehostet) | Wann immer möglich |
| **2** | **Free-Modelle** (GLM-5 zai, StepFun Free, Qwen Free) | Wenn lokal nicht geht |
| **3** | **Nous Portal** nur günstigste (StepFun Free) | Nur als Notfall |
| **KEIN** | **DeepSeek auf Nous** (weder V4 Flash noch V4 Pro) | Nur via provider: deepseek, nicht nous |

## Subagent-Briefing-Pflichtfeld

Jeder `delegate_task` Aufruf MUSS untenstehendes Tool-Tier-Feld enthalten:

```
Tool-Tier: lokal first / free only / notfall: nous cheapest
```

## Warum

- 44€ Nous-Budget soll für ~1200 Tage reichen
- Schritt-für-Schritt eskalieren: lokal → free Provider → Nous-Notfall
- KEIN DeepSeek auf Nous weil es pro Token kostet und das Budget frisst