# Pattern-Governance (NEU 2026-07-22)

Seit PR #66 (gemerged 2026-07-21) hat das Repo `Toqsick/greyscripts` eine
**Pattern-Governance-Architektur** als additive Schicht über dem Legacy-Code.
Dieses Dokument erklärt die Struktur, die CI-Jobs und wie neue Pattern promoted
werden.

## Struktur

```
patterns/
├── build/        # Local-Tool-Build-Pattern
├── cli/          # CLI-Output/Table-Pattern
├── files/        # File-Read/Write/Tree/Permissions-Pattern
├── net/          # Net-Connect-Check-Pattern
├── router/       # Router-Lookup-Pattern
├── typing/       # Input-Validation-Pattern
└── verified/     # 7 verified + 1 deprecated Gegenbeispiel
```

Jede Kategorie enthält GreyScript-Pattern-Dateien (`.src`) plus optional
`.meta.md`-Files für Metadaten (Score, Source-Origin, etc.).

## Score-System

| Score-Class | Level | Status |
|-------------|-------|--------|
| A | `verified` | promoted, in `patterns/verified/index.md` |
| B | `reviewed` | reviewed, nicht promoted |
| C | `draft` | work in progress |

**Promotion-Regel:** Score ≥90/100 + reviewed → Level: verified.
**Deprecated-Gegenbeispiel:** Score 80-89, dokumentiert warum es NICHT der
neue Standard ist.

## 12 verified-Patterns (PR #66 + PR #67)

| Pattern | Score | Quelle |
|---------|-------|--------|
| `patterns/files/file-read-safe.src` | 93/100 | `src/core/filecore.src` (`fc_read`) |
| `patterns/files/file-write-safe.src` | 91/100 | `src/core/filecore.src` (`fc_write`) |
| `patterns/files/file-tree-walk.src` | 92/100 | `src/security/hardening.src` (`list_children`+`chmod_recursive`) |
| `patterns/files/file-permissions-scan.src` | 91/100 | `src/tools/suid_exploit.src` (`suid_scan_local`) |
| `patterns/typing/validate-typed-input.src` | 94/100 | `src/core/netcore.src` (`validIP`) |
| `patterns/typing/guard-numeric-range.src` | 93/100 | `src/crypto/grsa_v2.src` (`rsa_generate` n <= 255) |
| `patterns/net/net-connect-check.src` | 91/100 | `src/core/netcore.src` (`getRouter`+`getPortsOfTarget`) |
| `patterns/router/router-lookup.src` | 92/100 | `src/core/netcore.src` (`getRouter`/`publicIP`/`localIP`) |
| `patterns/cli/cli-output.src` | 90/100 | `src/core/cli_core.src` (Teilmenge) |
| `patterns/cli/cli-table.src` | 90/100 | `src/core/cli_core.src` (`cli_repeat`+`cli_pad`+`cli_width`+`cli_table`) |
| `patterns/build/build-local-tool.src` | 92/100 | Template-Referenz |
| `patterns/build/build-local-tool-old.src` | 84/100 | Deprecated Gegenbeispiel |

## CI-Job `pattern-governance`

Im `.github/workflows/ci.yml` ist seit PR #66 der Job `pattern-governance`
hinzugefügt. Er ruft `make check-all` auf, was 5 Checks ausführt:

1. `check-doc-links.sh` — Wiki-Cross-Links zwischen `docs/patterns/*.md`
2. `check-meta.sh` — Meta-Files (`*.meta.md`) haben konsistente Score-Klasse
3. `check-naming.sh` — Pattern-Files folgen Naming-Convention
4. `check-pattern-layout.sh` — alle Pattern starten mit `get_shell` oder
   sind explizit als "kein System-Zugriff nötig" markiert (siehe
   Known Warnings)
5. `check-verified-index.sh` — `patterns/verified/index.md` listet alle
   verified-Patterns korrekt auf

**Lokaler Test:** `make check-all` aus dem Repo-Root.

## Unterstrich-API-Konvention (Pflicht)

Alle verified-Patterns verwenden die **Unterstrich-API-Formen**:

- `get_shell` (nicht `getshell`)
- `host_computer` (nicht `hostComputer`)
- `get_content` (nicht `getcontent`)
- `set_content` (nicht `setcontent`)
- `get_ports` (nicht `getports`)
- `device_ports` (nicht `deviceports`)
- `network_gateway` (nicht `networkGateway`)

**Historie:** Commit #61 (PR #61) hat diese Konvention festgelegt.
`tests/test_src_regressions.py` prüft dass die no-underscore-Formen in
Grey Hack **nicht existieren und zur Laufzeit crashen**.

## Promotion-Workflow (neues Pattern hinzufügen)

1. **Identifikation:** Suche nach `src/<category>/*.src` Funktionen die
   isoliert als Einzweck-Pattern funktionieren
2. **Extraktion:** Erstelle `patterns/<category>/<name>.src` mit Unterstrich-API
3. **Meta-File:** Erstelle `patterns/<category>/<name>.meta.md` mit Score,
   Source-Origin, Beschreibung
4. **Lokaler Check:** `make check-all` muss grün sein
5. **Review:** Score ≥90 + reviewed (PR-Reviewer) → Level: verified
6. **Promotion:** PR öffnen mit `refactor/pattern-promotions-N` Branch

## Known Warnings (akzeptiert)

4 Patterns haben ehrliche WARN-Zeilen in `check-pattern-layout.sh`, weil sie
kein `get_shell` brauchen:

| Datei | Warum kein `get_shell` |
|-------|------------------------|
| `patterns/typing/validate-typed-input.src` | Reine String-/Zahl-Validierung |
| `patterns/typing/guard-numeric-range.src` | Reine Wert-Pruefung |
| `patterns/cli/cli-output.src` | Reine Ausgabelogik |
| `patterns/cli/cli-table.src` | Reine Tab-Formatierung |

Diese sind by-design und in `KNOWN-WARNINGS.md` dokumentiert.

## Was bewusst NICHT migriert wird

| Bereich | Warum |
|---------|-------|
| `src/**` physische Pfade | `tests/test_src_regressions.py` prüft feste Pfade; `import_code` läuft nur in-game |
| `greyhack-tools/**` | funktionale Tools/Monolithen, keine Einzweck-Referenzmuster |
| `docs/**` Legacy | bestehende Bug-/Audit-Docs bleiben; Governance-Docs liegen unter `docs/patterns/` |
| `scripts/ci-build.sh`, `hermes-automation.py` | unverändert; nur ergänzt (CI-Job `pattern-governance`) |

## Prinzip

Migriert wird nur was zu einem sauberen, einzweckigen Referenzmuster
(≥ 90/100) umgeschrieben werden kann. Es gibt **keine halb-migrierten Pfade**
in `patterns/`; alles andere bleibt lauffähig im Repo oder ist benannter
Kandidat in `patterns/verified-candidates.md`.

## Migration-Map (Detail)

→ `MIGRATION-MAP.md` im Repo-Root listet alle 12+4 promoted Patterns
mit Quelle, Zielpfad, Kategorie, Score, Status. Update-Checkliste für
zukünftige Promotions.