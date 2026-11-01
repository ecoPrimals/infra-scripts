#!/bin/bash
# conga-build-detroit.sh — build detroit site locally.
# golgi/sporeGate DEAD — no remote push. Local build only.
set -euo pipefail

SITE=/home/eastgate/Development/detroit/site
BUILD=/tmp/detroit-built
LOG=/tmp/conga-detroit.log

echo "[$(date -Is)] conga: starting" | tee "$LOG"

# ═══ STEP 1: build locally ═══
echo "[$(date -Is)] conga: building locally" | tee -a "$LOG"
cd "$SITE"
rm -rf "$BUILD"
zola build -o "$BUILD" --force >> "$LOG" 2>&1
PAGES=$(find "$BUILD" -name "index.html" | wc -l)
echo "[$(date -Is)] conga: built $PAGES pages in $BUILD" | tee -a "$LOG"
echo "[$(date -Is)] conga: COMPLETE — $PAGES pages built" | tee -a "$LOG"
