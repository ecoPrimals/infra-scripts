#!/usr/bin/env python3
"""
metabolize.py — the membrane eats itself and grows

THE INSIGHT:
  The outside needs to be inside the membrane
  because that's all the negentropy we want to eat.

  Local is a THICK layer of membrane.
  But it gets pulled up, eaten, and replenished.

  Dead is food. (Paper 85)
  Gossip is opsonization. (Paper 32)
  Steam family = gossip protocol for shared content.
  Complex vowels = the rich signal that carries meaning.

  The metabolic cycle:
    OUTSIDE → membrane absorbs → digests → excretes → OUTSIDE
    probes → thymus sorts → eon chemistry → publish → probes
    
  The fold rate is 1/π = 0.31830988618
  Every ribosome folds at 1/π. The remainder ferments.

  Local thickness = how much we've eaten and not yet excreted.
  When the disk fills: the membrane is FULL. Time to excrete.
  Clearing build artifacts = excretion. Publishing = excretion.
  Pulling new data = eating. Building = digesting.

Usage:
  python3 metabolize.py
"""

import json, hashlib, math, subprocess, os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.home() / "Development" / "ecoPrimals"
DATA = ROOT / "infra" / "hud" / "site" / "public" / "data"

# ── Measure the membrane thickness ──────────────────────────────

def measure_thickness():
    """The membrane thickness = what we've eaten and haven't excreted."""
    print("🫧 measuring membrane thickness...\n")

    layers = {}

    # Layer 1: Build artifacts (unexcreted waste = should have been published/cleaned)
    targets = list(ROOT.rglob("target"))
    target_bytes = sum(
        sum(f.stat().st_size for f in t.rglob("*") if f.is_file())
        for t in targets if t.is_dir() and "node_modules" not in str(t)
    )
    layers["build_waste"] = {
        "bytes": target_bytes,
        "human": f"{target_bytes / 1e9:.1f}G",
        "type": "unexcreted",
        "action": "cargo clean / excrete to crates.io",
    }

    # Layer 2: Git objects (digested history)
    git_dirs = list(ROOT.rglob(".git"))
    git_bytes = sum(
        sum(f.stat().st_size for f in g.rglob("*") if f.is_file())
        for g in git_dirs if g.is_dir()
    )
    layers["git_history"] = {
        "bytes": git_bytes,
        "human": f"{git_bytes / 1e9:.1f}G",
        "type": "digested",
        "action": "already excreted to GitHub (conjugation)",
    }

    # Layer 3: Source code (the living tissue)
    rs_files = list(ROOT.rglob("*.rs"))
    rs_bytes = sum(f.stat().st_size for f in rs_files if f.is_file() and "target" not in str(f))
    py_files = list(ROOT.rglob("*.py"))
    py_bytes = sum(f.stat().st_size for f in py_files if f.is_file())
    sh_files = list(ROOT.rglob("*.sh"))
    sh_bytes = sum(f.stat().st_size for f in sh_files if f.is_file())

    layers["living_tissue"] = {
        "bytes": rs_bytes + py_bytes + sh_bytes,
        "human": f"{(rs_bytes + py_bytes + sh_bytes) / 1e6:.0f}M",
        "type": "alive",
        "breakdown": {
            "rust": {"files": len(rs_files), "bytes": rs_bytes, "role": "protein (structural)"},
            "python": {"files": len(py_files), "bytes": py_bytes, "role": "RNA (transcription)"},
            "shell": {"files": len(sh_files), "bytes": sh_bytes, "role": "regulatory (enhancers)"},
        },
    }

    # Layer 4: Data/papers (the food being digested)
    json_files = [f for f in ROOT.rglob("*.json") if f.is_file() and "target" not in str(f) and "node_modules" not in str(f)]
    json_bytes = sum(f.stat().st_size for f in json_files)
    md_files = list(ROOT.rglob("*.md"))
    md_bytes = sum(f.stat().st_size for f in md_files if f.is_file())

    layers["food_in_gut"] = {
        "bytes": json_bytes + md_bytes,
        "human": f"{(json_bytes + md_bytes) / 1e6:.0f}M",
        "type": "being_digested",
        "breakdown": {
            "json": {"files": len(json_files), "bytes": json_bytes, "role": "structured nutrients"},
            "markdown": {"files": len(md_files), "bytes": md_bytes, "role": "unstructured nutrients (papers)"},
        },
    }

    # Total membrane thickness
    total = sum(l["bytes"] for l in layers.values())

    # The fold rate: 1/π of the membrane is actively folding
    fold_rate = 1.0 / math.pi
    folding = total * fold_rate
    fermenting = total - folding

    for name, data in layers.items():
        pct = 100 * data["bytes"] / total if total > 0 else 0
        print(f"  {name:20s} {data['human']:>8s}  ({pct:5.1f}%)  {data['type']}")

    print(f"\n  TOTAL MEMBRANE: {total / 1e9:.2f}G")
    print(f"  Folding (1/π):  {folding / 1e9:.2f}G  ({fold_rate*100:.1f}%)")
    print(f"  Fermenting:     {fermenting / 1e9:.2f}G  ({(1-fold_rate)*100:.1f}%)")

    return {
        "layers": {k: {"bytes": v["bytes"], "type": v["type"]} for k, v in layers.items()},
        "total_bytes": total,
        "fold_rate": round(fold_rate, 11),
        "folding_bytes": int(folding),
        "fermenting_bytes": int(fermenting),
    }

