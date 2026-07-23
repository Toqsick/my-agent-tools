# GreyScript In-Game Deployment (V1.4)

GreyHack hat **kein wget/curl/http im Spiel**. GreyScript läuft in einer sandboxierten Sprache ohne Netzwerk- oder Shell-API.

## Was GreyScript im Spiel KANN

- `if/then/else/end if` (keine inline-ifs!)
- `while/end while`
- `function/end function`
- `params[i]` für CLI-Argumente
- `print()`, `exit()`, `val()`, `floor()`, `rnd`
- `.len`, `.indexOf()`, String-Concat (`+`)
- `include_lib("/lib/metaxploit.so")` — **nur auf fremden Systemen via get_shell**
- `get_shell.host_computer` — Zugriff auf NPC-Rechner

## Was GreyScript NICHT kann

- ❌ `wget`, `curl`, `http_get`, `download`
- ❌ `cat`, `ls`, `cd`, `rm`, `mv` (nur via `get_shell.host_computer`)
- ❌ `str_repeat`, `is_folder()`, `import` (stattdessen `include_lib`)
- ❌ HTTP-Requests, JSON-Parsing (nur String-Manipulation)

## Deployment-Strategie (3 Wege)

**⚠️ WICHTIG: wget/curl existieren NICHT im GreyHack-Spiel!** Siehe `references/greyhack-deployment-pitfalls.md`

**Weg 1 — Fileserver + Copy-Paste (SICHERSTER, funktioniert IMMER)**

```bash
# Auf dem Host:
cd /mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/yuno-tools
python3 -m http.server 8765

# Im GreyHack-Spiel: Browser öffnen → http://HOST_IP:8765/
# Datei klicken → STRG+A → STRG+C
# CodeEditor → New → STRG+V → Save → Build → Run
```

**Weg 2 — greybel import (wenn Port 8332 offen)**

```bash
greybel import /path/to/script.src -pt 8332 -id "/home/PLAYER"
```

**Weg 3 — CodeEditor manuell**

- CodeEditor → New → Code einfügen → Save → Build → Run

## GreyScript 1.5.1 Syntax-Regeln (KRITISCH)

```
✅ if cond then
     body
   end if
✅ while cond
     body
   end while
✅ function name(args)
     body
   end function
✅ char(10) für newline
✅ params[0], params[1], ...
❌ if cond then body end if  (einzeilig!)
❌ "string\n"  (stattdessen char(10))
❌ is_folder()  (stattdessen is_binary())
❌ str_repeat()
❌ HTTP/negative Indizes
```

## Sicherheitsregeln für GreyScript-Strikes

- NIEMALS Klartext-Passwörter in Logs/print() — nur im .src selbst
- `--redact` Flag für CLI-Ausgaben
- Backup-Admin erstellen BEVOR Passwörter geändert werden
- `computer.add_user("sysadmin", "STARKES_PW", "/home/sysadmin")` als Notausgang

## greybel-vs Interpreter (Mock-Env) — Vorsicht!

Der [greybel-vs](https://github.com/Toqsick/greybel-vs) (VSCode Extension) enthält einen **GreyScript-Interpreter** mit Mock-Environment. ABER: Der Mock ist **veraltet** und unterstützt viele Game-APIs nicht.

- ✅ Funktioniert: `include_lib("/lib/metaxploit.so")`, `include_lib("/lib/crypto.so")`, `params`, `print`, `if/while/function`
- ❌ NICHT: `shell.cat()`, `shell.users`, `shell.ConfigOS`, `net.so` — "Path not found in map"
- **Für echte Game-API-Tests: Code muss im Spiel ausgeführt werden!**
- Setup: `git clone https://github.com/Toqsick/greybel-vs.git`, `npm install`, `code --extensionDevelopmentPath=. test-workspace/`
- Test: CTRL+SHIFT+P → "Greybel: Run/Debug file from context"
- Repo: https://github.com/Toqsick/greybel-vs

## Workflow

```
1. VSCode → ~/greybel-vs/ öffnen
2. Neues .src File erstellen
3. Code schreiben mit get_shell, include_lib etc.
4. F5 / "Greybel: Run/Debug" → Output SOFORTIG im VSCode Terminal!
5. Wenn Code grün → ins Spiel deployen (Fileserver + Copy-Paste oder greybel import)
```

## Message-Hook (optional)

Mit BepInEx + Message-Hook-Plugin kann man Code direkt ins Spiel importieren:

```bash
greybel import script.src -pt 8332 -id "/home/Bratan"
```

**Referenz:** `references/greybel-vs-interpreter.md` — vollständige Setup-Anleitung