# Yuno V5 — 18 Compiler Bugs gefixt (2026-07-03)

Quelle: Session 2026-07-03, Model: MiniMax-M3 → deepseek-v4-flash → qwen3.7-max → glm-5.2

## Bugs Kategorie 1: `//command:` Marker fehlt

**Problem:** Yuno V5 Source hatte kein `//command:` als erste Zeile. GreyHack erkennt Source-Files nur daran.

**Fix:** `"//command: yuno_v5" + char(10) + original_content` in DB schreiben.

**Verifikation:** Alle 52 funktionierenden Commands in der GreyHackDB starten mit `//command:`.

## Bugs Kategorie 2: String-in-String in `cmd_jump`

**Ort:** Funktion `cmd_jump.run`, Zeilen ~1308-1318 (nach V4-V5 Verschiebung)

**Problem:** Code baut GreyScript-Quellcode als String zusammen:
```greyscript
content = content + "pass = "pass"" + char(10)
```
Das innere `"` vor `pass` beendet den String — der Compiler sieht dann `pass` als Identifier wo EOL erwartet wird.

**Fehlermeldung:** `Compiler Error: got Identifer(pass) where EOL is required`

**Betroffene Zeilen:**
- `"pass = "pass""` → `"pass = " + char(34) + "pass" + char(34)`
- `"interop["shell"] = shell"` → `"interop[" + char(34) + "shell" + char(34) + "] = shell"`
- `"interop["cmd"] = main_session"` → analog
- `"interop["hack"] = cmd_hack"` → analog

**Fix:** Alle inneren `"` durch `+ char(34) +` ersetzen.

## Bugs Kategorie 3: Fehlende Kommas in Object-Closures

### Pattern
**Error:** Der Compiler erwartet ein Komma vor `}` bei Object-Literalen.

**Betroffene Zeilen (letzter Eintrag im Object ohne Komma):**

| Zeile | Kontext | Letzter Key |
|-------|---------|-------------|
| 23 | THEME_DEFAULT | `"cyan": "#00ffff"` |
| 35 | THEME_DARK | `"cyan": "#aaffff"` |
| 47 | THEME_OCEAN | `"cyan": "#88ffff"` — (geteiltes Theme-Pattern mit Zeilen 23, 35, 47) |
| 433 | exploit result | `"user": main_session.current_user` |
| 605 | result object | `"user": "?"` |
| 726 | shell object | `"user": "?"` |
| 876 | ssh connection | `"user": user` |
| 1446 | lib info | `"used": 1` |
| 1834 | plugin info | `"size": content.len` |
| 1879 | mission add | `"added": "YUNO_V5"` |

**Thema:** Das letzte Property in einem Object-Literal hat kein Komma, obwohl GreyScripts Compiler es verlangt.

**Fix:** Komma am Ende jeder Property-Zeile hinzufügen — auch beim letzten vor `}`.

## Bugs Kategorie 4: Kommentare in Object-Literals

**Ort:** `main_session = { ... }` — Zeile 119 (original):
```greyscript
main_session = {
    "target": null,
    // === V5 STATE ===   ← ILLEGAL!
    "recording": false,
}
```

**Problem:** GreyScript-Compiler erlaubt KEINE Kommentare innerhalb von Object-Literals.

**Fix:** Kommentar entfernen.

## Bugs Kategorie 5: V4-Banner (nicht kritisch)

**Fix:** Alle "YUNO V4.0" Banner durch "YUNO V5.0" ersetzt (5 Stellen).

## Workflow-Lektionen

1. **Game-Restart ist PFLICHT** nach jeder DB-Änderung — GreyHack caches beim Start
2. **Tiny-POC zuerst:** 1.5 KB Script deployed in `/bin/` um Pipeline zu verifizieren
3. **Dateigrösse:** Source >12 KB kann Probleme machen — in Module splitten
4. **LIVE DB checken:** Nicht von Backup-Schema ausgehen — LIVE DB hat nur `ID, Content, refCount`
5. **Unerwartete DB-Felder:** `comando`-Feld existiert in 0.9.6771-beta NICHT — das war ein Red-Herring
