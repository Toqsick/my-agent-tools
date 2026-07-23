---
id: repo-cleanup
name: Safe repo / folder cleanup
when_to_use: Tidying a directory, repo, or filesystem area — dedupe, archive, reorganize — without losing anything.
agents: [worker, coder]
skills: [tidy-folder, yuno-cleaner]
phases:
  - phase: Scan (read-only)
    owner_agent: worker
    skills: [yuno-cleaner, tidy-folder]
    exit_criteria: A dry-run inventory of candidates (dupes, cruft, stale files) with sizes exists.
    failure_modes: Deleting before scanning; trusting a stale doc over live state.
  - phase: Classify
    owner_agent: coder
    skills: [tidy-folder]
    exit_criteria: Each candidate labeled keep / archive / delete with a reason.
    failure_modes: Treating unfamiliar files as junk; touching another owner's runtime state.
  - phase: Backup
    owner_agent: worker
    skills: []
    exit_criteria: A reversible backup (tar) of everything about to be removed exists.
    failure_modes: Skipping insurance on an irreversible action.
  - phase: Execute
    owner_agent: worker
    skills: []
    exit_criteria: Only the approved set is removed/moved; user confirmed anything irreversible.
    failure_modes: rm -rf with a glob; removing symlink targets instead of the symlink.
  - phase: Verify
    owner_agent: coder
    skills: []
    exit_criteria: Nothing unique lost; references updated; result matches the plan.
    failure_modes: Not re-checking that dependents still resolve.
---

# Safe repo / folder cleanup

**Scan → Classify → Backup → Execute → Verify.** Read-only first, always reversible, confirm before
anything irreversible. Uses `yuno-cleaner` (dry-run system scan) and `tidy-folder` (organize), executed
by `worker` with `coder` judgment on classification.

**Route in:** "clean up / tidy / organize / dedupe / archive." Never delete or overwrite something you
did not create without looking at it first and surfacing what you find.
