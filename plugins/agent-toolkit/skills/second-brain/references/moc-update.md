# MOC-Update-Workflow (nur auf Zuruf)

> **Grundregel zuerst:** MOCs sind bestehende Notizen — sie werden **ausschließlich auf explizite Anweisung von Basti** editiert. Dieser Workflow beschreibt das *Wie*, er erteilt keine Erlaubnis. Ohne Zuruf gilt Inbox-first (siehe SKILL.md).

## MOC-Typen im Vault

| Typ | Beispiele | Zweck |
|---|---|---|
| **Hub** | `MOC - Home.md` (Top-Level) | Vault-Zentrum: Status-Dashboards, Ordner-Übersicht, Recent-Changes |
| **Themen-MOC** | `MOC - Gaming-Performance`, `MOC - KI-Architektur`, `MOC - Security-Hardening`, `MOC - System-Tuning`, … (Top-Level) | Cross-Cutting-Cluster über mehrere Ordner |
| **Folder-MOC** | `02 Inbox/MOC - Inbox`, `03 Projekte/MOC - Projekte`, `04 Bereiche/MOC - Bereiche`, … | Übersicht eines Ordners, meist Dataview-getrieben |

## Wo neue Links eingetragen werden

1. **In die thematisch passende Sektion**, nie einfach ans Dateiende. Themen-MOCs sind in benannte Abschnitte gegliedert (z.B. „Satelliten", „Roh-Referenzen", Themenblöcke) — den Abschnitt lesen und den Link dort einreihen, wo verwandte Notizen stehen.
2. **Format an Nachbarzeilen angleichen**: manche MOCs listen `[[Note]] — Kurzbeschreibung`, andere Tabellen (`| MOC | Fokus | Verbindet |`). Bestehenden Stil kopieren.
3. **Dataview-Sektionen nicht manuell befüllen** — Listen unter einem ` ```dataview `-Block entstehen zur Laufzeit; dort nichts hineinschreiben. Nur statische Link-Sektionen editieren.
4. **Frontmatter `letzter-review:`** (falls vorhanden, z.B. in `MOC - Security-Hardening`) beim Update auf das aktuelle Datum setzen.
5. **Gegencheck Backlink-Ziel**: die verlinkte Notiz sollte den MOC zurückverlinken (unter `## Verbindet zu`) — sonst entsteht ein einseitiger Link, der im Backlink-Cluster-Query nur halb auftaucht. Wenn die Ziel-Notiz dafür editiert werden müsste, gilt auch dort: nur auf Zuruf.

## Typische Zurufe und was sie bedeuten

- „Nimm X in den Gaming-MOC auf" → ein Link + Kurzbeschreibung in die passende Sektion von `MOC - Gaming-Performance.md`.
- „Aktualisiere den Home-Status" → den betreffenden Status-Block in `MOC - Home.md` anfassen, nichts anderes.
- „Verlinke die neue Inbox-Note im MOC" → normalerweise unnötig: `MOC - Inbox` listet per Dataview automatisch. Erst prüfen, ob ein statischer Eintrag überhaupt gebraucht wird.
