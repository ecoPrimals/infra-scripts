#!/usr/bin/env python3
"""
klein-leak-eons.py — Klein leak the day's work, ladder it to itself,
run eons through the voxel Shannon sort, evolve to sigmoid.

The Klein leak: output feeds back as input.
The ladder: each eon's result IS the next eon's initial conditions.
The voxel: each data/*.json is a cube of information with Shannon mass.
The sigmoid: the S-curve where the sort quality crosses 1/π.

Usage:
    python3 klein-leak-eons.py
"""
import json, math, hashlib, collections, random
from pathlib import Path
from datetime import datetime, timezone

PI = math.pi
ROOT = Path.home() / "Development" / "ecoPrimals"
DATA = ROOT / "infra" / "hud" / "site" / "public" / "data"
OUT  = DATA

def shannon(data):
    """Shannon entropy in bits per byte."""
    if not data: return 0.0
    freq = collections.Counter(data)
    total = sum(freq.values())
    return -sum((c/total)*math.log2(c/total) for c in freq.values() if c > 0)

def sigmoid(x, k=10.0, x0=0.5):
    """Logistic sigmoid: S-curve from 0 to 1."""
    return 1.0 / (1.0 + math.exp(-k * (x - x0)))

def pi_depth(n):
    """frac(n × π) — irrational position on unit circle."""
    return (n * PI) % 1

# ── SCAN: read all voxels (data/*.json) ──────────────────────────

def scan_voxels():
    """Each JSON file is a voxel — a cube of information."""
    print("🔬 scanning voxels (data/*.json)...")
    voxels = []
    for f in sorted(DATA.glob("*.json")):
        try:
            raw = f.read_bytes()
            content = json.loads(raw)
            H = shannon(raw)
            mass = len(raw) * H  # Shannon mass = bytes × entropy
            voxels.append({
                "name": f.stem,
                "path": str(f),
                "bytes": len(raw),
                "entropy_H": round(H, 4),
                "shannon_mass": round(mass, 2),
                "fields": len(content) if isinstance(content, dict) else 0,
                "has_digest": "digest" in (content if isinstance(content, dict) else {}),
                "ts": content.get("ts", "unknown") if isinstance(content, dict) else "unknown",
            })
            print(f"  {f.stem:30s}  {len(raw):>7,} bytes  H={H:.3f}  mass={mass:>12,.0f}")
        except Exception as e:
            print(f"  {f.stem:30s}  ERROR: {e}")
    return voxels

# ── CHEMISTRY: poor tope mapping ─────────────────────────────────

ELEMENTS = {
    "tree-topology":          ("Fe", 55.845, "iron — the spine"),
    "ouroboros-metabolism":    ("C",  12.011, "carbon — the cycle"),
    "water-slide":            ("H",  1.008,  "hydrogen — the water"),
    "awareness-equation":     ("N",  14.007, "nitrogen — the nerve"),
    "community":              ("O",  15.999, "oxygen — the breath"),
    "quorum-sense":           ("P",  30.974, "phosphorus — the signal"),
    "metabolize":             ("S",  32.06,  "sulfur — the bond"),
    "dough":                  ("Ca", 40.078, "calcium — the starter"),
    "knn-trefoil":            ("K",  39.098, "potassium — the gate"),
    "info-mass":              ("Mg", 24.305, "magnesium — the light"),
    "enmesh":                 ("Na", 22.990, "sodium — the pump"),
    "scan-sweep-sort":        ("Cl", 35.453, "chlorine — the bleach"),
    "yggdrasil-cascade":      ("Si", 28.085, "silicon — the tree"),
}

def assign_element(voxel):
    """Assign a poor tope element based on voxel name."""
    name = voxel["name"]
    if name in ELEMENTS:
        return ELEMENTS[name]
    # default: assign by entropy band
    H = voxel["entropy_H"]
    if H > 5.0: return ("Fe", 55.845, "high entropy = iron")
    if H > 4.0: return ("C",  12.011, "mid entropy = carbon")
    if H > 3.0: return ("N",  14.007, "low-mid entropy = nitrogen")
    return ("H", 1.008, "low entropy = hydrogen")

