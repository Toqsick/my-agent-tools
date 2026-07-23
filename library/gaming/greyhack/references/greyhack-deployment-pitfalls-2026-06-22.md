# GreyHack Deployment — Session 2026-06-22

## WICHTIG: GreyHack hat KEIN wget/curl/http_get im Spiel!

Dies ist eine kritische Korrektur gegenüber früheren Annahmen. Der Skill-Eintrag "Per wget vom Fileserver" war **falsch** für In-Game-Nutzung.

## Was funktioniert NICHT im Spiel
```
// ALLE DASEN FUNKTIONIEREN NICHT:
pc.wget("http://...", "/home/Bratan/...")  // wget existiert nicht
shell.curl(...)                               // curl existiert nicht
shell.run("wget ...")                         // wget im Bash gibt es nicht
```

## Was FUNKTIONIERT

### 1. Copy-Paste (sicherster Weg, immer verfügbar)
```
Host: cd ~/greyhack-tools && python3 -m http.server 8765 &
Browser: http://<HOST_IP>:8765/
GreyHack: CodeEditor → New → STRG+V → Save → Build → Run
```

### 2. greybel import via Message-Hook (BepInEx)
```
Voraussetzung: BepInEx + GreyHackMessageHook.dll installiert
Befehl: greybel import <file.src> -pt 8332 -id "/home/Bratan"
```

### 3. Manuell im CodeEditor schreiben
```
CodeEditor → New → Code schreiben → Save → Build → Run
```

### 4. greybel-js Interpreter (außerhalb des Spiels)
```
~/greybel-vs/ Extension Development Host
→ Script mit get_shell/include_lib testen
→ Mock-Environment simuliert das Spiel
```

## Pure GreyScript (kein get_shell nötig)
Falls du Code schreiben willst, der im Spielterminal OHNE get_shell läuft:
- Nur `print()`, `char(10)`, `params[i]`, `val()`, `floor()`, `rnd`
- `if/then/else/end if`, `while/end while`, `function/end function`
- String-Operationen: `.len`, `.indexOf()`, `.split()`, `.join()`
- KEIN Netzwerk, KEIN Dateizugriff, KEIN Shell

## Session Artefakte
```
/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/yuno-tools/
├── hardening_pure.src     → Reines GreyScript (kein get_shell)
├── bruteforce.src         → Passwort-Generator (reines GreyScript)
├── dee_strike_pure.src    → Dee-Info-Output (reines GreyScript)
├── strike1_dee_grettib.src → Dee Strike mit get_shell
├── bank_grab.src          → Bank-Transfer mit get_shell
└── multihop_strike.src    → Multi-Hop mit get_shell
```
