---
name: user-profile-memory
description: >-
  Use when user asks for recalling Basti preferences, answering what is known about the user, loading the working agreement, or warming up a session with stable profile context. NOT for recalling project-specific task state or editing or inventing profile memories. Performs read-only retrieval of stable user identity, preferences, and working-style facts from the profile memory scope.
version: 1.0.0
author: Yuno
license: MIT
lane: koenigin
reasoning_effort: medium
metadata:
  hermes:
    tags:
    - memory
    - recall
    - user-profile
    - mnemosyne
    - read-only
    related_skills:
    - hermes-memory
    - mnemosyne-memory-provider
trigger_keywords: ['user', 'profile', 'recalling', 'preferences', 'working']
keywords: ['user', 'profile', 'recalling', 'preferences', 'working']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['claude-code', 'yuno-user-preferences', 'hermes-memory']
---


# User-Profile-Memory (Basti Recall)

Liest Basti's stabile User-Profile-Memories aus Mnemosyne. Strukturiert die Ausgabe nach 5 Bereichen:

1. **Identität** — Name, Sprache, Hardware, Chassis
2. **Präferenzen** — Sprache, Ton, Reporting-Stil
3. **Working Agreement** — Telegram, File-Konventionen, Tabu-Bereiche
4. **Workspace-Konventionen** — Cluster-Pfade, Symlinks, Scripts
5. **Aktive Projekte** — laufende Initiativen mit aktuellen Bezügen

## Wann laden

Lade diesen Skill wenn Basti fragt:
- "Was weißt du über mich?"
- "Was sind meine Präferenzen?"
- "Zeig mir mein Working Agreement"
- "Recall mein User-Profile"
- Oder bei jeder Session-Eröffnung für **5-Second-Recall** der User-Identität (quick-warmup)

## Wie ausführen

```bash
python3 ~/.hermes/hermes-agent/venv/bin/python3 <<'PY'
import sqlite3, os, json
from collections import Counter

db = os.path.expanduser("~/.hermes/mnemosyne/data/mnemosyne.db")
con = sqlite3.connect(db)
cur = con.cursor()

# User-Profile: scope=global AND (source=user OR source=preference)
cur.execute("""
SELECT id, content, source, importance, recall_count, timestamp
FROM working_memory
WHERE scope='global'
  AND (source='user' OR source='preference' OR veracity='stated')
  AND importance >= 0.7
ORDER BY importance DESC, recall_count DESC
""")

mems = cur.fetchall()
con.close()

print(f"# Basti-User-Profile (Recall): {len(mems)} memories\n")

# Strukturierung nach Keyword-Tagging
buckets = {
    "Identität": [],
    "Präferenzen": [],
    "Working Agreement": [],
    "Workspace-Konventionen": [],
    "Aktive Projekte": [],
    "Sonstiges": []
}

KW = {
    "Identität": ["name", "basti", "gregor", "sprache", "deutsch", "hardware", "medion", "zorin", "cpu", "gpu"],
    "Präferenzen": ["präferenz", "mag", "will", "ton", "kawaii", "locker", "stil", "tiefe", "cli"],
    "Working Agreement": ["agreement", "telegram", "olympagentbot", "working agreement", "delivery", "tabu", "konvention"],
    "Workspace-Konventionen": ["workspace", "pfad", "cluster", "navigation", "symlink", "bin/", "scripts/", "tabu"],
    "Aktive Projekte": ["projekt", "voice-bot", "yuno", "orchestrator", "greyhack", "cp77", "werkstatt"],
}

for mid, content, source, imp, recall, ts in mems:
    cl = content.lower()
    placed = False
    for bucket, kws in KW.items():
        if any(kw in cl for kw in kws):
            buckets[bucket].append((mid, content, imp, recall))
            placed = True
            break
    if not placed:
        buckets["Sonstiges"].append((mid, content, imp, recall))

for bucket, items in buckets.items():
    if items:
        print(f"## {bucket} ({len(items)} memories)\n")
        for mid, content, imp, recall in items[:10]:  # Top 10 pro Bucket
            print(f"- **[{mid[:8]}]** imp={imp:.2f}, recall={recall}x")
            print(f"  {content[:200]}{'...' if len(content) > 200 else ''}\n")
PY
```

## Mnemosyne-Recall (live, semantisch)

Für kontextuelle Fragen lieber direkt `mnemosyne_recall` mit `query="Basti preferences working agreement"` und `importance_weight=0.5` — das findet auch memories die nicht in den Buckets oben landen.

## Pflege-Hinweise

- **Neue User-Präferenz erkannt?** → `mnemosyne_remember(scope='global', source='preference', importance=0.85+, veracity='stated')`
- **Widerspruch zu altem Memory?** → `mnemosyne_validate(action='invalidate', memory_id=<alt>)` + neuen Speichern
- **Wichtig:** NICHT in `~/Dokumente/`, `~/Downloads/` schreiben — alle Yuno-Reports in `~/.hermes/docus/`