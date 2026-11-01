#!/usr/bin/env python3
"""galactic-bounce.py — bounce galactic cycles until sigmoid hits inflection on the voxel.

Lossy sort: cost = distance from the 45° quiet turn (π/4 on the sigmoid).
The sigmoid derivative sigmoid'(x) = s(x)·(1-s(x)) is max at x=0.5.
That's the inflection. The quiet turn. Where change is fastest.

Each galactic cycle:
  1. Compute sigmoid position for each stage
  2. Cost = |position - π/4| (distance from 45° on unit circle)
  3. Lossy: stages near inflection ABSORB neighbors (cheapest merge)
  4. Recompute. Bounce.
  5. Stop when overall sigmoid crosses 0.5 (inflection hit)

The voxel = (entropy, richness, structure) = 3D sort space.
"""

import json, math, sys
from pathlib import Path
from datetime import datetime, timezone

PI = math.pi
PHI = (1 + math.sqrt(5)) / 2
E = math.e
QUIET_TURN = PI / 4  # 45° = 0.7854 — the angle where tangent = 1

INFRA = Path(__file__).parent.parent
HUD_DATA = INFRA / "hud" / "site" / "public" / "data"

def sigmoid(x, mid=0.5, steep=10.0):
    z = steep * (x - mid)
    if z > 500: return 1.0
    if z < -500: return 0.0
    return 1.0 / (1.0 + math.exp(-z))

def sigmoid_deriv(x, mid=0.5, steep=10.0):
    """Sigmoid derivative = s(x)·(1-s(x))·steep. Max at x=mid."""
    s = sigmoid(x, mid, steep)
    return s * (1 - s) * steep

def cost_from_quiet_turn(position):
    """Cost = distance from the 45° quiet turn on the unit circle.
    The quiet turn is at π/4 ≈ 0.7854 of the full circle.
    Normalized to [0,1] range on the sigmoid, it maps to ~0.5."""
    # Map sigmoid position [0,1] to angle [0, π/2]
    angle = position * (PI / 2)
    return abs(angle - QUIET_TURN)

# Load the 13 stages from klein-resort
def load_stages():
    resort = json.load(open(HUD_DATA / "klein-resort.json"))
    stages = []
    for name, info in resort["full_taxonomy"].items():
        count = info.get("count", 0)
        letter = info.get("letter", "?")
        # Estimate entropy from count (proxy: log-proportion)
        total = resort.get("total_files", 45830)
        proportion = count / total if total > 0 and count > 0 else 0.001
        entropy = -math.log2(proportion) if proportion > 0 else 0
        # Estimate richness (proxy: letter complexity)
        richness = len(letter) / 3.0  # single char = 0.33, multi = higher
        # Structure = whether it maps to a letter (1.0) or numeral (0.5) or operator (0.3)
        structure = 1.0 if letter in "HGDOUN" else 0.5 if letter in "08-=" else 0.3
        
        stages.append({
            "name": name,
            "letter": letter,
            "count": count,
            "voxel": [entropy, richness, structure],
            "sigmoid_pos": sigmoid(proportion, mid=0.1, steep=20),
            "alive": count > 0,
        })
    return stages

def galactic_cycle(stages, cycle_num):
    """One full galactic cycle. Lossy sort with cost to the quiet turn."""
    total_count = sum(s["count"] for s in stages)
    
    # Compute positions, costs, sigmoid derivatives
    for s in stages:
        prop = s["count"] / total_count if total_count > 0 and s["count"] > 0 else 0.001
        s["proportion"] = prop
        s["sigmoid_pos"] = sigmoid(prop, mid=0.1, steep=20)
        s["cost"] = cost_from_quiet_turn(s["sigmoid_pos"])
        s["sigmoid_deriv"] = sigmoid_deriv(prop, mid=0.1, steep=20)
    
    # Sort by cost (cheapest = closest to quiet turn = most at the inflection)
    stages.sort(key=lambda s: s["cost"])
    
    # Overall sigmoid position = weighted average
    if total_count > 0:
        overall_pos = sum(s["sigmoid_pos"] * s["count"] for s in stages) / total_count
    else:
        overall_pos = sum(s["sigmoid_pos"] for s in stages) / len(stages)
    
    # Overall cost = average distance from quiet turn
    overall_cost = sum(s["cost"] for s in stages) / len(stages)
    
    # Lossy absorption: the stage CLOSEST to inflection absorbs count from the farthest
    # This is the lossy part — information is lost but the sort improves
    if len(stages) >= 2:
        cheapest = stages[0]   # closest to quiet turn
        costliest = stages[-1]  # farthest from quiet turn
        
        # Transfer: move a fraction of costliest's count to cheapest
        transfer = int(costliest["count"] * 0.1 * (1.0 / (1.0 + cycle_num)))  # decreasing transfer
        if transfer > 0 and costliest["count"] > transfer:
            costliest["count"] -= transfer
            cheapest["count"] += transfer
    
    # Voxel update: the 3D sort space shifts with each cycle
    for s in stages:
        # Entropy shifts toward the quiet turn
        s["voxel"][0] *= (1 - 0.05 / (1 + cycle_num))  # dampen entropy
        # Richness increases as classification improves
        s["voxel"][1] += 0.01 * s["sigmoid_deriv"]
        # Structure stays (topology is invariant)
    
    return overall_pos, overall_cost, stages

