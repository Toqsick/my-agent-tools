# Controlled Write in Read-Only Briefings

**Nuance to Pitfall #31:** Read-only briefings are the SAFE DEFAULT, but **some tasks require exactly one controlled write operation** that the briefing explicitly authorizes.

## Example (Expert 2 in GreyHack audit)

- Briefing says: "ONLY read-only commands"
- But Question 10 is: "Run the actual build: `bash ci-build.sh --out-dir /tmp/...`"
- Solution: Explicitly authorize **just that one write to /tmp/** in the briefing

## Briefing Phrasing

```markdown
## TOOLING (Pitfall #31)

- ONLY read-only commands: `ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`, `stat`, `diff`
- AUTHORIZED EXCEPTION (Question 10): `bash ~/path/to/build.sh --out-dir /tmp/audit-build-$(date +%s)`
  - Output goes ONLY to /tmp/, NEVER to repo
- DO NOT execute: `chmod`, `chown`, `rm`, `mv`, `apt`, `systemctl`, `kill`
```

## Why This Works

- Parent and subagent both know the write boundary
- The single authorized write is auditable (visible in subagent trace)
- Other Write-Commands are still blocked by Background-Review
- The output location is sandboxed (`/tmp/` not the repo)

## When to Use Controlled Writes

- E2E test execution (run build/test, output to /tmp/)
- Snapshot creation (output to /tmp/, not source tree)
- One-shot diagnostic commands (memory check, df, free — already read-only)

## NOT For

- Config changes, permission changes, package installs — these require Pitfall #31 full read-only treatment