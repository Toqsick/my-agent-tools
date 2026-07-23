# Qwen3.5-9B MTP — Prompt Patterns & Model Patch

> Created 2026-07-15 from real prompt-engineering work on Basti's setup.
> See `~/10-Projekte/10-active/greyhack-tools/` for the target codebase.

## Model Patch (shared header for all task prompts)

When building a system prompt for Qwen3.5-9B, include a patch header like:

```markdown
## Model
- Local: `qwen35-9b-local` (Q4_K_M, ~5.9 GB, RTX 5060 8GB)
- Modelfile: `~/.ollama/custom-models/qwen35-9b-local.modelfile`

## Sampling
- `num_ctx: 16384` | `num_predict: 8192`
- `temperature: 0.6` | `top_p: 0.95` | `top_k: 20` | `repeat_penalty: 1.05`

## Mandatory Behavior
1. **Thinking mode active** — reasoning block before final output. NO code inside the thinking block.
2. **`max_tokens: 2048`** minimum (Qwen thinking consumes ~600+ chars).
3. **No KV-cache quantize** — otherwise garbled output.

## Language Stack
- System prompt and assistant reply: English
- Code comments: English
- Identifiers (variables, functions, file names): English
- Print/user-facing strings inside code: English

## Output Length Budget
Per reply ≤ 600 tokens reasoning + 1200 tokens output. Split into follow-up turn if longer.
```

## Anti-Pattern Table Technique

For 9B models, explicit ban-tables + inline-verify commands are more effective than prose. Format:

```markdown
| Pattern | Ban | Quick test |
|---|---|---|
| One-line `if X then Y end if` | NEVER | `rg '\bif\b.*\bthen\b.*\bend\s+if\b' <file>` |
| Ternary `X if C else Y` | NEVER | manual |
| `eval` with user input | NEVER | `rg '\beval\b' <script>` |
| `chmod 777` | NEVER | `rg 'chmod\s+777' <script>` |
| Unquoted variables `$var` | NEVER — use `"$var"` | `rg '[^\"]\$\w' <script>` |
```

**Why it works:**
- The model sees concrete examples of what NOT to do
- The `Quick test` column embeds a verifiable command the model runs after generating
- Self-check before snippet delivery reduces hallucinated code

## Reply Skeleton

Every task-specific prompt should define a structured reply skeleton:

```markdown
## Situation
[1-2 sentences]

## Assumptions / Deployment Kind
- [ ] Option A
- [ ] Option B

## Code
[complete snippet, English comments]

## [Domain]-Specific Audit (short)
- [✓/✗] Item 1: ...
- [✓/✗] Item 2: ...

## Verification
bash <command>  # expected: <output>

## Watch-out
[1-2 lines]
```

## User Template

Include a fill-in template at the bottom of the prompt so the user knows what context to provide:

```markdown
## Task
[1-2 sentences]

## Context
- Tool name: [...]
- Deployment: [...]
- Repo path: [...]

## What I already tried
[short, omit if empty]

## Expected output
[complete snippet | diff | bug list with fix suggestion]
```

## Provenance
- First used: B1 GreyScript + B2 Bash-Audit prompts (2026-07-15)
- Target model: `qwen35-9b-local` (Q4_K_M, MTP variant)
- Plan: `~/.hermes/plans/2026-07-15_160851-qwen-prompts-b1-b2-greyscript-bash-audit.md`
- Handoff report: `~/.hermes/docus/reports/qwen-prompts-b1-b2-handoff-2026-07-15.md`