---
name: queen-bee-queen-verify
title: "Queen-Bee — Queen-Verify, Override, Pre-Execute"
description: "Use when running queen-verify after a wave, applying queen-override patterns, or doing queen pre-execute while bees scout. NOT for dispatch setup (use queen-bee-dispatch-patterns)."
category: queen-bee-schwarm-dispatch
version: '1.0'
created: '2026-07-23'
author: Yuno (split from queen-bee-schwarm-dispatch)
lane: koenigin
agent: universal
trigger_keywords: ['queen-verify', 'override', 'pre-execute', 'verify', 'pitfall', 'pfad']
keywords: ['queen-verify', 'override', 'pre-execute', 'queen-bee', 'verification']
related_skills: ['queen-bee-dispatch-patterns', 'queen-bee-advanced']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from queen-bee-schwarm-dispatch 2026-07-23)'

license: MIT
---

# Queen-Bee — Queen-Verify, Override, Pre-Execute

_Extracted from queen-bee-schwarm-dispatch on 2026-07-23._

## Queen-Verify nach jeder Welle

Verifiziere **gegen das echte Filesystem**, nicht gegen den Biene-Self-Report:

```bash
# Beispiel für WebUI-Crash-Loop-Behauptung
systemctl --user is-active hermes-webui
systemctl --user is-enabled hermes-webui
ss -tlnp | grep -E ':8787|:9119'
journalctl --user -u hermes-webui --no-pager -n 30

# Beispiel fuer Audit-Biene (Drift-Matrix)
echo "Files: $(sqlite3 GreyHackDB.db 'SELECT COUNT(*) FROM Files')  (Notiz sagt 247)"
echo "Passwords: $(sqlite3 GreyHackDB.db 'SELECT COUNT(*) FROM Passwords')  (Notiz sagt 267)"
```

## Pfad-Pitfalls — Koenigin-Verify Pflicht ⚠️

Vor jedem `ls`/`cat`/`grep` zur Verify: **welches Dateisystem-Root hat der Subagent gesehen?** Haeufige Falle aus 2026-07-10 Phase 1:

| Was die Biene sagt | Was die Koenigin tippt | REALITAET |
|-------------------|------------------------|----------|
| `~/.obsidian/plugins/dataview/` | `ls ~/.obsidian/...` -> "kein Zugriff" | Der Vault-Lokation: `~/Dokumente/Obsidian Vault/.obsidian/` (NICHT Home-Obsidian!) |
| `~/.config/opencode/agents/` | `ls ~/.config/opencode/` | Direkt OK, weil im Home |
| `~/10-Projekte/...` | `ls /home/bratan/10-Projekte/...` | Direkt OK |

**Pitfall:** Obsidian legt das `.obsidian/`-Dir IM Vault-Root ab (`~/Dokumente/Obsidian Vault/.obsidian/`), nicht im Home (`~/.obsidian/` existiert gar nicht). Wenn Biene Pfade zu Plugin-Verzeichnissen liefert → IMMER zuerst `find ~ -maxdepth 5 -name '<datei>'` zur Root-Bestimmung, danach `ls -la` an der richtigen Stelle.

**Rule-of-Thumb:** Wenn ein Biene-Pfad "existiert nicht" zurueckgibt aber die Biene ihn behauptet:
1. NICHT der Biene misstrauen — oft hat die Queen die falsche Root.
2. `pwd` printen, kurz ueberlegen wo wir tatsaechlich sind.
3. Erst dann Verdict faellen.

## Koenigin-Override Pattern (NEU 2026-07-13)

Wenn die Queen-Verifikation ergibt, dass ein Biene-Output **Format-Constraints verletzt** (Boldface, Inline-Header, Em-Dashes, etc.):

**NICHT** die Biene neu dispatchen oder das ganze File neu schreiben. Stattdessen: **gezielte Patches als Queen direkt.**

