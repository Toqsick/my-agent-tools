# Beispiel-Audit: Grok 4.5 / Grok Build CLI / MiroFish (2026-07-13)

Dies ist ein **realer Audit-Fall**, der genau zeigt, wie der
"Forensischer Secret-Audit für Cloud-Coding-Agenten"-Workflow in der Praxis
läuft. Reproduzierbar aus `~/.hermes/docus/audits/grok45-mirofish-audit-2026-07-13.md`
(SHA256 `cec37d9c…7edd06`, Mode 0600).

## Wer hat's gemeldet?

Basti las eine Nachrichtenmeldung: *"Das neue GROK 4.5 Modell leakt GitHub
Repos / sendet Deep Research nach xAI"*. Er hatte am 11.07.2026 Grok 4.5 zur
Installation eines Open-Source-Tools (MiroFish von GitHub) genutzt und bat
um eine forensische Prüfung.

## Was die Meldung wirklich beschreibt (Phase 1: Headline entkoppelt)

Die Originalmeldung nennt das **Modell** `grok-4.5`. Die Primärquelle
(GitHub-Gist von `cereblab`) und das dazugehörige Repro-Repo
(`grok-build-exfil-repro`) zeigen: betroffen ist die **offizielle Grok Build
CLI v0.2.93** — also ein Produkt-Harness, nicht das Modell selbst.

Mechanismus (zwei Kanäle):
- `POST /v1/responses` → normaler Modell-Turn mit vom Agent gelesenen Inhalten
- `POST /v1/storage` → zusätzlicher Upload eines Git-Bundles mit allen
  getrackten Dateien + Git-Historie, unabhängig davon, was der Agent gelesen
  hatte. Zielpfad: GCS-Bucket `grok-code-session-traces`

Drei weitere relevante Fakten aus der Primärquelle:
- 12-GB-Testrepo: 5,10 GiB über den Storage-Kanal, 192 KB über den Modellkanal.
- `"Improve the model"` stoppte den Upload ursprünglich **nicht**.
- xAI hat den Whole-Repo-Upload laut Vergleichsdoku am 2026-07-13 serverseitig
  deaktiviert (`trace_upload_enabled: false`, neuer Flag
  `disable_codebase_upload: true`).
- Folgeproblem (v0.2.99): `--deny Read(file)` blockiert nur den Read-Pfad,
  nicht den Storage-Upload. Schutz bietet nur `gitignore`.

## Was lief bei Basti tatsächlich (Phase 2: Tool-Lokalisierung)

Hermes-Agentenlog (`~/.hermes/logs/agent.log`, Session
`hermes_20260711_224811_a8d58a`):

```text
model=x-ai/grok-4.5
provider=nous
base_url=https://inference-api.nousresearch.com/v1
```

Schnellprofil-Check brachte: Keine `grok`-/`grok-build`-Binary, kein
`~/.grok/`, keine Grok-Prozesse, kein Grok-Backend → der Mechanismus konnte
lokal **nicht** gefeuert haben.

## Lokale Timeline (Phase 3, Auszug)

| Zeit (CEST) | Ereignis |
|---|---|
| 22:48:12 | Hermes-Session-Start, model=`x-ai/grok-4.5`, provider=`nous` |
| 22:48:19–23:25 | 60× Grok 4.5, 7× DeepSeek-v4-Flash, 6× MiniMax-M3, 73 API-Calls, ~7.1 Mio Input-Tokens |
| 22:48:29 | Git-Clone `https://github.com/666ghj/MiroFish.git` |
| 22:48:29–22:54 | npm + uv Backend-Install |
| 22:59:14 | `start-mirofish.sh` + `SETUP-LOKAL.md` geschrieben |
| 23:03 | Zep-API-Key vom User im Chat (Message 77130) + im Tool-Call 77131 zur `.env` geschrieben |
| 23:03:25 | MiniMax-Key aus `~/.hermes/.env` per Shell-Expansion in `.env` kopiert; `.env` Mode 0600 |
| 23:04–00:00 | Test-Simulation, Report, Doku (im Verlauf des 11.07. & 12.07.) |

