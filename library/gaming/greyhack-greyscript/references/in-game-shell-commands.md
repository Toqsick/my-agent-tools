# In-Game Terminal Commands

> GreyHack hat KEINEN `edit` Befehl. Dateien werden im Terminal mit Standard-Unix-Befehlen verwaltet.
> Der GreyHack-Terminal (was du bei `username@host:~$` siehst) ist eine Unix-ähnliche Shell, NICHT eine GreyScript-REPL.

## Datei-/Verzeichnis-Management

| Befehl | Wirkung |
|--------|---------|
| `ls` | Dateien auflisten |
| `pwd` | aktuelles Verzeichnis zeigen |
| `cat <datei>` | Datei-Inhalt lesen |
| `cat > <datei>` | **Datei erstellen und Inhalt schreiben** (paste content, Enter, Strg+C zum beenden) |
| `rm <datei>` | löschen |
| `mv <quelle> <ziel>` | verschieben/umbenennen |
| `cp <quelle> <ziel>` | kopieren |
| `mkdir <verzeichnis>` | Ordner erstellen |
| `cd <verzeichnis>` | Verzeichnis wechseln |

## Prozesse & Rechte

| Befehl | Wirkung |
|--------|---------|
| `ps` | Prozesse anzeigen |
| `chmod <modus> <datei>` | Rechte ändern |
| `chown <user> <datei>` | Besitzer ändern |
| `chgrp <gruppe> <datei>` | Gruppe ändern |
| `sudo <cmd>` | als root ausführen |

## Sonstige Terminal-Befehle

| Befehl | Wirkung |
|--------|---------|
| `clear` | Terminal leeren |
| `exit` | Terminal schließen |
| `build <src> <bin>` | GreyScript-Datei kompilieren |
| `launcher` | Tool-Launcher starten |

## Netzwerk-Befehle

| Befehl | Wirkung |
|--------|---------|
| `ifconfig` | Netzwerk-Interfaces |
| `iwconfig` | WLAN-Interfaces |
| `iwlist` | WLAN-Netzwerke scannen |
| `whois <ip>` | Whois-Abfrage |

## CodeEditor (GUI)

Es gibt einen **CodeEditor** als GUI-Programm im Spiel (Startmenü / Desktop). Dort Dateien öffnen, Inhalt einfügen, speichern. Das ist die Alternative zu `cat > datei` für große Dateien.

## Wichtige Hinweise

- **Shell ≠ GreyScript.** `name = get_shell.get_name` direkt im Terminal gibt `name: command not found` — die Shell sieht `name` als Kommando. GreyScript-Code läuft NUR in `.src` Dateien, kompiliert mit `build`.
- **Build-Binaries sind flüchtig.** Nach jedem Spielneustart sind alle `build`-Binaries weg — sie werden nur im Arbeitsspeicher gehalten. Die `.src`-Source-Dateien müssen persistiert werden (per Installer neu erstellt oder in DB gespeichert).
