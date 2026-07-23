---
name: single-writer-inbox
title: Single-Writer-Regel für Obsidian-Vault /02 Inbox/
description: "Use when multiple agents (Hermes/Yuno, Claude Code second-brain, or external tools) need to write notes into the Obsidian Vault /02 Inbox/ directory and concurrent sessions risk race conditions, lost edits, or template-frontmatter collisions. Apply the single-writer rule (file-lock + writer-audit-log). NOT for read-only access to existing notes, MOCs, or .obsidian/ config (those don't need locking)."

version: 1.0.0
author: Hermes Agent (Welle-2 Biene A)
triggers:
  - Agent will in /home/bratan/Dokumente/Obsidian Vault/02 Inbox/ schreiben
  - Parallele Sessions/Agenten aktiv (Claude Code second-brain + Hermes/Yuno)
  - 'Wer darf in den Vault schreiben? / Inbox Locking'
  - Nach Crash oder fehlenden Notizen in 02 Inbox/
  - Vor jedem Schreibvorgang eines neuen Agent-Typs in den Vault
lane: koenigin
reasoning_effort: high
agent: Writer
license: MIT
trigger_keywords: ['need', 'notes', 'obsidian', 'writer', 'multiple']
keywords: ['need', 'notes', 'obsidian', 'writer', 'multiple']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['obsidian-subagent-briefing-template', 'obsidian-vault-sync']
---
# Single-Writer-Regel — Obsidian Vault `/02 Inbox/`

Verbindliche Schreib-Regel für **alle KI-Agenten** (Hermes/Yuno, Claude Code
second-brain, externe Tools), die Notizen nach
`/home/bratan/Dokumente/Obsidian Vault/02 Inbox/` ablegen wollen.

Hintergrund: Welle-0-Audit vom 2026-07-10 ergab, dass **Claude Code** (Skill
`second-brain` unter `~/.claude/skills/second-brain/`) und **Hermes/Yuno**
(Skill `system-documentation` unter
`~/.hermes/skills/note-taking/system-documentation/`) parallel auf denselben
Vault schreiben. Ohne Locking drohen konkurrierende Notes, Race-Conditions bei
Templater-Frontmatter (`datum`, `prioritaet`) und verlorene Edits.

## Vault-Pfad & Guard

```bash
V="/home/bratan/Dokumente/Obsidian Vault"   # Zorin/Ubuntu deutsches Locale
INBOX="$V/02 Inbox"
LOCK="$INBOX/.writer.lock"
AUDIT="$INBOX/.writer-audit.log"
TPL="$V/_templates/Inbox-Note.md"
```

Pfad-Resolution VOR jedem Schreiben via `ls -d "$V"` verifizieren — niemals
`~/Documents/Obsidian Vault/` (eng) oder `~/Documents/` annehmen.

## Single-Writer-Zuweisung

Pro Zeitschlit **maximal EIN Writer-Pfad aktiv** (lastwrite-wins
mit nachvollziehbarem Audit-Trail).

| Rolle | Agent-Prozess | Schreib-Pfad erlaubt | Schreib-Pfad verboten |
|---|---|---|---|
| **Single-Writer** | `Claude Code` mit Skill `second-brain` (Foreground-Session) | `02 Inbox/`, `99 Capture/`, `06 Daily Notes/` | `01 Kontext/`, `03–05/`, `07–08/`, MOCs, `.obsidian/` |
| **Single-Writer (Backup)** | `Hermes/Yuno` mit Skill `system-documentation` (Foreground-Session) | gleich wie oben — aber NUR wenn Claude-Pfad frei | gleich wie oben |
| **Read-only-Konsumenten** | jeder Agent | `01–09/`, MOCs, `.obsidian/`, Templates (nur lesen!) | jedes `.md` außerhalb der Inbox |