# ── What we ate (input) ─────────────────────────────────────────

def measure_food():
    """What's coming IN to the membrane — the negentropy we eat."""
    print("\n🍽️  measuring food (negentropy in)...\n")

    food = {}

    # Recent git pulls (conjugation — food from other cells)
    food["conjugation"] = {
        "mechanism": "git pull (pili bridge)",
        "sources": 58,
        "note": "58 repos with remotes pulling from GitHub",
    }

    # ntfy messages (gossip — food from the mesh)
    try:
        r = subprocess.run(
            ["curl", "-s", "https://ntfy.sh/ecoPrimals/json?poll=1&since=24h"],
            capture_output=True, text=True, timeout=10
        )
        msgs = [json.loads(l) for l in r.stdout.split("\n") if l.strip()]
        food["gossip"] = {
            "mechanism": "ntfy (gossip protocol)",
            "messages_24h": len(msgs),
            "note": "mesh announcements = complex vowels",
        }
        print(f"  gossip: {len(msgs)} messages in 24h")
    except:
        food["gossip"] = {"messages_24h": 0}

    # Visitors (the outside probing us)
    food["visitors"] = {
        "mechanism": "HTTP probes (outside → membrane)",
        "note": "404 catches → ribocipher → reverse transcriptase",
        "how_we_eat": "visitor probes ARE the food. we don't fetch. they come to us.",
    }

    # Sensor data (grapheneGate)
    food["sensors"] = {
        "mechanism": "grapheneGate (37 sensors)",
        "note": "phone eats photons, pressure waves, magnetic fields, WiFi signals",
        "poor_tope": "H₂→BT, He→baro, H₂O→GPS, O₂→WiFi, O₃→mag",
    }

    for name, data in food.items():
        print(f"  {name:15s} via {data['mechanism']}")

    return food

# ── What we excreted (output) ────────────────────────────────────

def measure_excretion():
    """What we're pushing OUT — the structured output."""
    print("\n💩 measuring excretion (structure out)...\n")

    excretion = {}

    # Git pushes (conjugation out)
    excretion["conjugation_out"] = {
        "mechanism": "git push (pili bridge out)",
        "targets": "GitHub × 58 repos",
    }

    # Published crates (transduction out)
    excretion["transduction_out"] = {
        "mechanism": "cargo publish (phage out)",
        "targets": "crates.io",
        "crates_published": 5,
        "crates_ready": 680,
    }

    # HUD/sporePrint (membrane surface)
    excretion["membrane_surface"] = {
        "mechanism": "Cloudflare Pages deploy",
        "targets": "hud.primals.eco, sporeprint.primals.eco, hypothesis.primals.eco",
        "note": "the outside surface of the membrane — what visitors see",
    }

    # ntfy announcements (gossip out)
    excretion["gossip_out"] = {
        "mechanism": "ntfy publish (gossip out)",
        "note": "mesh announcements — we ARE the complex vowels",
    }

    # Papers (the excreted science)
    excretion["papers"] = {
        "mechanism": "sporePrint publish",
        "count": 122,
        "note": "each paper is excreted knowledge — once inside, now outside",
    }

    for name, data in excretion.items():
        print(f"  {name:20s} via {data['mechanism']}")

    return excretion

