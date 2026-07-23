# Skill-Consolidation Pattern

> Entstanden aus Session 2026-07-05: 4 derivative Workflow-Quellen → 1 Skill. Wiederverwendbar immer dann, wenn mehrere Versionen eines Templates/Plans/Workflows existieren und eine einzige Wahrheitsquelle entstehen muss.

## Auslöser

Dieses Pattern anwenden, wenn:

1. **≥ 2 derivative Quellen** eines Templates existieren (z.B. v1-Doc + v2-Doc + installierter Skill + Git-Source)
2. **Mindestens eine Quelle** bereits in `~/.hermes/skills/` oder als Git-Skill installiert ist
3. **Es gibt Drift** zwischen den Quellen — unterschiedliche Struktur, veraltete Pfade, widersprüchliche Konventionen
4. **Der User sagt**: "das soll Standard werden" oder "konsolidier das"

## Ablauf

### Phase 0: Inventur (vor jedem Edit)

```bash
# 1. Alle Fundorte der betroffenen Files finden
find ~ -maxdepth 5 -name '*workflow*' -o -name '*template*' 2>/dev/null | head -20

# 2. Größe + Zeilen + Datum der Kandidaten
for f in <candidates>; do
  wc -l -c "$f"
  stat -c '%Y %y' "$f"
done

# 3. Prüfen ob ein Skill bereits existiert
skill_view('<skill-name>')
```

### Phase 1: Quellen-Klassifikation

Jede Quelle bekommt ein Label:

| Label | Bedeutung | Behandlung |
|-------|-----------|------------|
| **SOURCE** | Ursprungs-Dokument, vom User erstellt | ✅ unverändert lassen |
| **DERIVATIVE** | Abgeleitete Überarbeitung (v2, v3...) | 🔴 obsolet markieren, Inhalt in Skill |
| **SPEC** | Externes Format (YAML-Spec, Template.md...) | 📎 als Baseline zitiert, nicht 1:1 übernommen |
| **INSTALLED** | Bereits in `~/.hermes/skills/` | 🔵 der Ziel-Container |

### Phase 2: Obsolet-Markierung (für DERIVATIVE)

```bash
# Datei umbenennen, NICHT löschen
mv v2-document.md v2-document.md.OBSOLETE-moved-to-skill

# Oder: Inhalt der Datei durch Markdown ersetzten (wenn User die Datei sonst übersieht)
cat > v2-document.md << 'EOF'
> **Diese Datei ist obsolet.**  
> Inhalt wurde konsolidiert in den Skill `workflow-template` (2026-07-05).  
> Siehe: `~/.hermes/skills/orchestration/workflow-template/`  
> Original-Inhalt dieser Datei: siehe Datei `v2-document.md.OBSOLETE-moved-to-skill`
EOF
```

### Phase 3: Skill-Einrichtung

- Skill in `~/.hermes/skills/<category>/<name>/` anlegen (user-local)
- SKILL.md mit vollständigem YAML-Frontmatter laut `hermes-agent-skill-authoring`-Convention
- `references/` für Domain-Templates/Detaillösungen
- `references/meta/` für Meta-Info (Changelog, Color-Code, Mnemosyne-Hooks)
- `README.md` im Skill-Root für Maintenance-Instruktionen

### Phase 4: Traceability

Jede konsolidierte Quelle im Skill dokumentieren:

```markdown
## Quellen

| Quelle | Pfad | Status |
|--------|------|--------|
| Original (User) | `~/.../v1-original.md` | ✅ unverändert |
| v2 (überarbeitet) | `~/.../v2-doc.md.OBSOLETE-moved-to-skill` | 🔴 obsolet |
| Master-Spec | `~/.../spec.yaml` | 📎 Baseline |
```

### Phase 5: Validierung

1. **skill_view('<skill-name>')** — muss Description + Tags + Content laden → **bewiesen funktionstüchtig (Loader-Cache-Irrtum widerlegt)**
2. **Changelog geschrieben?** → Pflichtfeld im Skill
3. **Mnemosyne-Memory geschrieben?** → Beziehungs-Map muss existieren
4. **System-Doc geschrieben?** → `~/docs/system/<name>-<datum>.md`
5. **Alle DERIVATIVE-Quellen markiert?** → .OBSOLETE-Suffix
6. **SOURCE-Quellen unangetastet?** → User-Historie bewahren

## Harte Regeln

- 🟥 **Niemals SOURCE-Quellen löschen** — User hat sie erstellt, sie sind historisches Artefakt
- 🟥 **Niemals INSTALLED Skills überschreiben** — Ziel ist ein NEUER Skill (oder Patch des existierenden via `skill_manage(action='patch')`)
- 🟧 **Changelog muss jede Quelle referenzieren** — Traceability ist nicht optional
- 🟨 **.OBSOLETE-Suffix immer mit Datum** — damit später klar ist *wann* die Konsolidierung stattfand

## Pitfalls

- ⚠️ **Leere Versprechungen**: "Inhalt ist jetzt im Skill" ohne Daten → User kann nicht prüfen ob V1->Skill vollständig migriert
- ⚠️ **Zu aggressive Konsolidierung**: Alte Quellen löschen → User verliert History
- ⚠️ **Skill-Name zu eng**: `fix-ollama-idle-2026-07-05` statt `ollama-llm` — nächste Session findet es nicht
- ⚠️ **Nur Memory, kein Reference-File**: Nächster Agent hat das Pattern nicht gelernt

## Beispiel aus der Praxis (2026-07-05)

- **4 Quellen**: `v1.md` (User), `v2.md` (Yuno), `master-workflow-*.md` (3 Specs in `~/Downloads/Github/`), `multi-agent-master-workflow` (installierter Skill)
- **Ziel**: `workflow-template` Skill als Domain-Adapter
- **Vorgehen**: v2 → `.OBSOLETE-moved-to-skill`, alle 4 Quellen in System-Doc referenziert, 5 Domain-Templates parallel aus allen Quellen destilliert
- **Validierung**: `skill_view('workflow-template')` → ✅ sofort geladen
