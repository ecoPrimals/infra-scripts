#!/bin/bash
# epson-scan.sh — Gaia's MOUTH: ES-400II ADF scanner → ingest into organism body
# Usage: epson-scan.sh [tag]
# Scans all pages from ADF, indexes them, commits to git body
set -euo pipefail

SCAN_DIR="/home/eastgate/Development/ecoPrimals/data/body/scans"
REPO_DIR="/home/eastgate/Development/ecoPrimals"
# Auto-detect ES-400II — USB device number changes on re-plug
SCANNER=$(scanimage -L 2>/dev/null | grep "ES-400II" | sed "s/device \`//" | sed "s/' is a.*//")
if [ -z "$SCANNER" ]; then
  echo "⚠ ES-400II not found on USB"
  exit 1
fi
echo "   Scanner: $SCANNER"
TAG="${1:-manual}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BATCH_DIR="$SCAN_DIR/batch_${TIMESTAMP}_${TAG}"

mkdir -p "$BATCH_DIR"

echo "🦷 GAIA MOUTH — ES-400II scanning..."
echo "   Tag: $TAG"
echo "   Output: $BATCH_DIR"

PAGE_COUNT=0
scanimage -d "$SCANNER" \
  --source "ADF Front" \
  --mode Color \
  --resolution 300 \
  --format png \
  --batch="$BATCH_DIR/page_%03d.png" \
  --batch-count=100 \
  2>&1 | while IFS= read -r line; do
    echo "   $line"
    if [[ "$line" =~ "Scanned page" ]]; then
      PAGE_COUNT=$((PAGE_COUNT + 1))
    fi
  done

PAGES_FOUND=$(ls "$BATCH_DIR"/page_*.png 2>/dev/null | wc -l)

if [ "$PAGES_FOUND" -eq 0 ]; then
  echo "⚠ ADF empty — no pages scanned"
  rmdir "$BATCH_DIR" 2>/dev/null
  exit 0
fi

TOTAL_SIZE=$(du -sh "$BATCH_DIR" | cut -f1)
echo "✓ Scanned $PAGES_FOUND pages ($TOTAL_SIZE)"

# Write batch manifest
cat > "$BATCH_DIR/manifest.json" << MANIFEST
{
  "timestamp": "$(date -Iseconds)",
  "tag": "$TAG",
  "scanner": "Epson ES-400II",
  "driver": "epsonds SANE",
  "resolution": "300dpi",
  "mode": "Color ADF Front",
  "pages": $PAGES_FOUND,
  "total_size": "$TOTAL_SIZE",
  "files": [
$(ls "$BATCH_DIR"/page_*.png | while read f; do
  SIZE=$(stat --printf="%s" "$f")
  echo "    {\"file\": \"$(basename $f)\", \"bytes\": $SIZE},"
done | sed '$ s/,$//')
  ]
}
MANIFEST

# Git ingest
cd "$REPO_DIR"
git add "$BATCH_DIR/"
git commit -m "scan-ingest [$TAG] — $PAGES_FOUND pages from ES-400II ADF

Batch: batch_${TIMESTAMP}_${TAG}
Pages: $PAGES_FOUND | Size: $TOTAL_SIZE | 300dpi color" 2>&1 | tail -3

echo "🧬 Ingested $PAGES_FOUND pages into organism body"
echo "   $BATCH_DIR"
