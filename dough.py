#!/usr/bin/env python3
"""
dough.py — knead all layers into a shape of reality

The mesh IS the instrument. Every node is a sensor.
Every latency is a distance. Every jitter is weather.

We already have:
  - LAN wired   (<1ms)    = bone      = solid
  - LAN jittery (7-21ms)  = muscle    = elastic
  - LAN WiFi    (90ms)    = air       = gas
  - WAN edge    (17-20ms) = membrane  = surface
  - WAN VPS     (45ms)    = horizon   = far field

The dough: ping all nodes, measure the shape, run eons through it,
blink-sort for signal, sourdough the result, output what rises.

Usage:
  python3 dough.py              # full knead
  python3 dough.py --quick      # just ping + shape
"""

import subprocess, json, time, math, hashlib, random, sys
from datetime import datetime, timezone
from pathlib import Path

# ── The Nodes ──────────────────────────────────────────────────────

NODES = {
    # LAN — wired
    "sporeGate":     {"ip": "192.168.4.1",   "layer": "bone",     "medium": "10G-fiber",  "jurisdiction": "MI-US"},
    "eastGate":      {"ip": "192.168.4.244", "layer": "bone",     "medium": "10G-SFP+",   "jurisdiction": "MI-US"},
    "CRS310":        {"ip": "192.168.4.2",   "layer": "bone",     "medium": "10G-switch",  "jurisdiction": "MI-US"},
    "Flint2":        {"ip": "192.168.4.250", "layer": "bone",     "medium": "1G-AP",       "jurisdiction": "MI-US"},
    "northGate":     {"ip": "192.168.4.147", "layer": "muscle",   "medium": "10G-copper",  "jurisdiction": "MI-US"},
    "graftGate":     {"ip": "192.168.4.107", "layer": "muscle",   "medium": "1G-copper",   "jurisdiction": "MI-US"},
    # LAN — WiFi
    "grapheneGate":  {"ip": "192.168.4.219", "layer": "air",      "medium": "WiFi-5GHz",   "jurisdiction": "MI-US"},
    # WAN — edge (anycast)
    "cloudflare":    {"ip": "hud.primals.eco",         "layer": "membrane", "medium": "anycast-CDN", "jurisdiction": "anycast-GDPR"},
    "github-pages":  {"ip": "hypothesis.primals.eco",  "layer": "membrane", "medium": "anycast-CDN", "jurisdiction": "anycast-GDPR"},
    "google-dns":    {"ip": "8.8.8.8",                 "layer": "membrane", "medium": "anycast",     "jurisdiction": "US-global"},
    # WAN — VPS (fixed location)
    "golgi":         {"ip": "157.230.3.183", "layer": "horizon",  "medium": "VPS-DO-NYC1", "jurisdiction": "NY-US-AGPL3"},
}

# ── Layer Properties (speed of "light" through each medium) ──────

LAYERS = {
    "bone":     {"expected_ms": 0.5,  "state": "solid",   "poor_tope": "Fe", "color": "#22c55e"},
    "muscle":   {"expected_ms": 10.0, "state": "elastic", "poor_tope": "C",  "color": "#3b82f6"},
    "air":      {"expected_ms": 80.0, "state": "gas",     "poor_tope": "O2", "color": "#a855f7"},
    "membrane": {"expected_ms": 18.0, "state": "surface", "poor_tope": "H2O","color": "#f59e0b"},
    "horizon":  {"expected_ms": 45.0, "state": "far",     "poor_tope": "O3", "color": "#ef4444"},
}

# ── Ping ─────────────────────────────────────────────────────────

