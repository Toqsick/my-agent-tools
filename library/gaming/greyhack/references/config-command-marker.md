# KRITISCH: //command: Marker + Config/ Pfad

## Marker-Anforderung

**Jeder Source-Script-Eintrag in der DB MUSS als erste Zeile `//command: <name>` haben UND in `/home/<USER>/Config/` liegen.** Der User-Home-Ordner root (`/home/gregor/`) funktioniert NICHT für Command-Detection.

Ohne diesen Marker erkennt das Spiel die Datei nicht als Script ("Can't build. Binary file." beim Build-Versuch).

| Mit Marker | Ohne Marker |
|-----------|-------------|
| `//command: yuno_v6` + Inhalt | `// =========` + Inhalt |
| ✅ `<name>` aus Shell aufrufbar | ❌ Wird nicht als Command erkannt |

## Prüfung vor DB-Insert

Die erste Zeile des Contents muss mit `//command:` beginnen. Alle 46 Source-Scripts in der Live-DB haben dieses Pattern.

## DB-Injection Parameter (für Manuelles Einspielen)

- `typeFile: 0` (nicht 1! — 0 = regular file, verified in Live-DB)
- `isBinario: false`
- `comando: ""` (leer lassen — wird über `//command:` gesteuert)
- `size = len(Content)` (KEIN `size: 0`, sonst erkennt das Spiel die Datei nicht)
- Dateiname muss auf `.src` enden