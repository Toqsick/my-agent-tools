# Subagent-Briefing-Patterns

Wie man den gerouteten Persona-Preamble in einen Hermes `delegate_task`-Aufruf verpackt.

## Pattern 1: Single-Domain (Standard)

```python
from personas import load_registry, match_persona, build_preamble

registry = load_registry()
task = "build a Python CLI that summarizes CSVs"
matches = match_persona(task, registry)
persona = matches[0][0]  # Top-Match

# Hermes hat keinen direkten Python-API für delegate_task.
# Aufruf via Tool-Call:
delegate_task(
    goal=task,
    context=build_preamble(persona, registry),
    toolsets=registry["routing_table"][persona]["toolset_hints"]
)
```

## Pattern 2: Multi-Domain-Decomposition

```python
matches = [("researcher", [...]), ("writer", [...])]

# Phase 1: Parallel-Dispatch (jede Persona isoliert)
for persona_key, _ in matches:
    if persona_key == "verifier":
        continue  # Gate am Ende, nicht in Phase 1
    delegate_task(
        goal=f"{task} (Perspective: {persona_key})",
        context=build_preamble(persona_key, registry),
        toolsets=registry["routing_table"][persona_key]["toolset_hints"]
    )

# Phase 2: Yuno synthetisiert die Resultate inline

# Phase 3: Verifier-Gate
delegate_task(
    goal=f"Audit the synthesized deliverable: {synthesized_output}",
    context=build_preamble("verifier", registry),
    toolsets=registry["routing_table"]["verifier"]["toolset_hints"]
)
```

## Pattern 3: Verifier-only (Gate nach manuellem Fix)

```python
# User hat manuell was gebaut, will nur Audit
delegate_task(
    goal=f"Audit this deliverable: <paste code/output here>",
    context=build_preamble("verifier", registry),
    toolsets=["terminal", "file", "code_execution", "web"]
)
```

## Pattern 4: Researcher → Writer-Hand-off

Wenn Researcher erst Research macht, dann Writer daraus ein Doc baut:

```python
# Step 1: Researcher sammelt Fakten
research_result = delegate_task(
    goal="Research vector databases 2026",
    context=build_preamble("researcher", registry),
    toolsets=["web", "browser"]
)

# Step 2: Writer baut Doc aus den Research-Fakten
delegate_task(
    goal=f"Write a blog post based on these research findings:\n\n{research_result}",
    context=build_preamble("writer", registry),
    toolsets=["file"]
)
```

## Working-Contract-Template

Jeder Subagent bekommt am Ende des Preamble einen Working-Contract:

```markdown
────────────────────────────────────────────────────
Working contract for this run:
- You are an isolated subagent. The parent (Yuno) is waiting.
- Deliver: a clear, structured result the parent can synthesize.
- If blocked: name the EXACT missing piece. Do NOT guess.
- When done: report file:line references, test outputs, risks.
────────────────────────────────────────────────────
```

Damit der Subagent weiß: er ist isoliert, soll klar liefern, nicht raten.

## Toolset-Auswahl

Toolsets sind **Hints**, nicht hardcoded. Die tatsächlichen Tools des Subagent werden durch `toolsets=` bestimmt. Für die meisten Personas reichen:

| Persona | Toolsets |
|---------|----------|
| Engineer | `terminal`, `file`, `code_execution` |
| Researcher | `web`, `browser` |
| Designer | `image_gen`, `vision`, `file` |
| Analyst | `code_execution`, `file` |
| Writer | `file` |
| Verifier | `terminal`, `file`, `code_execution`, `web` |

Falls mehr gebraucht (z.B. Engineer braucht git-MCP), kann der Parent beim Dispatch explizit ergänzen.

## Pitfalls

1. **Persona-Preamble im `context`-Feld**: Nicht als `goal`. Das `goal` ist die Task-Beschreibung, der `context` ist die Persona-Identität. Vermischen = Persona-Bleed.

2. **Verifizierbare Claims**: Engineer-Persona sagt "Build and test before declaring done". Wenn der Subagent "tests pass" berichtet ohne Test-Output → Pitfall #5 (VERIFY EVERY CLAIM). Parent muss selbst nachprüfen.

3. **Multi-Domain ≠ Multi-Subagent-blind**: Bei "research and write" erst Researcher fertig werden lassen, dann Writer mit den Research-Resultaten füttern. Nicht parallel — sonst schreibt Writer ohne Fakten.

4. **Verifier am Ende, nicht am Anfang**: Verifier ist ein Gate, kein Producer. Erst bauen, dann auditieren.

5. **Fix-Loop vs One-Shot**: Bei adversarial-brittle Deliverables ist EIN Verifier-Pass nicht genug. Loop: Verifier-Audit → Engineer-Fix → Verifier-Re-Audit → bis PASS. Pattern siehe `references/fix-loop-pattern.md`.

6. **Verifier-Mechanik ≠ Verifier-Repro**: Verifier kann Bugs identifizieren aber den Repro-Trigger zu eng wählen. Parent prüft die Mechanik, nicht nur die 1:1-Repro.

7. **Briefing-Größe für Fix-Loops**: Verifier-Bug-Liste mit file:line + Repro + Fix-Hint = ca. 3-4 KB. Engineer kann 6-8 Bugs in einem Run fixen, mehr = Scope-Ballon-Risiko.