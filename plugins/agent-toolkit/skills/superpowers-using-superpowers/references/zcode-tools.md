# ZCode Tools Reference

ZCode is a Claude-Code-derived CLI agent harness. Skills speak in actions ("dispatch a subagent", "create a todo"); on ZCode those actions resolve to the tools below.

## Skill Invocation

```
Skill(skill="superpowers-writing-plans")                          # bare name (agent-toolkit family)
Skill(skill="agent-toolkit:superpowers-writing-plans")            # qualified plugin:skill form — always unambiguous
```

- Invocation is **by name or `plugin:skill`** — never by file path, never with a leading `/` (that's the user-facing slash-command syntax, not the tool argument).
- Sibling skills in this toolkit use the `superpowers-<name>` prefix. Do not confuse them with the official `superpowers:<name>` plugin family (different files, not maintained here).
- The user invokes skills interactively as `/<skill-name>`.

## Core Tool Table

| Action | ZCode tool | Notes |
|-------------------|-----------|-------|
| Dispatch implementer subagent | `Agent(subagent_type="general-purpose", description="...", prompt="...")` | Isolated context; the primary SDD primitive |
| Dispatch read-only explorer | `Agent(subagent_type="Explore", prompt="...")` | Read-only fan-out search; returns conclusions, not file dumps |
| Dispatch parallel agents | Multiple `Agent` calls in **one message** | All calls in a single assistant turn run concurrently |
| Track tasks / checklist | `TodoWrite(todos=[{content, status, priority}, ...])` | One item in_progress at a time |
| Enter plan mode | `EnterPlanMode()` | Read-only exploration before implementation |
| Exit plan mode (approval) | `ExitPlanMode(plan="...", allowedPrompts=[...])` | The user reviews and approves the plan |
| Ask structured question | `AskUserQuestion(questions=[...])` | 1-4 questions, 2-4 options each |
| Read / Edit / Write | `Read`, `Edit(file_path, old_string, new_string)`, `Write` | Use `limit` on large reads |
| Shell | `Bash(command="...", timeout=N, run_in_background=B)` | `timeout` in ms, max 600000 |
| Search | `Grep(pattern, path)`, `Glob(pattern, path)` | Always scope with `path` |
| Background tasks | `TaskOutput(task_id, block=B)`, `TaskStop(task_id)` | For `run_in_background=true` shells |
| Web | `WebFetch(url, prompt)`, `WebSearch(query)` | Prompt filters what gets extracted |

## Subagent Dispatch Briefings

Each `Agent` dispatch sees **only the prompt you write** — never session history. A briefing states, in order: role, goal, exact input file paths, constraints (read-only scope, no commits, TDD), output file path or return format, and a hard-stop rule ("if blocked, report the blocker — do not guess"). Anything over ~30 lines (diffs, code blocks, reports) is handed over as a file path, never pasted.

## What ZCode Does NOT Have (vs Hermes)

| Hermes tool | ZCode equivalent |
|-------------|-----------------|
| `delegate_task` | `Agent(subagent_type="general-purpose", prompt="...")` |
| `mnemosyne_remember` / `mnemosyne_recall` | `Write`/`Read` on memory files (ZCode has its own memory system) |
| `skill_view` | `Skill(skill="<name>")` |
| `terminal(background=true)` | `Bash(command, run_in_background=true)` + `TaskOutput` |
| `patch` | `Edit(file_path, old_string, new_string)` |
| `write_file` / `read_file` / `search_files` | `Write` / `Read` / `Grep` |

**Never use Hermes tool names on ZCode.**
