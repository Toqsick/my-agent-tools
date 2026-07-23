# Baseline Drift Comparison — Example from 2026-07-13

This reference documents the concrete drift comparison workflow from the
2026-07-13 security audit session. Use it as a template for future audits.

## Setup

- **Audit script:** `~/50-System/bin/maxclaw-security-audit.sh`
- **Script output:** `~/logs/maxclaw-security-audit-LAST.json`
- **Previous report:** `~/logs/maxclaw-security-audit-20260705-1326.json`
- **Baseline markdown:** `~/20-Workspace/results/security-audit-2026-07-05.md`
- **Constraint:** No TTY — `sudo bash` fails. Run without sudo.

## Schritt 1: Beide JSON-Reports + Baseline-Markdown laden

```bash
cat ~/logs/maxclaw-security-audit-LAST.json
cat ~/logs/maxclaw-security-audit-20260705-1326.json  # previous run
cat ~/20-Workspace/results/security-audit-2026-07-05.md
```

Alle drei parallel lesen (nicht seriell — die Vergleiche brauchen beide Reports
gleichzeitig im Kontext).

## Schritt 2: Score-Trend bestimmen

| Metrik | 2026-07-05 | 2026-07-13 | Trend |
|--------|-----------|-----------|-------|
| Overall Score | 0 | 19 | ↑ Verbessert |
| P0 Count | 2 | 1 | ↓ Verbessert |
| P1 Count | 5 | 5 | – Gleich |
| P2 Count | 1→2 | 2 | ↑ Neu (1×) |
| OK Count | 9 | 10 | ↑ Verbessert |

## Schritt 3: Finding-Delta pro Kategorie

### ✅ Besser geworden (echte Verbesserung)

| Finding | 2026-07-05 | 2026-07-13 | Nachweis |
|---------|-----------|-----------|----------|
| `P4.fs.world_writable` | P0 — `/home/bratan/.hermes/hermes-agent/.venv/.lock` (0666) | OK — jetzt 0644 | `stat -c '%a' <path>` |
| `P2.port.world_listeners:8200` | P2 — MiniDLNA auf `0.0.0.0:8200` | OK — Port weg | `ss -tlnp \| grep 8200` |
| `P0.backup.recent` | 3 Tage alt | 1 Tag alt | JSON-Report |

### ⚖️ Gleich geblieben (keine Änderung)

| Finding | Status | Grund |
|---------|--------|-------|
| `P0.backup.secretref_exists` | P0 — stale | Skript checkt `~/.openclaw/out`, nie eingerichtet |
| `P1.write_paths.*` | P1 — not applicable | Config-Key existiert in installiertem Hermes nicht |
| `P1.git.main_push_denied` | P1 — not applicable | Config-driven deny nicht implementiert |
| `P1.sudo.deny` | P1 — not applicable | Config-driven deny nicht implementiert |
| `P3.fw.ufw_active` | P2 — false-positive ohne root | `ufw status` kann ohne root nicht ausgewertet werden |
| `P5.cron.root` | P1 — false-positive | Standard-Ubuntu `run-parts /etc/cron.hourly`, kein Bedrohungsindikator |
| `M.budget.declared` | P1 — not applicable | `monthly_limit_eur` wird nicht lokal erzwungen |

### ⚠️ Neu aufgetaucht

| Finding | Neu seit | Grund |
|---------|----------|-------|
| `P2.port.world_listeners:27036` | 2026-07-13 | Steam Flatpak auf `0.0.0.0:27036` (PID 7038) — normaler Steam-Discovery-Port |
| User-Cron-Einträge: 3→13 | 2026-07-13 | 10 neue Cron-Jobs seit letztem Audit — OK (kein sudo), aber auffällig |

## Schritt 4: Multi-Source Cross-Reference

Jeden Finding gegen alle drei Quellen validieren.

**Beispiel: `P3.fw.ufw_active`**

| Quelle | Aussage |
|--------|---------|
| MaxClaw JSON | `P2: ufw nicht aktiv` |
| Baseline Markdown | „UFW active, default-deny incoming (verified live via `sudo ufw status verbose`)" |
| Live system | `ufw status` ohne root → kann nicht verifizieren; `sudo -n` → fehlgeschlagen |

→ **Urteil:** Known false-positive. Baseline-Doc mit eigener Live-Verifikation
ist vertrauenswürdiger als der MaxClaw-Script-Check ohne root.

**Beispiel: `P0.backup.secretref_exists`**

| Quelle | Aussage |
|--------|---------|
| MaxClaw JSON | `P0: /home/bratan/.openclaw/out existiert nicht` |
| Baseline Markdown | „Skript checkt `~/.openclaw` — ein pre-Restructure Konzept" |
| Live system | `ls ~/.openclaw` → existiert nicht |

→ **Urteil:** False-positive. Script prüft ein Konzept, das nie realisiert wurde.
System nutzt Hermes-native auth, kein OpenClaw.

## Schritt 5: Structured-Delta-Bericht

Nach der Analyse einen kurzen Structured-Delta-Bericht ausgeben:

```
Score 0→19 · echte Verbesserung: .venv/.lock (0666→0644), MiniDLNA Port weg
Neue Findings: Steam auf :27036 (normal), 10 neue Cron-Jobs (OK)
Unverändert: 5× P1 (alle not-applicable), 1× P0 (stale), 1× P2 (ufw false-positive ohne root)
Echte offene Action-Items: security.allow_private_urls, tirith_fail_open (nicht im Skript)
```

## Fallstricke

1. **Nicht alle P0/P1-Punkte des Skripts sind echt.** Das Skript prüft ggf.
   Pfade aus einer vorherigen Restruktur oder Config-Keys, die Hermes gar nicht
   implementiert. Immer gegen Baseline-Markdown + Live-System cross-referenzieren.
2. **Score allein sagt nichts.** Ein Score von 0 kann durch 2× stale P0s
   verursacht sein — der wahre Security-Posture kann trotzdem gut sein.
   Score ist ein Trend-Indikator, kein Absolutwert.
3. **Baseline-Docs driften** — nie blind vertrauen. Immer live verifizieren
   (mindestens `ss -tlnp`, `stat`, `systemctl status`).
4. **Echte offene Items sind oft NICHT im MaxClaw-Skript.** Die P0/P1/P2 des
   Skripts sind hauptsächlich Config-Checks und System-Hygiene. Echte
   Hermes-Config-Schwachstellen (`allow_private_urls`, `tirith_fail_open`)
   werden vom Skript nicht erkannt — die müssen im Baseline-Doc aus
   vorherigen Deep-Dives nachgeschlagen werden.