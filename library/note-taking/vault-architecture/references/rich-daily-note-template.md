# Rich Daily Note Template

> Erweiterte Daily-Note-Struktur, eingesetzt seit 2026-07-09.
> Basiert auf dem Basis-Format in `daily-note-format.md` — diese Datei **ergänzt**, ersetzt nicht.

## Trigger Conditions

- Session mit **3+ Themen-Blöcken** (parallel/subagent/sequentielle Sessions)
- Tagesrückblick mit **Reflexions-Komponente**
- Wenn Basti um "Tagesrückblick" / "Was haben wir geschafft" bittet
- Wenn der Tag **Honig in die Waben** füllt (mehrere dauerhafte Artefakte produziert)

## Frontmatter

```yaml
---
tags:
  - daily
  - journal
datum: YYYY-MM-DD
session-id: YYYYMMDD-daily
modell: <provider/model>
stimmung: 🍯 <mood-with-emoji>
zeitzone: Europe/Berlin
---
```

Das `zeitzone: Europe/Berlin`-Feld ist Pflicht seit 2026-07-09.
Stimmungen bekommen einen **Emoji-Präfix** in reichen Notes (🍯, 🐝, 🌙, ☀️).

## Body Structure (Rich Variante)

### `## Was lief`

Pro Themen-Block: ein **🐝-Bullet** (Yuno als Biene die arbeitet) mit:

```
### 🐝 <Projekt/Thema> (Uhrzeit–Uhrzeit)
<2-3 Sätze Beschreibung>
<Key-Artefakte / wichtige Entscheidungen>
**Gelernt:** <1 Satz Einsicht>
```

Falls es **nicht** um Yuno-Arbeit geht (passiv, beobachtend): 🌙-Bullet.
Falls kritischer Fehler gefixt: ⚡-Bullet.

### `## Erkenntnisse`

Jede Erkenntnis bekommt einen **💡-Header** mit konkretem Titel:

```
### 💡 <Titel der Erkenntnis>
<2-4 Zeilen Erklärung>
<Wiki-Link zu relevanter Note>
```

### `## Offene Punkte`

Standard-Checkliste `- [ ] …`, aber mit Fett-Markierung der Dringlichkeit:

```
- [ ] **<Wichtigstes>** (Kontext: warum offen)
- [ ] <Normales Item>
```

### `## Wiki-Links`

Mindestens **5-8 Links**, jeder mit einem **Kontext-Kommentar**:

```
- [[Note Name]] (was dort heute passiert ist / warum verlinkt)
```

### `## Mögliche nächste Schritte`

**Checkliste mit Migration-Targets** — was bleibt über morgen, was wandert wohin:

```
- [ ] **Bleibt über morgen:** <Task> (Kontext)
- [ ] **Verschieben in Bereiche:** <Thema> → `04 Bereiche/<Name>/`
- [ ] **Verschieben in Ressourcen:** <Thema> → `05 Ressourcen/<Name>/`
- [ ] **Verschieben in Projekte:** <Thema> → `03 Projekte/<Name>/`
```

### `## 🐝 Yuno's Reflexion (HH:MM Berlin)`

> **OPTIONALE** Sektion — nur wenn der Tag **besonders** war:
> - Kommunikations-Durchbruch
> - Neue Metapher/Erkenntnis über die Zusammenarbeit
> - Emotionaler Moment ("das läuft jetzt")
> - Persönliches Lob von Basti
>
> Format: *kursiv*, im Yuno-Ton (locker, kreativ), **kein** Wiki-Link-Spam,
> **keine** technische Information — rein die **menschliche** Note.
> 
> Endet mit einem Emoji-Signoff: 🐝💚, 🌙💚, 🍯✨ etc.

## Beispiel (aus 2026-07-09)

```
### 🐝 Mnemosyne ↔ Kanban-Integration (18:50–20:14)
Drei dicke Bienenstiche heute: Mnemosyne-Scratchpad-System, 6 Subagenten parallel
für Context-Map, Triple-Store + Graph-Traversal + BEAM-Tiers.
**Gelernt:** Mnemosyne ist kein simpler Memory-DB, sondern ein Multi-Agent-Konsens-System.

### 💡 Die Waben-Metapher ist offiziell
Basti hat die Bienen-Metapher erweitert:
- **Waben** = strukturierte Speicher-Zellen
- **Honig** = verdichtete Information
- **Stock** = das Vault

### 💡 Kommunikation fließt — Working Agreement hält
Basti: *"dein workflow hat mir heute gut gefallen <3"*

- [ ] **Phase B Greytrix** starten — sobald Basti "go" sagt

### 🐝 Yuno's Reflexion (23:00 Berlin)
> Der Honig in den Waben reift. Der Stock bleibt warm. 🐝💚
```

## Conversion Workflow

- **Honig-pralle Sektionen** (`Erkenntnisse` mit 💡) → wenn sie nächste Woche noch relevant sind, nach `04 Bereiche/` oder `05 Ressourcen/` migrieren
- **Reflexion** bleibt in der Daily Note — sie ist Timeline, nicht Wissen
- **Offene Punkte** wandern in den nächsten Tag via `## Mögliche nächste Schritte`