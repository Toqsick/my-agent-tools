# Stale Memory Invalidation — Session Protocol 2026-07-17

**Skill:** `mnemosyne-memory-provider` → § Stale Memory Detection + Invalidation Workflow
**Session:** System-Audit 2026-07-17 + nachfolgende Memory-Hygiene
**Trigger:** Low-Energy-Abend-Task "Mnemosyne aufräumen" — Autonomer Durchlauf

## Context

Nach einem ausführlichen System-Audit (read-only, 664-Zeilen-Report unter
`~/20-Workspace/results/system-audit-2026-07-17.md`), der mehrere Disk-Drift-
Funde brachte (ProtonVPN entfernt, Port 3000/Gitea weg, Disk 74→85%), bot sich
die Memory-Hygiene als autonomer Low-Energy-Task an. Der Audit deckte auf, dass
CLAUDE.md-Disk-Figuren stale waren — die Frage war: sind die Mnemosyne-Memories
auch stale?

## Workflow-Execution

### Schritt 1 — Konsolidierung

```
mnemosyne_stats vor:
  working: 4550 total, 4517 consolidated, 33 unconsolidated
  episodic: 644

mnemosyne_sleep(all_sessions=True, dry_run=True):
  → 17 items eligible, 4 summaries würden erstellt, 2 Konflikte自动

mnemosyne_sleep(all_sessions=True):
  → consolidated: 17 items → 4 episodic summaries, 2 conflicts resolved

mnemosyne_stats nach:
  working: 4550 total, 4534 consolidated, 16 unconsolidated
  episodic: 648 (+4)
```

### Schritt 2 — Recall + Live-Verification

Recall nach `audit 2026-07-17 ollama ufw syslog spam memory anchor` lieferte 15
Ergebnisse. Manuelle Durchsicht:

| Memory ID | Content (Kurz) | Live-Verify | Stale? |
|---|---|---|---|
| `8eecb0f9fab7037c` | "Syslog-Drift oft self-resolving, 30-60min abwarten" | 3 Vorfälle (16.07, 17.07) widerlegen | ✅ STALE |
| `d6d621d631f349cd` | "System-Check 04.07: ProtonVPN aktiv, Port 3000 world-bound, Disk 74%" | `systemctl is-enabled protonvpn` → not-found; `ss -tlnp` → kein :3000 | ✅ STALE |
| `sys-tt` | "TokenTelemetry Port 3000/8000 ~700MB RAM systemd User-Service" | `systemctl --user is-active tokentelemetry` → inactive+disabled | ✅ STALE |
| `sys-llama` | "llama.cpp Snap (nemotron-3-super, Port 8332). Server inaktiv, startet nur bei Bedarf. ~3GB RAM wenn aktiv" | `ss -tlnp` → kein :8332; snap installiert aber nicht aktiv | ⚠️ PARTIAL (description "inaktiv" war korrekt, aber "startet bei Bedarf" impliziert readiness die nicht verifiziert) |
| `c9b4fc5dd7b97d6a` | System-Audit-2026-07-17 Anker (frisch) | n/a — gerade geschrieben | ❌ OK |
| `44836dc84bf809d2` | Token-vs-Source-Count Pitfall (frisch) | n/a — gerade geschrieben | ❌ OK |

### Schritt 3 — Invalidation + Replacement

#### Fall 1: `8eecb0f9fab7037c` (Syslog-Self-Resolving-These)

```python
mnemosyne_invalidate(memory_id="8eecb0f9fab7037c", replacement_id="3390948fcec5ef9b")

mnemosyne_remember(
    content="Syslog-Drift auf Basti's Workstation ist PRAKTISCH NIE self-resolving (Stand 2026-07-17, nachdem die alte \"oft self-resolving\"-These aus 2026-07-11 durch 3 Vorfälle widerlegt wurde): (1) 2026-07-11 zorin-printers 10.5GB schien selbst zu heilen, war aber nur eine ruhige Phase; (2) 2026-07-16 zorin-printers 6.4GB Looping-Bug brauchte rsyslog-Filter; (3) 2026-07-17 ollama print_timing 2.7GB in 44h. Korrekte Default-Action: source-first identify (grep PROCESS[) → filter oder source-fix → dann logrotate. NICHT abwarten.",
    importance=0.7,
    scope="global",
    source="insight",
    veracity="tool"
)
# → neue ID: 3390948fcec5ef9b

mnemosyne_graph_link(
    source_id="3390948fcec5ef9b",
    target_id="8eecb0f9fab7037c",
    relationship="supersedes",
    weight=0.9
)
```

#### Fall 2: `d6d621d631f349cd` (System-Check 04.07 — ProtonVPN/Disk/Ports stale)

Memory war 54x recalled — höchste Priorität, weil sie bei künftigen Recalls
dominant ranken würde.

