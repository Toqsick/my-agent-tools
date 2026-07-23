# External Analysis Verification Workflow

> **Eingesetzt:** 2026-07-07 (Claude-Audit von 248 Hermes Skills)
> **Ergebnis:** 7 Claims verifiziert, 1 Major-Misinterpretation korrigiert, 55MB gespart
> **Kern:** Externe Audits sind KEINE Wahrheit — immer Code lesen vor Vertrauen.

## Der 6-Phasen-Flow

```
Empfang → Claims extrahieren → Live-Code prüfen → Safe Fixes → Mnemosyne → Report
Phase 1         Phase 1           Phase 2        Phase 3       Phase 4    Phase 5
                                                                    ↓
                                                              Phase 6: Korrektur
                                                              in Skill verewigen
```

## Phase 1: Empfang + Struktur-Erfassung

### Eingabe-Formate

| Format | Aktion |
|--------|--------|
| Zwei Files (Report + Fix-Skript) | Beide lesen — Fix-Skript zeigt Autor-Intention |
| Einzel-File | Report-Struktur parsen, Claims markieren |
| Analyse-Text | Manuell Claims extrahieren — Begriffe zählen |

### Claims extrahieren

Nur **überprüfbare Behauptungen** notieren:

| Claim-Kategorie | Erkennung | Beispiel |
|---|---|---|
| **Zahlen** | "N Stücke", "N% Overhead" | "0/72 Hash-Matches" |
| **Pfade** | "/pfad/zu/datei" | "140 hardcoded /home/bratan" |
| **Code-Zitate** | "Funktion X macht Y" | "skill_usage.py verhindert Load" |
| **Strukturen** | "N Skills über M Verzeichnisse" | "8 GreyHack-Skills, 3 Orte" |

### Priorität zuweisen

Autor-Bewertung übernehmen, aber ohne blind zu vertrauen:

- P0: "Security", "Kritisch", "Zerstört" → **höchste Prüfpriorität** (hier liegen die Fehlinterpretationen)
- P1: "Wichtig", "Sollte fixen" → normale Prüfung
- P2: "Nice-to-have" → oberflächliche Prüfung
- P3: "Vorschlag", "Optional" → ignorieren wenn andere Claims wichtiger sind

**Erfahrung 2026-07-07:** Der P0-Claim "0/72 Hash-Tod" war die größte Fehlinterpretation. P0-Claims sind am riskantesten für Overreaction.

## Phase 2: Live-Verifikation

### Tool-Strategie

| Claim-Typ | Verifikationstool | Beispiel |
|-----------|-------------------|----------|
| **Datei-Existenz** | `ls -la`, `cat` | `.bundled_manifest` existiert? |
| **Eintragsanzahl** | `wc -l`, `grep -c` | Wieviele Einträge im Manifest? |
| **Code-Logik** | `grep -rn`, Code-Read | WAS macht `skill_usage.py` wirklich? |
| **Storage** | `du -sh` | Speicher-Overhead live messen |
| **Verzeichnisstruktur** | `ls -R`, `find` | GreyHack-Skills über N Verzeichnisse |
| **Hardcoded-Paths** | `grep -rn '/home/bratan'` | Count vs. Kontext prüfen |

### Live-Code-Reads

Für Code-Logik-Claims: **Immer den tatsächlichen Code lesen**, nie nur die Doku.

```bash
# Code-Pfad finden (tools/ oder agent/)
grep -rn '<Funktion>' ~/.hermes/hermes-agent/tools/ --include='*.py'

# Code lesen
cat -n tools/skills_sync.py | head -50
```

### 3 Outcomes pro Claim

| Outcome | Bedeutung | Kriterium | Aktion |
|---------|-----------|-----------|--------|
| 🟩 **Bestätigt** | Audit hat recht | Zahlen stimmen, Code-Logik bestätigt | In Fix-Plan aufnehmen |
| 🟨 **Teils richtig** | Kernwahrheit, aber Fehlinterpretation | Zahl stimmt, aber Bedeutung ist anders | Adjustiert speichern, Korrektur-Lesson |
| 🟥 **Falsch** | Nicht belegbar | Code zeigt andere Logik, Zahl stimmt nicht | Mnemosyne-Lesson mit Gegenbeweis |

**Faustregel:** Wenn der Audit ein Problem sieht, wo ein Dev-Tool eine *Feature*-Entscheidung getroffen hat, ist es meist 🟨 oder 🟥.

#### Klassischer Fall 2026-07-07: `.bundled_manifest`

```
Audit-Interpretation: "Hash-Provenance-System → 0/72 Matches = Supply-Chain-Angriff"
→ Code-Read: tools/skills_sync.py verwendet Manifest als "wurde modifiziert? → skip update"-Tracker
→ Wahrheit: 0/72 = alle Skills wurden lokal modifiziert = **erwünschtes Verhalten**
→ Ergebnis: 🟥 Falsch
→ Lesson gespeichert mit tags: ["hermes", "audit-correction", "bundled_manifest"]
```