```
1. Problem identifizieren: grep -nE '\*\*[^*]+\*\*' oder aehnlich
2. Jede Verletzung einzeln patchen (nicht Bulk-Rewrite)
3. Bei Inline-Header Listen (L1, L2, ...) → in Prosa-Fliesstext umwandeln
4. Nach jedem Patch: grep erneut auf die Rest-Verletzungen
5. Erst wenn 0 Treffer: inhaltliche Pruefung (kein Sinnverlust durch Patch)
```

**Warum (validiert 2026-07-13):** Biene 2 lieferte 17 Boldface + 5 Inline-Header. 4 targeted Patches (je 1-2 Zeilen) haben das in unter 2 Minuten gefixt. Ein Neu-Dispatch haette 3-4 Minuten + erneute Verifikation + 50% Chance auf neuen Fehler gebraucht.

**Faustregel:** Korrektur per Queen-Direct-Patch dauert ca. 30 Sekunden pro Verletzungs-Typ. Dispatch + Verify + ggf. Override dauert 3-5 Minuten. Bei <= 20 Verletzungen → Queen macht selbst. Bei > 20 oder strukturellen Fehlern → Biene mit praeziserem Briefing neu dispatchen.

## Vault-Skizze-Korrektur (Pattern)

Wenn eine Skizze/Note **Live-States falsch behauptet** (z.B. "disabled/Crash-Loop", aber Service laeuft) — korrigiere die Skizze selbst, **nicht nur einen MOC**:

```
1. Update YAML mit `drift-korrigiert-YYYY-MM-DD` Tag
2. update-log Block im Frontmatter mit Quelle der Korrektur
3. Body-Text patchen — Original fett durchstreichen, Korrektur klar markiert
4. Niemals die ganze Skizze loeschen — Original ist historischer Wert
5. Hinweis im MOC ergaenzen, nicht entfernen
```

Beispiel 2026-07-10: WebUI-Skizze behauptete "disabled" — Realitaet war active. Korrigiert mit Tag + update-log, Original-Text blieb sichtbar fuer Audit.

## Queen Pre-Execute While Bees Scout (NEU 2026-07-15 — validated Viper-Redeploy)

**Kern-Erkenntnis:** Die Queen MUSS nicht warten, bis alle Scout-Bienen gelandet sind, bevor sie handelt — **wenn sie unabhängigen Tool-Zugriff und ausreichend Kontext hat.**

### Wann anwenden

- Queen hat `terminal`-Zugriff auf dieselben Systeme (Build-Tools, DB-Client, Netzwerk)
- Die Aktion ist **deterministisch und reversibel** (Backup → Dry-Run → Execute → Verify)
- Scout-Bienen sind **Insurance/Oversight**, nicht Gate — sie validieren nach, nicht vor
- Blackbox CLI-Tools (greybel) sind sicher und von Queen direkt aufrufbar

### Wann NICHT anwenden

- Aktion zerstört State ohne Rollback (rm -rf ohne Backup, DROP TABLE, Service-Kill)
- Queen fehlen direkte Tools (braucht web_search, Browser, spezielle API-Keys)
- Aktion braucht Reasoning/Urteil der Bienen-Ergebnisse (Architektur-Entscheid, Strategie-Wahl)
- Eine der Bienen könnte einen unterschätzen Blocker melden

### Validierter Workflow (2026-07-15 — Viper-Redeploy)

```text
Phase 0 — Queen dispatches 3 Scout-Bienen (parallel, background)
          MACHWEITER OHNE AUF BIENEN ZU WARTEN:

Phase 1 — Queen macht selbst:
  ├── Source-Backup auf Host (cp in /tmp, yuno-tools-Verzeichnis)
  ├── greybel build 5/5 (direkter Build, kein Bee-Report nötig)
  ├── Redeploy-Script schreiben (--dry-run + Backup-Logik)
  ├── Dry-Run gegen Live-DB (5/5 Content byte-gleich)
  └── Live-Deploy (Backup → Upsert → Verify → integrity_check)

Phase 2 — Queen bestätigt Ergebnis (5/5 byte-gleicher Content, integrity ok)
Phase 3 — Scout-Bienen landen (Post-Validierung, nix verbrannt)
```