**Gleichzeitige Schreibvorgänge zweier Foreground-Sessions auf dieselbe Datei
sind verboten.** Wer zuerst den Lock hält, schreibt; der zweite Writer
schreibt in eine eigene Datei (`YYYY-MM-DD - <topic> - <agent>.md`), niemals
überschreibend.

## Locking-Strategie

Atomares File-Lock auf POSIX `mkdir`-Basis (kein `flock` nötig):

```bash
# 1. Lock holen (mit PID + Timestamp + Host)
ACQUIRE() {
  local pid=$$ host=$(hostname) ts=$(date -Iseconds)
  if mkdir "$LOCK" 2>/dev/null; then
    echo "$ts pid=$pid host=$host" > "$LOCK/writer.id"
    return 0
  fi
  return 1   # Lock existiert → anderer Writer aktiv
}

# 2. Schreiben + Audit-Eintrag (immer EIN letzter write)
WRITE_AND_AUDIT() {
  local file="$1" agent="$2" topic="$3"
  local ts=$(date -Iseconds)
  echo "[$ts] writer=$(cat "$LOCK/writer.id" 2>/dev/null || echo unknown) \
agent=$agent file=$(basename "$file") topic=\"$topic\" \
op=append size=$(wc -c < "$file")" >> "$AUDIT"
}

# 3. Lock freigeben (am Session-Ende, IMMER)
RELEASE() {
  rm -f "$LOCK/writer.id"
  rmdir "$LOCK" 2>/dev/null
}
```

**Lock-Lebensdauer:** hält maximal für die Dauer **einer** Foreground-Session.
Beim Crash bleibt der Lock liegen — Recovery: `rmdir "$LOCK"` nach
Plausibilitäts-Check (`cat "$LOCK/writer.id"` zeigt PID/Host).

**Stale-Lock-Detection:** `pid=$(grep -oE 'pid=[0-9]+' "$LOCK/writer.id")`,
`ps -p "${pid#pid=}" >/dev/null && echo ACTIVE || echo STALE`.

## Format-Konventionen (Wiki-Links + Dataview-konform)

Pflicht-Frontmatter aus `_templates/Inbox-Note.md`:

```yaml
---
tags:
  - inbox
  - quick-pickup
  - <agent-tag>      # claude-code | yuno | hermes | manuell
datum: YYYY-MM-DD
quelle: <Prozess-Name>   # z.B. "Claude Code (Fable 5)" oder "Yuno/Hermes"
prioritaet: niedrig | mittel | hoch
---
```

**Wiki-Links:** mindestens **2 `[[Wiki-Links]]`** auf existierende Notizen
(Vault-Konvention: Link-Density ≥ 6,5 avg, keine verwaisten Notizen — siehe
`second-brain/SKILL.md` §"Dataview-Emulation").

**Dataview-Verträglichkeit:** Tags stehen ausschließlich im Frontmatter-Block
(nicht im Body); Dateinamen exakt `YYYY-MM-DD - Titel.md` (drei Leerzeichen
um den Bindestrich), damit `MOC - Inbox` `LIST from "02 Inbox"` korrekt
auflöst.

**Keine Edits an bestehenden Notizen, MOCs oder `.obsidian/`** — auch nicht
"kleine Fixes". Nur `02 Inbox/` + `99 Capture/` + `06 Daily Notes/` als
Schreibzonen. Sortierung/Inbox-Hygiene macht Basti manuell im Obsidian-UI.

## Pflicht-Sequenz vor jedem Schreibvorgang

1. **Lock prüfen** — `test -d "$LOCK" && echo BUSY || echo FREE`
2. **Wenn FREE:** `ACQUIRE` (mkdir `$LOCK`, `writer.id` schreiben)
3. **Wenn BUSY:**
   - Option A: warten (max 30 s, polling)
   - Option B: eigenen Dateinamen mit Agent-Suffix:
     `2026-07-10 - Open Items - claude.md`