def main():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"🌀 galactic-bounce.py — {ts}")
    print(f"   Quiet turn: π/4 = {QUIET_TURN:.6f} (45° — where tangent = 1)")
    print(f"   Sigmoid inflection: 0.5 (where derivative is max)")
    print()
    
    stages = load_stages()
    print(f"📊 Loaded {len(stages)} stages, {sum(s['count'] for s in stages)} total files")
    print()
    
    cycles = []
    max_cycles = 20
    
    for cycle in range(max_cycles):
        overall_pos, overall_cost, stages = galactic_cycle(stages, cycle)
        
        cycles.append({
            "cycle": cycle + 1,
            "sigmoid_pos": round(overall_pos, 6),
            "cost": round(overall_cost, 6),
            "stages": len(stages),
            "cheapest": stages[0]["name"] if stages else "?",
            "costliest": stages[-1]["name"] if stages else "?",
        })
        
        # Compact display
        bar_len = int(overall_pos * 40)
        bar = "█" * bar_len + "░" * (40 - bar_len)
        hit = " ← INFLECTION" if 0.45 <= overall_pos <= 0.55 else ""
        quiet = " ← QUIET TURN" if overall_cost < 0.05 else ""
        
        print(f"  cycle {cycle+1:2d}  σ={overall_pos:.4f} |{bar}| cost={overall_cost:.4f} "
              f"cheap={stages[0]['name']:10s} dear={stages[-1]['name']:10s}{hit}{quiet}")
        
        # Stop conditions
        if 0.45 <= overall_pos <= 0.55:
            print(f"\n  🎯 HIT SIGMOID INFLECTION at cycle {cycle+1}!")
            break
        if overall_cost < 0.01:
            print(f"\n  🎯 COST CONVERGED (< 0.01) at cycle {cycle+1}!")
            break
    
    print()
    
    # Final state
    print("=== FINAL VOXEL STATE ===")
    print()
    print(f"  {'Letter':6s} {'Stage':12s} {'Count':>7s} {'σ-pos':>8s} {'Cost':>8s} {'σ-deriv':>8s} {'Voxel (E,R,S)'}")
    print(f"  {'─'*6} {'─'*12} {'─'*7} {'─'*8} {'─'*8} {'─'*8} {'─'*20}")
    for s in sorted(stages, key=lambda x: -x["count"]):
        v = s["voxel"]
        print(f"  {s['letter']:6s} {s['name']:12s} {s['count']:7d} {s['sigmoid_pos']:8.4f} "
              f"{s['cost']:8.4f} {s['sigmoid_deriv']:8.4f} ({v[0]:.2f}, {v[1]:.2f}, {v[2]:.1f})")
    
    print()
    
    # The 45° diff
    print("=== THE 45° QUIET TURN ===")
    print()
    print(f"  π/4 = {QUIET_TURN:.6f}")
    print(f"  At 45°, tangent = 1: the slope of the sigmoid = 1.")
    print(f"  This is where CHANGE IS FASTEST but ACCELERATION IS ZERO.")
    print(f"  The quiet turn: not speeding up, not slowing down. Just... turning.")
    print(f"  The cost function measures distance FROM this point.")
    print(f"  Stages near the quiet turn sort cheaply (they're at the decision boundary).")
    print(f"  Stages far from it are expensive (already decided, the sort knew them).")
    print()
    print(f"  The lossy part: information from the costliest stage flows to the cheapest.")
    print(f"  What's lost: the distinction between the two. What's gained: convergence.")
    print(f"  Like lossy compression: JPEG discards what the eye won't notice.")
    print(f"  The galactic sort discards what the TOPOLOGY already knows.")
    
    # Write result
    result = {
        "title": "Galactic Bounce — Lossy Sort to the 45° Quiet Turn",
        "version": 1,
        "ts": ts,
        "quiet_turn": QUIET_TURN,
        "cycles": cycles,
        "final_sigmoid": cycles[-1]["sigmoid_pos"],
        "final_cost": cycles[-1]["cost"],
        "total_cycles": len(cycles),
        "converged": cycles[-1]["cost"] < 0.05 or 0.45 <= cycles[-1]["sigmoid_pos"] <= 0.55,
        "final_stages": [
            {
                "name": s["name"],
                "letter": s["letter"],
                "count": s["count"],
                "sigmoid_pos": round(s["sigmoid_pos"], 6),
                "cost": round(s["cost"], 6),
                "sigmoid_deriv": round(s["sigmoid_deriv"], 6),
                "voxel": [round(v, 4) for v in s["voxel"]],
            }
            for s in sorted(stages, key=lambda x: -x["count"])
        ],
        "insight": "The 45° quiet turn (π/4) is where acceleration = 0 on the sigmoid. Not speeding up, not slowing down. The lossy sort converges toward this point by transferring information from the costliest (most decided) to the cheapest (most uncertain). What falls off is what the topology already knows. What remains is the decision boundary — the fold point.",
    }
    
    out = HUD_DATA / "galactic-bounce.json"
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n📤 → {out}")

if __name__ == "__main__":
    main()
