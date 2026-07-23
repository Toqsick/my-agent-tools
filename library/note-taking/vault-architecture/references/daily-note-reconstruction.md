# Daily Note Reconstruction

When a day's note was missed, reconstruct it factually from session history — **never hallucinate content**.

## Workflow (4 steps)

### 1. Search for the target day

```python
session_search(query="YYYY-MM-DD", role_filter="user,assistant,tool", limit=3)
```

Include tool output in the filter — the tool calls contain file paths, git SHAs, exit codes, and test results that are the factual backbone.

### 2. Anchor with temporal sort

```python
session_search(query="YYYY-MM-DD", sort="newest", role_filter="user,assistant,tool", limit=3)
```

Use `sort="newest"` when the day is recent but you want the end-state of what was built, or `sort="oldest"` to trace how a sequence unfolded.

### 3. Cross-reference with related queries

Search for project names, error messages, or file paths that appeared in step 1 to build a complete picture of the day:

```python
session_search(query="<project-name-or-fix-name>", role_filter="user,assistant,tool", limit=5)
```

### 4. Synthesize into structured sections

- Extract concrete outputs (commits, SHAs, file paths, test results) from tool output — these are the `## Was lief` bullets
- Extract decisions and bugs found — these become `## Erkenntnisse`
- Extract open-ended threads and next steps — these become `## Offene Punkte`
- Derive wiki-links from recognized project names, tool names, or referenced notes
- Set `stimmung` based on the dominant theme (troubleshooting breakthrough? research-heavy? productive consolidation?)

## Rules for Review-Notiz (reconstructed entries only)

- Must include the exact `session_search` commands used as source references
- Must say "rückwirkend rekonstruiert aus Session-History" explicitly
- Must list any disclaimers like "Session-ID unklar — könnte auch Tag X sein"
- Never fabricate content — if session_search yields nothing for a day, note "Keine Session-Spuren gefunden" instead of inventing