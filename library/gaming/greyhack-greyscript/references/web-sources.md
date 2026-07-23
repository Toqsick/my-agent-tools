# GreyScript Web-Quellen — bewertetes Inventar (Stand 2026-07-14)

> Curated inventory of web sources for GreyScript documentation.
> Use this to pick the right source for a given task.
> Each entry includes: URL, strengths, weaknesses, and best use case.

---

## 1. documentation.greyscript.org — Community-Doku (UMFANGREICHSTE)

**URL:** https://documentation.greyscript.org/

| Aspekt | Bewertung |
|--------|-----------|
| Umfang | ⭐⭐⭐⭐⭐ Vollständigste API-Doku mit **Self-Return-Types** (welcher Typ von welcher Methode zurückkommt) |
| Aktualität | ⭐⭐⭐⭐ Gut gepflegt, folgt V0.9.x |
| Lesbarkeit | ⭐⭐⭐⭐ Nach Klassen/Objekten sortiert, gute Navigation |
| Indexierung | ❗ Sagt **1-based** — konsistent mit GreyHack Engine |

**Stärken:**
- Self-Return-Type-Deklarationen: sieht man auf einen Blick, ob eine Methode `string`, `shell`, `null` oder `file` zurückgibt
- Nach Objekt-Klassen (Shell, Computer, File, Router, Crypto, Metaxploit, AptClient) strukturiert
- Enthält alle wichtigen API-Methoden mit Parametern

**Schwächen:**
- Keine vollständige Reserved-Keywords-Liste
- Keine Compiler-Fehler-Referenz (Error-Signaturen)
- Community-betrieben, nicht offiziell

**Best Use Case:** Primäre API-Referenz für Methoden-Signaturen und Return-Types.

---

## 2. main.greyscript.org/manuals/ — Offizielle Manuals (MiniScript-basiert)

**URL:** https://main.greyscript.org/manuals/

Verfügbare Manuals:
- Numbers (Zahlen, Arithmetik, Operatoren)
- Strings (Literale, Methoden, Escape-Verhalten)
- Lists (Erstellung, Iteration, Methoden)
- Maps (Erstellung, Zugriff, Methoden)
- Functions (Definition, Parameter, Rückgabewerte)

| Aspekt | Bewertung |
|--------|-----------|
| Umfang | ⭐⭐⭐⭐ Abgedeckt: Grundlagen-Typen, aber **keine** Game-spezifischen Objekte |
| Aktualität | ⭐⭐⭐⭐⭐ Offiziell, direkt aus dem Spiel |
| Lesbarkeit | ⭐⭐⭐⭐⭐ Didaktisch aufbereitet mit Beispielen |
| Indexierung | ❗ Sagt **0-based** — **WIDERSPRICHT** GreyHack Engine (1-based)! |

**Stärken:**
- Offizielle Quelle — einzige direkte Verbindung zum Spiel
- Gut strukturierte Einführungen mit Code-Beispielen
- Zeigt Unterschiede zwischen MiniScript und GreyScript

**Schwächen:**
- Deckt NUR die 5 Grundtypen ab (Numbers, Strings, Lists, Maps, Functions)
- KEINE Game-spezifischen Objekte (Shell, Computer, Router, File, Crypto, Metaxploit, AptClient)
- Indexierung ist **falsch für das Spiel**: MiniScript-Spec sagt 0-based, aber GreyHack Engine ist 1-based
- Keine Build-Pipeline / Compiler-Doku

**Best Use Case:** Sprachgrundlagen lernen, Typ-Verhalten verstehen, offizielle Source-of-Truth für MiniScript-Syntax.

---

## 3. greyscript.net/api — Kompakte API-Übersicht (Klassen-sortiert)

**URL:** http://greyscript.net/api

| Aspekt | Bewertung |
|--------|-----------|
| Umfang | ⭐⭐⭐ Konzentriert sich auf API-Objekte, weniger Sprachdetails |
| Aktualität | ⭐⭐⭐ Teils veraltet, einige Methoden fehlen |
| Lesbarkeit | ⭐⭐⭐⭐ Sehr kompakt, schnell erfassbar |
| Indexierung | ✅ Sagt explizit: "GreyScript uses 1-based indexing" |

**Stärken:**
- Schnellste Übersicht: alle API-Klassen auf einer Seite
- Expliziter Vermerk zur 1-based Indexierung
- Gute erste Anlaufstelle für API-Quick-Checks

**Schwächen:**
- Weniger detailliert als documentation.greyscript.org
- Einige neuere API-Methoden fehlen
- Keine Error-Signaturen, keine Fallstricke