## Phase 3: Fixes anwenden

### Safe Fixes (immer OK)

| Fix | Command | Rückgängig |
|-----|---------|------------|
| Python-Bytecode | `find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null` | ✗ autom. Neugenerierung |
| Backup-Rekursion | `rm -rf .archive/<snapshot>/.hub .archive/<snapshot>/.curator_backups` | Docker-Neusync |
| Curator-Retention | `ls -1dt .curator_backups/*/ \| tail -n +4 \| while read old; do rm -rf "$old"; done` | Nur Backup-Verlust |
| Manifest neugenerieren | `find . -name SKILL.md \| while read f; do ...; done > .bundled_manifest.sha256` | Git-Restore |

### Unsafe Fixes (NICHT ohne Freigabe)

| Fix | Grund | Benötigt |
|-----|-------|----------|
| Code patchen | Hermes-Framework-Änderung | Basti-Freigabe + PR |
| Configs ändern | Können Gateway/Provider beeinflussen | Basti-Freigabe |
| Services restarten | Produktionsunterbrechung | Basti-Freigabe |
| Pfade auslagern | Verschieben = Code-Änderung | Basti-Freigabe |
| Skills löschen | Curator-Veto + Datenverlust | Basti-Freigabe |

### Storage-Messung

Vorher/Nachher dokumentieren:

```bash
echo "Vorher:" && du -sh ~/.hermes/skills/
# ... Fixes anwenden ...
echo "Nachher:" && du -sh ~/.hermes/skills/
echo "Gespart: $((VORHER - NACHER)) MB"
```

## Phase 4: Mnemosyne-Lessons

### Pflicht-Lessons nach Audit

| Lesson | Content-Fokus | Tags | Importance |
|--------|---------------|------|------------|
| 1. Korrektur | Was falsch war + Code-Beweis + Gegenbeweis | `audit-correction, <domain>` | 0.75 |
| 2. Fix-Report | Was angewendet + wieviel gespart + was offen | `audit-fix, cleanup, applied` | 0.8 |

### Tags-Schema

```python
tags=["lesson", "hermes", "audit-correction", "<domain>", "verified"]
metadata={
    "category": "self-improving-lesson",
    "status": "verified",
}
```

### Prüfung vor Speichern

Immer prüfen ob schon eine ähnliche Lesson existiert:
```python
mnemosyne_recall(query="audit correction bundled_manifest")
```

## Phase 5: Report-Struktur

```markdown
## 🔬 Yuno's Audit-Review

### Verifizierte Fakten
| # | Claim | Audit sagt | Live geprüft | Status |
|---|-------|-----------|-------------|--------|
| 1 | Hash-Provenance | 🟥 P0 Security | Code: sync-tracker | 🟩 Korrigiert |
| 2 | Usage-Dupes | 🟧 36 Dupes | `du -sh` + inspect | 🟩 Bestätigt |

### Storage-Bilanz
- Vorher: X MB
- Nachher: Y MB
- Gespart: Z MB (N%)

### Angewendete Fixes
1. ✅ Pycache entfernt (N Files)
2. ✅ Archiv-Rekursion gekappt
3. ✅ Curator-Backups (3 behalten)
4. ✅ SHA-256 Manifest (N Einträge)

### Kein Fix (mit Begründung)
| Aus Audit | Nicht gemacht | Grund |
|-----------|--------------|-------|
| Hub-Cache auslagern | ❌ | Pfad hartcodiert in skills_hub.py |
| hardcoded Paths ersetzen | ❌ | Framework-set, kein aktiver Schaden |

### Nächste Schritte
- Phase 2: Usage-Dedup (braucht Code-Änderung)
- Phase 3: Konsolidierung überlappender Skills
```

## Phase 6: Korrektur in Self-Improving

Nach Abschluss: die gesamte Verifikations-Methodik als Best-Practice in `self-improving` SKILL.md verewigen, damit zukünftige Sessions denselben Fehler nicht wiederholen.

---

## Typische Audit-Fehler (aus der Praxis)

| # | Fehler | Symptom | Gegenmittel |
|---|--------|---------|-------------|
| 1 | **Provenance-Überinterpretation** | Ein Sync-Tracker wird als Security-Feature missverstanden | Code lesen, nicht Doku |
| 2 | **Zahlen ohne Kontext** | "36 Dupes!" — aber normal bei 248 Skills | Prüfe ob echte Duplikate |
| 3 | **Hardcoded-Path-Alarm** | "140× /home/bratan!" — vom Framework gesetzt | Prüfe ob Path aktiv schadet |
| 4 | **Doc ≠ Code** | Kommentar sagt X, Code macht Y | Lese den tatsächlichen Code |
| 5 | **False Authority** | Claude/Gemini/Hub-Audit wird blind vertraut | Jeder kann irren — verifiziere alles |
