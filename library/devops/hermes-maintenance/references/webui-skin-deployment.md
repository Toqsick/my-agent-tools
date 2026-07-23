# WebUI Skin Deployment — Yuno Skin Family

> **Umbrella:** `hermes-maintenance` §12 (Port-Conflict + Clean Restart)
> **Session:** 2026-07-08 — PR #1 Yuno Skins + Dashboard → live auf :8787

## Ziel

Nach einem Pull/Merge der Hermes WebUI (nesquena/Python-Variante) auf dem
lokalen Server die neuen Skins deployen, verifizieren und das Live-System
testen.

## Deployment-Workflow

### 1. Code holen

```bash
cd /home/bratan/hermes-webui  # Hardlink zu 40-archive/hermes-webui (gleicher Inode)
git fetch toqsick master --no-tags
git checkout -b feature/deploy-<name>
git merge toqsick/master
```

### 2. Targeted Tests (statt Vollsuite)

Die Vollsuite hat 12.373 Tests und timeoutet bei 5 Minuten. Bei Skin-
Änderungen nur die relevanten Testdateien laufen lassen:

```bash
.venv/bin/python -m pytest \
  tests/test_yuno_skins.py \
  tests/test_skin_registry_parity.py \
  tests/test_dashboard_panel_view.py \
  tests/test_dashboard_link_ui.py \
  --timeout=30
```

Erwartet: ~36 passed in ~3s.

### 3. Service Clean Restart

```bash
systemctl --user stop hermes-webui.service
sleep 3
ss -tlnp | grep 8787 || echo "port free"  # MUSS leer sein
systemctl --user start hermes-webui.service
sleep 2
systemctl --user is-active hermes-webui.service
```

### 4. Skin-Verifikation (3 Ebenen)

```bash
# Ebene 1 — Settings-API antwortet
curl -sS http://127.0.0.1:8787/api/settings | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('skin:', d.get('skin'), '| webui:', d.get('webui_version'))
"

# Ebene 2 — Skin existiert im index.html (Client-Side allowlist)
curl -sS http://127.0.0.1:8787/ | grep -oE 'yuno[a-z-]*' | sort -u
# Erwartet: yuno, yuno-cyberpunk, yuno-hc

# Ebene 3 — Skin setzen und persistenz prüfen
curl -sS -X POST -H "Content-Type: application/json" \
  -d '{"skin":"yuno-cyberpunk","theme":"dark"}' \
  http://127.0.0.1:8787/api/settings | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d.get('skin') == 'yuno-cyberpunk', f'Skin not saved: {d.get(\"skin\")}'
print('Skin persistence OK:', d.get('skin'))
"
```

### 5. Master Sync

```bash
git checkout master
git merge --ff-only feature/deploy-<name>
git branch -d feature/deploy-<name>
```

**Nicht zu origin pushen** (shows 16 commits ahead of nesquena — das ist normal,
weil `origin` ≠ `toqsick`).

## Skin-Registry Pitfalls

### Dreifache Registrierung

`available_skins` muss an **drei Stellen** konsistent sein:

| Registry | Fundort | Was passiert bei Lücke |
|----------|---------|------------------------|
| **Server allowlist** | `server.py` → `SKIN_ALLOWLIST` | POST `/api/settings` schlägt 400 — Skin wird rejected |
| **Client boot.js** | `static/boot.js` → `AVAILABLE_SKINS` | Skin erscheint nicht im Dropdown |
| **HTML no-flash guard** | `static/index.html` → `ALLOWED_SKINS` | Reload fällt auf `default` zurück (Flash-of-wrong-theme) |

### Skin-Persistenz-Drift

Vor dem PR war `server.py`'s Allowlist **stale** — einige Skins (`github`,
`codex`, `terracotta`, `hepburn`, `neon`) waren im JS-Registry aber nicht im
Server → POST wurde rejected, Reload fiel auf `default` zurück.

**Fix:** `tests/test_skin_registry_parity.py` prüft jetzt automatisch dass
alle drei Registries synchron sind.

## Verifikation bei Session-Start

Wenn ein Modellwechsel oder Session-Drop die Verifikation des letzten Deploy
verlangt:

```bash
# Ist Yuno Cyberpunk aktiv?
curl -sS http://127.0.0.1:8787/api/settings | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('skin:', d.get('skin'))
print('webui_version:', d.get('webui_version'))
print('skins_in_html:', len([k for k in ['yuno','yuno-cyberpunk','yuno-hc']]))
"

# Dashboard verfügbar?
curl -sS http://127.0.0.1:8787/api/dashboard/status | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('dashboard active:', d.get('running'))
"
```