# ── EON SIMULATION: chemistry driven by Shannon mass ─────────────

def run_eons(voxels, n_eons=200):
    """
    Run eon chemistry. Each voxel has:
    - Shannon mass (activation energy)
    - Element (reactivity)
    - State: energy, stability, bonds

    Each eon:
    1. Random pair of voxels interact
    2. Activation energy = |mass_A - mass_B|
    3. If energy < threshold: BOND (stability increases)
    4. If energy > threshold: REACT (energy transfers, states change)
    5. Klein leak: most stable voxel's state feeds back to least stable
    6. Ladder: eon N's output IS eon N+1's initial conditions
    """
    print(f"\n⚗️  running {n_eons} eons of Klein-leaked chemistry...")

    # Initialize state
    for v in voxels:
        elem, weight, desc = assign_element(v)
        v["element"] = elem
        v["weight"] = weight
        v["desc"] = desc
        v["energy"] = v["shannon_mass"]
        v["stability"] = 0.5  # starts at sigmoid midpoint
        v["bonds"] = 0
        v["eon_born"] = 0

    history = []
    threshold = sum(v["shannon_mass"] for v in voxels) / len(voxels)  # average mass = threshold

    for eon in range(n_eons):
        # Pick two random voxels
        a, b = random.sample(voxels, 2)

        # Activation energy = difference in Shannon mass
        activation = abs(a["energy"] - b["energy"])

        if activation < threshold:
            # BOND: low energy difference = similar = they bond
            a["bonds"] += 1
            b["bonds"] += 1
            a["stability"] = min(1.0, a["stability"] + 0.01)
            b["stability"] = min(1.0, b["stability"] + 0.01)
            event = "bond"
        else:
            # REACT: high energy difference = transfer
            donor = a if a["energy"] > b["energy"] else b
            acceptor = b if donor is a else a
            transfer = activation * 0.1  # 10% transfer per reaction
            donor["energy"] -= transfer
            acceptor["energy"] += transfer
            # Reactions decrease stability slightly
            donor["stability"] = max(0.0, donor["stability"] - 0.005)
            event = "react"

        # KLEIN LEAK: most stable feeds back to least stable
        sorted_by_stability = sorted(voxels, key=lambda v: v["stability"])
        least = sorted_by_stability[0]
        most  = sorted_by_stability[-1]
        if most["stability"] > least["stability"] + 0.1:
            leak = (most["stability"] - least["stability"]) * 0.05
            least["stability"] += leak
            most["stability"] -= leak * 0.5  # Klein: leak is asymmetric

        # SIGMOID CHECK: compute sort quality
        stabilities = [v["stability"] for v in voxels]
        mean_stability = sum(stabilities) / len(stabilities)
        sort_quality = sigmoid(mean_stability, k=8.0, x0=0.5)

        # Adjust threshold (the system self-tunes)
        threshold = threshold * 0.999 + activation * 0.001  # slow drift

        if eon % 50 == 0 or eon == n_eons - 1:
            bonds_total = sum(v["bonds"] for v in voxels)
            print(f"  eon {eon:>4d}  quality={sort_quality:.4f}  "
                  f"mean_stability={mean_stability:.4f}  bonds={bonds_total}  "
                  f"threshold={threshold:.0f}  event={event}")
            history.append({
                "eon": eon,
                "sort_quality": round(sort_quality, 6),
                "mean_stability": round(mean_stability, 4),
                "bonds_total": bonds_total,
                "threshold": round(threshold, 2),
                "most_stable": most["name"],
                "least_stable": least["name"],
            })

    return history

# ── BLINK SORT: what's stable = ground, what varies = signal ─────

