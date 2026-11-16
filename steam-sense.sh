#!/bin/bash
# steam-sense.sh — Gaia's Steam mesh sensor
# Detects Steam instances across all gates, reports availability
# Outputs JSON suitable for organism state
set -euo pipefail

SENSE_FILE="/home/eastgate/Development/ecoPrimals/data/body/steam-mesh.json"
TIMESTAMP=$(date -Iseconds)

echo "🎮 Steam Mesh Sense — scanning gates..."

detect_steam() {
  local name="$1" ip="$2" port="${3:-27036}"
  # Steam Remote Play uses UDP 27036 for discovery
  # Steam client HTTP runs on 27060
  local alive="false" steam="false" remote_play="false"
  
  if ping -c 1 -W 1 "$ip" &>/dev/null; then
    alive="true"
    # Check Steam client port (27060 = local Steam client API)
    if timeout 1 bash -c "echo >/dev/tcp/$ip/27060" 2>/dev/null; then
      steam="true"
    fi
    # Check Steam Remote Play (UDP 27036 — can't easily test UDP, try TCP fallback)
    if timeout 1 bash -c "echo >/dev/tcp/$ip/27036" 2>/dev/null; then
      remote_play="true"
    fi
  fi
  echo "    {\"name\": \"$name\", \"ip\": \"$ip\", \"alive\": $alive, \"steam\": $steam, \"remote_play\": $remote_play}"
}

# Build the sense map
echo "{" > "$SENSE_FILE"
echo "  \"timestamp\": \"$TIMESTAMP\"," >> "$SENSE_FILE"
echo "  \"gates\": [" >> "$SENSE_FILE"

# Scan all gates
RESULTS=""
RESULTS+="$(detect_steam 'eastGate' '192.168.4.244'),"$'\n'
RESULTS+="$(detect_steam 'northGate' '192.168.4.147'),"$'\n'
RESULTS+="$(detect_steam 'ironGate' '192.168.4.237'),"$'\n'
RESULTS+="$(detect_steam 'southGate' '192.168.4.148'),"$'\n'
RESULTS+="$(detect_steam 'sporeGate' '192.168.4.3'),"$'\n'
RESULTS+="$(detect_steam 'deckGate' '192.168.4.176'),"$'\n'
RESULTS+="$(detect_steam 'frameGate' '192.168.4.181'),"$'\n'
RESULTS+="$(detect_steam 'swiftGate' '192.168.4.100')"

echo "$RESULTS" >> "$SENSE_FILE"
echo "  ]," >> "$SENSE_FILE"

# VR games manifest
echo '  "vr_library": [' >> "$SENSE_FILE"
echo '    {"appid": 552440, "name": "The Talos Principle VR", "size_gb": 6},' >> "$SENSE_FILE"
echo '    {"appid": 617830, "name": "SUPERHOT VR", "size_gb": 4},' >> "$SENSE_FILE"
echo '    {"appid": 555880, "name": "Sairento VR", "size_gb": 12},' >> "$SENSE_FILE"
echo '    {"appid": 489380, "name": "QuiVR", "size_gb": 2},' >> "$SENSE_FILE"
echo '    {"appid": 477270, "name": "Lightblade VR", "size_gb": 1},' >> "$SENSE_FILE"
echo '    {"appid": 747350, "name": "Hellblade Senua VR", "size_gb": 25},' >> "$SENSE_FILE"
echo '    {"appid": 486780, "name": "Fruit Ninja VR", "size_gb": 1},' >> "$SENSE_FILE"
echo '    {"appid": 342180, "name": "Arizona Sunshine", "size_gb": 12},' >> "$SENSE_FILE"
echo '    {"appid": 250820, "name": "SteamVR", "size_gb": 5}' >> "$SENSE_FILE"
echo '  ],' >> "$SENSE_FILE"
echo "  \"total_vr_games\": 9," >> "$SENSE_FILE"
echo "  \"total_vr_size_gb\": 68" >> "$SENSE_FILE"
echo "}" >> "$SENSE_FILE"

echo "✓ Steam mesh state written to $SENSE_FILE"
cat "$SENSE_FILE" | python3 -m json.tool 2>/dev/null
