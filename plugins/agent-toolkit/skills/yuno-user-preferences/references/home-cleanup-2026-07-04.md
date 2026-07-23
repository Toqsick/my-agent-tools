# Home Cleanup 2026-07-04 — Scout Findings + Königin Structure Design

## Session Context
- Date: 2026-07-04
- Task: Home directory reorganization of /home/bratan/
- Basti's Philosophy: "Keep & Update, don't replace" — existing NAVIGATION.md from 27.06. was kept as backbone
- Workspace Convention: Basti explicitly wants Yuno to work in `~/.hermes/`, not in `~/Documents/` or other home dirs

## 4 Scouts — Summary

### Scout A — Top-Level Ordner (39 erfasst)
- 39 Top-Level-Ordner in ~/
- 7 tabu: `.hermes/`, `docs/`, `.gnupg/`, `.ssh/`, `.ollama/`, `.steam/`, `.wine/`
- Tote Ordner: cyberpunk-clips (leer), Documents (Duplikat), reports (leer), hermes-chat (Stubs)
- Hermes-Caches: hermes/ (20K, redundant zu .hermes/), hermes-chat/ (8K, tot)

### Scout B — Files in ~/ (56 Files, 42 inventarisiert)
- 13 Müll-Files, ~1.7 GB freigebbar
- Largest offender: hermes-backup-2026-06-12-090248.zip (1.35 GB)
- Doku-Files: README.md, DESCRIPTION.md, NAVIGATION.md → Meta-Cluster
- Multi-agent-frameworks-research.md (27 KB) → AI/Research

### Scout C — Dotfiles & Tool-Ordner (24 erfasst)
- Tabu-Kategorie: `.gnupg/` (private-keys-v1.d), `.gmail-organizer.json` (Klartext-Passwort!), `.chelper/config.yaml` (API-Key)
- Verwaist: `.llama-app/` (555M, kein laufender Prozess), `.cert/` (leer)
- Aktiv: `.yuno-cleaner/` (1.1G Backups), `.chelper/` (kaputt — opencode nicht in PATH)
- Secrets: Google OAuth `client_secret_*.json` in Yuno-Backups!

### Scout D — Repos & Projekte (28 erfasst, 14 Git)
- Hermes-V7-Familie: 5 Repos (wt, zorin, orphan, webui, desktop-companion) — Worktree-Cluster
- GreyHack-Toolchain: 4 Ordner (tools, greyscripts mirror, repos, docs) — tools+greyscripts sind Dubletten
- Yuno-Tools: 4 Separate (yuno-cleaner, cockpit, dashboard, voice-bot) — cockpit gehört in dashboard
- Cyberpunk: cp77-modding (1.2G aktiv), music (52K aktiv), clips (leer → löschen)
- Basti-Projekte: build/, projects/, github-mcp-server, linux-assistant, odysseus, workspace

## Königin Structure Design v2

### 6-Cluster Layout

```
00-Meta/        ← navigation.md, README, DESCRIPTION, MODEL_HANDOFF
10-Projekte/    ← 10-active/, 20-experimental/, 30-staging/, 40-archive/
20-Workspace/   ← Daily Driver (scripts, fix-scripts, Ausgaben, logs, tmp, voice-memos)
30-Library/     ← Read-Only (greyhack-repos, Calibre, LenovoLegionLinux, steam_backup_toolkit)
40-Media/       ← XDG-Standard bleibt (Bilder/Videos/Musik/Schreibtisch/Dokumente/Downloads)
50-System/      ← Maintenance (backups, bin, export)
99-Hidden/      ← Soft-Reference-Table (KEINE echten Files)
```

### Phase Plan
1. **Cleanup (3A)**: 13 Müll-Files löschen (~1.7 GB)
2. **Totes löschen (3B)**: 4 tote Ordner
3. **Umparken (3C)**: 2 große Files in richtige Ordner
4. **Move (3D)**: 28 Ordner in 4 Cluster migrieren
5. **navigation.md (3E)**: Neue Version schreiben
6. **Abnahme (4)**: Königin prüft, Symlinks/PATH prüfen, Alles läuft?

### Offen für Basti
- Schreibtisch/minimax hub (1.7 GB Installer) — löschen?
- tmp/youtube-transcript/*.wav (90 MB) — löschen?
- yuno-cockpit in yuno-dashboard integrieren?
- greyscripts vs greyhack-tools mergen?

## See Also
- `~/.hermes/notes/structure-design-v2.md` (12 KB, voller Struktur-Entwurf)
