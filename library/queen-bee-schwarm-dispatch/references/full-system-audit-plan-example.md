# Full System Audit 2026-07-17 — Implementation Plan (Example)

> **Zweck dieser Referenz:** Konkretes Beispiel eines Pre-Scout-basierten, multi-wave-qualitätsgesicherten Full-System-Audit-Plans. Dieser Plan entstand aus der Welle-1→Welle-2-Verbesserung und zeigt die P0/P1/P2/P3-Architektur mit echten Live-Recon-Daten.
>
> **Für Hermes:** Nutze dieses Beispiel als Template für zukünftige System-Audits. Ersetze die Live-Daten durch aktuelle Werte, behalte die P0-P3-Struktur und die Pre/Post-Verification-Gates.

## Header

**Goal:** Vollständiger Audit-Durchlauf von Bastis Zorin OS Workstation — Disk, Logs, Cron, Security, Memory, Skills, Hermes-Internals — mit priorisierten, read-only verifizierten Fixes.

**Architecture:** Read-only Recon → priorisierter Report → Fix-Tasks nach Risiko gestaffelt (P0 = sofort, P1 = bald, P2 = wenn Zeit). Jede Fix-Task hat Pre/Post-Verification und ist reversibel.

**Tech Stack:** bash, systemd, cron, du/df, journalctl, ufw, nvidia-smi, mnemosyne CLI, skill-reviewer

---

## Current Context — Live-Recon-Ergebnisse

### 🔴 P0 — Kritisch / Sofort

| # | Fund | Größe/Status | Risiko |
|---|------|------|--------|
| 1 | **Disk: `/` bei 88% (75GB frei)** | 502G/607G belegt | Schrumpfender Puffer → System-Instabilität |
| 2 | **logrotate.service FAILED** | `rsyslog.bak.20260716` verursacht duplicate-entry Errors | Logs rotieren nicht → syslog.1 wächst unbegrenzt |
| 3 | **`/var/log/syslog.1` = 6.4GB** | Folge von logrotate-Failure | BlockiertDisk + logrotate kann nie aufholen |
| 4 | **Ollama aktiv entgegen AGENTS.md** | `enabled+active`, 4 Models, 38GB | AGENTS.md sagt "disabled+inactive" — Lüge |

### 🟡 P1 — Hoch / Bald

| # | Fund | Größe | Aktion |
|---|------|-------|--------|
| 5 | `~/Videos/20230909_194135-003.mp4` | **15GB** einzelnes Video (2023!) | User-Entscheidung: Archivieren/löschen |
| 6 | `~/.var/app/com.valvesoftware.Steam/` | **155GB** (Flatpak) | Shader-Cache/Downloads prüfen |
| 7 | `~/.cache/` | **31GB** (Plan sagt 18GB — Live-Abweichung!) | Safe-to-clear Kandidat |
| 8 | `~/.hermes/Grayhack Game + Data (fork)/` | **794MB** im Hermes-Sandbox | Gehört nicht dorthin |
| 9 | Downloads: Windows-Installer | kimi (751M), vortex (345M), autoclaw (281M) | Löschen wenn nicht gebraucht |
| 10 | `.steampath` symlink broken | → `.steam/sdk32/steam` (dead, Flatpak-Rest) | Löschen |
| 11 | Cron: `nextcloud-processor.log` = 4MB/34860 Zeilen | Läuft alle 2min | Log-Rotation oder Suppression |

### 🟢 P2 — Mittel / Periodisch

| # | Fund | Status | Aktion |
|---|------|--------|--------|
| 12 | Mnemosyne: 305 unconsolidated working memories | Sleep läuft täglich 02:30 | `mnemosyne_sleep(all_sessions=true)` |
| 13 | Skill Library: 494 Skills, 42 Monolithe >500 Zeilen | Last audit 07-16 (43 Fixes) | P2 Backlog abarbeiten |

### 🔵 P3 — Low / Nur Monitoring

| # | Fund | Status |
|---|------|--------|
| 14 | UFW: aktiv, RDP (3389) geblockt, 0 SSH-Fails | ✅ Gesund |
| 15 | NVIDIA: OC active, 43°C/1% idle | ✅ Gesund |
| 16 | zram: 3.7G/7.7G (48%) | ✅ Normal |
| 17 | Cron Jobs: 15 aktiv, keine Errors in journalctl | ✅ Gesund |

---

## Fix-Plan — Tasks nach Priorität (Template)

### Task N: [Aufgabe] [P-Priorität]

**Objective:** Was diese Task erreicht.

**Files:**
- Inspect: `path/to/config`
- Modify: `path/to/file`

**Step 1: Verify Pre-State**

```bash
commando # Zeigt Ausgangszustand
```

**Step 2: Execute Fix**

```bash
commando # Fix mit reversibler Aktion
```

**Step 3: Verify Post-State**

```bash
commando # Zeigt Zielzustand
```

**Risks:** Bewertung (Niedrig/Mittel/Hoch)

---

## Open Questions (User-Decision needed)

1. Frage 1
2. Frage 2

---

## Risks & Tradeoffs (Übersicht)

| Risiko | Mitigation |
|--------|-----------|
| Risiko 1 | Mitigation 1 |

---

*Vollständiges Beispiel unter `~/.hermes/plans/2026-07-17_001800-full-system-audit.md`*
