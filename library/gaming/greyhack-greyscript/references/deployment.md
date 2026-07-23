# GreyHack Tool Deployment — Installer-Workflow

## CRITICAL: 4 Deployment Rules (verifiziert V0.9.6771-beta)

1. **`//command:` Marker PFLICHT** — Jede `.src` Datei muss `//command: <name>` als ERSTE Zeile haben. Ohne diesen Marker wird das Script nicht als Command registriert.
2. **Quelle in `Config/` ablegen** — Scripts in `/home/<USER>/Config/` werden automatisch als Shell-Commands erkannt. Scripts im Home-Verzeichnis-Root (`/home/<USER>/`) NICHT.
3. **Game-Restart ERFORDERLICH** — Neue `//command:` Scripts registrieren sich NUR beim Login. SQLite-Injection während das Spiel läuft wird erst nach Quit→Reload aktiv.
4. **DB-Backup VOR jeder Injection** — GreyHack korrumpiert die DB bei inkonsistenten Einträgen. IMMER zuerst: `cp GreyHackDB.db GreyHackDB.db.bak`

**Siehe auch:** `greyhack-greyscript` → Referenz `references/build-command-internals.md` für alle `build`-Error-Messages.

## Problem

GreyScript hat KEINEN `HTTP.Request()` Befehl. Das Spiel kann nicht direkt vom Host herunterladen. Alle Tools müssen entweder:
1. Per greybel-js Installer ins Spiel gebracht werden
2. Manuell per Copy-Paste in den In-Game Editor eingefügt werden
3. Direkt in die SQLite-DB injiziert werden

## Weg 1: greybel-js Installer (empfohlen)

### Voraussetzungen
- `greybel-js` installiert: `npm install -g greybel-js`
- Node.js PATH gesetzt: `export PATH="$(npm prefix -g)/bin:$PATH"`

### Schritt 1: Installer generieren

```bash
cd ~/greyhack-tools
greybel build launcher.src --installer --uglify --ingame-directory /home/Bratan/bin
```

Output: `build/installer0.src` (eine einzelne Datei, <160K Zeichen)

### Schritt 2: Ins Spiel kopieren

**Host:**
```bash
cat build/installer0.src | xclip -selection clipboard
```

**Im Spiel:**
1. `cat > /home/Bratan/bin/installer.src` — Inhalt einfügen (`Ctrl+V`), Enter, **Strg+C** zum beenden
2. `build /home/Bratan/bin/installer.src /home/Bratan/bin/installer`
3. `installer`
4. `cp /home/Bratan/bin/zKsav/*.src /home/Bratan/bin/` (greybel-uglify legt Dateien in Unterordner ab)
5. `build /home/Bratan/bin/build_all.src /home/Bratan/bin/build_all` + `build_all /home/Bratan/bin` + `launcher`

### Schritt 3: Kompilieren & ausführen

```
build /home/Bratan/bin/installer.src /home/Bratan/bin/installer
installer
```

Der Installer erstellt automatisch alle `.src`-Dateien und kompiliert sie.

## Weg 2: Manueller Copy-Paste (für einzelne Dateien)

Für Dateien <160K Zeichen:

**Host:**
```bash
cat /home/bratan/greyhack-tools/lib_core.src | xclip -selection clipboard
```

**Im Spiel:**
```
cat > /home/Bratan/bin/lib_core.src
```
→ Inhalt einfügen (`Ctrl+V`), Enter, **Strg+C** zum beenden

```
build /home/Bratan/bin/lib_core.src /home/Bratan/bin/lib_core
```

Alternativ: CodeEditor (GUI) im Startmenü öffnen, Datei erstellen, Inhalt einfügen, speichern.

## Weg 3: SQLite-Injektion (für Persistenz)

Siehe `greyhack-hermes-api` Skill, Abschnitt "Stufe 3 — Hermes als In-Game-Computer".

## Wichtige Limits

- Max 160.000 Zeichen pro `.src`-Datei im Spiel
- Max ~250 Dateien pro Ordner
- Max 3125 Dateien/Ordner pro Computer
- Nach Spielneustart sind alle Binaries weg (nur RAM) — `.src`-Dateien bleiben

## Fehlerbehebung

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| `undefined identifier: 'HTTP'` | `HTTP.Request` verwendet | GreyScript hat kein HTTP — Installer verwenden |
| `File too large` | >160K Zeichen | Mit `greybel --uglify` minifizieren oder aufteilen |
| `build: can't find` | Pfad falsch | Absolute Pfade verwenden: `/home/Bratan/bin/...` |
| `command not found` nach Neustart | Binary im RAM | `.src` neu kompilieren mit `build` |
