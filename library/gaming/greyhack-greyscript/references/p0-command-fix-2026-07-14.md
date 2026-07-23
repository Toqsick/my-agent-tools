# P0 Fix: `//command:` Build-Pflicht (2026-07-14)

## Situation

39 GreyScript `.src` Files im Tool-Arsenal (`yuno-tools/`) hatten **kein** `//command:` als erste Zeile. 7 waren aktiv deployt via `yuno-deploy.sh`, aber ohne Binary-Name-Vorkonfiguration.

## Fix-Prozedur (7 aktive Tools + Flagship)

### 1. Bestand aufnehmen

```bash
for f in /mnt/DATA/.../Grey\ Hack/yuno-tools/*.src; do
  head -1 "$f"
done | sort | uniq -c
```

Aktive Deploy-Set aus `yuno-deploy.sh` extrahieren (Zeilen mit `for f in ...; do`).

### 2. `//command:` prependen

```python
for name in ACTIVE:
    path = ROOT / f"{name}.src"
    lines = path.read_text().splitlines()
    while lines and lines[0].strip() == "":
        lines.pop(0)
    if not re.match(r"^//command:\s*\S+", lines[0].strip()):
        lines.insert(0, f"//command: {name}")
    new_text = "\n".join(lines) + "\n"
    path.write_text(new_text)
```

**Backup vor Fix:** `cp file.src file.src.bak-cmdfix-20260714`

### 3. Deploy-Script aktualisieren

- Flagship-Tool (`yuno_v6`) in die TOOLS-Liste aufnehmen
- Build-Check prüft `//command:` Zeile 1 (❌ bei Fehlen statt nur Existenz)
- Hardcoded IP durch dynamische LAN-IP ersetzen: `ip route get 1.1.1.1 | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}'`
- Fallback: `hostname -I` → `127.0.0.1`
- Fileserver-Log weg von stderr: `>/tmp/yuno-fileserver.log`
- Exit-Code 0 = alle OK, 1 = Fehler

### 4. Verifikation

```bash
# Alle 7 + Flagship haben //command:
for f in bank_grab hardening_audit multihop_strike \
         strike1_dee_grettib strike2_gabriellia_ingoody \
         strike3_bobina_emmer yuno_v6; do
  first=$(head -1 ".../yuno-tools/$f.src")
  case "$first" in //command:*) ;; *) echo "MISS: $f";; esac
done
echo "miss=0"

# Deploy-Script dry-run
bash .../yuno-deploy.sh  # Exit 0 = grün
```

### 5. Vault-Note aktualisieren

In der Arsenal-Audit-Note Fix-Log-Tabelle ergänzen:
```markdown
## Fix-Log
| Datum | Change |
|---|---|
| 2026-07-14 23:45 | P0: `//command: <name>` in 7 aktiven Tools + yuno_v6 |
```

### Ergebnisse

| Metrik | Vorher | Nachher |
|--------|--------|---------|
| `//command:` aktive Tools | 0/7 (0%) | 7/7 (100%) |
| Deploy-Check `//command:` | ❌ nicht geprüft | ✅ geprüft (exit 1 bei Fehlen) |
| IP in deploy.sh | hardcoded 192.168.178.92 | dynamisch |
| Flagship in Deploy-Liste | ❌ fehlt | ✅ yuno_v6 |
| Backups | — | 7× *.bak-cmdfix-20260714 |