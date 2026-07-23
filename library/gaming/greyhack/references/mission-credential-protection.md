# Mission Credential & Attack-Plan Protection

## Problem

GreyHack-Mission-Sessions produzieren **sensible In-Game-Daten** im Working-Tree eines lokalen Git-Repos:

- **Credentials**: `root:rocksons`, `root:pirelan`, SSH-Keys, Bank-PINs
- **Angriffspläne**: Step-by-Step-Exploit-Pläne pro IP
- **IP-Listen**: Alle bekannten aktiven Hosts im LAN
- **Build-Artefakte**: `build/yuno_v6.src` (45 KB) — kann revealed creds aus vorherigen Läufen enthalten

**DAS REPO IST ÖFFENTLICH.** `Toqsick/greyscripts` auf GitHub. Ein `git add .` + Commit leakt automatisch alle Credentials.

## Lebenszyklus (MaxClaw-Modell)

```
                   ┌─────────────────┐
                   │ Fileserver :8765 │
                   │ (dient nur der   │
                   │  Code-Auslieferung)│
                   └────┬────────────┘
                        │
  ┌────────────────────▼──────────────────┐
  │  ~/greyhack-tools/ Working Tree        │
  │  (öffentliches Git-Repo)               │
  │                                        │
  │  attack_tiers.src ──┐                  │
  │  attack_plan_tiers.txt ─┤              │
  │  build/yuno_v6.src ──┘  (SENSITIV)    │
  │                                        │
  │  greyhack-tools/ ← Code (öffentlich)   │
  └────────────────┬───────────────────────┘
                   │
                   ▼ (via .gitignore ignoriert)
        ┌─────────────────────┐
        │ Crons konsumieren   │  ← greyhack-tool-builder (alle 2h)
        │ die Daten           │    greyhack-db-watcher (alle 30min)
        │ und laden sie in    │    greyhack-knowledge-distiller (So 22h)
        │ Wissensgraphen      │
        └─────────────────────┘
                   │
                   ▼ (nach ~1h / nach Cron-Run)
            ┌──────────┐
            │ Archive, │  → ~/docs/system/greyhack-weekly-insights-*.md
            │ Löschen  │  → oder manuelle Entscheidung: was darf ins Repo?
            └──────────┘
```

**Faustregel:** "Bleiben nur ~1 Stunde lokal bis MaxClaw sie alle geladen hat." (Basti)

## .gitignore-Pattern (v3.0)

```gitignore
# --- v3.0-sensitivity: credentials/attack plans/mission drafts ---------------
# In-game logs that contain credentials, IPs, SSH commands — bleiben LOKAL bis
# der MaxClaw-DB-Watcher / Knowledge-Distiller sie gelesen und in MongoState
# konsolidiert hat. Die Mission-Datei ist ein 'draft', kein offizielles Artefakt.
/attack_plan_tiers.txt
/attack_tiers.src
/_drafts/
/mission_drafts/
# Build artefacts that may contain revealed creds/ssh-tokens
/build/
# Runtime caching files
/.last-ci-check
/.node-persist/
/xmem/
```

### Warum diese Pfade?

| Pfad | Warum sensitiv | Wann sicher löschbar |
|------|---------------|---------------------|
| `attack_tiers.src` | Enthält IP-Liste + SSH-Befehle | Nach Cron-Konsolidierung |
| `attack_plan_tiers.txt` | root-Credentials + Step-by-Step | Nach Cron-Konsolidierung |
| `build/` | yuno_v6.src (45 KB) — kann alte creds enthalten | Nach Build-Cleanup |
| `_drafts/` | Noch nicht geprüfte Missions-Drafts | Nach manuellem Review |
| `.last-ci-check` | Runtime-Cache, keine Creds | Sofort (nur Cache) |
| `.node-persist/`, `xmem/` | Runtime-State | Nach Session-Ende |

## Git-Workflow bei sensiblen Daten

### Push nur Code, keine Daten

```bash
# 1. GITIGNORE zuerst patchen — sensitive Files müssen ignored sein!
# 2. Dann git add NUR die nicht-sensitiven Änderungen:
git add greyhack-tools/ps/ps.src          # Code-Fix (öffentlich)
git add .gitignore                         # Schutzregeln (öffentlich)

# 3. Commit nur Code + gitignore:
git commit -m "fix(ps): beschreibung"      # KEINE sensitiven Files drin

# 4. Push
git push origin develop

# 5. Verifizieren: NUR Code auf GitHub
git diff origin/develop --name-only        # Sollte keine sensitiven Pfade zeigen
```

### Checkliste vor jedem Push

1. ✅ `.gitignore` enthält `/attack_tiers.src`, `/attack_plan_tiers.txt`, `/build/`
2. ✅ `git status` zeigt nur erwartete geänderte Files (keine `attack*`, `build/*`)
3. ✅ `git check-ignore -v` — bestätigt dass sensitive Files ignored sind
4. ✅ Working Tree sauber nach Push (`git status` → "nothing to commit")

## MaxClaw-Cron-Konsumierung

Die Crons die die sensiblen Daten verarbeiten:

| Cron | Frequenz | Was macht es mit den Daten? |
|------|----------|-----------------------------|
| `greyhack-tool-builder` | alle 2h | Baut Tools, liest `attack_tiers.src` in wiederverwendbare Module |
| `greyhack-db-watcher` | alle 30min | Überwacht DB-Änderungen, konsolidiert neue Targets |
| `greyhack-knowledge-distiller` | So 22h | Erstellt Weekly-Insights aus allen Quellen |
| `greyhack-mission-tracker` | alle 4h | Trackt Mission-Progress |

**Nach erfolgreichem Cron-Run** (`last_status: ok`): Die sensiblen Daten sind konsolidiert. Du kannst sie dann entweder:
- **Löschen** (wenn keine Wiederholung nötig): `rm attack_tiers.src attack_plan_tiers.txt`
- **Ins Repo committen** (nach manueller Prüfung, dass keine Creds drin sind): nur redacted/reine Struktur-Version
- **Archivieren** als `~/docs/system/greyhack-mission-<date>.md`

## Beispiel aus der Praxis (2026-07-04)

**Repository:** `Toqsick/greyscripts` (public) → Branch `develop`
**Auslöser:** Basti sagte "pushe grayhack tools in repo hinterher"
**Risk:** 4 unversionierte Files im Working Tree: `attack_tiers.src`, `attack_plan_tiers.txt`, `build/yuno_v6.src`, `.last-ci-check`

**Fix:**
1. `.gitignore` um 9 Schutzregeln erweitert
2. Nur `greyhack-tools/ps/ps.src` (Code-Fix NP-49/66/67) + `.gitignore` committed
3. Push zu `Toqsick/greyscripts/develop` (2 commits ahead)
4. Sensitive Files bleiben lokal orphan im Working Tree
5. Cron `greyhack-tool-builder` getriggert — konsolidiert Daten in Wissensgraphen
6. Mnemosyne-Eintrag: `grayhack-tools-repo protection 2026-07-04`

**Mnemosyne:** `grayhack-tools-repo protection 2026-07-04 ~05:54 — ~/greyhack-tools/ (Toqsick/greyscripts, develop branch): .gitignore Patch (00518a9) fuer 9 paths + runtime cache. Sensitive files bleiben lokal bis MaxClaw-DB-Watcher / Knowledge-Distiller sie konsolidiert.`
