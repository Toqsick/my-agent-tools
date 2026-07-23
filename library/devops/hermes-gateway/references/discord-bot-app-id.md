# Discord Bot App-ID aus Token extrahieren

Wenn du nur den Bot-Token hast, aber die Application-ID brauchst (z.B. für den Discord Developer Portal Link):

## Methode

Discord Bot-Tokens haben das Format: `<base64_app_id>.<base64_timestamp>.<hmac>`

Das erste Segment (vor dem ersten Punkt) ist die **Application-/Bot-User-ID**, base64-codiert.

```bash
# Token aus .env holen und decoden
grep DISCORD_BOT_TOKEN ~/.hermes/.env | cut -d'=' -f2 | cut -d'.' -f1 | base64 -d

# Beispiel-Ausgabe: 1511229776600367256
```

## Ergebnis verwenden

Mit der decodeten App-ID kannst du direkt zum Bot-Einstellungs-Portal navigieren:

```
https://discord.com/developers/applications/<APP_ID>/bot
```

Beispiel:
https://discord.com/developers/applications/1511229776600367256/bot

## Warum?

- Der Discord Developer Portal-Link braucht die **Application-ID** (nicht den Bot-Token)
- Der Bot-Token ist im `.env` gespeichert, die App-ID meist nirgendwo
- Das erste Base64-Segment des Tokens IST die User-ID des Bots, die der App-ID entspricht
- Kein Login ins Portal nötig — einfach aus dem Token decoden