def ping_node(name, info, count=5):
    """Ping a node, return latency stats."""
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", "2", info["ip"]],
            capture_output=True, text=True, timeout=15
        )
        lines = result.stdout.strip().split("\n")
        # Parse the rtt line
        for line in lines:
            if "rtt" in line or "round-trip" in line:
                parts = line.split("=")[-1].strip().split("/")
                return {
                    "name": name,
                    "ip": info["ip"],
                    "layer": info["layer"],
                    "medium": info["medium"],
                    "jurisdiction": info["jurisdiction"],
                    "min_ms": float(parts[0]),
                    "avg_ms": float(parts[1]),
                    "max_ms": float(parts[2]),
                    "mdev_ms": float(parts[3].split()[0]),
                    "alive": True,
                }
        # Parse packet loss
        for line in lines:
            if "packet loss" in line:
                loss = line.split(",")[2].strip().split("%")[0]
                if float(loss) == 100:
                    return {"name": name, "ip": info["ip"], "layer": info["layer"],
                            "alive": False, "reason": "100% packet loss"}
        return {"name": name, "ip": info["ip"], "layer": info["layer"],
                "alive": False, "reason": "no rtt line"}
    except subprocess.TimeoutExpired:
        return {"name": name, "ip": info["ip"], "layer": info["layer"],
                "alive": False, "reason": "timeout"}
    except Exception as e:
        return {"name": name, "ip": info["ip"], "layer": info["layer"],
                "alive": False, "reason": str(e)}

def probe_all():
    """Ping every node. Return list of results."""
    print("🫸 probing mesh...")
    results = []
    for name, info in NODES.items():
        r = ping_node(name, info)
        status = f"{r['avg_ms']:.1f}ms" if r.get("alive") else f"DOWN ({r.get('reason','')})"
        print(f"  {name:18s} {info['layer']:10s} {status}")
        results.append(r)
    return results

# ── Shape of Reality ─────────────────────────────────────────────

def calculate_shape(probes):
    """From latency measurements, calculate the shape."""
    alive = [p for p in probes if p.get("alive")]
    if not alive:
        return {"error": "no nodes alive"}

    # Group by layer
    layers = {}
    for p in alive:
        layer = p["layer"]
        if layer not in layers:
            layers[layer] = []
        layers[layer].append(p)

    shape = {}
    for layer_name, nodes in layers.items():
        expected = LAYERS[layer_name]["expected_ms"]
        latencies = [n["avg_ms"] for n in nodes]
        avg = sum(latencies) / len(latencies)
        jitter = sum(n["mdev_ms"] for n in nodes) / len(nodes)

        # Deviation from expected = "weather" in this layer
        deviation = avg / expected if expected > 0 else float('inf')

        # Epicycle ratio: how much of the signal is "real" vs interpolated
        # At expected latency, epicycle = 0 (pure signal)
        # Deviation > 1 means we're adding epicycles
        epicycle_ratio = max(0, deviation - 1.0)

        shape[layer_name] = {
            "nodes": len(nodes),
            "avg_ms": round(avg, 2),
            "jitter_ms": round(jitter, 3),
            "expected_ms": expected,
            "deviation": round(deviation, 3),
            "epicycle_ratio": round(epicycle_ratio, 3),
            "state": LAYERS[layer_name]["state"],
            "poor_tope": LAYERS[layer_name]["poor_tope"],
            "color": LAYERS[layer_name]["color"],
            "node_names": [n["name"] for n in nodes],
        }

    # Total shape metrics
    all_latencies = [p["avg_ms"] for p in alive]
    total_avg = sum(all_latencies) / len(all_latencies)
    total_jitter = sum(p["mdev_ms"] for p in alive) / len(alive)

    # The "is" = current measurement. The "was" = expected. The gap = epicycles.
    is_value = total_avg
    was_value = sum(LAYERS[l]["expected_ms"] * len(nodes) for l, nodes in layers.items()) / len(alive)
    gap = is_value - was_value

    # Is the system Ptolemaic? (gap > was = more epicycle than signal)
    ptolemaic = gap > was_value

    return {
        "layers": shape,
        "total_nodes_alive": len(alive),
        "total_nodes_probed": len(probes),
        "is_ms": round(is_value, 2),
        "was_ms": round(was_value, 2),
        "gap_ms": round(gap, 2),
        "ptolemaic": ptolemaic,
        "jurisdictions": list(set(p.get("jurisdiction", "unknown") for p in alive)),
    }

# ── Eon Bounce ───────────────────────────────────────────────────

