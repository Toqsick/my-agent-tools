# Gate Dispatch Parent-Direct Fallback

**Applies to:** `multi-agent-orchestration`

## Trigger

`delegate_task(tasks=[...])` is rejected by HermesUltraCode or the model provider, including:

```text
[HermesUltraCode gate · blocked · tier=trivial] base_prompt is empty; nothing to dispatch
```

or provider-gate/provider-HTTP failures such as:

```text
[HermesUltraCode gate · escalated · tier=elevated] reviewer provider error: OpenRouter HTTP 404: Not Found
```

## Response Pattern

1. Stop retrying the same dispatch.
2. Re-run the three expert scopes in the parent agent.
3. Use direct terminal/file/web measurements, not estimates.
4. Write three explicit expert reports.
5. Synthesize them into `~/docs/system/`.
6. State clearly: subagent dispatch was blocked; parent-direct fallback was used.
7. Keep the final synthesis focused on prioritized next actions and verified state.

## GreyHack P2 #5/#6 Example — 2026-06-19

User invoked `multi-agent-orchestration` for roadmap items 5 and 6:

1. GreyHack Mission-Integrations-Guide.
2. `exploit_finder`.

Three dispatch attempts were blocked by OpenRouter HTTP 404 through HermesUltraCode, so parent-direct fallback was used.

Parent-direct expert outputs:

- Expert 1 — Mission workflow/tool-chain:
  - `/home/bratan/docs/system/mission-integration-guide-expert-2026-06-19.md`
- Expert 2 — `exploit_finder` concept/safety:
  - `/home/bratan/docs/system/exploit-finder-expert-2026-06-19.md`
- Expert 3 — Build/repo integration:
  - `/home/bratan/docs/system/exploit-finder-build-integration-expert-2026-06-19.md`
- Synthesis:
  - `/home/bratan/docs/system/greyhack-p2-mission-exploit-finder-2026-06-19.md`

Key synthesis outcome:

- Recommended next step is not to implement `exploit_finder` immediately.
- First run In-Game-Smoke-Tests with Fileserver.
- Then update `install_all.src`.
- Then finalize Mission-Integrations-Guide.
- Then create a P2 feature branch and implement `exploit_finder` V1.

## Non-Goal

Do not store this as “subagents do not work.” Store the retry/fallback workflow: dispatcher failures are recoverable by parent-direct measurement.
