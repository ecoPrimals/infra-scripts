#!/usr/bin/env bash
set -euo pipefail

HUD_DIR="${HUD_DIR:-/home/eastgate/Development/ecoPrimals/infra/hud}"
cd "$HUD_DIR"

# Check for uncommitted changes in data/
CHANGED=$(git diff --name-only site/public/data/ 2>/dev/null | wc -l)
UNTRACKED=$(git ls-files --others --exclude-standard site/public/data/ 2>/dev/null | wc -l)
TOTAL=$((CHANGED + UNTRACKED))

if [ "$TOTAL" -eq 0 ]; then
    echo "[gaia-publish] no changes to publish"
    exit 0
fi

# Which mushrooms ran recently? (check tmp logs modified in last 15 min)
MUSHROOMS=""
for log in /tmp/mushroom-*.log; do
    if [ -f "$log" ]; then
        AGE=$(( $(date +%s) - $(stat -c %Y "$log" 2>/dev/null || echo 0) ))
        if [ "$AGE" -lt 900 ]; then
            NAME=$(basename "$log" .log | sed 's/mushroom-//')
            MUSHROOMS="${MUSHROOMS:+$MUSHROOMS, }$NAME"
        fi
    fi
done
[ -z "$MUSHROOMS" ] && MUSHROOMS="background processes"

git add site/public/data/
git commit --trailer "Co-authored-by: Cursor <cursoragent@cursor.com>" -m "🍄 gaia auto-publish: ${TOTAL} files updated by ${MUSHROOMS}" || true

# Push (handle conflicts gracefully)
git push origin main 2>/dev/null || {
    git pull origin main --no-rebase --no-edit 2>/dev/null
    git push origin main 2>/dev/null || true
}


echo "[gaia-publish] published ${TOTAL} files (mushrooms: ${MUSHROOMS})"

# Skip ephemeral files that overwrite every cycle
git checkout -- site/public/data/ear-latest.json 2>/dev/null || true
git checkout -- site/public/data/immune-state-live.json 2>/dev/null || true
git checkout -- site/public/data/heartbeat.json 2>/dev/null || true
git checkout -- site/public/data/pihz-emotion-stream.json 2>/dev/null || true
git checkout -- site/public/data/pihz-emotion-stream-ring.json 2>/dev/null || true
