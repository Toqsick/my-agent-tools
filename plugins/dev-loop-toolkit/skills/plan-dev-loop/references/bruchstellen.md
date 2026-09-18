# bruchstellen.md — Bruchstellen-Rezepte (verallgemeinert)

Der Standard-Loop (Baseline → implementieren → Verify → kleinste Ursache zuerst)
reicht fast überall. Diese sechs Muster sind die Stellen, an denen er erfahrungsgemäß
nicht reicht — generalisiert aus dem pokerogue-M9-Plan (B-1…B-6). Prüfe bei jedem
Plan, welche davon (oder welche Analoga) zutreffen, und schreibe pro Treffer ein
konkretes Rezept in den Plan.

## Muster 1 — „Unbekannte Input-Fülle bricht den Parser/Importer"

Erfahrungsgemäß an Vollexport-/Migrations-/Konverter-Tasks.

- **Vorlauf außerhalb des Repos**: das Werkzeug mit vollem Input gegen ein
  temporäres Ausgabeverzeichnis laufen lassen — nichts committen, bis ein Lauf sauber ist
- **Feldgleichheits-Regressionsdetektor**: der bekannte Teil der Daten muss im
  Vollexport feldgleich zum bisherigen Stand bleiben (`jq`/diff-Vergleich); ein Fix,
  der das bricht, hat eine Regression eingebaut — fängt mehr als jeder Test
- **Nach Familien fixen, nicht nach Einzeleintrag**: Fehlermeldung nennt Datei+Zeile;
  die Frage ist immer „welche strukturelle Form ist das", sonst dreht man hunderte
  Einzelrunden
- **Abbruch**: 5 Iterationen ohne sauberen Lauf → blocked:-Issue mit Liste der
  fehlschlagenden Formen — nicht weiterraten

## Muster 2 — „Die stille Dateilisten-Falle"

Build-/Test-Harness mit festen Quelldatei-Listen: eine neue Datei, die nicht drinsteht,
wird nie kompilausgeführt/getestet — **und der Verify bleibt grün**.

- 10-Sekunden-Gegenprobe: absichtlich Syntaxfehler in die neue Datei, Verify laufen
  lassen; bleibt er grün, ist die Datei nicht verdrahtet; Fehler wieder entfernen
- Listeneintrag in denselben Commit wie die Datei
- Betroffen: C++-Sourcen-Listen, Test-Discovery-Filter, lint-glob-Listen

## Muster 3 — „Referenzdaten-Regeneration adelt den Bug"

Golden Vectors / Snapshots / erwartete Fixtures: wer Generator ändert und
regeneriert, kann einen Fehler zur Wahrheit erklären.

1. Referenzdaten **vor** der Implementierung ändern (wer zuerst Code schreibt,
   schreibt die Referenz danach gegen den eigenen Code)
2. Kategorie-Isolation beweisen: alte Referenz beiseite, neu generieren, kategorieweise
   diffen — nur begründete Kategorien dürfen sich ändern, Rest byte-identisch
3. Mutationstest: eine bewusste Fehl-Mutation in die Engine muss die Cases rot machen;
   bleiben sie grün, testen sie nichts
4. Versions-Bump + DECISIONS-Eintrag, sonst ist die Änderung für die nächste Session
   unsichtbar

## Muster 4 — „Die Assert-Kaskade beim großen Import"

Kapazitäts-Assertions (Größen, Limits, Typbreiten) brechen planmäßig, wenn der
Datenumfang wächst — das ist gewollt, kein Bug.

- Größen **vor** dem Build sichtbar machen (Selbsttest des Konverters zeigt
  erzeugte Zahlen, bevor ein Header kompiliert)
- Ressourcen-Verbrauch zuletzt **messen**, nicht schätzen; Budget überschritten →
  Entscheidung an den Menschen (Budget anheben vs. anderer Ansatz), kein Agenten-Alleingang

## Muster 5 — „CI und lokal bauen unterschiedliche Daten"

Umgebungsunterschiede (fehlender Klon, andere Envs, andere Tools) erzeugen still
divergierende Artefakte — nichts fängt es, solange niemand die Differenz liest.

- Nachweis statt Vermutung: CI-Artefakt herunterladen, Prüfsummen gegen lokal
  vergleichen; solange sie differieren, ist der Task nicht fertig
- Fallbacks **fail-closed** machen: lieber harter Abbruch als still falsche Werte

## Muster 6 — „Nicht emulierbare Interaktion"

Manche Akzeptanz (Touch, Hardware, Optik, Gefühl) ist im Automatisierer nicht
prüfbar — der Emulator prüft das Zeichnen, nicht das Antippen.

- Was rein/reaktiv ist, host-testbar machen (Geometrie-, Logik-Funktionen mit
  eigenen Referenzcases — das ist der eigentliche Beweis, nicht der Screenshot)
- Für das Unprüfbare: Checkliste an den Menschen im Gate-Issue, nicht „gilt als ok"
- Timebox für den Automatisierungsversuch; nicht bestanden → Checkliste, weiter
  (kein Task-Blocker)

## Loop-Hygiene, die überall gilt (aus Session-Praxis)

- Format/Lint **lokal vor jedem Push** — wenn der lokale Verify sie nicht prüft,
  prüft sie die CI, und main färbt sich rot
- Nie auf roter Baseline weiterbauen
- Eine Hypothese pro Fix-Iteration — sonst weiß hinterher niemand, was gewirkt hat
