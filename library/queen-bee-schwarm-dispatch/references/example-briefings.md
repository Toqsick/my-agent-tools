# Original-Briefings vom 2026-07-10 Schwarm

> Diese Datei enthält die **echten Original-Briefings** aus den ersten Yuno-Schwarm-Wellen. Beim nächsten Mal als Template verwenden — zeigt was funktioniert hat (kurz, präzise, Self-Verify-Pflicht).

---

## Welle 1 / Biene 1A — Dataview-Doku-Drift fixen

**Outcome:** 4 Skill-Patches erfolgreich, alle verifiziert.

```text
Kontext: 10 MOCs + 3 Skills behaupten "Dataview nicht installiert" — Plugin ist real installiert (community-plugins.json + .obsidian/plugins/dataview/main.js 2.3 MB).

DEINE TASKS:
1. Lies /home/bratan/Dokumente/Obsidian Vault/.obsidian/community-plugins.json + ls .obsidian/plugins/dataview/
2. Lies MOC - KI-Architektur + MOC - Obsidian-Vault + ~/.claude/skills/second-brain/SKILL.md
3. EXECUTE FIX:
   - Fall A: Plugin aktiv + Doku falsch → PATCH die Doku mit patch() (NICHT Vault-MOCs, die brauchen Genehmigung)
   - Erlaubte Writes: ~/.hermes/skills/{note-taking/,obsidian-vault/}
4. VERIFY: grep -r 'installiert' ~/.hermes/skills/

OUTPUT (max 500 Wörter):
- ## Befund (Plugin-Wahrheit vs. Doku)
- ## 4 Patches mit Quote
- ## Verify-Live-Result
- ## 10 MOCs die Basti-Genehmigung brauchen
```

**Warum das funktioniert hat:** Briefing war unter 500 Wörter, Self-Verify-Pflicht war konkret (grep), Write-Pfade waren explizit erlaubt + Tabu war explizit (MOCs).

---

## Welle 1 / Biene 1C — `/api/cron-status`-Endpoint in `yuno-dashboard`

**Outcome:** Endpunkt live, smoke-test grün (13 Jobs, summary konsistent zu `hermes cron list`).

```text
Kontext: yuno-dashboard hat /api/data, /api/history, /health. Cron-Status fehlt.

DEINE TASKS:
1. Lies /home/bratan/10-Projekte/10-active/yuno-dashboard/server.py KOMPLETT + README
2. ENTSCHEIDE Architektur: (a) hermes cron list JSON, (b) ~/.hermes/cron-output/, (c) ~/.hermes/cron/{db,jobs.json}. Wähle robust.
3. EXECUTE: Patch server.py mit patch() (NICHT write_file, weil andere Endpoints existieren)
4. NICHT TUN: service-restart, pip-install, dep-update.
5. VERIFY: `python3 -m py_compile server.py` + `cat server.py | grep -A20 'cron-status'`

OUTPUT (max 600 Wörter):
- ## Architektur-Wahl + Begründung
- ## Diff / neuer Endpoint
- ## curl-Test-Anleitung
- ## Caveats (restart nötig?)
```

**Warum das funktioniert hat:** Konkrete "NICHT TUN"-Liste verhindert Over-Reach. Architektur-Entscheidung wurde Biene überlassen (sie hat `~/.hermes/cron/jobs.json` gewählt — robuster als CLI-Parse).

---

## Welle 2 / Biene 2A — Single-Writer-Skill

**Outcome:** 8.1 KB Skill geschrieben mit Frontmatter, Single-Writer-Tabelle, POSIX-Lock-Strategy.

```text
Kontext: Biene 3 (W0) fand: Claude Code + Yuno/Hermes schreiben beide in Vault, kein Locking.

DEINE TASKS:
1. Lies /home/bratan/.claude/skills/second-brain/SKILL.md KOMPLETT
2. Lies /home/bratan/.hermes/skills/note-taking/system-documentation/SKILL.md (Sektion Obsidian-Vault-Modus)
3. EXECUTE: Erstelle /home/bratan/.hermes/skills/collaboration/single-writer-inbox/SKILL.md
   (mkdir -p davor) — YAML-Frontmatter + 3-Rollen-Tabelle + Lock-Strategy
4. VERIFY: file existiert + cat für stichprobe.

OUTPUT (max 500 Wörter):
- ## Geschriebener Pfad
- ## Inhalt-Outline
- ## Verify (ls + head)
- ## Welche Lücken offen
```

---

## Welle 2 / Biene 2C — TokenTelemetry-Reaktivierungs-Audit

**Outcome:** 1.1 GB eingefroren, ~5 Wo stale. Recommendation: Upstream-Plugin statt lokaler Reaktivierung.

```text
Kontext: Biene 2 (W0) fand: TokenTelemetry-Fork seit 06.06. eingefroren. Eigener Code (1.1 GB) — Frage Reaktivierung?

DEINE TASKS (READ-ONLY + kleine Edits):
1. ls -la /home/bratan/10-Projekte/10-active/tokentelemetry/ (top 15)
2. cat README.md | head -50
3. find -name 'STATUS.md' / 'CHANGELOG.md'
4. ls .git 2>&1 + cd && git log --oneline -10
5. grep -rE 'ingested' --include='*.md' --include='*.py'

OUTPUT (max 600 Wörter):
- ## Aktueller Code-Stand (Branch, letzte Commits, README-Summary)
- ## 3-5 Schritte zur Reaktivierung
- ## Cross-Links mit Yuno-Dashboard/Hermes
- ## Recommendation: Reaktivieren? Konservieren? Löschen?
```

**Pitfall-Vermeidung hier:** Reine READ-Anweisung mit 1-2 erlaubten Inspections (git log). Kein pip, kein Branch-Switch. Biene hat alles korrekt dokumentiert.