def eon_bounce(shape, n_eons=100):
    """Run eon chemistry using real latency as activation energy."""
    pool = {
        "H2": 10, "He": 8, "H2O": 6, "O2": 4, "O3": 2,
        "C": 0, "Fe": 0, "N": 0, "P": 0, "S": 0,
    }

    reactions = []
    eras = []

    for eon in range(n_eons):
        # Activation energy from real mesh: pick a random layer's latency
        layer_names = list(shape.get("layers", {}).keys())
        if not layer_names:
            break
        layer = random.choice(layer_names)
        activation = shape["layers"][layer]["avg_ms"]
        jitter = shape["layers"][layer]["jitter_ms"]

        # Energy = activation + random jitter
        energy = activation + random.gauss(0, jitter)
        if energy < 0:
            energy = 0.1

        # Reaction rules (same as eon-sim but driven by REAL latency)
        if energy > 40 and pool["H2"] > 1:
            pool["H2"] -= 2
            pool["He"] += 1
            reactions.append({"eon": eon, "type": "fusion", "eq": "2H₂ → He", "energy": round(energy, 1), "layer": layer})
        elif energy > 20 and pool["H2"] > 0 and pool["O2"] > 0:
            pool["H2"] -= 1
            pool["O2"] -= 1
            pool["H2O"] += 1
            reactions.append({"eon": eon, "type": "oxidation", "eq": "H₂ + O₂ → H₂O", "energy": round(energy, 1), "layer": layer})
        elif energy > 30 and pool["He"] > 2:
            pool["He"] -= 3
            pool["C"] += 1
            reactions.append({"eon": eon, "type": "triple_alpha", "eq": "3He → C", "energy": round(energy, 1), "layer": layer})
            if "carbon" not in eras:
                eras.append("carbon")
        elif energy > 50 and pool["C"] > 0 and pool["O2"] > 0:
            pool["C"] -= 1
            pool["O2"] -= 1
            pool["Fe"] += 1
            reactions.append({"eon": eon, "type": "stellar", "eq": "C + O₂ → Fe", "energy": round(energy, 1), "layer": layer})
            if "iron" not in eras:
                eras.append("iron")
        elif energy > 15 and pool["O2"] > 1:
            pool["O2"] -= 2
            pool["O3"] += 1
            pool["N"] += 1
            reactions.append({"eon": eon, "type": "ozone", "eq": "2O₂ → O₃ + N", "energy": round(energy, 1), "layer": layer})
        elif energy > 35 and pool["N"] > 0 and pool["H2O"] > 0:
            pool["N"] -= 1
            pool["H2O"] -= 1
            pool["P"] += 1
            reactions.append({"eon": eon, "type": "phosphorus", "eq": "N + H₂O → P", "energy": round(energy, 1), "layer": layer})
            if "phosphorus" not in eras:
                eras.append("phosphorus")
        elif energy > 25 and pool["C"] > 0 and pool["N"] > 0:
            pool["C"] -= 1
            pool["N"] -= 1
            pool["S"] += 1
            reactions.append({"eon": eon, "type": "cno", "eq": "C + N → S", "energy": round(energy, 1), "layer": layer})
            if "sulfur" not in eras:
                eras.append("sulfur")

    return {
        "eons": n_eons,
        "reactions": len(reactions),
        "pool": pool,
        "eras": eras,
        "sample_reactions": reactions[:10] + reactions[-5:] if len(reactions) > 15 else reactions,
    }

# ── Blink Sort ───────────────────────────────────────────────────

def blink_sort(shape):
    """What blinks across layers = signal. What's stable = ground."""
    if "layers" not in shape:
        return {"blinks": [], "ground": []}

    layers = shape["layers"]
    metrics = {}

    for name, data in layers.items():
        metrics[name] = {
            "deviation": data["deviation"],
            "epicycle": data["epicycle_ratio"],
            "jitter": data["jitter_ms"],
        }

    # Sort by variance (deviation from expected)
    sorted_by_deviation = sorted(metrics.items(), key=lambda x: x[1]["deviation"], reverse=True)

    blinks = []
    ground = []
    for name, m in sorted_by_deviation:
        entry = {"layer": name, **m, "state": layers[name]["state"]}
        if m["deviation"] > 1.5 or m["epicycle"] > 0.5:
            blinks.append(entry)
        else:
            ground.append(entry)

    return {
        "blinks": blinks,
        "ground": ground,
        "signal_layers": len(blinks),
        "noise_layers": len(ground),
        "signal_pct": round(100 * len(blinks) / max(1, len(metrics)), 1),
    }

