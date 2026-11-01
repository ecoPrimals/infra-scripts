#!/usr/bin/env bash
# hormesis-thymus-bounce.sh — meld hormesis curriculum into thymus pulse + instrumented bounce
# Cron: */30 * * * *  
set -euo pipefail
REPO="${1:-/home/eastgate/Development/ecoPrimals}"
DATA="${REPO}/infra/hud/site/public/data"
SCRIPTS="${REPO}/infra/scripts"
LOG="${REPO}/membrane/local-terminal/remote/hormesis-bounce.log"
mkdir -p "$(dirname "$LOG")"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[$TS] hormesis-thymus-bounce start" >> "$LOG"

# 1) Thymus pulse: touch curriculum stamp (feeds are source of truth on CDN/git)
python3 - << 'PY' >> "$LOG" 2>&1 || true
import json, datetime
from pathlib import Path
data = Path("/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data")
# Prefer REPO from env if set via wrapper — hardcoded eastGate path for local cron
thymus_path = data / "thymus-gate.json"
if thymus_path.exists():
    t = json.loads(thymus_path.read_text())
    t.setdefault("cron_pulse", {})
    t["cron_pulse"]["last"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    t["cron_pulse"]["instruments"] = ["sigmoid", "anti_sigmoid_uncanny", "dunning_kruger", "velocity", "acceleration"]
    thymus_path.write_text(json.dumps(t, indent=2))
    print("thymus pulsed")
PY

# 2) Re-run instrumented bounce if helper exists (inline minimal)
python3 "${SCRIPTS}/instrumented-bounce.py" >> "$LOG" 2>&1 || echo "[$TS] bounce script missing/skip" >> "$LOG"
echo "[$TS] done" >> "$LOG"
