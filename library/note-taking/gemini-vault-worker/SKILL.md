---
name: gemini-vault-worker
description: |
  Use when delegating a bounded Obsidian-vault task to Gemini CLI 3, preparing worker context, or validating a worker's note changes before acceptance.
  NOT for direct interactive note editing, unscoped autonomous vault rewrites, or accepting worker claims without inspecting produced artifacts.
  Defines a worker-bee delegation pattern with constrained prompts, isolated responsibilities, and verification gates for vault operations.
category: note-taking
platforms:
- linux
- macos
tags:
- gemini
- vault
- worker-tool
- external-llm
- vault-cluster
related_skills:
- obsidian-vault-cluster-operations
- vault-architecture
- coding-agents
triggers:
- gemini vault
- gemini yolo
- gemini-cli worker
- vault phase 7
- vault phase 8
- vault phase 9
- external LLM vault
- worker bee gemini
lane: koenigin
reasoning_effort: high
metadata:
  hermes:
    tags:
    - gemini
    - vault
    - worker-tool
    - external-llm
    - vault-cluster
    related_skills:
    - obsidian-vault-cluster-operations
    - vault-architecture
    - coding-agents
    triggers:
    - gemini vault
    - gemini yolo
    - gemini-cli worker
    - vault phase 7
    - vault phase 8
    - vault phase 9
    - external LLM vault
    - worker bee gemini
author: Hermes Agent
version: 1.0.0
license: MIT
trigger_keywords: ['worker', 'vault', 'note', 'delegating', 'bounded']
keywords: ['worker', 'vault', 'note', 'delegating', 'bounded']
last_curated: '2026-07-23'
curated_by: 'Yuno'
---


# Gemini-CLI als Vault-Worker

> **Add-On Skill** fur `obsidian-vault-cluster-operations`. Gemini-CLI-spezifische Patterns (G-Pattern 1-5), Backup-Strategie, Pattern-7-Verifikation, Gemini-Verhaltens-Eigenheiten.

## Wann diesen Skill laden

- Du planst einen Vault-Cluster-Run mit Gemini-CLI als Worker-Tool
- User hat Google AI Pro Abo (oder API-Key)
- User will Default `gemini-3.1-pro-preview`
- Du brauchst die Gemini-spezifischen Pitfalls (--yolo, Mull-Skripte, 07-Archiv-Anfassen)

## Wann NICHT diesen Skill

- Read-only Analyse ohne Vault-Edits -> kein --yolo notig, einfacher Aufruf
- Claude-Code/Codex/OpenCode als Worker -> andere Auth, andere Flags
- Local offline -> OpenCode + Ollama
- Multimodal mit Bildern/PDFs -> Gemini-CLI hat das zwar, aber andere Tools evtl. besser

## Die 5 G-Patterns (proven 2026-07-05)

### G-Pattern 1: Auth-Mode Pre-Check

Vor jedem Run:

```bash
cat ~/.gemini/settings.json | python3 -c "import json,sys; print(json.load(sys.stdin)['security']['auth']['selectedType'])"
cat ~/.gemini/.env | grep -E "^(GEMINI_API_KEY|DISABLE_TELEMETRY)" | sed 's/=.*/=<set>/'
[ -f ~/.gemini/oauth_creds.json ] && echo "oauth_creds: present"
which gemini || find ~/.nvm/versions/node -name gemini -executable 2>/dev/null
```

### G-Pattern 2: --yolo fur Vault-Edits

Default approval mode hat keine Tools. Fur Vault-Schreibzugriff: `--yolo`.

```bash
# Standard-Aufruf fur Vault-Cluster-Operation:
timeout 600 gemini --yolo \
  --include-directories "/home/bratan/Dokumente/Obsidian Vault" \
  -m gemini-3.1-pro-preview \
  -p "$(cat plan.md) + cluster-spezifischer Auftrag im Subagent-Briefing"
```

**Alternativen:**
- `--approval-mode auto_edit` - nur Edits, keine Bash (sicherer)
- `--approval-mode plan` - read-only mit Edit-Anweisungen (kontrolliertester)

### G-Pattern 3: Subagent-Mull-Pravention

Gemini-CLI legt manchmal Mull-Skripte im Vault-Root ab (proven Phase 8: `update_mocs.py`).

**Pflicht im Subagent-Briefing:**
> Nach Gemini-Finish: `find <vault>/ -maxdepth 1 \( -name '*.py' -o -name '*.sh' \)` - alle Scripts die Gemini angelegt hat entfernen.

### G-Pattern 4: Telemetrie-Disable

`Error flushing log events: HTTP 400: Bad Request` nervt im Debug-Output. Fix:

```bash
echo 'DISABLE_TELEMETRY=1' >> ~/.gemini/.env
```

Kein Funktionsverlust.

### G-Pattern 5: Model-Override Konsistenz

Basti-Praferenz (memory-verankert): **IMMER `gemini-3.1-pro-preview`**.

Subagent-Briefing muss IMMER `-m gemini-3.1-pro-preview` enthalten. NIEMALS Flash ohne explizite User-Anweisung.

## Backup-Strategie (NICHT rsync!)

```bash
tar cf - \
  --exclude='.obsidian/plugins' \
  --exclude='.trash' \
  --exclude='workspace.json' \
  --exclude='*.bak*' \
  --exclude='.obsidian.backup-*' \
  . | (cd "$BACKUP" && tar xf -)
```

rsync hat Pattern-Bugs (Phase 8 Incident - kopiert keine .css/.json in .obsidian/).

