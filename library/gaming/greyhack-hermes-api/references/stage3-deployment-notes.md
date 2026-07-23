# Stufe 3 Deployment-Notizen

> Aus der Session vom 06.06.2026 — konkrete Blocker und Workarounds für das In-Game-Deployment.

## Was funktioniert

- Hermes-Computer in `GreyHackDB.db` eingetragen (IP: `172.217.22.14`, MAC: `42:48:52:4D:45:53`)
- `Map`-Eintrag erstellt (Essid: `Hermes_AI`, AccessType: 1)
- Filesystem mit 5 Dateien + 2 Usern (root + hermes) in DB persistiert
- `hermes_daemon.src` erstellt (269 Zeilen, Tool 12 im Launcher)
- API-Server (Port 8333) und Temp-Fileserver (Port 8765) laufen auf Host

## Was NICHT funktioniert

### HTTP Bootstrap (blockiert)

**Annahme:** GreyScript könnte per `HTTP.Request()` vom Host herunterladen.
**Realität:** GreyScript hat **keinen** `HTTP.Request()` Befehl. Der Bootstrap-Ansatz mit einem Python-HTTP-Fileserver auf Port 8765 scheitert komplett.

**Folge:** Alle `.src`-Dateien müssen manuell ins Spiel gebracht werden:
1. `edit /home/Bratan/bin/<tool>.src` im Spiel öffnen
2. Code vom Host kopieren (`cat ~/greyhack-tools/<tool>.src`)
3. Im Spiel einfügen (`Ctrl+V`)
4. Speichern & schließen (`Ctrl+S`, `Ctrl+Q`)
5. `build /home/Bratan/bin/<tool>.src /home/Bratan/bin/<tool>`

### RAM-only Binaries

Nach jedem Spielneustart sind alle `build`-Binaries weg. Nur die `.src`-Source-Dateien bleiben erhalten (wenn sie in der DB oder im Spiel-Dateisystem persistiert wurden).

**Workaround:** `.src`-Dateien in der `Files`-Tabelle der DB speichern (Hash als ID, Content als Text). Dann sind sie nach Neustart noch da und können neu kompiliert werden.

## Getestete Ansätze

| Ansatz | Status | Ergebnis |
|--------|--------|----------|
| HTTP Fileserver (Port 8765) + Bootstrap | ❌ | GreyScript hat kein HTTP |
| SQLite-Injektion in `GreyHackDB.db` | ✅ | Computer + Map + Files eingetragen |
| Manueller Copy-Paste | ✅ | Funktioniert, aber mühsam für 14 Dateien |
| greybel-js Installer | 🔄 | Noch nicht getestet — vielversprechendster Weg |

## Nächster Schritt

`greybel-js` mit `--installer` aus `~/greyhack-tools/` generieren lassen. Das erzeugt eine einzelne `.src`-Datei, die alle Tools im Spiel automatisch erstellt — ohne HTTP, nur mit reinem GreyScript.