4. **`WRITE_AND_AUDIT`** nach jedem Append/Write (Zeile in `.writer-audit.log`)
5. **`RELEASE`** am Session-Ende (nicht vergessen — sonst Lock bleibt liegen)

## Audit-Datei Format

`.writer-audit.log` (Plain-Text, append-only, eine Zeile pro Schreibvorgang):

```
[2026-07-10T10:22:01+02:00] writer=2026-07-10T10:22:01+02:00 pid=12345 host=zorin agent=claude-code file="2026-07-10 - X.md" topic="X" op=append size=1496
```

Sichtbar via `tail -n 50 "$AUDIT"` — Pflicht-Inhalt für nachträgliche
"Konfliktauflösung" wenn zwei Agenten parallel denselben Topic schreiben.

## Pitfalls

1. **Lock vergessen.** Wenn Session crasht bleibt `02 Inbox/.writer.lock/`
   liegen — nächster Writer muss `cat .writer.lock/writer.id` prüfen,
   dann `rmdir` wenn stale (PID nicht mehr aktiv).
2. **Pfad-Resolution-Bug.** `~` expandiert nicht in Strings mit Leerzeichen;
   immer `"$V"` (quoted) nutzen. Nie `cd` in Vault ohne vorher
   `ls -d "$V"` (Locales-Falle: deutsches vs englisches `Documents`).
3. **Frontmatter im Body statt YAML-Block.** Tags MÜSSEN in den
   Frontmatter-`tags:`-Block — sonst matcht `MOC - Inbox`
   `contains(file.tags, "inbox")` nicht.
4. **Wiki-Link-Anzahl < 2.** Vault-Konvention (second-brain §"Capture-Workflow")
   verlangt mindestens 2 `[[Links]]` pro neuer Inbox-Note. Sonst gilt die
   Note als "verwaist" nach `MOC - Obsidian-Vault` Audit-Logik.
5. **MOCs/`.obsidian/` editieren.** Streng verboten ohne explizite
   Basti-Anweisung — auch "kleine Header-Korrekturen". Konkurrenz-Risiko zu
   hoch.
6. **Lock-Konkurrenz bei zwei Read-only-Konsumenten.** Konsumenten dürfen
   lesen ohne Lock zu setzen — Lock nur für Schreibvorgang.
7. **Audit nicht appenden.** Wenn `WRITE_AND_AUDIT` vergessen wird, ist im
   Konfliktfall nicht nachvollziehbar wer wann geschrieben hat.

## Verify (manuell nach Setup)

```bash
# 1. Skill existiert + lesbar
test -f ~/.hermes/skills/collaboration/single-writer-inbox/SKILL.md && echo OK

# 2. Lock-Skript funktioniert (trocken, ohne echten Lock)
bash -c 'ACQUIRE(){ mkdir /tmp/.test-lock 2>/dev/null && echo GOT || echo BUSY; }; ACQUIRE'

# 3. Vault-Pfad korrekt aufgelöst
ls -d "$V" && test -d "$V/02 Inbox" && echo "INBOX_OK"

# 4. Audit-Datei leer bisher (oder erste Writes sichtbar)
wc -l "$AUDIT" 2>/dev/null || echo "AUDIT_NOT_YET_CREATED"
```

## Verwandt

- `~/.claude/skills/second-brain/SKILL.md` — Vault-Struktur, Recall, Capture-Workflow
- `~/.hermes/skills/note-taking/system-documentation/SKILL.md` §"Obsidian-Vault-Modus" + §"Post-Deployment Multi-Target Documentation Workflow"
- `~/Dokumente/Obsidian Vault/02 Inbox/MOC - Inbox.md` — Inbox-Konventionen
- `~/Dokumente/Obsidian Vault/_templates/Inbox-Note.md` — Pflicht-Template
- Welle-0-Audit-Bericht (2026-07-10): Konkurrenz-Risiko Claude Code ⇄ Hermes
