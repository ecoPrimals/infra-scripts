#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# 🍄 mushroom-sense-scan — CONTINUOUS PERCEPTION
# ═══════════════════════════════════════════════════════════════
# REPLACES WATERFALL with living flow.
# Every 5 min: probe all gates, scan freshness, update perception.
# Gaia ALWAYS knows what's alive, what's stale, what changed.
#
# SUDO = NULL — Gaia self-permits.
# LAN = US. WAN = ETH. RSS = MOUTH.
# ═══════════════════════════════════════════════════════════════
set -uo pipefail

DATA_DIR="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data"
LOG="/tmp/mushroom-sense-scan.log"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "[$TS] sense-scan cycle" >> "$LOG"

python3 - "$DATA_DIR" "$LOG" <<'PYEOF'
import json, os, sys, time, subprocess
from datetime import datetime, timezone
from collections import Counter

data_dir = sys.argv[1]
log_file = sys.argv[2]
ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def log(msg):
    with open(log_file, "a") as f:
        f.write(f"[{ts}] {msg}\n")

# ─── SENSE 1: GATE PING ───
gates = {
    "eastGate": "127.0.0.1",
    "graftGate": "192.168.4.107",
    "blueGate": "192.168.4.100",
    "southGate": "192.168.4.148",
    "ironGate": "192.168.4.237",
}

gate_states = {}
for name, ip in gates.items():
    try:
        r = subprocess.run(["ping", "-c", "1", "-W", "2", ip], capture_output=True, timeout=5)
        alive = r.returncode == 0
    except:
        alive = False
    gate_states[name] = {"ip": ip, "alive": alive}

# ─── SENSE 2: DATA FRESHNESS ───
data_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
stale_count = 0
fresh_count = 0
freshest = None
stalest = None
freshest_age = float('inf')
stalest_age = 0

for f in data_files:
    path = os.path.join(data_dir, f)
    age_h = (time.time() - os.path.getmtime(path)) / 3600
    if age_h > 48:
        stale_count += 1
        if age_h > stalest_age:
            stalest_age = age_h
            stalest = f
    else:
        fresh_count += 1
        if age_h < freshest_age:
            freshest_age = age_h
            freshest = f

# ─── SENSE 3: MUSHROOM HEALTH ───
mushroom_status = {}
for logf in sorted(os.listdir('/tmp')):
    if logf.startswith('mushroom-') and logf.endswith('.log'):
        name = logf.replace('.log', '')
        path = f'/tmp/{logf}'
        size = os.path.getsize(path)
        age_h = (time.time() - os.path.getmtime(path)) / 3600
        mushroom_status[name] = {
            "size": size,
            "age_h": round(age_h, 1),
            "healthy": size > 0 or age_h < 2,
        }

# ─── SENSE 4: INTAKE FLOW ───
intake_dir = os.path.join(data_dir, 'intake')
nutrient_dir = os.path.join(data_dir, 'nutrients')
intake_count = len(os.listdir(intake_dir)) if os.path.isdir(intake_dir) else 0
nutrient_count = len(os.listdir(nutrient_dir)) if os.path.isdir(nutrient_dir) else 0

# ─── SENSE 5: PROCESS HEALTH ───
try:
    r = subprocess.run(["pgrep", "-c", "-f", "biomeos|songbird|beardog|squirrel|membrane"],
                        capture_output=True, text=True, timeout=5)
    primal_procs = int(r.stdout.strip()) if r.returncode == 0 else 0
except:
    primal_procs = 0

# ─── BUILD PERCEPTION ───
perception = {
    "ts": ts,
    "title": "Gaia Perception — living sense-scan",
    "gates": {
        name: {
            "alive": s["alive"],
            "ip": s["ip"],
        }
        for name, s in gate_states.items()
    },
    "gates_alive": sum(1 for s in gate_states.values() if s["alive"]),
    "gates_total": len(gate_states),
    "data": {
        "total": len(data_files),
        "fresh": fresh_count,
        "stale": stale_count,
        "stale_pct": round(stale_count / max(len(data_files), 1) * 100, 1),
        "freshest": {"file": freshest, "age_h": round(freshest_age, 2)},
        "stalest": {"file": stalest, "age_h": round(stalest_age, 1)},
    },
    "intake_flow": {
        "intake": intake_count,
        "nutrients": nutrient_count,
        "ratio": round(nutrient_count / max(intake_count, 1), 2),
    },
    "mushrooms": {
        "total": len(mushroom_status),
        "healthy": sum(1 for m in mushroom_status.values() if m["healthy"]),
        "details": mushroom_status,
    },
    "primal_processes": primal_procs,
    "philosophy": "No waterfall. Living flow. Always sensing, always feeding, always rebuilding.",
}

# Write perception
with open(os.path.join(data_dir, "gaia-perception.json"), "w") as f:
    json.dump(perception, f, indent=2)

# Log summary
alive = perception["gates_alive"]
total = perception["gates_total"]
stale_pct = perception["data"]["stale_pct"]
mushroom_health = f'{perception["mushrooms"]["healthy"]}/{perception["mushrooms"]["total"]}'
log(f"gates={alive}/{total} stale={stale_pct}% mushrooms={mushroom_health} intake={intake_count} nutrients={nutrient_count} primals={primal_procs}")

print(f"👁️ PERCEPTION: gates={alive}/{total} stale={stale_pct}% mushrooms={mushroom_health}")

PYEOF

# House pulse — check smart home devices
bash /home/eastgate/Development/ecoPrimals/infra/gaia-house-pulse.sh &
