#!/bin/bash
# steam-vr-install.sh — Install all VR games from Napalm's family library
# Run on the TARGET gate (northGate, ironGate, etc.)
# Uses steam:// protocol to queue installs in the running Steam client
set -euo pipefail

echo "🎮 GAIA VR LIBRARY INSTALLER"
echo "   Installing Napalm's HTC Vive era VR games via Steam Family"
echo "   Target: $(hostname) @ $(hostname -I | awk '{print $1}')"
echo ""

# VR Games from Napalm's library (gaia@gaming family)
declare -A VR_GAMES=(
  [552440]="The Talos Principle VR"
  [617830]="SUPERHOT VR"
  [555880]="Sairento VR"
  [489380]="QuiVR"
  [477270]="Lightblade VR"
  [747350]="Hellblade Senua VR Edition"
  [486780]="Fruit Ninja VR"
  [342180]="Arizona Sunshine"
  [250820]="SteamVR"
)

INSTALLED=0
QUEUED=0

for APPID in "${!VR_GAMES[@]}"; do
  NAME="${VR_GAMES[$APPID]}"
  
  # Check if already installed
  if [ -f "$HOME/.steam/steam/steamapps/appmanifest_${APPID}.acf" ]; then
    echo "  ✓ $NAME ($APPID) — already installed"
    INSTALLED=$((INSTALLED + 1))
  else
    echo "  ⬇ $NAME ($APPID) — queuing install..."
    # Queue via steam:// protocol (opens in running Steam client)
    steam steam://install/$APPID &>/dev/null &
    QUEUED=$((QUEUED + 1))
    sleep 2  # brief pause between queue requests
  fi
done

echo ""
echo "═══════════════════════════════════════"
echo "  Already installed: $INSTALLED"
echo "  Queued for install: $QUEUED"
echo "  Total VR games: ${#VR_GAMES[@]}"
echo "═══════════════════════════════════════"
echo ""
echo "Steam will download in the background."
echo "Check progress: steam steam://downloads"