**Vorteil:** ~60% kürzere Wall-Time. Bienen brauchen 2–4 Min Initialisierung + Arbeit; Queen macht denselben Job in <90s wenn sie Tool-Zugriff hat.

### Pitfall: Queen muss Disziplin bewahren

Nicht vorzeitig ausführen wenn:
- Die Aktion nicht vollständig reversibel ist (kein Backup / kein Dry-Run)
- Queen den Source-Stand nicht selbst verifizieren kann (nur die Biene sah die echten Canonicals)
- Ein Bee-Report fundamental widersprechen KÖNNTE (Daten-Interpretation statt Mechanik)

**Faustregel:** Mechanik/IO-Tasks = Queen kann sofort loslegen. Reasoning/Urteils-Tasks = auf Bienen warten.

### Abgrenzung zu anderen Patterns

| Pattern | Reihenfolge | Wann |
|---------|-----------|------|
| **Standard bee swarm** | Bienen → Queen verify → Bienen Welle 2 | Strategie, Analyse, Content-Erstellung |
| **Queen pre-execute** (NEU) | Bienen parallel + Queen sofort | Reversible Host-Aktionen mit Mechanik-Check |
| **Queen baseline pre-execute** (NEU 2026-07-16) | Bienen parallel + Queen Baseline-Scans | Audit/Survey — Queen erhebt Ground Truth bevor Bienen landen |
| **Orthogonal scout bees** (NEU 2026-07-15) | Bienen parallel + Queen sofort | Queen macht Mutationen, Bienen auditieren orthogonal (unterschiedliche Tasks) |
| **Skill-Polish 2-Wave** (NEU 2026-07-16) | 2 Wellen: Audit (Tag) + Polish (Tag) | Skill-Catalog-Qualität — siehe `skill-polisher` |
| **Queen alone (no swarm)** | Kein Dispatch | Reine Lesetasks, einfache Entscheidung |

**Skill-Polish 2-Wave (validiert 2026-07-16, 107 Fixes):**
Die Skill-Polish-Orchestrierung kombiniert Queen Baseline Pre-Execute (für Description-Metriken) + Queen Pre-Execute (für deterministische Rewrites) + Orthogonal Scout Bienen (für Broken-Ref-Kategorisierung) + Verify-Bienen (für Cross-Check). Das Pattern ist in `skill-polisher` als Complete Workflow dokumentiert: Audit-Phase (Morgen, 43 Fixes) und Polish-Phase (Nachmittag, 64 Fixes). Trigger-Coverage-KPI ist der Qualitätsindikator.

### Werkstatt-Pattern-Erweiterung

Die bestehende Werkstatt-Regel "Phase 1 nur Inspektion, keine Edits" ist für Audit/Drift/Strategie-Aufgaben weiterhin korrekt. Für **Mechanik-Deploy-Aufgaben** (Build + DB-Injection + Verify) greift das **Queen-Pre-Execute-Pattern**. Unterscheidung:

| Signal | Pattern | Begründung |
|--------|---------|-----------|
| "Orchestriere Bienen für Thema X" | Werkstatt | X braucht Analyse/Judgment |
| "Nutze Bienen-Orchestration für Y" | Pre-Execute | Y ist ein Build/Bau/Deploy mit deterministischen Tools |
| "Skill-Audit / Library-Health-Scan" | Baseline Pre-Execute | Queen erhebt Ground Truth parallel zu Bienen |

**Referenz:** `references/queen-pre-execute-pattern.md` — vollständiges Viper-Redeploy worked example mit Befehlen + Verify-Gates.
`references/queen-baseline-scan-pattern.md` — Baseline-Scan-Befehle für Audit/Survey-Aufgaben.
