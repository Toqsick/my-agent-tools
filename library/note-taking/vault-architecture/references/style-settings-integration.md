# Style-Settings Plugin Integration

> **Plugin:** [obsidian-community/obsidian-style-settings](https://github.com/obsidian-community/obsidian-style-settings) (v1.0.9)
> **Kontext:** Obsidian CSS-Snippets via `/* @settings */`-Annotation für Style-Settings-Tab konfigurierbar machen.
> **Protokolliert:** 2026-07-09 (Yuno-Session: Yuno Palette in yuno-variables.css)

## Funktionsprinzip

Style-Settings scannt **alle aktiven CSS-Snippets** nach `/* @settings */`-Blöcken.
Diese Blöcke enthalten ein YAML-ähnliches Setting-Deklarations-Schema, das eine
**UI im Plugin-Tab** erzeugt. Ändert der User einen Wert, überschreibt
Style-Settings die entsprechende CSS-Variable als Inline-Style — ohne die `.css`-Datei zu berühren.

> **Konsequenz:** Style-Settings schreibt nur in `data.json` (`plugins/obsidian-style-settings/data.json`),
> niemals in die `.css`-Datei selbst. Der `@settings`-Block definiert die **Initialwerte default-light/default-dark**.

## Leeres `data.json` erkennen

Ein `{}` in der `data.json` bedeutet **kein einziges Setting wurde je geändert**.
Das Plugin wurde installiert + aktiviert, aber entweder nie geöffnet oder nie
ein Setting angepasst. Ist ein `@settings`-Block syntaktisch korrekt, taucht er
sofort nach Plugin-Neustart (oder Snippet-Toggle) als UI auf.

## `@settings`-Annotation-Grammatik

Der Block steht **innerhalb eines CSS-Kommentars `/* ... */`** mit dem
aufklappenden Syntax:

```
/* @settings
name: "<Gruppenname>"
id: <eindeutige-id>
settings:
  - id: "<css-variable-name>"
    title: "<UI-Titel>"
    description: "<UI-Beschreibung>"
    type: "<setting-type>"
    ...
*/
/* @settings-end */
```

### Verfügbare Setting-Types

#### `variable-themed-color` — Farb-Picker

```yaml
type: "variable-themed-color"
format: "hex"           # oder "hsl", "rgb"
opacity: false          # true für Alpha-Kanal-Slider
default-light: "#7c3aed"  # Wert im Light-Theme
default-dark: "#a78bfa"   # Wert im Dark-Theme
```

- Erzeugt einen **farbigen Color-Picker** im Style-Settings-Tab
- Der Name in `id:` **muss** exakt der CSS-Variablen `--<id>` entsprechen
- Light/Dark-Wechsel im Obsidian-Theme schaltet zwischen den defaults um
- User-Änderungen überschreiben die Variable global

#### `variable-number-slider` — Zahlen-Schieberegler

```yaml
type: "variable-number-slider"
default: 15
min: 10
max: 24
step: 1
```

#### `variable-select` — Dropdown

```yaml
type: "variable-select"
default: "default-value"
options:
  - label: "Sichtbar"
    value: "visible"
  - label: "Ausgeblendet"
    value: "hidden"
  - label: "Automatisch"
    value: "auto"
```

#### `class-toggle` — aktiviert/deaktiviert eine CSS-Klasse

```yaml
type: "class-toggle"
default: false
```

- Fügt die `<id>` als Klasse auf `<body>` hinzu
- Ideal für ganze Snippet-Blöcke, die nur optional sein sollen

#### `heading` — Zwischenüberschrift im Tab

```yaml
type: "heading"
level: 2                # 1, 2, oder 3
```

### Mehrere Settings-Blöcke

Jedes Snippet kann **einen eigenen `@settings`-Block** haben. Die UI gruppiert
sie im Style-Settings-Tab **nach Snippet-Namen**. Ein Snippet mit mehreren
unabhängigen Gruppen braucht pro Gruppe einen eigenen Block.

---

## Konkreter Workflow

### 1. Voraussetzung prüfen

```
Plugin aktiv?           → .obsidian/community-plugins.json → "obsidian-style-settings"
Snippet aktiv?          → .obsidian/appearance.json → enabledCssSnippets
Plugin bereits genutzt? → .obsidian/plugins/obsidian-style-settings/data.json
```

### 2. `@settings`-Block in ein bestehendes Snippet einfügen

```
Position: Direkt nach dem Header-Kommentar, vor dem ersten `:root`-Block
Pitfall: Das Plugin parst nur EINEN `@settings`-Block pro Snippet (fürs erste)
```

### 3. Snippet aktivieren (falls nötig)

Wenn das Snippet bereits aktiv war und du einen `@settings`-Block nachgerüstet hast:
- **Obsidian restart** ODER
- **Toggle-Trick:** Settings → Appearance → CSS-Snippets → Snippet deaktivieren → wieder aktivieren

Danach erscheint die Gruppe im Style-Settings-Tab.

### 4. Verifikation

```css
/* Brace-Balance prüfen: { und } müssen gleich sein */
/* grep -o '{' datei.css | wc -l  vs.  grep -o '}' datei.css | wc -l */

/* Settings-Annotationen: */
/* grep '@settings' datei.css  → mind. 1 */
/* grep '@settings-end' datei.css  → genau 1 */
```

Öffne dann: Obsidian → Settings → Style Settings → nach der Gruppe suchen.

---

## Session-Beispiel: Yuno Palette (2026-07-09)

**Snippet:** `yuno-variables.css`  
**Neue Settings:** 7 Color-Picker (Purple, Purple-Deep, Pink, Mint, Coral, Sky, Sun)  
**Typ:** `variable-themed-color`, Format `hex`, mit Light/Dark-Defaults

### Struktur im Snippet

```css
/* @settings
name: "Yuno Palette"
id: yuno-palette
settings:
  - id: "yuno-purple"
    title: "Yuno Purple"
    description: "Hauptakzent — Wiki-Links, MOC-Marker, Tags."
    type: "variable-themed-color"
    format: "hex"
    opacity: false
    default-light: "#7c3aed"
    default-dark: "#a78bfa"
  - id: "yuno-pink"
    title: "Yuno Pink"
    description: "Sekundärakzent — MOC-Tags, Dataview-Marker."
    type: "variable-themed-color"
    format: "hex"
    opacity: false
    default-light: "#db2777"
    default-dark: "#f472b6"
  # ... weitere Farben analog
*/
/* @settings-end */

:root {
  --yuno-purple: #a78bfa;
  --yuno-pink: #f472b6;
  /* ... */
}
```

### Was nach dem Neustart passiert

1. Style-Settings liest den `@settings`-Block
2. Erzeugt Untergruppe `Yuno Palette` im Plugin-Tab
3. 7 Color-Picker mit Farbfeldern + Hex-Eingabe
4. Light/Dark-Separatoren: ein Klick auf Dark-Mode-Label zeigt Dark-Default an
5. User-Änderungen ⇒ in `data.json` gespeichert
6. Alle Snippets, die `var(--yuno-purple)` referenzieren, aktualisieren sich live

---

## Bekannte Pitfalls

| P1 | Variable-Name ≠ id | Die `id:` im YAML muss exakt dem `--<id>`-Namen im CSS:root entsprechen |
|---|---|:--|
| P2 | `@settings` außerhalb von `/*` | Der gesamte Block muss **innerhalb** eines CSS-Kommentars stehen |
| P3 | Doppelte ids | Jede `id:` muss über alle Snippets hinweg eindeutig sein (Plugin mischt sie) |
| P4 | Leeres `data.json` | `{}` heißt Plugin nie genutzt — **nicht** defekt |
| P5 | Kein Live-Reload | CSS-Änderungen an `@settings`-Blöcken brauchen Toggle oder Restart |
| P6 | `variable-themed-color` requires exact defaults | `default-light` + `default-dark` sind **erforderlich**, sonst kein UI |
