# Archive Prune: ~/.hermes/archive/ — 2026-07-04

**Kontext:** 292M archive dir, safe-to-delete signal vom README. Komplette Inventur + Löschung auf 72K (99.97% Einsparung).

## Vorgehen (Schritt-für-Schritt)

### 1. Initialer Scan (Phase 1-2 Survey + Deep-Dive)
```bash
# Gesamtgröße + Top-Level-Struktur
du -sh ~/.hermes/archive/
ls -la ~/.hermes/archive/

# Sub-Dir-Größen sortiert
du -sh ~/.hermes/archive/* | sort -h

# Rekursive Tiefe (maxdepth 3)
find ~/.hermes/archive -maxdepth 3 -type d | sort
```

### 2. README-Erkundung (Phase 3 — Domain Classification)
Jedes Sub-Dir hatte README.md. Wichtigste Erkenntnisse:
- `state/README.md`: "state.db Snapshots — Backup vor Updates. Können bei Platzbedarf gelöscht werden."
- `sessions/README.md`: "Nur relevant fuer Debugging von API-Fehlern. Kein Einfluss auf Funktionalitaet."
- `media/README.md`: "Wird bei naechster Nutzung neu erstellt."
- `gateway/README.md`: "Gateway laeuft nicht mehr (deaktiviert). use_gateway: false in config.yaml."

### 3. Cross-Reference mit aktivem System (Phase 6a)
Zentraler Schritt: bevor archivierte Daten gelöscht werden, prüfen ob sie noch aktiv sind:

```bash
# 1. Prüfe aktives state.db
ls -la ~/.hermes/state.db
# → 588M, 04.07. — aktiv und frisch

# 2. Prüfe aktive state-snapshots
ls ~/.hermes/state-snapshots/
# → 20260704-173804-pre-update/ (vom HEUTIGEN Tag!)
# → Archivierter Snapshot 20260611-154317-pre-update/ (153M, 23d alt) ist OBSOLET

# 3. Prüfe aktive config
head -3 ~/.hermes/config.yaml  # vs archivierte configs vom 10.06.

# 4. Prüfe Skills (unberührt)
ls ~/.hermes/skills/ | wc -l  # → 54

# 5. Prüfe Gateway-Status (falls nicht offensichtlich)
hermes config get use_gateway  # → false
```

### 4. Inventory-Tabelle (Phase 5)
Vor dem Löschen: vollständige Klassifikation pro Sub-Dir:

| Item | Größe | Alter | Aktion | Begründung |
|------|-------|-------|--------|------------|
| state/20260611-154317-pre-update/ | 153M | 23d | DELETE | Obsolet: aktiver Snapshot vom 04.07. |
| state/state.db.pre-prune-20260608-132722.bak | 117M | 26d | DELETE | Pre-Prune-Backup, nach Prune obsolet |
| curator_backups/2026-06-09/ | 12M | 25d | DELETE | Dupliziert aktive skills |
| media/screenshots/ | 5.2M | 24d | DELETE | Regenerierbar |
| sessions/ (22 dumps) | 4.6M | 23d+ | DELETE | Debug-Dumps, "kein Einfluss" |
| config/ (21 backups) | 424K | 24d | DELETE | Alte configs, aktive aktuell |
| env/ (7 .bak) | 168K | 26d+ | DELETE | Alte .env-Backups (API-Keys!) |
| gateway/ (stale state) | 44K | 24d | DELETE | Gateway deaktiviert |
| rollback_20260602_121622/ | 104K | 32d | DELETE | Alter Rollback |
| Kleinfiles + leer-Dirs | ~16K | 23-32d | DELETE | Diverse Einzelfunde |
| README.md (top-level) | 491B | 23d | KEEP | Übersichts-Doku |

### 5. Phasen-basierte Löschung (Phase 6c)
```bash
# Phase A: Große Brocken (270M in 3 rm-Befehlen)
rm -rf state/20260611-154317-pre-update/
rm -f state/state.db.pre-prune-20260608-132722.bak
rm -rf curator_backups/2026-06-09T05-45-06Z/

# Phase B: Container-Inhalte (READMEs erhalten)
rm -rf media/screenshots/
find sessions -mindepth 1 -not -name 'README.md' -delete
find config -mindepth 1 -not -name 'README.md' -delete
find env -mindepth 1 -not -name 'README.md' -delete
find gateway -mindepth 1 -not -name 'README.md' -delete

# Phase C: Kleine Files
rm -rf rollback_20260602_121622
rm -f plans/2026-06-07_Matrix-Element-Installation-Plan.md
rm -rf sandboxes
rm -rf skill-bundles
rm -f audit-infra-messaging-gateway-2026-06-06.md
rm -f interrupt_debug.log next_session_note.md SOUL.md
rm -f desktop-build-stamp.json .install_method auth.lock kanban.db.init.lock
```

### 6. Verifikation (Phase 6d)
```bash
# Größen-Kontrolle
du -sh ~/.hermes/archive/
# → 72K (war 292M)

# Struktur-Kontrolle — READMEs noch da?
ls -la ~/.hermes/archive/
# → state/, config/, env/, gateway/, sessions/, media/ — alle mit READMEs

# Aktiv-System-Check — nichts kollateral
ls -la ~/.hermes/state.db          # → unberührt, 588M
ls -la ~/.hermes/state-snapshots/  # → aktiver Snapshot unberührt
ls ~/.hermes/skills/ | wc -l       # → 54, unverändert
```

### 7. API-Key-Sicherheit (Phase 6e)
`env/` enthielt 7 `.env.bak`-Dateien mit API-Keys. Gelöscht ohne sie zu lesen.
Aktive `.env` war separat und nie gefährdet.

## Wichtige Erkenntnisse

1. **READMEs als effektivster Filter:** Archive mit READMEs die "Kann gelöscht werden" sagen → kein Brainer. Ohne README: mehr Recherche nötig.
2. **state-snapshots vs archive/state:** `hermes update` legt automatisch Snapshots in `state-snapshots/` an. `archive/state/` sind manuelle/andere Snapshots — doppelt gemoppelt.
3. **Phasen-Reihenfolge macht sicher:** Große isolierte Brocken zuerst = größte Einsparung bei geringstem Risiko. Container zuletzt = maximale README-Bewahrung.
4. **Verifikation ist schnell:** 4 einfache Befehle nach dem Löschen reichen für Sicherheit.
5. **API-Key-Backups nicht lesen:** Auch nicht "nur kurz gucken". Vertraue README + nuke.