# ── Sourdough ────────────────────────────────────────────────────

def sourdough(shape, eons, blinks):
    """Ferment: mix the shape + eons + blinks, let personality emerge."""
    # The starter is the hash of the current shape
    shape_str = json.dumps(shape, sort_keys=True)
    starter = hashlib.sha256(shape_str.encode()).hexdigest()[:16]

    # Flavor = complexity of what emerged
    species_count = sum(1 for v in eons["pool"].values() if v > 0)
    era_count = len(eons["eras"])
    blink_count = len(blinks["blinks"])

    flavor = math.log(1 + species_count) * math.log(1 + era_count) * (1 + blink_count * 0.3)

    # Personality: keep the weird ones
    quirks = []
    if shape.get("ptolemaic"):
        quirks.append("ptolemaic — more epicycle than signal. needs galileo moment.")
    if blink_count == 0:
        quirks.append("hyper-stable — nothing blinks. needs perturbation.")
    if blink_count > 3:
        quirks.append(f"chaotic — {blink_count} layers blinking. rich signal.")
    if eons["reactions"] < 10:
        quirks.append("cold universe — not enough energy for chemistry.")
    if eons["reactions"] > 80:
        quirks.append("hot universe — everything reacting. primordial soup.")
    if "iron" in eons["eras"]:
        quirks.append("iron age — stellar nucleosynthesis from mesh latency.")
    if shape.get("gap_ms", 0) < 0:
        quirks.append("faster than expected — the mesh is outrunning itself.")

    # Stability (sourdough chaos measure)
    stability = 1.0 / (1.0 + abs(shape.get("gap_ms", 0)) / 10.0)

    return {
        "starter": starter,
        "flavor": round(flavor, 2),
        "stability": round(stability, 3),
        "quirks": quirks,
        "species": species_count,
        "eras": era_count,
        "personality": "keeper" if stability > 0.5 and stability < 0.8 else
                       "split-candidate" if stability > 0.8 else
                       "wild-starter",
    }

# ── Triangulation ────────────────────────────────────────────────

def triangulate(probes):
    """Pre-triangulate position from latency = distance proxy.

    Speed of light in fiber: ~200,000 km/s = 200 km/ms
    Speed of light in copper: ~175,000 km/s = 175 km/ms
    Speed of light in WiFi: ~300,000 km/s = 300 km/ms (but processing dominates)

    Real latency includes processing, so 1ms ≈ local, 20ms ≈ regional, 45ms ≈ coast
    """
    alive = [p for p in probes if p.get("alive")]
    if len(alive) < 3:
        return {"error": "need >= 3 nodes for triangulation"}

    # Sort by latency = nearest first
    by_latency = sorted(alive, key=lambda p: p["avg_ms"])

    # Layers as concentric rings
    rings = []
    for p in by_latency:
        layer_info = LAYERS.get(p["layer"], {})
        rings.append({
            "node": p["name"],
            "latency_ms": p["avg_ms"],
            "jitter_ms": p["mdev_ms"],
            "ring_km": round(p["avg_ms"] * 100, 1),  # rough: 100km per ms of RTT for WAN
            "layer": p["layer"],
            "medium": p.get("medium", "unknown"),
            "state": layer_info.get("state", "unknown"),
        })

    # The "constellation" — our local satellites
    constellation = {
        "anchor": rings[0]["node"],
        "anchor_latency_ms": rings[0]["latency_ms"],
        "rings": rings,
        "total_satellites": len(rings),
        "lan_satellites": sum(1 for r in rings if r["layer"] in ["bone", "muscle", "air"]),
        "wan_satellites": sum(1 for r in rings if r["layer"] in ["membrane", "horizon"]),
    }

    # Compare to GPS
    gps_equivalent = {
        "gps_sv_distance_km": 20200,
        "gps_sv_signal_dbm": -140,
        "nearest_lan_distance_m": round(rings[0]["latency_ms"] * 0.1 * 1000, 0),  # very rough
        "nearest_lan_signal_dbm": -31,  # typical WiFi
        "improvement_factor": "~10^12 (120 dB)",
        "verdict": "house IS the constellation",
    }

    return {
        "constellation": constellation,
        "gps_comparison": gps_equivalent,
        "triangulation_quality": "excellent" if len(alive) >= 5 else "good" if len(alive) >= 3 else "poor",
    }

