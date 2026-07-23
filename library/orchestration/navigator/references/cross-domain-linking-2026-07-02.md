# Cross-Domain Skill Linking — Session Notes (2026-07-02)

## Ausgangslage

4 GreyHack-Skills im `gaming/`-Cluster hatten KEINE Verweise auf Orchestration-Skills
(`multi-agent-orchestration`, `multi-agent-pitfalls-cheatsheet`, `skill-navigator`).

Der Orchestration-Cluster hatte auch keine Verweise zurück zu den Domain-Skills.

**Problem:** Ein Basti, der GreyHack-Subagent-Audits machen will, muss erst *wissen* dass
es `multi-agent-pitfalls-cheatsheet` gibt, bevor er es laden kann. Die Domain-Skills
helfen nicht bei der Discovery.

## Durchgeführte Änderungen

### 1. Bidirektionale Referenzen im Orchestration-Cluster
- `multi-agent-pitfalls-cheatsheet` → verlinkt jetzt `skill-navigator` + `skill-library-maintenance`
- `skill-navigator` → war bereits cheatsheet-verlinkt

### 2. GreyHack-Cluster (4 Skills)

Jeder Skill erhielt eine `## 🧭 Related Skills (Cross-Cluster Navigation)`-Sektion:

| Skill | Verweist auf |
|---|---|
| `gaming/greyhack/SKILL.md` | navigator, cheatsheet, orchestration |
| `gaming/greyhack-greyscript/SKILL.md` | navigator, cheatsheet, orchestration |
| `gaming/greyhack-sandbox/SKILL.md` | navigator, cheatsheet, orchestration, maintenance |
| `gaming/greyhack-hermes-api/SKILL.md` | navigator, cheatsheet, orchestration |

### 3. Einschubstelle

- Skills mit `References`/`Support Files`-Sektion am Ende → danach
- Skills ohne → ans Ende der Datei

## Pattern

→ Siehe `skill-navigator/SKILL.md` §"Cross-Domain Navigation" für das allgemeine Pattern.
→ Siehe `skill-library-maintenance` für Library-Hygiene-Kontext.

## Verifikation

Cross-Reference-Matrix (vorher/nachher):

```
                   vorher                  nachher
  cheatsheet → navigator     ✗           ✓
  navigator → cheatsheet     ✗           ✓
  greyhack → cheatsheet      ✗           ✓
  greyhack-greyscript → ch   ✗           ✓
  sandbox → cheatsheet       ✗           ✓
  hermes-api → cheatsheet    ✗           ✓
```

Alle 6 patchierten Skills: YAML intakt, keine CLI-Drift, keine broken refs.
