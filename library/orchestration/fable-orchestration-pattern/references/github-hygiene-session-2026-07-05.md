# GitHub-Hygiene Session 2026-07-05 — Referenz

## Session-Spezifische Details (nicht für Wiederholung, sondern zur Validierung des Patterns)

### Setup
- 34 GitHub-Repos inventarisiert (6 original Toqsick, Rest Forks/Stale)
- 30 lokale Clones
- A/B/C/D Entscheidungsmatrix für Fortführung

### A3 B3 C1 D2 (Bastis Wahl)
- A3 = Full aggressive cleanup (alles aufräumen, löschen, SSH)
- B3 = Fable 5 triage + execution by M3
- C1 = P0 first, then parallel
- D2 = Weekly recurring

### P0 Token Leak (reale Gefahr!)
- `gho_2X...Lz1g` Token in `hermes-v7-orphan/.git/` in `gh auth status` History geleakt
- Token war **aktiv** (gh auth status zeigte gültigen User Toqsick)
- **Sofort-Maßnahmen:**
  1. Token via Browser revoken (gh CLI hat kein Revoke-Command)
  2. SSH-Migration ALLER Repos die vorher Token nutzten
  3. Dirty-Files-Check in allen 30 lokalen Clones
  4. `notes.md` mit Passwort `password123` → .gitignore (Commit verhindert)
- **Lesson:** Bei jedem GH-Hygiene-Run: `grep -r "gho_" ~/ --include="*" 2>/dev/null | head -5`

### SSH-Migration
- 3 weitere Clones auf SSH umgestellt (zusätzlich zum bereinigten orphan)
- Workaround für fehlenden `delete_repo` Scope: Forks auf ARCHIVE taggen statt löschen
- 11 Forks archiviert, 4 warten auf Browser-Löschung

### Fable 5 CLI Bug
- `--bare` Flag zum Claude CLI überspringt OAuth/Keychain
- Resultat: "Not logged in · Please run /login"
- Fix: `--bare` weglassen (der angebliche $0.05 Cache-Kaltstart ist vernachlässigbar)
- `--max-turns 3` → Fable bekommt 0 Antwort-Turns → "Reached max turns"
- Output in `docs/system/schwarm-github-hygiene-2026-07-05/`

### M3 xhigh Subagenten
- 2 lokale Subagenten parallel: greyscripts-Analyse + hermes-v7-Clone-Bereinigung
- 5 M3 xhigh parallel für Refactor-Analyse (Clone-Sync, Dedup, xmem, Dir-Structure, CI)
- Alle 5 subagierten erfolgreich parallel