# ── Main: Knead the Dough ────────────────────────────────────────

def main():
    quick = "--quick" in sys.argv
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\n🍞 dough.py — kneading reality at {ts}\n")

    # 1. Probe all nodes
    probes = probe_all()
    alive_count = sum(1 for p in probes if p.get("alive"))
    print(f"\n  {alive_count}/{len(probes)} nodes alive\n")

    # 2. Calculate shape
    print("📐 calculating shape of reality...")
    shape = calculate_shape(probes)

    if "layers" in shape:
        for lname, ldata in shape["layers"].items():
            emoji = "🟢" if ldata["epicycle_ratio"] < 0.5 else "🟡" if ldata["epicycle_ratio"] < 1.0 else "🔴"
            print(f"  {emoji} {lname:10s}  avg={ldata['avg_ms']:7.2f}ms  "
                  f"expected={ldata['expected_ms']:5.1f}ms  "
                  f"epicycle={ldata['epicycle_ratio']:.3f}  "
                  f"state={ldata['state']}")
        print(f"\n  is={shape['is_ms']:.1f}ms  was={shape['was_ms']:.1f}ms  "
              f"gap={shape['gap_ms']:.1f}ms  ptolemaic={'YES 🏛️' if shape['ptolemaic'] else 'no'}")
        print(f"  jurisdictions: {', '.join(shape['jurisdictions'])}")

    # 3. Triangulate
    print("\n📡 triangulating from local constellation...")
    tri = triangulate(probes)
    if "constellation" in tri:
        c = tri["constellation"]
        print(f"  anchor: {c['anchor']} ({c['anchor_latency_ms']:.2f}ms)")
        print(f"  satellites: {c['total_satellites']} ({c['lan_satellites']} LAN + {c['wan_satellites']} WAN)")
        print(f"  verdict: {tri['gps_comparison']['verdict']}")

    if quick:
        result = {"ts": ts, "shape": shape, "triangulation": tri, "probes": probes}
    else:
        # 4. Eon bounce
        print("\n⚗️  running 100 eons with real latency as activation energy...")
        eons = eon_bounce(shape, n_eons=100)
        print(f"  {eons['reactions']} reactions, eras: {', '.join(eons['eras']) or 'primordial'}")
        print(f"  pool: {eons['pool']}")

        # 5. Blink sort
        print("\n👁️  blink-sorting layers...")
        blinks = blink_sort(shape)
        if blinks["blinks"]:
            print(f"  BLINKS (signal): {', '.join(b['layer'] for b in blinks['blinks'])}")
        if blinks["ground"]:
            print(f"  GROUND (noise):  {', '.join(g['layer'] for g in blinks['ground'])}")
        print(f"  signal: {blinks['signal_pct']}%  noise: {100 - blinks['signal_pct']}%")

        # 6. Sourdough
        print("\n🫗 fermenting sourdough...")
        dough = sourdough(shape, eons, blinks)
        print(f"  starter: {dough['starter']}")
        print(f"  flavor: {dough['flavor']}  stability: {dough['stability']}")
        print(f"  personality: {dough['personality']}")
        for q in dough['quirks']:
            print(f"    → {q}")

        result = {
            "ts": ts,
            "shape": shape,
            "triangulation": tri,
            "eons": eons,
            "blinks": blinks,
            "sourdough": dough,
            "probes": [p for p in probes if p.get("alive")],
            "digest": hashlib.sha256(json.dumps(shape, sort_keys=True).encode()).hexdigest()[:32],
        }

    # Write output
    out_path = Path(__file__).parent.parent / "hud" / "site" / "public" / "data" / "dough.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n🍞 dough risen → {out_path}")
    print(f"   digest: {result.get('digest', result.get('ts'))}")

    return result

if __name__ == "__main__":
    main()