**Best Use Case:** Schnelle API-Übersicht, wenn man nur den Methodennamen oder die Klasse braucht.

---

## 4. codedocs.ghtools.xyz — Alternative Doku mit Suche

**URL:** https://codedocs.ghtools.xyz/

| Aspekt | Bewertung |
|--------|-----------|
| Umfang | ⭐⭐⭐ Solide, aber weniger vollständig als documentation.greyscript.org |
| Aktualität | ⭐⭐⭐ Nicht immer aktuell |
| Lesbarkeit | ⭐⭐⭐⭐ Suchfunktion als Hauptvorteil |
| Indexierung | ✅ 1-based |

**Stärken:**
- Integrierte Suchfunktion (einfach `strg+f`-tauglich im Browser)
- Alternative Perspektive — manche Methoden sind anders dokumentiert
- Gut für Cross-Referencing

**Schwächen:**
- Weniger umfassend als Nr. 1
- Teilweise veraltete Informationen
- Keine eigene Fehlerreferenz

**Best Use Case:** Zweitmeinung einholen, gezielte Suche nach einer bestimmten Methode.

---

## 5. github.com/ayecue/greybel-js — GreyScript-Toolkit (Source of Truth für Build)

**URL:** https://github.com/ayecue/greybel-js

| Aspekt | Bewertung |
|--------|-----------|
| Umfang | ⭐⭐⭐⭐⭐ Vollständigster Source-Code — **definiert** was kompiliert |
| Aktualität | ⭐⭐⭐⭐⭐ Upstream des greybel-Compilers |
| Lesbarkeit | ⭐⭐ TypeScript-Quellcode, keine Doku |
| Indexierung | ✅ 1-based in der Runtime-Implementierung |

**Stärken:**
- **Authoritative Quelle** für Compiler-Verhalten: was greybel akzeptiert/rejected
- `src/runtime/` zeigt genau, welche Runtime-Funktionen existieren (z.B. `pc.wget`, `Computer.File`)
- `src/parser/` zeigt, welche Sprachkonstrukte valide sind
- Man kann gezielt nach `FunctionDeclaration`, `MapConstructor` etc. suchen

**Schwächen:**
- TypeScript-Quellcode — kein Dokumentations-Tool
- Man muss sich im Repository auskennen
- Keine didaktische Aufbereitung

**Best Use Case:** Wenn man genau wissen muss, ob ein Sprachkonstrukt valide ist — im Zweifel den Parser-Code checken. Auch für Runtime-Funktionen, die in keiner Doku stehen.

---

## 6. In-Game Resource Browser — DIE letzte Wahrheit

**Zugriff:** Im GreyHack-Spiel: Computer → Resource Browser

| Aspekt | Bewertung |
|--------|-----------|
| Umfang | ⭐⭐⭐⭐⭐ Alles was im Spiel exekutiert wird |
| Aktualität | ⭐⭐⭐⭐⭐ Lebende Engine |
| Lesbarkeit | ⭐⭐ Nur über das Spiel zugänglich |
| Indexierung | ✅ 100% 1-based |

**Stärken:**
- Einzige 100% verlässliche Quelle — der Resource Browser zeigt Doku aus der laufenden Engine
- Enthält auch Funktionen, die online nirgends dokumentiert sind

**Schwächen:**
- Nur im Spiel zugänglich (kein schnelles Copy-Paste)
- Keine Suche, keine Verlinkung
- Nicht exportierbar

**Best Use Case:** Letzte Instanz bei Unstimmigkeiten zwischen Web-Quellen.

---

## Verwendungsmatrix

| Aufgabe | Empfohlene Quelle |
|---------|------------------|
| API-Methode suchen (Signatur + Return-Type) | #1 (documentation.greyscript.org) |
| Sprachgrundlage lernen (Typen, Syntax) | #2 (main.greyscript.org/manuals/) |
| Schnelle API-Übersicht | #3 (greyscript.net/api) |
| Gezielte Suche nach Methode | #4 (codedocs.ghtools.xyz) |
| Compiler-Verhalten prüfen (build/execute) | #5 (github.com/ayecue/greybel-js) |
| Unstimmigkeit auflösen | #6 (In-Game Resource Browser) |
| Indexierungs-Frage (0-based vs 1-based) | #3 + #5 + #6 (alle 3 sagen 1-based) |
| Nicht-konforme Built-ins checken (`format()`, etc.) | Alle 5 Web-Quellen: wenn nirgends gelistet → game-intern |