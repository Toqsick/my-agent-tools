---
name: obsidian-vault-sync
description: |
  Use when designing, scheduling, operating, or auditing synchronization between Mnemosyne memories and an Obsidian vault, including the daily bridge and conflict handling.
  NOT for general Obsidian note editing, syncing the .obsidian configuration directory, or copying low-confidence and session-ephemeral memories into the vault.
  Defines a three-phase, MOC-driven memory and vault sync architecture with eligibility filters, cron triggers, worker responsibilities, and deduplication safeguards.
platforms:
- linux
- macos
version: 1.0.0
author: Yuno
license: MIT
lane: worker-flash
reasoning_effort: high
tags:
- obsidian
- mnemosyne
- sync
- vault
- knowledge-base
trigger_keywords: ['obsidian', 'vault', 'memories', 'designing', 'scheduling']
keywords: ['obsidian', 'vault', 'memories', 'designing', 'scheduling']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['obsidian-vault-cluster-operations', 'obsidian', 'vault-gemini-cluster-worker']
---

# Obsidian Vault Sync

Bidirektionaler Sync zwischen Mnemosyne (private Memory, agent-intern) und Obsidian Vault (Bastis Wissensbasis, read-only per second-brain Skill). Drei Phasen mit klaren Triggern.

## Vault-Pfad

Default: `~/Dokumente/Obsidian Vault/`. Tagesform via `OBSIDIAN_VAULT_PATH` ENV überschreibbar. Backup-Pfad: `/mnt/DATA/_Archives/Dokumenten-BackUp/`.

## Phase 1 — Mnemosyne → Vault (Wissen sichern)

**Trigger:** Sonntags 04:00 (parallel zum Memory-Weekly-Consolidate).

**Was wandert:** Nur Memories mit `importance >= 0.7`, `scope = "global"`, `veracity = "stated"`, `source in ("insight", "fact", "identity", "preference")`. Rejects: 7-Tage-stale-Facts (PR/Issue/Commit-SHA), Session-Logs, Task-Progress, private conversation-Memories.

**Wo im Vault:** `04 Bereiche/Mnemosyne Highlights/`. MOC-getrieben. Format: `mnemosyne-{short-id}-{topic}.md`. Frontmatter: `id`, `importance`, `source`, `created`, `tags`.

**Worker:** `obsidian-vault-cluster-operations` Subagent-Pattern (Queen-Bee + 1 Worker, lese Mnemosyne → schreibe Vault). Worker bekommt genau 10 IDs pro Run (Batch-Limit), damit Output-Bomb-Risiko begrenzt.

**Risiko:** Schreibkonflikte (Flock notwendig). Skript: `~/50-System/bin/mnemosyne-to-vault.sh` mit `@ flock /var/lock/mnemosyne-vault.lock`.

**Cron:**
```
0 4 * * 0 /home/bratan/.hermes/hermes-agent/venv/bin/python3 /home/bratan/50-System/bin/mnemosyne-to-vault.sh >> /home/bratan/logs/mnemosyne-vault-sync.log 2>&1
```

## Phase 2 — Vault → Mnemosyne (Recall verbessern)

**Trigger:** Manuell via `/vault-sync` Slash-Command (geplant, noch zu implementieren). Initial-Trigger-Backlog: alle Notes in `02 Inbox/` und MOC-Dateien (`MOC - *.md`).

**Was wandert:** Inbox-Notes, MOC-Dateien, alle Notes mit Wiki-Linking-Dichte ≥ 4. Pro Note: `mnemosyne_remember` mit Source `vault-import`, Importance 0.5, Scope `global`. Batch-Limit: 20 Notes pro Run.

**Worker:** obsidian skill + mnemosyne_remember batch. Frontmatter-Extraktion (tags, created, status) für strukturierten Mnemosyne-Eintrag.

**Filter:** Nur Notes älter 1h, neuer als 7d. Verhindert Re-Import gerade geschriebener Notes und schließt archivierte Altlasten aus.

**Slash-Command:** `~/.hermes/skills/yuno/yuno-slash-vault-sync/SKILL.md` (TODO, noch anzulegen).

## Phase 3 — Daily-Bridge

**Trigger:** daily-note-cron.sh (0 6 \* \* \*). Nachdem die Daily erzeugt/geheilt wurde, am Ende des Cron-Skripts: `mnemosyne_remember` mit Tages-Summary (nicht komplette Daily, nur 3-5 Sätze Key-Facts).

**Format:** `content` = "Daily {date} {mood}/{energy}: {3-5 line summary of 'Was lief' section}". Importance 0.4, Source `task`, Veracity `tool`. Verhindert Token-Bomb: nur Summary, nicht 5 KB Daily komplett.

**Risiko:** Cron-Mode-Safety (`mnemosyne_remember` ist safe, kein Rekursionsproblem). Aber: `mnemosyne_remember` triggert keine weiteren Crons.

**Patch:** in `~/50-System/bin/daily-note-cron.sh` nach dem Quality-Gate-Aufruf einfügen:
```bash
python3 -c "
import sys; sys.path.insert(0,'/home/bratan/.hermes/hermes-agent')
from hermes_memory import remember
# Daily-Pfad + Key-Content extrahieren
remember(content=summary, importance=0.4, source='task', veracity='tool')
" >> $LOG 2>&1
```

## Validation Gates

- **Quality-Gate für Vault-Output:** EmDashes ≤1 pro Note, Boldface=0 in Hauptsektion, InlineHdr=0, WikiLinks ≥3.
- **Idempotenz:** Vault-Notes mit gleicher Mnemosyne-ID werden nicht dupliziert (File-Exist-Check vor write).
- **Backup vor Sync:** Vor Phase-1-Run: `rsync` Snapshot von Vault nach `/mnt/DATA/_Archives/Dokumenten-BackUp/`. Pattern etabliert 2026-07-20 (`obsidian-phantom-2026-07-20`).

## Pitfalls

- **Pitfall #36** (Mnemosyne-ID-Halluzination): Bei manuellen Subagent-Dispatches muss die Queen den `mnemosyne_get` Anker-Check machen, bevor der Worker den nächsten Run startet.
- **Vault-Resize-Risiko:** Backup ist 23 MB, Rsync-Sync pro Run sollte unter 5 MB bleiben. Bei > 10 MB Schreib-Volumen: Batch halbieren oder Run pausieren.
- **Cron-Recursion:** Phase 3 darf keine neuen Crons triggern. `mnemosyne_remember` ist safe.

## Status 2026-07-21

- **Phase 1:** Geplant, nicht implementiert. Crontab-Eintrag steht aus.
- **Phase 2:** Slash-Command TODO.
- **Phase 3:** daily-note-cron.sh Patch TODO.
- **Architektur-Entscheidung:** Sync läuft NICHT live, sondern batch-weise (Cron + manuell). Begründung: Basti arbeitet abends, Sonntags-Run trifft aktive Tagesabschlüsse.
