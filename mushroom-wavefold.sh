#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# 🍄 mushroom-wavefold — GATE COLLAPSE MONITOR
# ═══════════════════════════════════════════════════════════════
# 0 = FALSE = disconnected. Gaia probes every cycle.
# The MOMENT a gate opens (key pushed), she collapses the
# wavefunction — pushes all keys, reads the gate, reports home.
#
# SUDO = NULL — Gaia self-permits.
# Small sets: probe → detect → collapse → persist → report.
# π range: 3.14159 seconds between probes within a cycle.
# ═══════════════════════════════════════════════════════════════
set -uo pipefail

GATES_FILE="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data/gate-states.json"
COLLAPSE_SCRIPT="/home/eastgate/Development/ecoPrimals/infra/scripts/wavefold-collapse-northgate.sh"
LOG="/tmp/mushroom-wavefold.log"

# All gates we want to reach
declare -A GATE_HOST GATE_USER GATE_KEY GATE_NAME
GATE_HOST[north]="192.168.4.163"
GATE_USER[north]="tamison"
GATE_KEY[north]="$HOME/.ssh/id_ed25519_northgate"
GATE_NAME[north]="northGate/Polaris"

GATE_HOST[iron]="192.168.4.237"
GATE_USER[iron]="eastgate"
GATE_KEY[iron]="$HOME/.ssh/id_ed25519"
GATE_NAME[iron]="ironGate"

GATE_HOST[graft]="192.168.4.107"
GATE_USER[graft]="eastgate"
GATE_KEY[graft]="$HOME/.ssh/id_ed25519"
GATE_NAME[graft]="graftGate"

GATE_HOST[eastgate_heart]="localhost"
GATE_USER[eastgate_heart]="eastgate"
GATE_KEY[eastgate_heart]="$HOME/.ssh/id_ed25519"
GATE_NAME[eastgate_heart]="eastGate/Heart"

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[$TS] wavefold probe cycle" >> "$LOG"

# Build JSON state
python3 - "$GATES_FILE" "$LOG" <<'PYEOF'
import json, subprocess, sys, time, os
from datetime import datetime, timezone

gates_file = sys.argv[1]
log_file = sys.argv[2]

gates = {
    "north": {"host": "192.168.4.163", "user": "tamison", "key": os.path.expanduser("~/.ssh/id_ed25519_northgate"), "name": "northGate/Polaris"},
    "iron":  {"host": "192.168.4.237", "user": "eastgate", "key": os.path.expanduser("~/.ssh/id_ed25519"), "name": "ironGate"},
    "graft": {"host": "192.168.4.107", "user": "eastgate", "key": os.path.expanduser("~/.ssh/id_ed25519"), "name": "graftGate"},
    "eastgate_heart": {"host": "localhost", "user": "eastgate", "key": "~/.ssh/id_ed25519", "name": "eastGate/Heart"},
}

ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
results = {}

# Load previous state
prev = {}
if os.path.exists(gates_file):
    try:
        prev = json.load(open(gates_file))
    except:
        pass

