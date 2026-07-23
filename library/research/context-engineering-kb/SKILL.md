---
name: context-engineering-kb
description: "Kuratiere Paper/Blogs zu Context-Engineering als Wiki."
version: 1.0.0
author: Yuno for Basti
license: MIT
lane: koenigin
agent: Yuno
trigger_keywords:
  - kontext diät
  - context diet research
  - context engineering literatur
  - token diät wissensbasis
  - prompt dilution forschung
  - kv cache hygiene paper
keywords:
  - context-engineering
  - knowledge-base
  - research
  - token-budget
  - prompt-engineering
related_skills:
  - llm-wiki
  - research-tools
  - hermes-context-budget
  - arxiv
last_curated: 2026-07-21
curated_by: Yuno
routing_hint: "Use when Basti externe Quellen zu Context-Engineering-Themen sammeln und als Wiki kuratieren will."
---

# Context-Engineering Knowledge Base

Baut eine domänenspezifische Wissensbasis zu LLM-Context-Engineering auf: Token-Diäten, Prompt-Dilution, KV-Cache-Hygiene, Context Rot, Attention Budget, JIT-Retrieval, Compaction-Strategien. Differenz zum allgemeinen `llm-wiki`: feste Domain, kuratierte Quellliste, gezielte Multi-Angle-Suche pro Konzept, periodische Auffrischung.

## Scope und Abgrenzung

In-Scope: Externe Literatur (Papers, Blogposts, Gists, Talks, Threads) zu Context-Engineering-Themen. Aufbau und Pflege einer strukturierten Wissensbasis.

Out-of-Scope: Eigene Context-Budget-Regeln für den laufenden Agent-Betrieb (das macht `hermes-context-budget`). Allgemeine Wiki-Mechanik ohne Domainbezug (das macht `llm-wiki`).

## Wiki-Pfad

`WIKI_PATH="${CONTEXT_KB_PATH:-$HOME/wiki/context-engineering}"`

Seperate Wiki-Instanz, nicht das generelle `~/wiki/`. Hält die Domain fokussiert und verhindert Cross-Domain-Kontamination.

## Domain-Tag-Taxonomie

Feste Tags für diese KB (SCHEMA.md des Wikis):

| Tag | Bedeutung |
|---|---|
| `token-budget` | Token-Ökonomie, Context-Window-Auslastung |
| `prompt-dilution` | Prompt-Qualitätsverlust durch Kontext-Menge |
| `kv-cache` | KV-Cache-Hygiene, Hit-Rate, Latency |
| `context-rot` | Kontext-Vergiftung, Drift über lange Tasks |
| `jit-retrieval` | Just-in-Time Loading vs. Preload |
| `compaction` | Zusammenfassungs-Strategien, Levels |
| `subagent-isolation` | Context-Cross-Contamination-Vermeidung |
| `attention-budget` | Aufmerksamkeitsverteilung im Window |
| `few-shot-decay` | Degradation durch Beispiel-Schatten |
| `tool-output-hygiene` | Token-effiziente Tool-Returns |

## STEP 1: Research-Angle erfassen

Bevor Suche losgeht, konkreten Winkel klären:

1. Konzept: Welches der 10 Tags oben? Oder neues?
2. Quellentyp: Paper (arXiv), Blogpost (Firmenblogs), Thread, GitHub-Gist, Vortrag?
3. Frische: Nur 2025+ oder auch ältere Fundament-Paper?
4. Tiefe: Quick-Scan (3 Quellen) oder Deep-Dive (10+ Quellen mit Vergleich)?

Bei vagem Auftrag ("zeig mal was zu Context-Diät") Default: Tag `token-budget`, Quellenmix Paper+Blog, Frische 2024+, Tiefe Deep-Dive.

## STEP 2: Multi-Angle Source Discovery

Parallele `web_search`-Calls, mindestens 4 Winkel:

| Winkel | Query-Vorlage | Zweck |
|---|---|---|
| Akademisch | `site:arxiv.org <konzept> LLM context` | Peer-reviewte Fundamente |
| Praxis-Blog | `<konzept> agent context engineering blog` | Eingesetzte Rezepte |
| Community | `site:reddit.com/r/LocalLLaMA <konzept>` | Realwelt-Fehlschläge |
| Vendor | `site:anthropic.com OR site:openai.com <konzept>` | Offizielle Guidance |

Zusätzlich bei Paper-Fokus: `arxiv search "<konzept> context window"` via `arxiv`-Skill.

Ergebnis: 10 bis 20 Kandidaten-URLs.