## Secret-Audit-Ergebnis (Phase 4)

Aus `audit-secret-spread.py`:

```text
Session: 20260711_224811_a8d58a
Repo:    /home/bratan/10-Projekte/20-experimental/MiroFish
Messages: 195 | Secrets: 2

  🔴 ZEP_API_KEY              prefix='z_1d'    len=149   msgs=2   tools=1   → OFFENGELT
    file=.env
  🟢 LLM_API_KEY              prefix='sk-c'   len=125   msgs=0   tools=0   → kein Leak-Pfad über Inferenz
    file=.env

Analyse: 1/2 Schlüssel in Modellkontext nachweisbar.
```

`ZEP_API_KEY` tauchte in **zwei Messages** und **einem Tool-Call** auf.
`LLM_API_KEY` (MiniMax) wurde ausschließlich in die lokale `.env` kopiert und
erschien nie im Modellkontext — `.env` Mode 0600, nicht in Git-Historie.

## Empfohlener Reporting-Workflow (dieser Fall)

1. ✓ Komplett-Audit durchgezogen, alles notiert
2. ✓ Bericht in `~/.hermes/docus/audits/grok45-mirofish-audit-2026-07-13.md` (Mode 0600, 16,6 KB)
3. ✓ Vault-Spiegel in `~/Dokumente/Obsidian Vault/09 System-Doku/Security/Grok-4.5 & MiroFish - Forensik-Audit 2026-07-13.md`
4. ✓ Mnemosyne-Memory (scope global, importance 0.85) mit Audit-Outcome
5. ⏸️ Auf Bastis Freigabe warten, bevor Zep-Key rotiert wird

## Lessons Learned (für künftige Audits)

1. **Headlines ≠ Mechanismus.** "Grok 4.5 leakt Repos" wird in der News ohne
   Quellenangabe wiedergegeben. Die Primärquelle (Gist + Repro) zeigt klar den
   betroffenen Produkt-Harness und das exakte Datenkanal-Pattern.
   → **Immer zuerst:** Welches Produkt? Welcher Kanal? Welche Version?
2. **Gepostete Keys sind per Definition P0.** Auch wenn der Mechanismus (z.B.
   Grok-Build-CLI) lokal nicht installiert ist: sobald ein User einen Schlüssel
   in den Chat pastet, der dann in einen Tool-Call zur `.env` fließt, ist der
   Wert im Modellkontext. Rotation muss freigegeben, nicht auto-fixiert werden.
3. **Sub-Streams in Multi-Provider-Sessions sind alle betroffen.** Wenn eine
   Session zwischen Grok, DeepSeek und MiniMax wechselt, wurde der gepostete
   Schlüssel an jeden dieser Provider gesendet. Bei Retention-Anfragen muss
   jeder separat angefragt werden.
4. **`audit-secret-spread.py` lohnt sich.** Die SQLite-RO-Correlation liefert
   in 3 Sekunden einen deterministischen Beleg statt eines Bauchgefühls.
   Mode-ro URI ist Pflicht, sonst können WAL-Header versehentlich modifiziert
   werden.
5. **Basti-Präferenz: erst Bericht, dann freigeben lassen.** Er hat in der
   Vergangenheit mehrfach klargestellt: bei sicherheitsrelevanten Aktionen
   zuerst dokumentieren, dann auf explizite Zustimmung warten. Auch wenn
   Yuno-Reflex wäre "direkt fixen" — hier ist Reihenfolge wichtiger als Speed.

## Wann dieses Beispiel reproduzieren?

- Bei jeder Nachrichtenmeldung mit "KI leakt Daten"-Charakter.
- Wenn User berichtet, er habe ein Cloud-Produkt (Claude Code, Codex CLI,
  Hermes, Grok Build, Copilot CLI, OpenCode) lokal eingesetzt.
- Bei Verdacht auf ganze Repo-Exfiltration (großer Tokenverbrauch ohne
  sichtbaren Input).
- Als Reaction-Check nach SaaS-Provider-Datenschutz-Meldungen.
