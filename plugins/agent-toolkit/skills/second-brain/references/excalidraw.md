# Excalidraw-Dateiformat (`.excalidraw.md`)

Excalidraw-Zeichnungen im Vault sind Markdown-Dateien mit Endung `.excalidraw.md`. Sie sind gleichzeitig gültige Obsidian-Notizen (verlinkbar via `[[Name.excalidraw]]`) und enthalten die Zeichnungsdaten als JSON.

## Minimale, vom Plugin lesbare Datei

````markdown
---
excalidraw-plugin: parsed
tags:
  - excalidraw
---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==

# Text Elements
Beispieltext ^abc12345

%%
# Drawing
```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://github.com/zsviczian/obsidian-excalidraw-plugin",
  "elements": [
    {
      "id": "el-1",
      "type": "text",
      "x": 100, "y": 100,
      "width": 120, "height": 25,
      "angle": 0,
      "strokeColor": "#1e1e1e",
      "backgroundColor": "transparent",
      "fillStyle": "solid",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 1,
      "opacity": 100,
      "groupIds": [],
      "frameId": null,
      "roundness": null,
      "seed": 1,
      "version": 1,
      "versionNonce": 1,
      "isDeleted": false,
      "boundElements": null,
      "updated": 1,
      "link": null,
      "locked": false,
      "text": "Beispieltext",
      "rawText": "Beispieltext",
      "fontSize": 20,
      "fontFamily": 1,
      "textAlign": "left",
      "verticalAlign": "top",
      "containerId": null,
      "originalText": "Beispieltext",
      "lineHeight": 1.25
    }
  ],
  "appState": {
    "gridSize": null,
    "viewBackgroundColor": "#ffffff"
  },
  "files": {}
}
```
%%
````

## Regeln

- **Frontmatter**: `excalidraw-plugin: parsed` ist Pflicht, sonst erkennt das Plugin die Datei nicht.
- **`# Text Elements`**: jedes Text-Element der Zeichnung erscheint hier als Zeile mit Block-Referenz `^<8 Zeichen>` — so wird der Text in Obsidian durchsuchbar/verlinkbar. Beim Erstellen per Hand: eine Zeile pro Text-Element, ID frei wählbar (8 alphanumerische Zeichen, eindeutig).
- **`# Drawing`-Block**: steht in `%% ... %%` (Obsidian-Kommentar), enthält das Excalidraw-JSON im ` ```json `-Block. Das Plugin kann diesen Block auch **komprimiert** speichern (` ```compressed-json ` mit Base64/LZ-String) — komprimierte Blöcke nicht per Hand editieren; zum Lesen genügt die `# Text Elements`-Sektion.
- **Element-Typen**: `rectangle`, `ellipse`, `diamond`, `arrow`, `line`, `text`, `freedraw`, `image`, `frame`. Pfeile/Linien haben zusätzlich `points: [[0,0],[dx,dy]]` und optional `startBinding`/`endBinding` (Verbindung an Element-IDs).
- **Neue Zeichnungen**: Inbox-first → `02 Inbox/YYYY-MM-DD - Titel.excalidraw.md`. Nach dem Anlegen in Obsidian öffnen und im Excalidraw-View weiterbearbeiten — das Plugin normalisiert die Datei beim ersten Speichern selbst.
