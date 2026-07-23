# Detail-Companion-Pages

Erweiterung der Hauptskill für eine verwandte, aber eigenständige Aufgabe:
Aus bestehenden `Tool-*.md`-Seiten werden vertiefte Detail-Companion-Seiten mit
API-Referenz-Tabelle und nummerierten Code-Beispielen erzeugt. Außerdem
gehören die beiden Cross-Cutting-Sub-Typen `Patterns-QuickRef` und
`Tools-CheatSheet` zu diesem Muster.

Entstanden 2026-07-22 aus der Aufgabe "Erstelle 5 Sub-Pages fuer komplexe
Tools (Tier C)" auf dem greyscripts-Wiki (lib-core, grsa, portscan, patterns,
alle 33 Tools). Die Hauptskill deckte den Fall nicht ab — sie ist auf
"N READMEs -> N+1 Standard-Pages" optimiert. Die Detail-Variante
unterscheidet sich strukturell.

## Trigger (Detail statt Standard)

| Situation | Wahl |
|---|---|
| User fragt nach "N Detail-Pages", "API-Referenz", "Cheat-Sheet" | Detail-Page |
| Tool ist als Tier C klassifiziert (komplex, viele Funktionen, Crypto/Netzwerk) | Detail-Page |
| User nennt eine bestehende Wiki-Seite als Ausgangspunkt ("vertiefe Seite X") | Detail-Page |
| N >= 10 READMEs ohne Wiki-Page -> Standard-Pages | nicht Detail-Page |

## Struktur-Vergleich

| Standard-Page (Hauptskill) | Detail-Companion-Page (diese Erweiterung) |
|---|---|
| `## Übersicht` | `## Übersicht` (kürzer) |
| `## Verwendung` (1 Block) | `## Code-Beispiele` (2-3 nummerierte Beispiele) |
| `## Funktionen` (Bullet) | `## API-Referenz` (Tabelle `Signatur | Rückgabe | Zweck`) |
| `## Build-Anleitung` | `## Build und Betriebsregeln` |
| `## Hinweise` | `## Quelltrefe und Versionshinweis` |
| `## Verwandte Tools` | `## Verwandte Seiten` |

Detail-Pages tragen zusaetzlich den Header:

```markdown
**Detail-Level:** Vertieft (gegenüber Standard-Tool-Page)
```

## API-Referenz (verbindlich)

Spalten exakt: `| Signatur | Rückgabe | Zweck |`. Mehrere Tabellen pro Seite
nach Funktionsgruppe sind erlaubt und empfohlen (z. B. `### Pfad- und Datei-Helfer`,
`### Mathematik`, `### Schlüssel`).

Regel: nur Funktionen dokumentieren, die tatsaechlich im Source mit
`<name> = function(...)` definiert sind. Verifikation ueber
`grep -n '^[A-Za-z_][A-Za-z0-9_]*\s*=\s*function' <src>`. Nicht im Source
nachweisbare Namen aus der README NICHT uebernehmen — statt dessen im
Abschnitt `### Quelltrefe und Versionshinweis` explizit als Abweichung
kennzeichnen ("README nennt `safeWrite`, im Source nicht definiert").

## Code-Beispiele (verbindlich)

Mindestens 2, hoechstens 3 nummerierte Beispiele pro Detail-Page. Jedes
Beispiel traegt `### N. <Titel>` und steht in einem einzigen
`greyhack`- oder `greyscript`-Codeblock. Beispiele muessen lauffaehig
zusammenhaengen, nicht Fragment-Collagen. Wenn das Tool CLI-Parameter
akzeptiert, muss mindestens ein Beispiel nichttriviale Parameter zeigen.

## Cheat-Sheet-Sub-Typen

### Patterns-QuickRef
Spickzettel ueber die 11 verifizierten Patterns. Tabelle:
`| # | Pattern | Kategorie | Kernsignatur | Score | Quelle |`. Verlinkt
auf `patterns/<name>.meta.md` und auf die Pattern-Seiten. Mindestens
2-3 Pattern-Kombinationen in einem kurzen Codeblock.

### Tools-CheatSheet
Tabellarische Uebersicht aller N Tools nach Kategorie aus `Tools-Overview`.
Zeile: `| Tool | Zweck | Abhaengigkeit | Seite |`. Mit `## Code-Beispiele`
am Ende inklusive `build`-Reihenfolge und typischer Werkzeugketten
("Netzwerk", "Crypto", "Datei").

## Naming-Konvention

| Sub-Typ | Dateiname |
|---|---|
| Tool-Detail | `Tool-<kebab>-Detail.md` |
| Patterns-Spickzettel | `Patterns-QuickRef.md` |
| Tools-Spickzettel | `Tools-CheatSheet.md` |

`Tool-<kebab>-Detail.md` ist die ausdrueckliche Wahl, damit die
Detail-Seite klar von der Standard-Seite (`Tool-<kebab>.md`) getrennt
ist — sonst wirkt sie wie eine weitere Standard-Seite und bricht die
etablierte Wiki-Struktur.

