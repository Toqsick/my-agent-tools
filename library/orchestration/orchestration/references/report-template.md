# Multi-Agent Report Template

Standard template for the synthesized master report after a 3-expert multi-agent run.
Loaded from `multi-agent-orchestration` SKILL.md §"Report Template".

```
🐋 [TITLE]

*⚡ SOFORT ERLEDIGT (N Fixes)*
✅ [fix 1]
📊 [metric change]

*[SECTION]*
🟢 [finding]
🟡 [finding]
💡 [idea]
🔧 [action-needed]

*📋 GROSSPROJEKT-RANGLISTE*
1. [project] ([effort])

*📊 STATUS*
• [key metrics]
```

## Usage

- Save final synthesis to `~/docs/system/<NAME>-YYYY-MM-DD.md` or `~/docs/builds/`
- Always include the **Verifikations-Matrix** section (see `phase-3-synthesis.md`)
- Always include **Delegation Recovery Log** if any subagent timed out
- Update `~/docs/builds/README.md` with summary link