## STEP 3: URL-Verifikation

Aus `research-tools` übernommen:

- Jede URL taggen: `[VERIFIED]` (geladen), `[UNVERIFIED]` (Snippet-only), `[UNREACHABLE]`
- Nur `[VERIFIED]` zählt als Evidenz
- `web_extract` mit `char_limit=10000`, bei Paper-PDFs `char_limit=20000`
- Keine synthetisierten Inhalte aus Snippets erfinden

Bei Cloudflare/403: `curl -sL --compressed` als Fallback, HTML strippen via `sed 's/<[^>]*>//g'`.

## STEP 4: Wiki-Ingest

Folge `llm-wiki` Ingest-Workflow, angepasst:

1. Raw capture: `raw/articles/` (Blogs), `raw/papers/` (arXiv), `raw/threads/` (Reddit/Twitter). Frontmatter mit `source_url`, `ingested`, `sha256`.
2. Takeaways mit Basti besprechen (außer bei automatisierten Cron-Läufen).
3. Existierende Seiten prüfen: `index.md` lesen, `search_files` über das Wiki.
4. Seiten schreiben oder aktualisieren:
   - Neue Konzeptseite bei Tag-Zentralität oder 2+ Quellen
   - Bestehende Seiten updaten mit neuem `updated:`-Datum
   - Mindestens 2 `[[wikilinks]]` outbound pro Seite
   - `confidence:` setzen: `low` bei Einzelquelle, `medium` bei 2 bis 3, `high` bei 4+ konvergenten Quellen
   - `contested: true` bei Widersprüchen zwischen Quellen
5. Navigation updaten: `index.md` und `log.md`.

## STEP 5: Cross-Link und Synthese

Nach 3+ Ingests zu verwandten Konzepten: Comparison-Seite erstellen. Beispiel: `compaction-strategien-vergleich.md` vergleicht Token-Budget-Compaction vs. Subagent-Isolation vs. JIT-Retrieval mit Tabelle über Vor- und Nachteile.

## STEP 6: Periodische Auffrischung

Einmal pro Quartal oder bei explizitem Trigger:

1. `log.md` nach letzten 30 Einträgen scannen
2. Für jede Seite mit `updated:` älter als 90 Tage: `web_search` nach neueren Quellen zum Tag
3. Bei neuen Relevanten: STEP 2 bis 4 durchlaufen
4. `contested: true`-Seiten re-evaluieren
5. Log-Eintrag: `## [YYYY-MM-DD] refresh | Quartals-Auffrischung`

Cron-tauglich: STEP 6 lässt sich automatisieren. Vollautomatische Ingests bekommen `confidence: low` und Log-Markierung zur späteren Kuratierung.

## Quick-Start-Rezept

Basti sagt "bau mir eine Context-Diät-Wissensbasis auf". Default-Pfad:

1. Wiki initialisieren falls nicht vorhanden (SCHEMA.md, index.md, log.md mit obiger Taxonomie)
2. 4 Winkel parallel für `token-budget`: arXiv, Anthropic-Blog, LocalLLaMA, OpenAI-Docs
3. 8 bis 10 Quellen verifizieren
4. 5 bis 7 Konzeptseiten anlegen (Token-Budget-Grundlagen, 85%-Regel, KV-Cache-Hygiene, Context-Rot, JIT-Retrieval)
5. 1 Comparison-Seite: "Compaction-Strategien"
6. Ergebnis präsentieren: Wiki-Pfad, Index-Übersicht, offene Fragen

## Pitfalls

- Quellen ohne Verifikation: Snippets sehen oft informativ aus, sind aber trunciert oder veraltet. Immer `web_extract` oder `curl` nachladen.
- Tag-Sprawl: Nur die 10 definierten Tags verwenden. Neue Konzepte erst in SCHEMA.md eintragen, dann nutzen.
- Context-Window-Überlastung bei der Recherche selbst: ironic. Bei 10+ Quellen in Subagent auslagern (`delegate_task`), nur Synthese im Hauptkontext behalten. Siehe `hermes-context-budget`.
- Duplicate-Pages: Vor dem Anlegen immer `search_files` über das Wiki. Lieber vorhandene Seite updaten als neue erstellen.
- Alte Paper als Dogma: Context-Engineering entwickelt sich schnell. Paper von 2023 können veraltet sein. `confidence:` konservativ setzen bei älteren Fundament-Quellen.
- Cron-Läufe ohne Mensch: Vollautomatisierte Ingests sollten `confidence: low` setzen und im Log markieren, damit Basti später kuratieren kann.