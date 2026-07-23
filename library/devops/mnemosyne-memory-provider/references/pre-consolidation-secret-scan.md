# Pre-Consolidation Secret Scan

**Warum:** Basti's Sicherheits-Regel (2026-07-15): ALLE API-Keys NUR in `~/.hermes/.env`. NIEMALS in Mnemosyne, state.db, Chat-Output, Subagent-Briefings. Bevor `mnemosyne_sleep` unconsolidated Memories in Episodic festigt, MUSS ein Secret-Scan laufen.

**Wann ausführen:** Vor jedem `mnemosyne_sleep(all_sessions=True)` wenn `working.unconsolidated > 0`.

## Scan-Queries (sqlite3, read-only)

### Stufe 1: Grob-Scan (Count + Verteilung)

```bash
sqlite3 -cmd ".timeout 5000" ~/.hermes/mnemosyne/data/mnemosyne.db <<'SQL'
.mode line
SELECT 'TOTAL_UNCONSOLIDATED' as metric, COUNT(*) as value
FROM working_memory
WHERE consolidated_at IS NULL AND valid_until IS NULL
UNION ALL
SELECT 'WITH_POTENTIAL_KEY', COUNT(*)
FROM working_memory
WHERE consolidated_at IS NULL AND valid_until IS NULL
  AND (
    content LIKE '%sk-proj-%' OR content LIKE '%sk-ant-%' OR content LIKE '%sk-cp-%'
    OR content LIKE '%sk-live-%' OR content LIKE '%sk-%...%'
    OR content LIKE '%AIzaSy%' OR content LIKE '%ghp_%' OR content LIKE '%gho_%'
    OR content LIKE '%glpat-%' OR content LIKE '%xoxb-%' OR content LIKE '%xoxp-%'
    OR content LIKE '%AKIA%' OR content LIKE '%ya29.%'
    OR content LIKE '%Bearer sk-%' OR content LIKE '%Authorization: Bearer%'
  )
UNION ALL
SELECT 'IMPORTANCE_LT_0_5', COUNT(*)
FROM working_memory
WHERE consolidated_at IS NULL AND valid_until IS NULL AND importance < 0.5
UNION ALL
SELECT 'IMPORTANCE_GT_0_85', COUNT(*)
FROM working_memory
WHERE consolidated_at IS NULL AND valid_until IS NULL AND importance >= 0.85;
SQL
```

### Stufe 2: Detail-Liste (nur bei WITH_POTENTIAL_KEY > 0)

```bash
sqlite3 -cmd ".timeout 5000" ~/.hermes/mnemosyne/data/mnemosyne.db <<'SQL'
.mode line
SELECT
  id,
  importance,
  substr(content, 1, 200) AS preview_redacted,
  source,
  timestamp,
  CASE
    WHEN content LIKE '%sk-%' THEN '[CONTAINS sk- PATTERN — see preview]'
    WHEN content LIKE '%AIza%' THEN '[CONTAINS AIza PATTERN]'
    WHEN content LIKE '%ghp_%' THEN '[CONTAINS ghp_ PATTERN]'
    WHEN content LIKE '%Bearer%' THEN '[CONTAINS Bearer PATTERN]'
    ELSE '[no obvious key]'
  END AS redaction_flag
FROM working_memory
WHERE consolidated_at IS NULL AND valid_until IS NULL
  AND (
    content LIKE '%sk-proj-%' OR content LIKE '%sk-ant-%' OR content LIKE '%sk-cp-%'
    OR content LIKE '%sk-live-%' OR content LIKE '%Bearer sk-%'
    OR content LIKE '%AIzaSy%' OR content LIKE '%ghp_%' OR content LIKE '%gho_%'
    OR content LIKE '%glpat-%' OR content LIKE '%xoxb-%'
    OR content LIKE '%AKIA%' OR content LIKE '%ya29.%'
  );
SQL
```

## False-Positive Handling

Security rules that document which patterns to look for will **match themselves**. A memory like:
```
Gilt für: OpenAI sk-..., Anthropic sk-ant-..., GitHub ghp_/gho_/ghs_...
```
contains `sk-` and `ghp_` as examples, not real keys.

### Detection (ehrlicher als nur Count sagen):

1. **Content-Prüfung**: Ist der Matched-Text eine Regel/ein Hinweis auf das Pattern, nicht ein tatsächlicher Key? Schlüsselwörter: "Gilt für", "z.B.", "patterns", "Regex", "example", "Pattern", "sk-...", "ghp_/" — deutet auf Dokumentation hin.
2. **Source-Prüfung**: Source = 'preference', 'insight', 'instruction' → wahrscheinlich Regeltext. Source = 'tool', 'conversation', 'user' → wahrscheinlich echter Wert.
3. **Importance-Prüfung**: importance > 0.85 + source='preference' → sehr wahrscheinlich eine User-Regel, kein Leak.

### Wenn echter Leak

1. **Invalidieren** (`mnemosyne_invalidate`) — nicht `forget` (für Rollback)
2. **Info an Basti**: "Memory X mit potentiellen Key-Snippets invalidiert, damit Consolidation nichts festigt"
3. **Nicht in Chat pasten** was der Wert war — auch nicht redacted als "sk-...123"

## Consolidated Check: Nach Consolidation

Nach `mnemosyne_sleep`, prüfen ob neu konsolidierte Summaries Key-Patterns enthalten:

```bash
sqlite3 -cmd ".timeout 5000" ~/.hermes/mnemosyne/data/mnemosyne.db <<'SQL'
.mode line
SELECT COUNT(*) AS EPISODIC_WITH_POTENTIAL_KEY
FROM episodic_memory
WHERE (
    content LIKE '%sk-proj-%' OR content LIKE '%sk-ant-%'
    OR content LIKE '%AIzaSy%' OR content LIKE '%ghp_%'
  )
  AND created_at >= datetime('now', '-1 day');
SQL
```

## API-Key-Pattern-Reference

| Service | Key Prefix | Länge | Erkennungs-Query |
|---------|-----------|-------|------------------|
| OpenAI | `sk-proj-` | ~51 Zeichen | `LIKE '%sk-proj-%'` |
| OpenAI Legacy | `sk-` (ohne proj) | ~51 | `LIKE '%sk-%...%'` |
| Anthropic | `sk-ant-` | ~42 | `LIKE '%sk-ant-%'` |
| Google AI | `AIzaSy` | ~39 | `LIKE '%AIzaSy%'` |
| GitHub PAT | `ghp_` | ~40 | `LIKE '%ghp_%'` |
| GitHub OAuth | `gho_` | ~36 | `LIKE '%gho_%'` |
| GitLab PAT | `glpat-` | ~27 | `LIKE '%glpat-%'` |
| Slack Bot | `xoxb-` | ~28 | `LIKE '%xoxb-%'` |
| AWS Access Key | `AKIA` | ~20 | `LIKE '%AKIA%'` |
| Google OAuth | `ya29.` | ~50 | `LIKE '%ya29.%'` |
| Telegram Bot | `7xxxxx:AA` | ~46 | `LIKE '%:AA%'` |
| Discord Bot | `MTE5OD` | ~72 | `LIKE '%MTE5OD%'` |