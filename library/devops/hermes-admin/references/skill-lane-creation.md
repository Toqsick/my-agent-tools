# Skill Lane Creation via `hermes config set`

Neue Skill-Lanes (Worker-Rollen) können **nur** via `hermes config set` (nicht via `patch`/`write_file`) angelegt werden — die Config ist schreibgeschützt.

## Pattern (verified 2026-07-08 beim Anlegen von `worker-telegram`):

```bash
# 1. Modell + Provider + Profile setzen
hermes config set skill_lanes.X.model "model-name"
hermes config set skill_lanes.X.profile "profile-name"
hermes config set skill_lanes.X.profile_model_provider "provider"

# 2. Reasoning-Effort
hermes config set skill_lanes.X.reasoning_effort "high"

# 3. Purpose (humane Beschreibung, optional aber empfohlen)
hermes config set skill_lanes.X.purpose "Beschreibung der Lane-Rolle"

# 4. Skills als YAML-Flow-Sequence (String!)
hermes config set skill_lanes.X.skills "[skill1, skill2, skill3]"
```

## Wichtig:

`hermes config add skill_lanes.X.skills ...` gibt es NICHT (`invalid choice: 'add'`). Skills müssen als komplette YAML-Flow-Sequence in einem Set-Befehl gesetzt werden. Um später Skills hinzuzufügen, den gesamten Array-String erneut setzen.

## Nach dem Anlegen:

Gateway-Neustart via Subagent-Pattern nötig (siehe Gateway-Abschnitt), damit die Lane aktiv wird.

## Beispiel — in dieser Session erstellte Telegram-Lane:

```yaml
  worker-telegram:
    model: MiniMax-M2.7-highspeed
    profile: yuno-telegram
    profile_model_provider: minimax-oauth
    purpose: Telegram-Operations, Think-Tank-Messages, Bot-Commands, Group-Management
    reasoning_effort: high
    skills: '[telegram-clarification-prompt, inline-gate-fallback, messaging-gateway-setup]'
```