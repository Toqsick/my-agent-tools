# Pre-Flight Plan-Reality Verification

## Vollständiges Worked Example (Phase 6, Cluster 1, 2026-07-05)

### Ausgangslage

Der Plan sagte:

```
05 Ressourcen/MOC - Daily Notes.md (0 Zeilen)  → Zero-Content
```

### Reality-Check (Pattern 0a)

```bash
# 1. Existiert der Pfad aus dem Plan?
ls -la "/home/bratan/Dokumente/Obsidian Vault/05 Ressourcen/MOC - Daily Notes.md"
# → ls: cannot access '...': No such file or directory
# → Pfad existiert NICHT

# 2. Alternative Position suchen
find "/home/bratan/Dokumente/Obsidian Vault" -name "MOC - Daily Notes.md"
# → /home/bratan/Dokumente/Obsidian Vault/MOC - Daily Notes.md
# → Datei liegt im ROOT, nicht in 05 Ressourcen/

# 3. Ist die Datei wirklich Zero-Content?
wc -l "/home/bratan/Dokumente/Obsidian Vault/MOC - Daily Notes.md"
# → 0 (0 Zeilen)
stat --format=%s "/home/bratan/Dokumente/Obsidian Vault/MOC - Daily Notes.md"
# → 0 (0 Bytes)
# → JA, wirklich leer

# 4. Entscheidung: write_file auf korrektem Pfad
# → Dokumentierte Abweichung: "Plan said 05 Ressourcen/, reality is root/"
```

### Fazit

| Schritt | Erkenntnis |
|---------|-----------|
| Plan-Pfad prüfen | `05 Ressourcen/MOC - Daily Notes.md` existiert nicht |
| search_files nach Dateiname | Datei liegt in `/ (root)` |
| Zero-Content verifizieren | `wc -l = 0`, `stat = 0` → write_file safe |
| Abweichung dokumentieren | Pfad-Korrektur protokolliert, kein stillschweigendes Abweichen |

### Anti-Pattern

Ohne Pre-Flight Check hätte ich:
1. Auf `05 Ressourcen/MOC - Daily Notes.md` geschrieben → Datei nicht da → write_file erzeugt sie am falschen Ort
2. Die Root-Datei nicht gefunden → Bearbeitet die falsche Datei
3. Oder schlimmer: die Root-Datei übersehen und den gesamten MOC nicht aktualisiert

### Wann Pre-Flight Check überspringen?

- **Plan ist < 30 Minuten alt** und wurde in derselben Session erstellt — dann ist der Check optional
- **Plan wurde durch einen kürzlichen `search_files`-Aufruf validiert** — dann reicht ein stichprobenartiger Check
- Bei JEDEM Plan, der älter als 1 Stunde ist oder von einer früheren Session stammt → **zwingend Pre-Flight Check**
