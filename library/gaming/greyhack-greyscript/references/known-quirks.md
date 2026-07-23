# Known Quirks — Runtime-Bugs durch Sprach-Einschränkungen

> Aus der Bug-Search-Session vom 06.06.2026 — konkrete Bugs die bei Compile-ZEIT NICHT auffallen.

## Runtime-only Bugs (compile clean, crashen im Spiel)

| Funktion | Erwartung | Realität | Konsequenz |
|----------|-----------|----------|------------|
| `str_repeat(str, n)` | Python/MiniScript-Standard | **Existiert NICHT** | Runtime-Error bei Formatierung |
| `get_system_time()` | Timestamp als String | **Existiert NICHT** | Jeder Aufruf wirft Fehler |
| `is_folder` (File-Objekt) | Boolean wie `is_binary` | **Attribut existiert NICHT** | `not null = true` → zufällig ok |
| `"\n"` in Strings | Newline-Escape | **Literal `\n`** (2 Zeichen) | Log-Dateien kaputt, kein Linebreak |

**

### str_repeat — die unsichtbare Falle

GreyScript hat **keine** String-Wiederholung. `str_repeat` wirft einen
`undefined function`-Error erst zur Laufzeit, obwohl der Code kompiliert wird.

**Fix:**
```mini
space = function(n)
    if n < 0 then n = 0
    s = ""
    while s.len < n
        s = s + " "
    end while
    return s
end function
```

**Getroffene Dateien:** portscan.src (2x), backdoor.src (dieselbe Funktion)

---

### get_system_time — vollständig unbekannt

Wird oft fälschlich in Daemon-Skripten verwendet für Timestamps. GreyScript
hat **keine** Zeitfunktionen. Die offensichtliche Alternative `time()` existiert
gleichfalls nicht.

**Fix:** Statische Prefixe oder Counter verwenden:
```mini
entry = "[" + HERMES_NAME + "] " + msg
```

**Getroffene Dateien:** hermes_daemon.src

---

### is_folder auf File-Objekten

GreyScript File-Objekte haben:
- `is_binary` ✅
- `is_folder` ❌ (existiert NICHT)
- `get_content` ✅
- `set_content` ✅
- `chmod()` ✅ (gibt 1 zurück)

`result.is_folder` evaluiert zu `null`, `not null = true` → der Code läuft
zufällig durch, aber es ist ein versteckter Bug.

**Fix:** Nur `is_binary` prüfen, niemals `is_folder`:
```mini
if not result.is_binary then
    content = result.get_content
    if content then
        print(content)
    end if
end if
```

**Getroffene Dateien:** metaxploit.src

---

### "\n" statt char(10)

GreyScript interpretiert `"\n"` als zwei Literal-Zeichen (Backslash + n),
nicht als Newline. Das gilt auch für `"\t"` und andere Escape-Sequenzen.

**Fix:** `char(10)` für Newline, `char(9)` für Tab, `char(34)` für `"`:
```mini
line = "foo" + char(10) + "bar"
```

**Getroffene Dateien:** lib_core.src, backdoor.src, smtp_enum.src, hermes_daemon.src

## HTTP.Request — kein Timeout, crasst bei Offline

`HTTP.Request(url, "POST", data)` wirft einen uncaught error wenn der Server
nicht erreichbar ist. Der Fehler ist erst zur Laufzeit sichtbar.

**Fix:** try-catch um jeden HTTP-Aufruf:
```mini
response = null
try
    response = HTTP.Request(url, "POST", data)
catch e
    response = null
end try
if response == null then
    print("[X] Keine Verbindung")
    exit
end if
```

**Getroffene Dateien:** hermes_api.src

## Vanilla Terminal Commands — kein `edit`, `touch`, `echo` oder `nano`

GreyHack's vanilla Terminal (Terminal.exe) hat einen eingeschränkten Befehlssatz. Es gibt KEIN `edit`, `touch`, `echo`, `nano`, `vim`, oder `write`.

**Verfügbare vanilla Befehle:**
- `ls`, `pwd`, `cat`, `rm`, `mv`, `cp`, `mkdir` — Datei/Verzeichnis-Management
- `ps`, `chmod`, `chown`, `chgrp`, `sudo` — System
- `ifconfig`, `iwconfig`, `iwlist`, `whois` — Netzwerk
- `cd`, `reboot` — Navigation/System
- `scp`, `clear`, `exit` — Spezial

**Dateien mit Inhalt erstellen:**
1. **`cat > pfad/datei`** — Terminal-Klassiker: Inhalt einfügen, dann Ctrl+C / Ctrl+D zum beenden
2. **CodeEditor (GUI)** — Programm im Spiel-Startmenü, `New File` → `Save As` → Pfad angeben
3. **`cp quelle ziel`** — existierende Datei kopieren

**greybel-js Installer:** Die generierte `installer0.src` erstellt via `m()`-Funktionen automatisch alle Dateien. Wichtig: Die Dateien landen in einem `zKsav`-Unterordner (Build-Ausgabe des Compilers), nicht direkt im Zielverzeichnis. Nach dem Installer-Lauf die Dateien mit `cp` verschieben:
```
cp /home/Bratan/bin/zKsav/*.src /home/Bratan/bin/
```

## Suffix-Prüfung statt indexOf

`path.indexOf(".src")` matcht `.src` überall im Pfad — auch `.src_backup.lib`.
Für Dateiendungen immer Suffix-Prüfung mit Längencheck:

```mini
isSrc = false
if path.len >= 4 then
    if path.slice(path.len - 4) == ".src" then
        isSrc = true
    end if
end if
```

**Getroffene Dateien:** build_all.src
