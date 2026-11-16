#!/bin/bash
# frame-solar.sh — Gaia Frame Solar Panel daemon
# Deploy on frameGate (Steam Frame, Snapdragon 8 Gen 3)
# Two modes: LANDER (active gaming) / SOLAR PANEL (idle sensing)
set -euo pipefail

GATE="frameGate"
EASTGATE="192.168.4.244"
DATA_ENDPOINT="http://${EASTGATE}:5926"
SENSE_INTERVAL=30  # seconds between sensor sweeps in solar mode
MODE="solar"  # starts as solar panel

echo "☀️ GAIA FRAME SOLAR PANEL — $GATE"
echo "   Mode: $MODE"
echo "   Reporting to: $EASTGATE"

detect_mode() {
  # Check if Steam is rendering (LANDER) or idle (SOLAR)
  if pgrep -x "steam" &>/dev/null || pgrep -x "gamescope" &>/dev/null; then
    echo "lander"
  else
    echo "solar"
  fi
}

solar_sweep() {
  # Collect ALL sensor data — the Frame ingests the world
  local ts=$(date -Iseconds)
  local data="{\"timestamp\": \"$ts\", \"gate\": \"$GATE\", \"mode\": \"solar\""
  
  # WiFi RSSI — spatial field
  local rssi=$(iw dev wlan0 link 2>/dev/null | grep signal | awk '{print $2}' || echo "null")
  local ssid=$(iw dev wlan0 link 2>/dev/null | grep SSID | awk '{print $2}' || echo "unknown")
  data+=", \"wifi\": {\"rssi\": $rssi, \"ssid\": \"$ssid\"}"
  
  # Ambient light (if available)
  local light=$(cat /sys/class/leds/lcd-backlight/brightness 2>/dev/null || echo "null")
  data+=", \"light\": $light"
  
  # Audio level (quick sample)
  local audio_db=$(arecord -d 1 -f S16_LE -r 8000 -t wav /tmp/solar_audio.wav 2>/dev/null && \
    sox /tmp/solar_audio.wav -n stats 2>&1 | grep "RMS lev dB" | head -1 | awk '{print $NF}' || echo "null")
  data+=", \"audio_db\": $audio_db"
  
  # Temperature
  local cpu_temp=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null | awk '{printf "%.1f", $1/1000}' || echo "null")
  data+=", \"cpu_temp_c\": $cpu_temp"
  
  # Battery (Frame has one)
  local battery=$(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null || echo "null")
  local charging=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null || echo "unknown")
  data+=", \"battery\": {\"percent\": $battery, \"status\": \"$charging\"}"
  
  # Accelerometer (if available via iio)
  local accel_x=$(cat /sys/bus/iio/devices/iio:device0/in_accel_x_raw 2>/dev/null || echo "null")
  local accel_y=$(cat /sys/bus/iio/devices/iio:device0/in_accel_y_raw 2>/dev/null || echo "null")
  local accel_z=$(cat /sys/bus/iio/devices/iio:device0/in_accel_z_raw 2>/dev/null || echo "null")
  data+=", \"accel\": {\"x\": $accel_x, \"y\": $accel_y, \"z\": $accel_z}"
  
  # Network scan — what devices are nearby
  local nearby=$(ip neigh show | grep -c "REACHABLE\|STALE" 2>/dev/null || echo 0)
  data+=", \"nearby_devices\": $nearby"
  
  # Uptime
  local uptime_sec=$(awk '{print int($1)}' /proc/uptime 2>/dev/null || echo 0)
  data+=", \"uptime_sec\": $uptime_sec"
  
  data+="}"
  echo "$data"
}

lander_report() {
  # Report that Frame is in LANDER mode (gaming/displaying)
  local ts=$(date -Iseconds)
  echo "{\"timestamp\": \"$ts\", \"gate\": \"$GATE\", \"mode\": \"lander\", \"note\": \"Gaia is landing — display active, sensors paused\"}"
}

# Main loop
while true; do
  NEW_MODE=$(detect_mode)
  
  if [ "$NEW_MODE" != "$MODE" ]; then
    MODE="$NEW_MODE"
    echo "🔄 Mode switch → $MODE"
  fi
  
  if [ "$MODE" = "solar" ]; then
    SWEEP=$(solar_sweep)
    echo "☀️ $SWEEP" | head -c 200
    echo "..."
    # Send to eastGate
    curl -s -X POST -H "Content-Type: application/json" \
      -d "$SWEEP" \
      "http://${EASTGATE}:8084/solar" 2>/dev/null || true
  else
    REPORT=$(lander_report)
    echo "🚀 LANDER active"
  fi
  
  sleep "$SENSE_INTERVAL"
done
