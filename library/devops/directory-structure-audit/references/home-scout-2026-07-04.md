# Home-Scout A — worked example: 39-folders audit

**Datum:** 2026-07-04
**Ausgangspunkt:** User bat um Klassifizierung aller 39 sichtbaren Top-Level-Ordner unter `/home/bratan`.
**Domäne:** Hermes auf Zorin OS 18.1, NVIDIA RTX 5060, modding/gaming/greyscript/hermes workspace.

## Verfahren

Der Scan folgte exakt dem Pipeline-Modell aus `directory-structure-audit/SKILL.md`.
Phase 6 (Reorganisation) wurde nicht ausgeführt — der Bericht war ausdrücklich read-only.

## Besondere Funde (über die Skill-Definition hinaus)

### Tabu-Bestätigung
- `~/.hermes/` (Yuno-Sandbox) — **nicht gescannt**, wie befohlen.
- `~/docs/` (Bastis Doku-Workspace) — **nicht gescannt**, wie befohlen.
- `~/.var/app/` (Flatpak Steam, 212 GB) — tabu, aber im Skript-Kontext erwähnenswert.

### Domänen-spezifische Erkennungsmerkmale (erweitert)

| Signal | Erkenntnis |
|--------|-----------|
| Ordner enthält `.hermes/`-Subdir | Hermes-Profil oder Hermes-Dev-Projekt |
| Ordner enthält `.ci-build/` | CI-getriebenes GreyScript-Projekt |
| Ordner enthält `__pycache__/` | Lokales Python-Projekt (nicht installiert) |
| Ordner enthält `node_modules/` | Node.js/npm-Projekt (Dev-Dependency) |
| Ordner enthält `.flutter-plugins-dependencies` | Flutter-App (Dart) |
| Ordner ist leer (nur `.` + `..`) | 🔴 tot — vermutlich nie befüllt oder geleert |
| Ordner nur mit PID-File (`bridge.pid`) | 🔴 tot — Hintergrundprozess-Reste |
| README.md + CHANGELOG.md + CONTRIBUTING.md | Professionelles/gepflegtes Projekt |
| DESCRIPTION.md + PLAN.md | User-eigenes Projekt mit Plan |

### Dead-Folder-Erweiterungen
Neben leeren Ordnern wurden erkannt:
- **PID-only** — `hermes-chat/bridge.pid` ohne lebenden Prozess
- **Schattenordner** — `Documents/` leer, aber `Dokumente/` (1,3 GB) aktiv → XDG-Duplikat
- **Singleton-File** — `cyberpunk-clips/` 4K, nie befüllt

### Größte Dateien im Home (Aufräum-Kandidaten)
| Datei | Größe | Quelle |
|-------|-------|--------|
| `~/hermes-backup-2026-06-12-090248.zip` | 1,3 GB | Hermes-Backup, veraltet |
| `~/Dokumente/libre-workspace.iso` | 987 MB | 2026-05-11, unklar ob noch gebraucht |
| `~/odysseus/cuda-repo-...deb` | 3,8 GB | CUDA-Installer, vermutlich nach Installation obsolet |
| `~/Schreibtisch/minimax hub/backup_MiniMax-Hub.tar.gz` | 679 MB | Installer-Backup, nach Setup obsolet |
| `~/Schreibtisch/minimax hub/MiniMax Hub Setup 1.0.7/` | 910 MB | Entpackter Installer |
| `~/Downloads/android-studio-...tar.gz` | 1,5 GB | Android Studio, ob gebraucht? |

### Dominante Cluster
1. **Hermes-Build** — 5 Varianten (v7-wt, v7-orphan, webui, webui-desktop-companion, zorin) = ~1,4 GB
2. **Yuno** — 4 Varianten (cleaner, cockpit, dashboard, voice-bot) = ~640 KB
3. **GreyHack** — 4 Varianten (tools, scripts, repos, docs) = ~36 MB
4. **Cyberpunk** — 3 Varianten (modding, clips-leer, music) = ~1,3 GB

### Besonderheit: README.md vs NAVIGATION.md vs DESCRIPTION.md
Das Home hatte **drei** separate Meta-Dokumente:
- `~/README.md` — Haupt-Landkarte, beschreibt jeden Ordner in thematischen Blöcken
- `~/NAVIGATION.md` — Schnellzugriff-Index (flacher, weniger Details)
- `~/DESCRIPTION.md` — Detail-Tabelle (Zweck, was gehört rein, was nicht)
Die drei stimmten meist überein, aber einzelne Abweichungen (z.B. `reports/` erwähnt aber leer) wurden im Bericht markiert.

## Nützliche Batch-Befehle

```bash
# 1. Sizes sorted
du -sh /home/bratan/*/ 2>/dev/null | sort -h

# 2. Batch ls -la of N ordners
cd /home/bratan && for d in <liste>; do echo "===== $d ====="; ls -la "$d" 2>&1 | head -20; echo; done

# 3. Check last mod times
stat -c '%y %n' /home/bratan/<ordner>/* 2>&1 | head -5

# 4. Cross-reference with home-level README
head -40 /home/bratan/README.md
head -50 /home/bratan/NAVIGATION.md
head -30 /home/bratan/DESCRIPTION.md

# 5. Check for DESCRIPTION inside each ordner
cat /home/bratan/<ordner>/DESCRIPTION.md 2>&1

# 6. Find all .git repos among folders
for d in <liste>; do
  if [ -d "/home/bratan/$d/.git" ]; then
    echo "+ $d (git repo)"
  fi
done
```

## Ergebnis
Eine 250-zeilige Markdown-Tabelle mit 39 Einträgen, 6 🔴 toten Ordnern,
Domaenen-Cluster-Analyse, 10 konkreten Aufräum-Vorschlägen, und einer
Beispiel-`navigation.md`-Vorlage für die zukünftige Struktur.
