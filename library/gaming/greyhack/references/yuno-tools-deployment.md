# Yuno-Tools Deployment — In-Game Tools Directory (yuno-tools/)

## Overview

A second deployment directory lives **inside the game install folder**, separate from `~/greyhack-tools/` and `~/projects/greyhack-sandbox/`. This directory holds pre-built `.src` tools ready for copy-paste deployment.

**Canonical path:**
```
/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/yuno-tools/
```

## Contents (Standing as of 2026-06-25)

| Tool | Purpose |
|------|---------|
| `hardening_audit.src` | System security check (safe, read-only) |
| `strike1_dee_grettib.src` | Dee Grettib hack (Int:1, SSH PW: agle1) |
| `strike2_gabriellia_ingoody.src` | Gabriellia (Int:3) |
| `strike3_bobina_emmer.src` | Bobina (Int:3, PW: aaa) |
| `bank_grab.src` | Automated bank transfer |
| `multihop_strike.src` | Dee → LAN → Royal(ADMIN) multi-hop |
| `SESSION_HANDOFF.md` | Previous session state and next steps |

## Deploy Script

`yuno-deploy.sh` (in the same directory) provides a one-command deployment workflow:

```bash
bash /mnt/DATA/Programme/Steam/steamapps/common/Grey\\ Hack/yuno-deploy.sh
```

It does:
1. File presence check for all 6 `.src` files
2. Starts HTTP fileserver on port 8765 (if not already running)
3. Prints access URLs per tool

## Manual Fileserver Start (without deploy script)

```bash
cd /mnt/DATA/Programme/Steam/steamapps/common/Grey\\ Hack/yuno-tools
python3 -m http.server 8765
```

**Important:** Use `terminal(background=true)` for this — foreground with `&` is rejected by Hermes' terminal tool.

## Browser → CodeEditor — Manueller Copy-Paste Workflow (PRIMÄRE Methode)

**Das ist die wichtigste Deployment-Methode für Live-Sessions.** Der User hat GreyHack offen und kopiert Tools aus dem Browser. KEIN `wget`, KEIN `installer` — reiner Copy-Paste.

### Schritt-für-Schritt (genau so geben!)

#### Ein Tool deployen

1. **Browser öffnen** → `http://<LAN_IP>:8765/<toolname>.src`
   - Es öffnet sich ein Fenster/Tab mit rohem `.src` Code
2. **STRG+A** (alles markieren) → **STRG+C** (kopieren)
3. **In GreyHack:** Startmenü → Apps → **CodeEditor**
4. Oben links: **New** klicken (neues Dokument)
5. **STRG+V** — Code wird eingefügt
6. **Save** klicken
   - Dateiname: `<toolname>` (ohne `.src`-Endung — die hängt das Spiel dran)
   - Pfad: `/home/Bratan/` — einfach Enter drücken, Default ist das Home-Verzeichnis
7. **Build** klicken — warten bis "Build erfolgreich"
8. **Run** klicken — das Tool läuft

#### Mehrere Tools (3+ Browser-Fenster)

Wenn der User mehrere URLs öffnet und 3+ Browser-Fenster/Tabs offen hat:

1. **Ein Fenster nach dem anderen bearbeiten** — nicht zwischen Fenstern hin- und herspringen
2. **Fenster 1:** STRG+A → STRG+C → in CodeEditor → New → STRG+V → Save → Build
3. **Fenster schließen** (optional, reduziert Verwirrung)
4. **Fenster 2:** wiederholen
5. **Fenster 3:** wiederholen

**Wichtig:** Nie "mach alle drei gleichzeitig" sagen — immer sequentiell anleiten.

### Fallstricke

| Problem | Lösung |
|---------|--------|
| Browser zeigt nur HTML/Verzeichnis | Kein `.src` am URL-Ende — prüfen! |
| "Build fehlgeschlagen" | Syntax-Fehler im Source. Tool ist defekt → Bescheid sagen |
| "command not found" bei Run | Tool wurde nicht in `/home/Bratan/bin/` gebuildet → Pfad prüfen |
| CodeEditor zeigt leeres Dokument nach New | Auf "New" war gedrückt? Manchmal hängt der Editor — nochmal New klicken |
| User fragt "wo soll ich speichern" | `/home/Bratan/<toolname>` — einfach Enter, speichert automatisch im Home |

## Live-Session Onboarding Workflow

Wenn Basti fragt "kannst du mal durchschauen" oder eine Live-Coaching-Session startet:

1. **Explore** — `ls -laR` den game install dir, check `yuno-tools/`, `GreyHack_Data/GreyHackDB.db`
2. **Status report** — Tabelle aller Tools + Zweck + Sandbox-Toolkit
3. **Option list** — Was will er zuerst machen? (Hardening → Strike → Sandbox)
4. **Fileserver start** — `terminal(background=true)` auf `yuno-tools/`
5. **IP check** — `hostname -I` → LAN-IP filtern (nicht 172.*, nicht 127.*)
6. **URLs bereitstellen** — Jede URL `http://<LAN_IP>:8765/<tool>.src` nennen
7. **Coaching** — Schritt-für-Schritt: Browser → Copy → CodeEditor → Paste → Save → Build

### Browser-Fenster-Overload vermeiden

Der User öffnet URLs, die alle `.src` Dateien als Rohtext anzeigen. 3+ Fenster gleichzeitig = Verwirrung ("welche Datei war das?"). **Besser:** Nur 1-2 URLs gleichzeitig geben, den Rest nachfordern wenn er fertig ist.

### Tool-Reihenfolge für Neustart

Wenn der User ein neues Spiel startet (Player-Reset, Welt bleibt):

1. **Zuerst `hardening_audit`** — sicher, read-only, zeigt was auf dem eigenen PC los ist
2. **Dann `strike1_dee_grettib`** — einfachster NPC, schneller Erfolg
3. **Dann weiter:** strike2 → strike3 → bank_grab → multihop

Nicht alle 6 Tools auf einmal vorschlagen — überfordert. Schrittweise.

## New Game / Player Reset — World Verification

Wenn der User sagt "ich starte neues Spiel, lösche nur den Player, nicht die Welt":

### Was ich prüfen muss

```bash
# 1. GreyHackDB.db existiert und hat Größe (Welt-Daten)
ls -la "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db"

# 2. yuno-tools sind noch da
ls -la "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/yuno-tools/"

# 3. Game files intact
ls -la "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack.x86_64"
```

### Was sich ändert vs. bleibt

| Ändert sich (Player) | Bleibt (Welt) |
|---------------------|---------------|
| Neue IP-Adresse | ✅ NPC IPs (Dee, Gabriellia, Bobina) |
| Neues Geld/Konto | ✅ NPC Passwörter in der DB |
| Neue Hardware (Starter-PC) | ✅ Router Boonie Efanyanu |
| Skills zurückgesetzt | ✅ Firmengebäude mit Royal (Admin) |
| Neue User-Daten | ✅ `yuno-tools/` Ordner unberührt |

### Was ich antworten soll

Tabellarisch zeigen was noch da ist (DB-Größe, Tool-Anzahl, Game-Files). DB-Timestamp zeigt ob das Spiel gerade gespeichert hat (neuer Player wurde geschrieben). Wenn DB gewachsen ist — alles gut, Welt lebt.

## Typical First-Session Flow

```
1. Fileserver starten (background=true, port 8765)
2. LAN-IP checken → URLs zeigen
3. Tool 1 (hardening_audit): Browser → Copy → CodeEditor → Save → Build
4. User führt aus → live feedback von mir
5. Tool 2 (strike1_dee_grettib): gleiche Prozedur
6. User hackt Dee → ich geb IPs/Passwörter/Befehle live durch
7. Weiter mit loot/upgrade je nach Erfolg
```

## Relationship to Other Deploy Paths

| Path | Purpose | Method |
|------|---------|--------|
| `yuno-tools/` | Pre-built `.src` files in game directory | Manual copy-paste via browser |
| `~/greyhack-tools/` | Full toolset + source repos | greybel-js build pipeline + PC.wget |
| `~/projects/greyhack-sandbox/` | Python automation tools | Run on host, not in game |

## All-in-One Scripter Pattern (bei HDD-Knappheit)

**Problem:** GreyHack zählt binary-Größen absurd (5 KB Script → 5 GB binary). Wer 30+ Scripts in `/bin/` hat, sprengt die HDD (Standard 350 MB).

**Lösung:** Ein einziges `yuno.src` mit Sub-Commands (`run yuno scan/hack/loot/...`) ersetzt Dutzende Einzelscripts. Spart ~80 KB auf Disk UND ~200 GB in-game, weil nur EIN binary gebuildet wird.

**Pattern:**
```greyscript
cmd = params[0]
if cmd == "scan" then ... end if
if cmd == "hack" then ... end if
if cmd == "loot" then ... end if
// ... etc
```

Siehe `/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/yuno-tools/yuno.src` als Referenz-Implementierung (17 KB, 7 Befehle, greybel-buildable).

**Wann einsetzen:** Wenn der User "Speicherplatz knapp im Spiel" meldet oder `/bin/` viele Einträge hat. Vorher: `sqlite3 GreyHackDB.db "SELECT json_extract(FileSystem,'$')..." | python3` zur Inventur.