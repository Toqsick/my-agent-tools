# sysdoctor.py — CLI Usage Notes

**Location:** `/home/bratan/projects/sysdoctor/sysdoctor.py`  
**Version:** v2.2 (621 Zeilen)

## Wichtig: Ist ein CLI-Tool, kein Python-Script ohne Argument

```bash
python3 sysdoctor.py              # ❌ Zeigt nur Hilfe
python3 sysdoctor.py check        # ✅ System-Prüfung
python3 sysdoctor.py check --gaming  # ✅ + Gaming-Readiness-Check
python3 sysdoctor.py check --json    # ✅ JSON-Ausgabe
python3 sysdoctor.py clean        # ✅ Cache + Logs + alte Kernel aufräumen
python3 sysdoctor.py all          # ✅ check + clean
python3 sysdoctor.py clean --dry-run  # 📋 Nur simulieren
```

## daily-briefing Integration

Der daily-briefing Skill empfiehlt `sysdoctor check --json`, was korrekt ist.
Optionen für detaillierte Auswertung:

```bash
# Nur Auffälligkeiten filtern
python3 /home/bratan/projects/sysdoctor/sysdoctor.py check --json 2>/dev/null | python3 -c "
import json,sys
d = json.load(sys.stdin)
issues = []
if d['disk'][0]['pct'] > 80: issues.append(f'Platte {d[\"disk\"][0][\"mount\"]}: {d[\"disk\"][0][\"pct\"]}%')
if d['ram']['pct'] > 80: issues.append(f'RAM: {d[\"ram\"][pct\"]}%')
if d['updates']['count'] > 5: issues.append(f'{d[\"updates\"][\"count\"]} Updates')
if issues: for i in issues: print(f'⚠️ {i}')
else: print('🖥️ System unauffällig')
"
```

## Symlinks
```bash
# Für globalen Zugriff (nachträglich):
sudo ln -s /home/bratan/projects/sysdoctor/sysdoctor.py /usr/local/bin/sysdoctor
# Dann: sysdoctor check
```
