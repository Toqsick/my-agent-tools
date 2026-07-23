# Post-Update Checklist für Hermes Agent

Nach jedem `hermes update` abarbeiten.

## Sofort (< 2 Min)

- [ ] `hermes tools list` — Alle erwarteten Toolsets aktiv?
- [ ] `hermes status --deep` — Browser automation aktiv?
- [ ] `hermes cron list` — Alle Jobs mit korrekten Skills?
- [ ] `hermes doctor` — Neue Warnungen seit Update?

## Schnell (< 5 Min)

- [ ] Gateway-Logs auf Discord/Intents-Fehler prüfen:
  ```bash
  grep -iE "discord error|privileged|intent" ~/.hermes/logs/gateway.log | tail -5
  ```
- [ ] `hermes status --deep | grep "Access exp"` — Token noch frisch?
- [ ] Cron-Jobs Skills verifizieren (z.B. model-selector → daily-briefing)
- [ ] Auxiliary-Provider auf Konsistenz prüfen:
  ```bash
  python3 -c "
  import yaml
  c = yaml.safe_load(open('$HOME/.hermes/config.yaml'))
  for s,v in c.get('auxiliary',{}).items():
      if isinstance(v,dict) and v.get('provider')=='auto': print(f'  auto: {s}')
  "
  ```
- [ ] Platform toolsets auf Duplikate prüfen:
  ```bash
  python3 -c "
  import yaml
  c = yaml.safe_load(open('$HOME/.hermes/config.yaml'))
  for p,t in c.get('platform_toolsets',{}).items():
      if isinstance(t,list) and len(t)!=len(set(t)): print(f'  Duplicates in {p}')
  "
  ```

## Bei Problemen

| Symptom | Fix |
|---------|-----|
| Browser ✗ | `hermes tools enable browser` |
| Discord offline | Portal → Intents aktivieren → `hermes gateway restart` |
| Doctor: browser-cdp | `npm install -g agent-browser` oder ignorieren (P3) |
| npm vulnerabilities | P3, kosmetisch. Warten auf upstream |
| Cron falscher Skill | `cronjob(action='update', job_id='...', skills=['...'])` |

## Dokumentieren

- [ ] Update-Ergebnisse in `~/docs/builds/` notieren
- [ ] Neue Bugs/Quirks in Skill `hermes-maintenance` eintragen