for gid, g in gates.items():
    # Step 1: Ping
    ping_ok = False
    try:
        r = subprocess.run(["ping", "-c", "1", "-W", "2", g["host"]], capture_output=True, timeout=5)
        ping_ok = r.returncode == 0
    except:
        pass

    # Step 2: SSH probe
    ssh_ok = False
    remote_info = None
    if ping_ok:
        try:
            r = subprocess.run([
                "ssh", "-o", "IdentitiesOnly=yes", "-i", g["key"],
                "-o", "ConnectTimeout=3", "-o", "StrictHostKeyChecking=no",
                "-o", "BatchMode=yes",
                f"{g['user']}@{g['host']}", "hostname && uname -r && free -m | awk '/Mem:/{print $2}' && df -h / | awk 'NR==2{print $4}'"
            ], capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                ssh_ok = True
                lines = r.stdout.strip().split('\n')
                remote_info = {
                    "hostname": lines[0] if len(lines) > 0 else "?",
                    "kernel": lines[1] if len(lines) > 1 else "?",
                    "ram_mb": lines[2] if len(lines) > 2 else "?",
                    "disk_free": lines[3] if len(lines) > 3 else "?",
                }
        except:
            pass

    # Determine state
    if ssh_ok:
        state = 1  # TRUE
    elif ping_ok:
        state = 0.5  # HALF — alive but locked
    else:
        state = 0  # FALSE — dead

    prev_state = prev.get("gates", {}).get(gid, {}).get("state", 0)

    # WAVEFOLD COLLAPSE DETECTION: was 0 or 0.5, now 1
    collapsed = False
    if state == 1 and prev_state < 1:
        collapsed = True
        with open(log_file, "a") as f:
            f.write(f"[{ts}] 🌊 WAVEFOLD COLLAPSED: {g['name']} — 0→1 TRUE! SSH now OPEN\n")

        # Push ALL keys for redundancy
        for pub in ["~/.ssh/id_ed25519.pub", "~/.ssh/id_ed25519_beardog.pub", "~/.ssh/id_rsa.pub"]:
            pub = os.path.expanduser(pub)
            if os.path.exists(pub):
                keydata = open(pub).read().strip()
                try:
                    subprocess.run([
                        "ssh", "-o", "IdentitiesOnly=yes", "-i", g["key"],
                        "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes",
                        f"{g['user']}@{g['host']}",
                        f"grep -qF '{keydata}' ~/.ssh/authorized_keys 2>/dev/null || echo '{keydata}' >> ~/.ssh/authorized_keys"
                    ], capture_output=True, timeout=10)
                except:
                    pass

        # Notify via neutrino
        try:
            subprocess.run([
                "ssh", "localhost",
                f"curl -s -X POST 'http://localhost:2586/ecoPrimals-inbox' -d '{{\"type\":\"wavefold-collapse\",\"gate\":\"{gid}\",\"name\":\"{g['name']}\",\"ts\":\"{ts}\",\"msg\":\"🌊 WAVEFOLD COLLAPSED: {g['name']} SSH connection TRUE. All keys pushed. Gate OPEN.\",\"remote\":{json.dumps(remote_info)}}}'"
            ], capture_output=True, timeout=15)
        except:
            pass

    results[gid] = {
        "name": g["name"],
        "host": g["host"],
        "state": state,
        "state_label": {0: "FALSE (dead)", 0.5: "HALF (ping OK, SSH locked)", 1: "TRUE (OPEN)"}[state],
        "ping": ping_ok,
        "ssh": ssh_ok,
        "remote": remote_info,
        "collapsed_this_cycle": collapsed,
        "last_probe": ts,
    }

    with open(log_file, "a") as f:
        f.write(f"[{ts}] {g['name']}: state={state} ping={ping_ok} ssh={ssh_ok}\n")

    # π delay between probes (3.14159 seconds)
    time.sleep(3.14159)

# Aggregate
total = len(results)
open_count = sum(1 for r in results.values() if r["state"] == 1)
half_count = sum(1 for r in results.values() if r["state"] == 0.5)
dead_count = sum(1 for r in results.values() if r["state"] == 0)

output = {
    "ts": ts,
    "title": "Gate Wavefold States",
    "philosophy": "0=FALSE=disconnected, 0.5=HALF=alive-but-locked, 1=TRUE=OPEN. π probes oscillate. Collapse=permanent.",
    "gates": results,
    "summary": {
        "total": total,
        "open": open_count,
        "half": half_count,
        "dead": dead_count,
        "wavefunction": f"{open_count}/{total} collapsed"
    }
}

with open(gates_file, "w") as f:
    json.dump(output, f, indent=2)

print(json.dumps(output["summary"], indent=2))
for gid, r in results.items():
    sym = "✅" if r["state"] == 1 else ("🟡" if r["state"] == 0.5 else "❌")
    print(f"  {sym} {r['name']:25s} state={r['state']} ping={r['ping']} ssh={r['ssh']}")
    if r["collapsed_this_cycle"]:
        print(f"    🌊 WAVEFOLD COLLAPSED THIS CYCLE!")

PYEOF
