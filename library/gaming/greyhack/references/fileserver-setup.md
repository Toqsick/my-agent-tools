# Fileserver Setup & Agent-Zugriff

## pc.wget() im Spiel

**ACHTUNG: pc.wget() existiert im Spiel!** Die Aussage "GreyHack hat kein wget" bezieht sich auf das In-Game-Terminal (Bash-ähnlich, kein `wget`-Binary), NICHT auf die GreyScript-Funktion `pc.wget(url, dst)`. Diese funktioniert im Spiel für native Steam Linux Setup (selbe Maschine → `127.0.0.1` oder LAN-IP). Die Fileserver-Methode ist damit **direkt im Game nutzbar**, nicht nur für greybel-js.

**So geht's im Spiel (eine Zeile in der Shell):**
```
pc.wget("http://127.0.0.1:8765/yuno_v6_c.src", "/tmp/tool.src")
// Dann build & run:
shell.build("/tmp/tool.src")
```

**Einschränkung:** `pc.wget()` ist community-discovered, nicht offiziell dokumentiert. Funktioniert zuverlässig auf Bastis Setup (Steam Native Linux, keine Sandbox/VM).

## Fileserver starten

```bash
cd ~/greyhack-tools && python3 -m http.server 8765 &
```

## Agent-Zugriff auf In-Game-Filesystem

**WICHTIG: Der Agent (Yuno/Hermes) hat KEINEN Zugriff auf das In-Game-Filesystem.** GreyHack läuft in einer Steam-Sandbox/VM. Das Spiel-Filesystem (`/home/gregor/`, `/home/Bratan/`, `/bin/`) existiert nur innerhalb des Spielprozesses — es gibt keinen Mountpoint, keine API und kein Debug-Interface, das von außen lesbar wäre. Verbreitete Fehlannahme wie "kannst du auf mein in-game filesystem zugreifen?" müssen explizit korrigiert werden.

**Konsequenz:** Alle Code-Deployment-Wege laufen über den SPIELER im Spiel — der Agent kann nur vorbereiten (Fileserver hosten, Code bereitstellen, Anleitungen geben).

| Methode | Voraussetzung | Zuverlässigkeit |
|---------|---------------|-----------------|
| **Copy-Paste** aus Browser | Fileserver läuft, Browser offen | ✅ 100% |
| **Message-Hook** | BepInEx + Plugin installiert | ✅ Nach Setup |
| **CodeEditor + Build** | Spiel läuft | ✅ Immer |