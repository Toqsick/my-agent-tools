"""
install_prereqs.sh — Installiert alle Prerequisites für GreyHack Computer-Use

Verwendung:
    chmod +x install_prereqs.sh
    ./install_prereqs.sh
"""

#!/bin/bash
set -e

echo "==============================================="
echo "🛠️  GreyHack Computer-Use Prerequisites"
echo "==============================================="
echo ""

# Tesseract OCR
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract already installed: $(tesseract --version 2>&1 | head -1)"
else
    echo "📦 Installing Tesseract OCR..."
    sudo apt update
    sudo apt install -y tesseract-ocr tesseract-ocr-deu
    echo "✅ Tesseract installed"
fi

# Window-Detection Tool
if command -v wmctrl &> /dev/null; then
    echo "✅ wmctrl already installed (X11)"
elif command -v grim &> /dev/null; then
    echo "✅ grim already installed (Wayland)"
else
    echo "📦 Installing wmctrl (X11) und grim (Wayland)..."
    sudo apt install -y wmctrl grim
fi

# Screenshot-Tool (Fallback)
if command -v scrot &> /dev/null || command -v gnome-screenshot &> /dev/null; then
    echo "✅ Screenshot-Tool already installed"
else
    echo "📦 Installing scrot..."
    sudo apt install -y scrot
fi

# cua-driver
echo ""
echo "🔧 Installing cua-driver via Hermes..."
if command -v hermes &> /dev/null; then
    hermes computer-use install
    echo "✅ cua-driver installation attempted"
else
    echo "⚠️  'hermes' CLI not found in PATH"
    echo "   Please install manually: https://github.com/trycua/cua"
fi

echo ""
echo "==============================================="
echo "✅ INSTALLATION COMPLETE"
echo "==============================================="
echo ""
echo "📋 Nächste Schritte:"
echo "   1. Grey Hack via Steam starten"
echo "   2. Pre-Flight-Check laufen lassen:"
echo "      python3 ~/.hermes/skills/computer-use/greyhack-mission-orchestrator/scripts/preflight_check.py"
echo "   3. Bei GO-Status: Mission starten:"
echo "      python3 ~/.hermes/skills/computer-use/greyhack-mission-orchestrator/scripts/orchestrator.py \\"
echo "        \"/home/bratan/Dokumente/Obsidian Vault/03 Projekte/Queen-Bee-Lab/Missions/Mission-Reraldi-IP-154.md\""