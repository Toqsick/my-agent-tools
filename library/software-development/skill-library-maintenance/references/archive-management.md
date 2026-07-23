# Archive (.archive/) Management

When the skill library has accumulated `.archive/` snapshots — from curator backups, manual dedup batches, or rollback points — the goal is to distinguish **redundant snapshots** (safe to delete) from **reanimation candidates** (skills that exist only in archive, not in active use).

## Diagnostic Scan

```bash
# 1. Inventory: what's in .archive/ vs active skills?
find ~/.hermes/skills/skills/.archive -maxdepth 1 -mindepth 1 -type d | wc -l
find ~/.hermes/skills/skills/.archive -name "SKILL.md" | wc -l
du -sh ~/.hermes/skills/skills/.archive

# 2. Active skill names (for comparison)
find ~/.hermes/skills ! -path "*/.archive/*" ! -path "*/.hub/*" \
  -maxdepth 4 -name "SKILL.md" 2>/dev/null \
  | xargs grep -h "^name:" | sed 's/name: //' | sort -u

# 3. Reanimation candidates: archive dir names NOT in active set
# (run via execute_code for fuzzy matching)
```

## 0-Risk Duplikat-Removal (bewährtes Pattern)

**Trigger:** Datierte Duplikat-Batches im `.archive/` (z.B. `duplicates-2026-07-02/`, `duplicates-v2-2026-07-02/`).

**Prüf-Schritte vor Löschung:**

| Check | Befehl | Freigabe-Kriterium |
|---|---|---|
| Sind alle Skills aktiv vorhanden? | `find dup-batch/ -name "SKILL.md" \| xargs grep -h "^name:" \| sort -u` vs `find skills/ ... \| xargs grep "^name:" \| sort -u` | Jeder Name muss aktiv existieren |
| Hat der Batch ein Duplikat-Datum? | Pfad enthält Datum (z.B. `2026-07-02`) | Ja → Snapshot-Batch, kein originäres Skill-Paket |
| Ist es ein Zweit-Snapshot? | Zwei Batches vom selben Tag? | Ja → einer ist redundant |

**Wenn ALLE Prüfungen bestehen:**
```bash
rm -rf ~/.hermes/skills/skills/.archive/duplicates-*/   # sicher
```

**Verifiziert 2026-07-04:** 2 Batches (v1 + v2, selber Tag), 302 SKILL.md, 19 MB → `rm -rf` ohne Informationsverlust. OPUS 4.8 hatte 0-Risk vorher bestätigt.

## Reanimations-Kandidaten-Flow

**Frage:** Welche Skills im Archiv gibt es nicht mehr im aktiven Set?

```python
# execute_code-Pseudocode
archive_dirs = [...]     # find .archive/ -maxdepth 1
active_names = {...}      # grep "^name:" in active skills
candidates = [d for d in archive_dirs if d not in active_names]

# Fuzzy-Match für Namens-Varianten
fuzzy = [(d, [a for a in active_names if d.lower() in a.lower()])
         for d in candidates if any(d.lower() in a.lower() for a in active_names)]
```

**3 Kategorien:**

| Kategorie | Aktion | Beispiel (2026-07-04) |
|---|---|---|
| **Exakter Match** | Nichts tun (aktiv + Archiv identisch) | `airtable`, `arxiv`, `excalidraw` — 78/92 |
| **Fuzzy Match** | Prüfen ob Namens-Variante gleicher Skill | `segment-anything` → `segment-anything-model` |
| **❌ Komplett fehlend (Reanimations-Kandidat)** | Entscheidung: reanimieren oder löschen | `comfyui`, `copilot-cli`, `llm-wiki` u.a. — 11/92 |

## Diff-Check (Archiv vs aktiv)

```bash
for skill in skill-name; do
  echo "$skill:"
  wc -c ~/.hermes/skills/skills/.archive/"$skill"/SKILL.md 2>/dev/null || echo "NUR ARCHIV"
  wc -c <(find ~/.hermes/skills -path "*/$skill/SKILL.md" ! -path "*/.archive/*" -exec cat {} +) 2>/dev/null
done
```
Bei Gleichheit → entfernen. Bei Abweichung → max 1 Snapshot behalten.

## Modell-Selektion für Skill-Audit

| Modell | Kosten | Dauer | Genauigkeit | Wann wählen |
|---|---|---|---|---|
| **Fable 5** (Rabat) | ~$0.30-0.50 | Schnell | Gut für vorstrukturierte Judgment-Aufgaben | Inventur, Reanimations-Triage, 80%-Lösung — wenn die Datenbereinigung (md5sum-Diff) vorher lokal gemacht wurde |
| **OPUS 4.8 high** | ~$0.55-0.75 | 5-15 Min | Präzise — validiert Claims | Deep-Dive, Risk-Bewertung, finale Abnahme — wenn Fable widersprüchlich oder Scope unklar |

**3-Stufen-Pipeline (2026-07-04 bewährt):**
1. **md5sum-Diff** (lokal, 0 Kosten) — identische vs fehlende vs verschiedene Skills trennen
2. **Fable 5** (günstig) — Triage der fehlenden Skills: REANIMATE/KEEP-ARCHIVE/DELETE — funktioniert gut wenn Daten vorstrukturiert sind
3. **OPUS 4.8** (nur bei Bedarf) — Validierung von Fable's breiten Behauptungen (z.B. "alle 394 sind tot" — OPUS fand aktive Nachfolger bei allen)

## Erkenntnisse aus 2 Sessions (beide 2026-07-04)

- **Session 1 (OPUS, OPUS final):** Fable's "394 tote Skills" war falsch — alle haben aktive Nachfolger. OPUS validiert Claims.
- **Session 2 (Fable 5 allein für Judgment):** Fable's Reanimations-Triage (11 fehlende Skills) war **präzise und nutzbar** — 3 konkrete Picks mit soliden Argumenten. OPUS nicht nötig.

## Kernregel

- **md5sum vor Fable**: Lokale Analyse reduziert Fable's Arbeit von "alles scannen" auf "nur die 10-15% Unklaren bewerten" — spart Rabat-Volumen
- **Fable für Triage**: Wenn es um kategorisieren und priorisieren geht, nicht um absolute Wahrheits-Findung
- **OPUS für Validation**: Wenn eine Behauptung weitreichend ist ("alle löschen") oder Fable sich widerspricht