# Ollama Pull-Hang Workaround

## Symptom
- `ollama pull hf.co/ns/model:tag` startet, lädt bis ~80-95%
- Fortschritt bleibt stehen (Partial-Blob unverändert für >5 Minuten)
- Process läuft (PID existiert, 0% CPU)
- Kein Fehler-Log in `journalctl -u ollama`

## Root Cause
Reproduzierbarer Bug auf Ollama v0.30.x (2026-07-15/16 bestätigt). Tritt bei
großen Modellen (≥5 GB) auf, besonders wenn:
- Ein vorheriger Pull abgebrochen wurde (partial blob vorhanden)
- Parallele Pulls liefen und ein "Lock" im Daemon zurückblieb
- Der Systemd-Service während eines Pulls neugestartet wurde

Der Daemon hält am letzten erfolgreichen Chunk fest, aber die HTTP-Connection
zum Download-Server (Hugging Face / Ollama Registry) ist getrennt. Der
Ollama-Daemon wartet auf Timeout statt automatisch zu resumen.

## Resume via API (empfohlen)

```bash
# 1. Modellname exakt ermitteln
ollama list 2>&1 | grep -i "partial\|incomplete" || echo "(keine partial tags)"

# 2. Resume via POST — API erkennt partial blobs und setzt fort
curl -X POST http://127.0.0.1:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"model": "hf.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF:Q4_K_M"}'

# Output (läuft im Terminal bis success):
# {"status":"pulling <sha>","digest":"sha256:...","total":7381381664,"completed":6663015677}
# ...
# {"status":"verifying sha256 digest"}
# {"status":"writing manifest"}
# {"status":"success"}
```

**Vorteile:** Kein Re-Download, setzt vom Partial-Blob fort, schnell.
**Erfolgreich getestet für:** yuxinlu1 12B Q4_K_M (7.4 GB), DSV4-Flash Q4_K_M (5.6 GB).

## Quant-Wechsel (Alternative)

Wenn das Resume nicht funktioniert (z.B. weil der Partial-Blob korrupt ist):

```bash
# Anderen Quant pullen — umgeht den Bug komplett
ollama pull hf.co/Jackrong/Qwen3.5-9B-DeepSeek-V4-Flash-GGUF:Q5_K_M
```

**Warum das hilft:** Jeder Quant hat einen anderen SHA256-Blob. Der Daemon
startet eine frische Download-Connection ohne vorherigen State.

**Erfolgreich getestet:** DSV4-Flash Q4_K_M → Q5_K_M (Bug umgangen).

## Kill + Clean Pull (Letzte Option)

```bash
# 1. Alle hängenden Pull-Processe killen
pkill -f "ollama pull"
pkill -f "ollama create"
sleep 2

# 2. Partial-Blobs aufräumen
# Location: /usr/share/ollama/.ollama/models/blobs/ (system mode)
#          ~/.ollama/models/blobs/        (user mode)
ls -la /usr/share/ollama/.ollama/models/blobs/ | grep partial
sudo rm -f /usr/share/ollama/.ollama/models/blobs/*-partial*

# 3. Sauber neu starten — einzeln!
ollama pull hf.co/ns/model:tag
```

**Nachteil:** Kompletter Re-Download (kostet Zeit + Traffic).

## Prävention

- **Große Pulls (>4 GB) einzeln ausführen** — nie parallel
- **Nicht gleichzeitig pullen + Modelfile erstellen** — Create-Race triggert
  denselben Bug (siehe Troubleshooting in SKILL.md)
- **Nach Systemd-Service-Neustart:** Pull-Status prüfen, nicht blind neu
  starten — der Partial-Blob ist noch da
- **Bei Wiederholungstätern:** Den Bug durch anderen Quant umgehen (Q5_K_M
  statt Q4_K_M)

## Verifikation

Nach erfolgreichem Pull:
```bash
ollama list | grep <modell>
# Sollte das Modell zeigen (Size > 0, frischer timestamp)

ls /usr/share/ollama/.ollama/models/blobs/ | grep -c partial
# Sollte 0 sein (keine partial-blobs mehr)
```
