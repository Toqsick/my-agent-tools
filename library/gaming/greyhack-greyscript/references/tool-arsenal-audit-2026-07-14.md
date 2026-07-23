# Tool Arsenal Audit — Methodology & Findings (2026-07-14)

## Real-World Data Point

**Geprüft:** 39 GreyScript `.src` Files im Spielordner `yuno-tools/` (38) + `yunu-tools/` (1)
**Build-Pflicht (`//command:` Direktive):** 0 von 39 Files haben sie als erste Zeile

## Methodik (wiederverwendbares Pattern)

### Phase 1 — Directory Survey
```
ls *.src                                   # alle Files auflisten
du -ch *.src                               # Gesamtgröße
```

### Phase 2 — First-Line + LoC Extraction (batch)
Nutze `head -n1` + `wc -l` für alle Files in einem Terminal-Call:

```bash
for f in *.src; do
  FIRST=$(head -n1 "$f")
  LOC=$(wc -l < "$f")
  echo "FILE: $f | LOC: $LOC | FIRST: ${FIRST:0:80}"
done
```

### Phase 3 — Per-File Deep Read (parallel batch)
Lese 6-8 Files parallel via `read_file` für detaillierte Analyse (Zweck, verwendete Libraries). Für große Files (>500 Zeilen) reichen die ersten 50 Zeilen.

### Phase 4 — Independent Sub-Verification
Spawn eine `delegate_task`-Sub-Biene mit exakt demselben Ziel, aber **ohne die vorherigen Ergebnisse zu teilen**:

```
Ziel: Prüfe für jedes .src File ob die erste Zeile mit `//command:` beginnt
Output: Markdown-Tabelle + Summary
```

Vergleiche Sub-Bienen-Ergebnis mit eigener Analyse. Bei Abweichung → manuelle Klärung.

### Phase 5 — Structured Output (3 Files)
1. **Vault-Markdown** — ausführlicher Katalog mit Status-Klassifizierung, Tabellen, Empfehlungen → `/OBSIDIAN_VAULT/09 System-Doku/GreyHack/`
2. **JSON-Arsenal** — maschinenlesbar mit allen Properties (LoC, Libraries, Status) → `/tmp/gh-fullscan-beta/{session}.json`
3. **Sub-Verify-MD** — vom Sub-Agenten unabhängig erstellte Tabelle → `/tmp/gh-fullscan-beta/{session}-sub.md`

### Phase 6 — Self-Verification
Nach dem Schreiben: prüfe dass ALLE drei Output-Files existieren, JSON valide ist, Counts übereinstimmen.

## Erkenntnisse für den Arsenal-Katalog

Jeder Eintrag im Katalog hat diese Felder:

| Feld | Beispiel | Quelle |
|------|----------|--------|
| File | `strike1_dee_grettib.src` | `ls` |
| LoC | 77 | `wc -l` |
| Zweck (1-2 Sätze) | "Strike #1: Dee Grettib — SSH + /home + Bank.txt + Mail.txt" | Code-Analyse |
| Status | active / dead / test / prototype / demo / flagships | Bewertung |
| Libraries | metaxploit.so, crypto.so | `include_lib()` grep |
| Deploy-Listed | true/false | In `yuno-deploy.sh` erwähnt? |

### Status-Klassifizierung

| Status | Kriterium | Beispiel |
|--------|-----------|----------|
| **active** | Deploy-Listed ODER aktiv genutzt, funktionsfähig | `strike1_dee_grettib`, `bank_grab` |
| **dead** | Vorgänger einer neueren Version, obsolete Targets | Alle `dee_hack*`, `mission_*` |
| **test** | Nur lokaler Mock, kein externes Target | `test_local_v3`, `dee_recon` |
| **prototype** | Unvollständig, Work-in-Progress | `bruteforce.src`, `viper.src` |
| **demo/mock** | Nur Print-Output, keine echte Verbindung | `dee_strike_pure`, `hardening_pure` |
| **flagship** | Aktiv gepflegtes Haupt-Framework | `yuno_v6.src` (2462 LoC) |
| **library** | Passive Code-Bibliothek, wird nicht direkt deployed | `viper.src` (4189 LoC, AES128) |

## Empfehlungen (aus dem Audit)

1. **`yunu-tools/` löschen** — Tippfehler-Dir, 1 obsoletes File
2. **Dead-Pool aufräumen** — 14 `dee_hack*`/`dee_strike*`/`mission_*` Files ohne aktiven Wert
3. **`yuno_v1-v5` archivieren** — nur `yuno_v6` ist aktiv
4. **`yuno-deploy.sh` um `yuno_v6.src` erweitern** — aktuell fehlt das Flagship
5. **Hardcoded IP in `yuno-deploy.sh` ersetzen** — `hostname -I | awk '{print $1}'`