## Pattern-7-Verifikation (Pflicht nach jedem Run)

```bash
VAULT="/home/bratan/Dokumente/Obsidian Vault"
PLAN="$VAULT/05 Ressourcen/Vault-Phase-N-Plan*.md"

# Notes-Anzahl vorher -> nachher
find "$VAULT" -name '*.md' -not -path '*/.obsidian/*' -not -path '*/.trash/*' | wc -l

# Mull-Skripte (sollte 0 sein)
find "$VAULT" -maxdepth 1 \( -name '*.py' -o -name '*.sh' \)

# Verbotene Folder angefasst?
for forbidden in "01 Kontext" "02 Inbox" "07 Archiv" "08 Anhaenge" "_templates"; do
  hits=$(find "$VAULT/$forbidden" -name '*.md' -newer "$PLAN" 2>/dev/null | wc -l)
  echo "$forbidden: $hits modified"
done

# MOCs angefasst?
find "$VAULT" -iname "MOC*.md" -newer "$PLAN"

# Stichprobe behaupteter Edits (3 zufallige Files head)
```

## Anti-Pattern-Liste (Checkliste fur Subagent-Briefing)

- [ ] `01 Kontext/` (aufer Working Agreement, das Yuno inline macht)
- [ ] `02 Inbox/`
- [ ] `07 Archiv/` Inhalt (nur additiv OK)
- [ ] `08 Anhaenge/` (Binaries)
- [ ] `_templates/`
- [ ] `.obsidian/` config aufer `snippets/`, `appearance.json`, `graph.json`
- [ ] `.trash/`
- [ ] `.obsidian.backup-*` Ordner (nur Report)
- [ ] MOC-Files komplett ersetzen
- [ ] Mull-Skripte im Vault-Root
- [ ] Theme komplett overriden
- [ ] Yuno-Farbpalette andern
- [ ] Snippets loschen
- [ ] Fakten erfinden (Pattern 3)

## Gemini-Verhaltens-Eigenheiten

| Verhalten | Mitigation |
|---|---|
| Ehrliche "no tools" Meldung ohne Flags | Briefing muss `--yolo` enthalten |
| Mull-Skripte im Root | G-Pattern 3 |
| 07 Archiv/_MOC.md additiv | Briefing: "07 Archiv/_MOC.md NICHT anfassen" |
| Pattern 6 Satelliten | OK, Improvisation-Permission |
| Halluzinierte Versionsnummern | Pattern 3 Anti-Halluzination |
| Langsame Pro-Preview (>90s) | timeout 480-900s |
| Telemetrie-Spam | G-Pattern 4 |

## Aufruf-Templates

### Read-Only Plan-Analyse
```bash
timeout 240 gemini --yolo --include-directories "$VAULT" -m gemini-3.1-pro-preview -p "$(cat plan.md)"
```

### Cluster-Operation (Cross-Links + Satelliten)
```bash
timeout 600 gemini --yolo --include-directories "$VAULT" -m gemini-3.1-pro-preview -p "$(cat plan.md)"
```

### Design-Rework (CSS + MOCs)
```bash
timeout 900 gemini --yolo --include-directories "$VAULT" -m gemini-3.1-pro-preview -p "$(cat plan.md)"
```

## Proven Phase-Results (Vault-Basti, 2026-07-05)

| Phase | Resultat |
|---|---|
| Phase 7 (Cross-Links) | +2 Satelliten, +240 Wiki-Links, avg 11/Note |
| Phase 8 (Design-Rework) | +4 CSS-Snippets, +8 MOC-Sektionen, 16 Graph-Farben |
| Phase 9 (Finalisierung) | Cleanup + Doku + Skill-Ableitung |

## Pitfalls

1. **`-p` ohne `--yolo` -> keine Tools** - Gemini meldet ehrlich "I have no write tools". Briefing muss `--yolo` enthalten.
2. **rsync-Backup-Pattern-Bugs** - nutze tar statt rsync fur .obsidian/snippets/.css und .obsidian/*.json
3. **Pro-Preview Timeout** - mind. 480s, besser 600-900s
4. **Telemetrie-Spam** - `DISABLE_TELEMETRY=1` in ~/.gemini/.env
5. **Mull-Skripte im Root** - Gemini-CLI erzeugt manchmal Python-Helper-Files. Subagent muss entfernen.
6. **07 Archiv/_MOC.md** - wird oft additiv angefasst trotz Verbot. Briefing: "07 Archiv/_MOC.md NICHT anfassen" explizit.
7. **Mindest-Zeilen fur neue Snippets** - Gemini macht manchmal nur 50-55 Zeilen statt 60+ wenn nicht vorgegeben.

## Referenzen

- `obsidian-vault-cluster-operations` - Patterns 0a, 1-8 (Hauptskill)
- `vault-architecture` - Phase 5/5.5 CSS-Theming, MOC-Patterns
- `coding-agents` - Gemini-CLI-Ubersicht, Auth-Modes, Modelle
- Vault-Resource: `Skill-Ableitung - Vault-Phase-7-8-9.md`
- Vault-Resource: `Vault-Phase-7-Plan - Gemini-Audit.md`
- Vault-Resource: `Vault-Phase-8-Plan - Design-Rework.md`
- Vault-Resource: `Vault-Phase-9-Plan - Yuno+Gemini-Finalisierung.md`
- Memory-Anker: "PATTERN-CATALOG: Gemini-CLI als Worker-Bee-Tool im Schwarm"
