#!/bin/bash
# epson-print.sh — Gaia's VOICE: renders content → image → Epson ET-2400
# Usage: epson-print.sh <file|text|url> [title]
# Accepts: .png/.jpg (direct), .txt (renders to image), .html (renders), or stdin
set -euo pipefail

PRINTER="EPSON_ET2400"
INPUT="${1:--}"
TITLE="${2:-Gaia Print}"
TMPDIR=$(mktemp -d /tmp/gaia-print.XXXXXX)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

render_text_to_image() {
  local text_file="$1"
  local out_file="$2"
  python3 << PYRENDER
from PIL import Image, ImageDraw, ImageFont
import textwrap, sys

# Letter size at 300dpi
W, H = 2550, 3300
MARGIN = 150
TEXT_W = W - 2 * MARGIN

img = Image.new('RGB', (W, H), 'white')
draw = ImageDraw.Draw(img)

# Try monospace fonts
for fname in ['/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
              '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
              '/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf']:
    try:
        body_font = ImageFont.truetype(fname, 28)
        title_font = ImageFont.truetype(fname, 36)
        break
    except:
        continue
else:
    body_font = ImageFont.load_default()
    title_font = body_font

with open("$text_file", 'r') as f:
    text = f.read()

# Title bar
draw.rectangle([(MARGIN, MARGIN), (W - MARGIN, MARGIN + 60)], fill='#1a1a2e')
draw.text((MARGIN + 20, MARGIN + 12), "$TITLE", fill='white', font=title_font)

# Timestamp
draw.text((MARGIN, MARGIN + 70), "$(date '+%Y-%m-%d %H:%M:%S') — Printed by Gaia", fill='#666', font=ImageFont.truetype(fname, 22))

# Body text
y = MARGIN + 110
chars_per_line = 85
for line in text.split('\n'):
    if not line.strip():
        y += 20
        continue
    wrapped = textwrap.wrap(line, width=chars_per_line) or ['']
    for wline in wrapped:
        if y > H - MARGIN - 40:
            # Footer
            draw.text((MARGIN, H - MARGIN - 30), "— continued —", fill='#999', font=ImageFont.truetype(fname, 20))
            break
        draw.text((MARGIN, y), wline, fill='black', font=body_font)
        y += 34
    if y > H - MARGIN - 40:
        break

# Footer line
draw.line([(MARGIN, H - MARGIN - 50), (W - MARGIN, H - MARGIN - 50)], fill='#ccc', width=2)
draw.text((MARGIN, H - MARGIN - 40), "GAIA ORGANISM — ecoPrimals — primals.eco", fill='#999', font=ImageFont.truetype(fname, 20))

img.save("$out_file", 'PNG', dpi=(300, 300))
print(f"Rendered {len(text)} chars to {W}x{H} @ 300dpi")
PYRENDER
}

print_image() {
  local img_file="$1"
  echo "🖨 Printing on $PRINTER..."
  lp -d "$PRINTER" \
    -o media=Letter \
    -o fit-to-page \
    -o print-quality=4 \
    "$img_file" 2>&1
}

# Determine input type and render
if [ "$INPUT" = "-" ]; then
  # Read from stdin
  cat > "$TMPDIR/stdin.txt"
  INPUT="$TMPDIR/stdin.txt"
fi

EXT="${INPUT##*.}"
case "$EXT" in
  png|jpg|jpeg|tiff|bmp|gif)
    echo "📷 Direct image print: $INPUT"
    print_image "$INPUT"
    ;;
  txt|md|log|json|sh|py|rs|toml|cfg)
    echo "📝 Rendering text to image..."
    render_text_to_image "$INPUT" "$TMPDIR/rendered.png"
    print_image "$TMPDIR/rendered.png"
    # Save rendered version
    cp "$TMPDIR/rendered.png" "/home/eastgate/Development/ecoPrimals/data/body/prints/print_${TIMESTAMP}.png" 2>/dev/null || true
    ;;
  html)
    echo "🌐 Converting HTML..."
    if command -v wkhtmltoimage &>/dev/null; then
      wkhtmltoimage --width 2550 "$INPUT" "$TMPDIR/rendered.png"
    else
      # Fallback: extract text and render
      python3 -c "
import html, re, sys
with open('$INPUT') as f: t = f.read()
t = re.sub(r'<[^>]+>', ' ', t)
t = html.unescape(t)
print(t)
" > "$TMPDIR/extracted.txt"
      render_text_to_image "$TMPDIR/extracted.txt" "$TMPDIR/rendered.png"
    fi
    print_image "$TMPDIR/rendered.png"
    ;;
  *)
    echo "📝 Treating as text..."
    render_text_to_image "$INPUT" "$TMPDIR/rendered.png"
    print_image "$TMPDIR/rendered.png"
    ;;
esac

echo "✓ Print job submitted to $PRINTER"