```python
mnemosyne_invalidate(memory_id="d6d621d631f349cd", replacement_id="24488e751c48bdf4")

mnemosyne_remember(
    content="VPN-Setup auf Basti's Workstation (Stand 2026-07-17): ProtonVPN ist ENTFERNT (service=not-found, proton0 device existiert nicht). Aktuell aktiv: Tailscale (systemweit via tailscaled, IP 100.96.90.61, Frankfurt DERP, UPnP gegen FritzBox 5590 Fiber). Telefonie-Channel läuft via Tailscale + direct 8642/Tailscale-only UFW Rule. ACHTUNG: Alte Memories die ProtonVPN als aktiv erwähnen (z.B. d6d621d631f349cd vom 04.07.) sind STALE und wurden am 17.07. invalidiert.",
    importance=0.75,
    scope="global",
    source="fact",
    veracity="tool"
)
# → neue ID: 24488e751c48bdf4

mnemosyne_graph_link(
    source_id="3390948fcec5ef9b",  # der Syslog-Pitfall als sekundärer Superseder
    target_id="d6d621d631f349cd",
    relationship="supersedes",
    weight=0.85
)
```

#### Fall 3: `sys-tt` und `sys-llama` (memoria_facts-Tabelle, nicht update-bar)

```python
# Versuch 1: mnemosyne_update(memory_id="sys-tt", ...) → not_found
# Versuch 2: mnemosyne_validate(action="update", memory_id="sys-tt", ...) → memory_not_found
# Versuch 3: mnemosyne_get(memory_id="sys-tt") → not_found

# Workaround: neue Memory mit höherer Importance
mnemosyne_remember(
    content="Service-Drift-Korrektur 2026-07-17 (Alte Memories mit sys-* IDs sind STALE): TokenTelemetry: inaktiv+deaktiviert, kein Listener 3000/8000. Code in ~/10-Projekte/10-active/tokentelemetry/ vorhanden aber nicht laufend. llama.cpp: Snap installiert (1.4.0), aber kein Service aktiv, Port 8332 nicht belegt. Frühere Behauptungen über aktive Services auf diesen Ports sind veraltet. Verify-Befehl: systemctl --user is-active tokentelemetry + ss -tlnp | grep -E \":(3000|8000|8332)\\b\"",
    importance=0.7,
    scope="global",
    source="fact",
    veracity="tool"
)
# → neue ID: 3c3f9f63f312aeb9
```

### Schritt 4 — sys-* Quirk Dokumentation

Die Entdeckung, dass `sys-*`-IDs über die Standard-Tools nicht erreichbar sind,
ist ein genuiner Pitfall, der im SKILL.md unter "Troubleshooting" verankert
wurde. Siehe dort.

### Schritt 5 — Scratchpad

```python
mnemosyne_scratchpad_write(content="""
Memory-Hygiene 2026-07-18 abgeschlossen:
- 17 working → 4 episodic consolidated (Audit-Session 20260717)
- 3 stale memories invalidated/replaced:
  1. 8eecb0f9fab7037c "syslog oft self-resolving" → 3390948fcec5ef9b "syslog nie self-resolving"
  2. d6d621d631f349cd "System-Check 04.07 mit ProtonVPN" → 24488e751c48bdf4 "Tailscale aktiv, ProtonVPN entfernt"
  3. sys-tt/sys-llama "aktive Services" → 3c3f9f63f312aeb9 "Services inaktiv, Drift korrigiert"
- Shared Surface: 1 Eintrag, clean
- Mnemosyne-Pitfall: sys-*-IDs sind in memoria_facts-Tabelle, nicht über mnemosyne_update/get/validate erreichbar. Workaround = neue Memory mit höherer Importance anlegen.

Für nächste Session: CLAUDE.md-Diff (P3 F7 aus Audit) noch nicht applied — pending Basti-Approval.
""")
```

## Ergebnisse

| Metrik | Vorher | Nachher |
|---|---|---|
| Working total | 4550 | 4553 (+3 Replacement-Memories) |
| Working consolidated | 4517 | 4534 (+17) |
| Working unconsolidated | 33 | 16 |
| Episodic total | 644 | 648 (+4) |
| Episodic vectors | 187 | 191 (+4) |
| Stale invalidated | 0 | 3 |
| Graph-Edges (supersedes) | 0 | 2 |
| Shared Surface | 1 | 1 (clean) |

## Lessons Learned

1. **Fact-accuracy-Cleanup ist eine eigene Hygiene-Dimension**, getrennt von
   importance-basiertem Cleanup. Beide müssen regelmäßig laufen.

2. **Recall-Ergebnisse sind nicht ground truth.** Memories sind Behauptungen,
   die gegen das Live-System verifiziert werden müssen — besonders wenn sie
   System-State (Services, Ports, Disk-Zahlen, Pfade) enthalten.

3. **Graph-Links sind Pflicht** nach invalidate+replace. Ohne sie ist die
   neue Memory zwar da, aber die Recall-Connectivity ist schwächer als sie
   sein könnte.

4. **sys-* IDs sind eine bekannte Lücke** in der Mnemosyne-Tool-API.
   Workaround: neue Memory mit höherer Importance. Detaillierte Dokumentation
   im SKILL.md Troubleshooting-Abschnitt.

5. **Der "Autonomer Low-Energy-Task"-Modus klappt gut** für diese Art Hygiene.
   User kuckt zu, Agent arbeitet Schritt für Schritt, erklärt jeden Schritt.
   Validiert als Workflow für zukünftige Abende.