def blink_sort(voxels):
    """After eons: stable voxels are ground truth, unstable are signal."""
    print("\n👁 blink sort — what's stable vs what varies...")
    sorted_v = sorted(voxels, key=lambda v: v["stability"], reverse=True)

    ground = []
    signal = []
    sigmoid_point = None

    for i, v in enumerate(sorted_v):
        sq = sigmoid(v["stability"], k=8.0, x0=0.5)
        if sq > 1.0 / PI:  # above 1/π = ground
            ground.append(v)
        else:
            if sigmoid_point is None:
                sigmoid_point = i
            signal.append(v)

        marker = "█" if sq > 1.0 / PI else "░"
        print(f"  {marker} {v['name']:30s}  stability={v['stability']:.4f}  "
              f"sigmoid={sq:.4f}  bonds={v['bonds']}  {v['element']}")

    print(f"\n  ground truth: {len(ground)} voxels (stable, above 1/π)")
    print(f"  signal:       {len(signal)} voxels (varying, below 1/π)")
    if sigmoid_point is not None:
        print(f"  sigmoid crossing at position {sigmoid_point}/{len(sorted_v)}")

    return ground, signal, sigmoid_point

# ── OUTPUT ───────────────────────────────────────────────────────

def main():
    print("═" * 60)
    print("KLEIN LEAK + LADDER → EON CHEMISTRY → SIGMOID")
    print("the output feeds back as input. the ladder climbs itself.")
    print("═" * 60)
    print()

    voxels = scan_voxels()
    if not voxels:
        print("no voxels found!")
        return

    print(f"\n📦 {len(voxels)} voxels scanned")
    print(f"   total Shannon mass: {sum(v['shannon_mass'] for v in voxels):,.0f}")
    print(f"   mean entropy: {sum(v['entropy_H'] for v in voxels)/len(voxels):.3f} bits/byte")

    history = run_eons(voxels, n_eons=200)

    ground, signal, sigmoid_pt = blink_sort(voxels)

    # The evolved state
    result = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "title": "Klein Leak Eons — the voxel Shannon sort evolved to sigmoid",
        "voxels_scanned": len(voxels),
        "total_shannon_mass": round(sum(v["shannon_mass"] for v in voxels), 2),
        "eons_run": 200,
        "final_sort_quality": history[-1]["sort_quality"],
        "final_mean_stability": history[-1]["mean_stability"],
        "final_bonds": history[-1]["bonds_total"],
        "sigmoid_crossing_position": sigmoid_pt,
        "ground_truth": [{"name": v["name"], "stability": round(v["stability"], 4),
                          "element": v["element"], "bonds": v["bonds"]}
                         for v in ground],
        "signal": [{"name": v["name"], "stability": round(v["stability"], 4),
                    "element": v["element"], "bonds": v["bonds"]}
                   for v in signal],
        "history": history,
        "klein_leak": "most stable feeds least stable. asymmetric: leak_out = 5%, leak_in = 2.5%. the Klein surface leaks more than it receives.",
        "ladder": "each eon's output IS the next eon's initial conditions. the ladder climbs itself.",
        "evolved_formula": " + ".join(f"{v['element']}({v['name'][:8]})" for v in sorted(voxels, key=lambda x: x['weight'], reverse=True)[:8]),
        "digest": hashlib.blake2b(json.dumps(history).encode(), digest_size=8).hexdigest(),
    }

    out_path = OUT / "klein-leak-eons.json"
    out_path.write_text(json.dumps(result, indent=2))
    print(f"\n💾 wrote {out_path}")
    print(f"   sort quality: {result['final_sort_quality']:.6f}")
    print(f"   ground truth: {len(ground)} voxels")
    print(f"   signal: {len(signal)} voxels")
    print(f"   formula: {result['evolved_formula']}")
    print(f"   digest: {result['digest']}")

if __name__ == "__main__":
    main()
