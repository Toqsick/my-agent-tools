# Deep System Plan Pattern

> **Source:** 2026-07-15 Konversation — Yuno erstellte 43KB Plan (von 24KB) auf User-Rückfrage "plan noch tiefer ausbauen".
> **Topics:** System-Härtung, Skill-Polish, Memory-Persistence, Cron-Audit.

## Trigger

User sagt:
- "plan noch tiefer ausbauen"
- "mach ausführlicher"
- "das reicht nicht, geh tiefer"
- "expandiere das"

## Pattern-Struktur (Gesamtplan)

Ein "tief ausgebaute" Plan hat diese zusätzlichen Meta-Elemente:

### Task 0: Backup-Layer
Vor ALLEN Mutationen ein vollständiges Backup + Restore-Script:

```bash
BACKUP_DIR=~/.hermes/backups/YYYY-MM-DD-pre-hardening
mkdir -p "$BACKUP_DIR"

# Skills-Snapshot
find ~/.hermes/skills -name "SKILL.md" -print0 | tar czf "$BACKUP_DIR/skills-snapshot.tar.gz" --null -T -

# Config-Snapshots
cp ~/.hermes/SOUL.md "$BACKUP_DIR/soul-snapshot.md"
crontab -l > "$BACKUP_DIR/cron-snapshot.txt"

# Restore-Script
cat > "$BACKUP_DIR/restore.sh" << 'EOF'
#!/bin/bash
set -euo pipefail
SNAP="$HOME/.hermes/backups/YYYY-MM-DD-pre-hardening/skills-snapshot.tar.gz"
TARGET="$HOME/.hermes/skills"
[[ -f "$SNAP" ]] || { echo "Snapshot not found"; exit 1; }
echo "Files in archive: $(tar tzf "$SNAP" | wc -l)"
read -p "Continue? (yes/no): " confirm
[[ "$confirm" == "yes" ]] || exit 1
tar xzf "$SNAP" -C "$TARGET"
echo "Restored."
EOF
chmod +x "$BACKUP_DIR/restore.sh"

# Manifest
cat > "$BACKUP_DIR/MANIFEST.md" << 'MANIFEST'
# Backup Manifest
Enthält: skills-snapshot.tar.gz, soul-snapshot.md, cron-snapshot.txt, restore.sh
Erstellt: YYYY-MM-DD
MANIFEST
```

### Risiko-Matrix (pro Task)

| Kategorie | Risiko | Mitigation |
|---|---|---|
| author-fix | sehr niedrig | Default "Hermes Agent" ist etabliert |
| version-fix | niedrig | "1.0.0" ist SemVer-valid |
| period-fix | mittel | Manual spot-check 5 random Files; Rollback via tar |
| description-trunc | mittel-hoch | Dry-run + manuelles Review |

### Per-Task Validation

Jeder Task endet mit konkreten Commands + Expected Output:

```bash
# Test 1: Verifikation
python3 /tmp/audit_skills_v2.py | grep "TOTAL real"
# Expected: vorher 70-90, nachher <20

# Test 2: Kein SKILL.md ist corrupted (startet mit ---)
for f in $(find ~/.hermes/skills -name SKILL.md); do
    head -1 "$f" | grep -q "^---$" || echo "CORRUPT: $f"
done
# Expected: keine Ausgabe
```

### Rollback Plan

```bash
# 1. Skills komplett zurücksetzen
bash ~/.hermes/backups/YYYY-MM-DD-pre-hardening/restore.sh

# 2. Configs zurücksetzen
cp ~/.hermes/backups/YYYY-MM-DD-pre-hardening/soul-snapshot.md ~/.hermes/SOUL.md

# 3. Cronjobs entfernen
cronjob action=remove --job-id=<job-name>
```

### Dependency Diagram

```
Task 0 (Backup)
    ↓
Phase A: A1 → A2 → A3
    ↓
Phase B: B1 → B2 → B3 → B4
    ↓
Phase C: C1 → C2 → C3
```

## Decision Clarity

Wenn der Plan Entscheidungspunkte hat die der User treffen muss:

```markdown
## Open Questions (vor Execution)

### Entscheidung 1/4 — Phase A Scope
Soll fix-fm descriptions automatisch kürzen?

**Empfehlung:** Ja, auf ≤200 chars. Konsistenz mit house-style, Risiko gering.
```

Dann jedes als `clarify(choices=[...])` — Choices nie in Prosa vergraben.

## Pitfalls

- **Zeit-Schätzung nicht zu optimistisch** — Plan von 43KB mit 12 Tasks brauchte ~55min bei inline Execution (nicht Subagent).
- **"Kein Backup" ist ein Fail-Kriterium** — Task 0 muss erster Schritt sein, nicht nachgedacht.
- **Rollback nur mit Backup möglich** — Ohne Snapshot kein selektives Rollback pro Kategorie.