## Workflow (5 Phasen)

1. **Source-Inventar:** fuer jedes Tool die `.src`-Datei lesen, alle
   `function`-Definitionen mit `grep` extrahieren.
2. **README-Inventar:** Original-README daneben legen, um Diskrepanzen
   sichtbar zu machen (Beispiel: `greyhack-tools/portscan/README.md`
   behauptet "standalone", Source importiert aber `lib_core`).
3. **Tabellen entwerfen:** gruppieren nach Funktionsgruppe, pro Gruppe
   eine Tabelle `Signatur | Rueckgabe | Zweck`.
4. **Beispiele schreiben:** 2-3 zusammenhaengende Codebloecke pro Seite.
   Geprueft gegen die echte API (nicht gegen eine README-Behauptung).
5. **Verifikation:** `wc -l` (max. 200) + Stilregel-Check (em-dash,
   en-dash, Mid-Sentence-Bold, Frontmatter). Bei Detail-Pages ist
   em-dash und en-dash noch strenger zu vermeiden als in der
   Standard-Variante, weil Detail-Seiten dichter an Code-Identifiern
   schreiben.

## Pitfalls

| # | Pitfall | Mitigation |
|---|---|---|
| 1 | API-Referenz aus README abschreiben statt aus Source verifizieren | Vor dem Schreiben: `grep -n ' = function' <src>` auf das tatsaechliche Source-File |
| 2 | README-Stand und Source-Stand vermischen (z. B. portscan) | Versionshinweis-Abschnitt: explizit dokumentieren was README behauptet vs. was Source zeigt |
| 3 | Detail-Page ohne Header `**Detail-Level:** Vertieft` | Im Header-Block IMMER als 4. Zeile unter `**Stand:**` setzen |
| 4 | Code-Beispiele als Fragment-Collage mitten im Haupttext | Jedes Beispiel unter eigener `### N. <Titel>`-Ueberschrift, in einem einzigen Codeblock |
| 5 | Verwandte-Seiten-Liste zu kurz | Mindestens 4 Cross-Links, davon mindestens 1 auf die Standard-`Tool-*.md`-Seite (ohne `-Detail`) |
| 6 | Cross-Links aus anderen Detail-Pages ignorieren | Jede Detail-Page sollte in der Verwandte-Seiten-Liste des passenden Standard-Pendants referenziert sein (bidirektional) |
| 7 | Funktionen dokumentieren, die im Source mit anderem Namen existieren (z. B. README-Variante vs. Source-Variante) | Bei Namensvarianten die Source-Variante nehmen und im Versionshinweis vermerken |
| 8 | Service-Mapping-Tabelle leer oder "TODO" | Statisches Service-Mapping aus der Source-Tabelle 1:1 uebernehmen und explizit `unknown` fuer nicht-gemappte Ports |
| 9 | Build-Kommando ungeprueft aus README kopieren | Build-Pfad aus `greyhack-tools/<tool>/<tool>.src` lesen, nicht aus anderen Tools generalisieren |
| 10 | Beispiele ohne Import der Library zeigen | Wenn das Tool `lib_core` voraussetzt, das `import_code("lib_core")` in JEDEM Beispiel zeigen |

## Worked Example: greyscripts Tier-C Pass

Session 2026-07-22 produzierte diese 5 Detail-Seiten in einem Turn:

- `Tool-lib-core-Detail.md` (lib_core v2.2, 21 Funktionen gruppiert in
  4 API-Tabellen, 3 Code-Beispiele, Quell-README-Abweichungen explizit)
- `Tool-grsa-Detail.md` (grsa_v2, 17 Funktionen gruppiert in 4 API-Tabellen,
  3 Code-Beispiele, Abgrenzung zu legacy `grsa/grsa.src`)
- `Tool-portscan-Detail.md` (portscan, 1 lokale Funktion plus 8 Runtime-Aufrufe
  in einer separaten Tabelle, Service-Mapping-Tabelle, README-vs-Source-Hinweis)
- `Patterns-QuickRef.md` (11 Patterns als Sammeltabelle, Sub-API-Gruppen)
- `Tools-CheatSheet.md` (alle 33 Tools aus `Tools-Overview` in 8 Kategorien,
  Build-Reihenfolge + 3 Werkzeugketten)

Alle Seiten: 86-129 Zeilen, `---` Frontmatter nein, em-dash nein, en-dash nein,
mindestens 4 Cross-Links.

## Quelle

- Session 2026-07-22: Detail-Companion-Erweiterung der Bulk-Skill, 5 Seiten
  in `wiki/` des greyscripts-Repos, alle vom Hook `quality-gate-runner`
  geprueft.
- Hauptskill: `documentation/bulk-readme-to-wiki-pages` (Standard-Page-Variante).