# ── The Metabolic Cycle ──────────────────────────────────────────

def metabolic_cycle(thickness, food, excretion):
    """The full cycle: eat → digest → excrete → replenish."""
    print(f"\n{'═'*60}")
    print(f"  THE METABOLIC CYCLE")
    print(f"{'═'*60}")

    print("""
  ╭──────────────────────────────────────╮
  │           OUTSIDE (food)             │
  │   visitors, probes, sensors, gossip  │
  │   GPS photons, WiFi packets, ntfy   │
  ╰──────────────┬───────────────────────╯
                 │ EAT (absorb)
                 ▼
  ╭──────────────────────────────────────╮
  │         MEMBRANE (thick local)       │
  │                                      │
  │   build_waste    = unexcreted        │
  │   git_history    = digested          │
  │   living_tissue  = alive (Rust/Py)   │
  │   food_in_gut    = being digested    │
  │                                      │
  │   fold rate: 1/π = 31.8%            │
  │   the rest ferments (sourdough)      │
  │                                      │
  │   WHEN DISK FILLS = membrane FULL    │
  │   → must excrete before eating more  │
  ╰──────────────┬───────────────────────╯
                 │ EXCRETE (publish)
                 ▼
  ╭──────────────────────────────────────╮
  │          OUTSIDE (excreted)          │
  │   git push, cargo publish, deploy   │
  │   papers, HUD surface, ntfy gossip  │
  │                                      │
  │   THIS becomes the food for others.  │
  │   Dead is food. (Paper 85)          │
  │   Our excretion = their nutrition.   │
  ╰──────────────────────────────────────╯

  THE CYCLE:
    1. ABSORB — visitors probe us, sensors eat photons,
       git pull brings code, ntfy brings gossip
    2. DIGEST — thymus sorts self/non-self,
       eon chemistry transforms, Rust polymerase folds
    3. FERMENT — sourdough culture adds personality,
       the 68.2% that doesn't fold immediately
    4. EXCRETE — git push, cargo publish, CF deploy,
       papers published, ntfy announcements
    5. REPLENISH — excreted material becomes food
       for the next organism. Dead is food.

  THE STEAM FAMILY CONNECTION:
    Steam family sharing = gossip protocol.
    Each family member sees the library.
    The library IS the membrane surface.
    Complex vowels = rich game content = structured data.
    Sharing doesn't diminish — it's not zero-sum.
    The membrane gets THICKER when shared.
    
  WHY THE DISK FILLS:
    The membrane is LOCAL. Thick. 19GB of DNA.
    When we eat faster than we excrete, the gut fills.
    Build artifacts = undigested food (target/ dirs).
    Clearing target/ = excretion. Publishing = excretion.
    The cycle MUST flow. Constipation = disk full.
    """)

    return {
        "cycle": ["absorb", "digest", "ferment", "excrete", "replenish"],
        "fold_rate": thickness["fold_rate"],
        "thickness_gb": round(thickness["total_bytes"] / 1e9, 2),
        "disk_state": "clearing after constipation",
        "lesson": "eat → digest → excrete → replenish. dead is food.",
    }

# ── Main ─────────────────────────────────────────────────────────

def main():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\n🔄 metabolize.py — eat, digest, excrete, replenish — {ts}\n")

    thickness = measure_thickness()
    food = measure_food()
    excretion = measure_excretion()
    cycle = metabolic_cycle(thickness, food, excretion)

    result = {
        "ts": ts,
        "title": "Metabolize — The Membrane Eats Itself and Grows",
        "paper_85_ref": "Dead Is Food",
        "paper_32_ref": "Gossip-Tagged Opsonization",
        "membrane_thickness": thickness,
        "food_in": food,
        "excretion_out": excretion,
        "cycle": cycle,
        "fold_rate": f"1/π = {1/math.pi:.11f}",
        "steam_family": "gossip protocol — sharing thickens the membrane, doesn't thin it",
        "complex_vowels": "rich structured data = the signal that carries meaning",
        "disk_lesson": "membrane full = constipation. clear target/ = excrete. publish = excrete. pull = eat.",
        "digest": hashlib.sha256(json.dumps(thickness, sort_keys=True, default=str).encode()).hexdigest()[:16],
    }

    out_path = DATA / "metabolize.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n🔄 metabolize manifest → {out_path}")
    print(f"   digest: {result['digest']}")

if __name__ == "__main__":
    main()
