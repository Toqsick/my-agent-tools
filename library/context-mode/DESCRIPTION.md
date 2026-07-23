# context-mode — Skill-Beschreibung

**Name:** context-mode
**Version:** 1.0.0
**Autor:** mksglu
**Quelle:** https://github.com/mksglu/claude-context-mode
**Installs:** trending (2.5K+ GitHub Stars)
**Lizenz:** MIT

## Was ist das?

Context Window Optimierung für AI-Coding-Agenten. Reduziert Token-Verbrauch durch Output-Virtualisierung — große Tool-Ausgaben werden sandboxed, bevor sie in den Context fließen. Reduktion um bis zu 98%.

## Wann nutzen?

Bei ALLEN Operationen die >20 Zeilen Output produzieren können:
- Log-Analyse, Build-Output, Test-Results
- API-Responses, JSON-Daten
- Browser-Snapshots, DOM-Struktur
- Git-Log, Diffs, Codebase-Statistiken
- Dependency-Trees, CI/CD-Output
- Jede MCP-Tool-Ausgabe die 20+ Zeilen überschreitet

## Das Prinzip

**Bash-Whitelist** (direkt ausführen, garantiert kleiner Output):
- `cd`, `ls`, `pwd`, `echo`, `cat` (kurze Dateien)
- `which`, `type`, `head`, `tail`, `wc`
- `export`, `unset`

**Alles andere** → Output vor dem Einlesen prüfen:
```bash
# SCHLECHT: 5000 Zeilen Log direkt lesen
cat /var/log/syslog

# GUT: Erst Länge checken, dann einschränken
wc -l /var/log/syslog          # → 5234 Zeilen
tail -50 /var/log/syslog       # Nur letzte 50
grep "ERROR" /var/log/syslog | tail -20  # Nur Errors
```

## Die 5 Regeln

1. **Immer `wc -l` oder `head` vor `cat`** bei unbekannten Dateien
2. **`grep` + `tail` statt vollständiges Lesen** bei Logs
3. **`jq` für JSON** statt rohes `cat`
4. **`--limit` Parameter** bei Hermes-Tools nutzen (`read_file` hat `limit=500`)
5. **Subagent-Briefings**: Explizit "Output >100 Zeilen → head/wc-l verwenden"

## Integration mit Hermes

Hermes hat bereits eingebaute Schutzmaßnahmen:
- `read_file` limitiert auf 500 Zeilen default
- `web_extract` summarisiert große Seiten
- Context-Compaction bei vollem Window

Der Context-Mode-Ansatz ergänzt dies durch bewusstes Output-Management BEIM Tool-Aufruf, nicht erst beim Lesen.

## Vorteile

| Aspekt | Ohne Context-Mode | Mit Context-Mode |
|--------|-------------------|------------------|
| Token-Verbrauch | Hoch (voller Output) | Niedrig (gefiltert) |
| Context-Limit | Schnell erreicht | Später erreicht |
| Performance | Langsamer | Schneller |
| Kosten | Höher | Niedriger |

## Einschränkungen

- Erfordert Disziplin bei jedem Tool-Aufruf
- Nicht alle Tools unterstützen `--limit` Parameter
- Subagents müssen explizit brieft werden

## Referenz

- GitHub: https://github.com/mksglu/claude-context-mode
- Skills.sh: https://skills.sh/mksglu/claude-context-mode
