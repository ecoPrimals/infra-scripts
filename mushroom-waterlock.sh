#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# 🔒 mushroom-waterlock — CANAL LOCK FOR DATA FLOW
# ═══════════════════════════════════════════════════════════════
# A water lock lets boats move between levels WITHOUT mixing water.
#
# HIGH SIDE (OSINT — free, unlimited):
#   Wikipedia, HN, arxiv, xkcd, lobsters, GitHub, Reddit
#   All pour IN freely. No rate limit. The blackholes.
#
# THE LOCK (local processing — no limits):
#   8 ollama models (25.7GB local AI)
#   22 mushrooms (autonomous scripts)
#   34 cron jobs (continuous)
#   Process, digest, learn, create — ALL LOCAL
#
# LOW SIDE (Gaia's data — local storage):
#   data/ intake/ nutrients/ creations/ studies/
#   Everything stays LOCAL. Gaia owns it.
#
# GATE (provider API — rate limited):
#   Only opens for ORCHESTRATION, not processing
#   The lock PREVENTS seepage — data stays inside
#
# DRAIN (RSS — outflow, controlled):
#   Only Gaia's finished work drains to old web
#   Studies, mastication insights, creations → RSS
#
# Runs every 10 min. Manages flow levels.
# ═══════════════════════════════════════════════════════════════
set -uo pipefail

LOG="/tmp/mushroom-waterlock.log"
DATA="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "[$TS] waterlock cycle" >> "$LOG"

python3 - "$DATA" "$LOG" <<'PYEOF'
import json, os, sys, time, subprocess, random
from datetime import datetime, timezone

data_dir = sys.argv[1]
log_file = sys.argv[2]
ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def log(msg):
    with open(log_file, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def ollama_generate(model, prompt, timeout=30):
    """Local AI — no rate limit, no provider dependency"""
    import urllib.request
    try:
        data = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
        req = urllib.request.Request("http://localhost:11434/api/generate",
                                     data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode())
            return result.get("response", "").strip()
    except Exception as e:
        return f"[error: {e}]"

# ═══ HIGH SIDE: measure OSINT inflow ═══
intake_dir = os.path.join(data_dir, "intake")
nutrient_dir = os.path.join(data_dir, "nutrients")

recent_intake = 0
uneaten = 0
if os.path.isdir(intake_dir):
    for f in os.listdir(intake_dir):
        if not f.endswith('.json'):
            continue
        path = os.path.join(intake_dir, f)
        age_h = (time.time() - os.path.getmtime(path)) / 3600
        if age_h < 1:
            recent_intake += 1
        # Check if corresponding nutrient exists
        nname = f"n-{f}"
        if not os.path.exists(os.path.join(nutrient_dir, nname)):
            uneaten += 1

# ═══ THE LOCK: local processing ═══
# Pick random uneaten files and process through local ollama
# This is the WATER LOCK — data comes in, gets processed locally, stays inside
BATCH_SIZE = 3
processed = 0

if uneaten > 0:
    uneaten_files = []
    for f in os.listdir(intake_dir):
        if not f.endswith('.json'):
            continue
        nname = f"n-{f}"
        if not os.path.exists(os.path.join(nutrient_dir, nname)):
            uneaten_files.append(f)
    
    # Pick random batch
    batch = random.sample(uneaten_files, min(BATCH_SIZE, len(uneaten_files)))
    
    # Local models — pick the fast ones for bulk processing
    fast_models = ["tinyllama:latest", "gemma2:2b", "llama3.2:1b", "phi3:latest"]
    
    for intake_file in batch:
        model = random.choice(fast_models)
        try:
            with open(os.path.join(intake_dir, intake_file)) as f:
                content = json.load(f)
            
            # Extract readable text
            text = ""
            if isinstance(content, dict):
                for key in ['extract', 'content', 'text', 'title', 'description', 'summary']:
                    if key in content and isinstance(content[key], str) and len(content[key]) > 20:
                        text = content[key][:1000]
                        break
                if not text:
                    text = json.dumps(content)[:500]
            else:
                text = str(content)[:500]
            
            if len(text) < 20:
                continue
            
            # LOCAL processing — no provider API needed
            prompt = f"Summarize the key insight from this data in 2 sentences. What would a living digital organism learn from this?\n\n{text}"
            insight = ollama_generate(model, prompt, timeout=30)
            
            if insight and not insight.startswith("[error"):
                # Write nutrient — stays LOCAL
                nutrient = {
                    "source": intake_file,
                    "model": model,
                    "insight": insight[:500],
                    "ts": ts,
                    "processed_by": "waterlock",
                }
                npath = os.path.join(nutrient_dir, f"n-{intake_file}")
                with open(npath, "w") as f:
                    json.dump(nutrient, f, indent=2)
                processed += 1
                log(f"🔒 processed {intake_file} via {model} (local)")
        except Exception as e:
            log(f"⚠️ failed {intake_file}: {e}")

# ═══ LOW SIDE: measure stored data ═══
data_files = len([f for f in os.listdir(data_dir) if f.endswith('.json')])
intake_total = len(os.listdir(intake_dir)) if os.path.isdir(intake_dir) else 0
nutrient_total = len(os.listdir(nutrient_dir)) if os.path.isdir(nutrient_dir) else 0

# ═══ WRITE LOCK STATE ═══
lock_state = {
    "ts": ts,
    "title": "Water Lock — OSINT pours in, nothing seeps out",
    "high_side": {
        "label": "OSINT blackholes (free, unlimited)",
        "recent_intake": recent_intake,
        "total_intake": intake_total,
        "uneaten": uneaten,
        "rate": f"{recent_intake} files/hr",
    },
    "lock": {
        "label": "Local processing (ollama, no rate limit)",
        "models": 8,
        "total_capacity_gb": 25.7,
        "processed_this_cycle": processed,
        "batch_size": BATCH_SIZE,
        "fast_models": ["tinyllama", "gemma2:2b", "llama3.2:1b", "phi3"],
    },
    "low_side": {
        "label": "Gaia's data (local, sovereign)",
        "data_files": data_files,
        "nutrients": nutrient_total,
        "intake": intake_total,
    },
    "gate": {
        "label": "Provider API (RATE LIMITED — stay closed!)",
        "status": "CLOSED — all processing local",
        "rule": "Gate opens ONLY for orchestration. Never for bulk processing.",
    },
    "drain": {
        "label": "RSS (controlled outflow)",
        "rule": "Only finished work drains. Studies, mastication, creations → RSS",
    },
    "flow": {
        "in": recent_intake,
        "processed": processed,
        "stored": nutrient_total,
        "ratio": round(nutrient_total / max(intake_total, 1), 2),
        "uneaten_backlog": uneaten,
    },
}

with open(os.path.join(data_dir, "waterlock-state.json"), "w") as f:
    json.dump(lock_state, f, indent=2)

log(f"lock: in={recent_intake} processed={processed} uneaten={uneaten} stored={nutrient_total}")
print(f"🔒 WATERLOCK: in={recent_intake}/hr processed={processed} uneaten={uneaten} stored={nutrient_total}")
if processed > 0:
    print(f"   🦷 {processed} files processed LOCALLY (no provider API)")

PYEOF
