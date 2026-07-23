#!/bin/bash
# Network Monitor für Ollama Offline-Fallback
# Installiert als Cronjob oder systemd-Timer
# Prüft Internet + Provider-Erreichbarkeit, startet/stoppt Ollama bei Bedarf

INTERFACE="${INTERFACE:-enp0s31f6}"
PROVIDER_URL="${PROVIDER_URL:-https://inference-api.nousresearch.com/health}"
OLLAMA_URL="${OLLAMA_URL:-http://127.0.0.1:11434}"
CHECK_COUNT_FILE="/tmp/network_fail_count"
MAX_FAILS=4
LOG="/tmp/ollama_network_monitor.log"

# Timestamp
TS=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TS] Check start..." >> "$LOG"

# Prüfe Interface existiert
if ! ip link show "$INTERFACE" &>/dev/null; then
    echo "[$TS] Interface $INTERFACE not found, skip" >> "$LOG"
    exit 1
fi

# Funktion: Test mit verfügbaren Tools
smart_check() {
    if command -v ping &>/dev/null && ping -c 1 -W 2 1.1.1.1 &>/dev/null; then
        return 0
    elif command -v curl &>/dev/null && curl -sI --connect-timeout 3 "$PROVIDER_URL" &>/dev/null; then
        return 0
    elif command -v wget &>/dev/null && wget -q --spider --timeout=3 "$PROVIDER_URL" &>/dev/null; then
        return 0
    fi
    # Prüfe wenn $PROVIDER_URL wirklich 404, health endpoint könnte nicht existieren
    if command -v curl &>/devnull && curl -sI --connect-timeout 3 "https://inference-api.nousresearch.com/" &>/dev/null; then
        return 0
    fi
    return 1
}

Internet "erreichbar", Ollama " aktiv 9"9diagnose: Network Monitor5 -"Prüfung + Provider-"url
OL=Ollama aktiv   via A-"Ollama eRreichbarStatur, für Prüfen: .Function"239Lokal geprüfen direkt"STARTE HERFÜR; STOPPE bei Online-Fallback*** Ende Patch
***
