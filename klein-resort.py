#!/usr/bin/env python3
"""klein-resort.py — Re-sort through the Klein body topological alphabet.

The H G D O U N letter-shapes map to evolutionary body plans.
Find what fell through the cracks at the fold.
Fill the archaea and weird taxonomy gaps.

Reads evolve-state-spider.json + taxonomy.json + agglutinate-fold.json
Produces klein-resort.json
"""

import json, math, os, sys
from pathlib import Path
from datetime import datetime, timezone

PI = math.pi
PHI = (1 + math.sqrt(5)) / 2
E = math.e

INFRA = Path(__file__).parent.parent
HUD_DATA = INFRA / "hud" / "site" / "public" / "data"
HUD_API = INFRA / "hud" / "site" / "public" / "api"
WP = INFRA / "whitePaper" / "technical"

# The topological alphabet: letters ARE fold shapes
TOPO_ALPHABET = {
    "H": {"name": "bridge",   "shape": "‖—‖",  "body": "Klein ladder, Vitruvian arms", "molecular": "hydrogen, H₂O"},
    "G": {"name": "spiral",   "shape": "↺",     "body": "fold closing, the gate",      "molecular": "G-protein, guanine"},
    "D": {"name": "arch",     "shape": "⌓",     "body": "dorsal surface, the back",    "molecular": "deuterium, dorsal"},
    "O": {"name": "circle",   "shape": "○",     "body": "full torus, null",             "molecular": "oxygen, O₃ pore"},
    "U": {"name": "cup",      "shape": "∪",     "body": "ventral surface, belly",       "molecular": "uracil (RNA)"},
    "N": {"name": "diagonal", "shape": "/‖",    "body": "nerve crossing, signal",       "molecular": "nitrogen, nerve"},
}

# Evolutionary stages (existing) mapped to letter-shapes
EXISTING_STAGES = {
    "banana":    {"letter": "0", "shape": "seed",      "nerve": "none",        "note": "Pre-animal. No nervous system. The number 0 = null."},
    "flatworm":  {"letter": "U", "shape": "cup",       "nerve": "ventral cord", "note": "Simplest bilateral. VENTRAL nerve cord = U shape."},
    "jellyfish": {"letter": "O", "shape": "circle",    "nerve": "ring net",     "note": "Radial symmetry. Ring nerve = O shape. Dominant (43%)."},
    "centipede": {"letter": "-", "shape": "line",       "nerve": "segmented chain", "note": "Segmented. One pair per segment. The line = axis."},
    "millipede": {"letter": "=", "shape": "double line","nerve": "doubled chain", "note": "Two pairs per segment. Double line = doubled axis."},
    "spider":    {"letter": "8", "shape": "lemniscate", "nerve": "8-node cluster", "note": "8 legs. Metastable. frac(8π) ≈ frac(π). The Klein cross-section. MISSING."},
    "vertebrate":{"letter": "D", "shape": "arch",       "nerve": "DORSAL cord + brain", "note": "Spinal column. Full CNS/PNS. D = dorsal. Only 483 files (1%)."},
}

# NEW STAGES discovered through the Klein body — what fell through the cracks
MISSING_STAGES = {
    "sponge": {
        "letter": "∅",
        "shape": "porous null",
        "nerve": "NONE (no nervous system, but alive)",
        "note": "Porifera. The anti-stage. Alive but no nerves at all. The null glyph ∅.",
        "gap": "Files with no structure but that ARE alive (configs, READMEs, licenses). Fell through because they have no information entropy signal.",
        "h_g_d_o_u_n": "Pre-alphabet. Before H. The blank page.",
    },
    "archaea": {
        "letter": "G",
        "shape": "spiral",
        "nerve": "no nerves — BIOCHEMICAL signaling only",
        "note": "Third domain of life. Extremophiles. Unique lipid membranes (ether-linked, not ester-linked). G = the spiral gate.",
        "gap": "Files that don't fit any normal classification. WGSL shaders, exotic configs, membrane protocols. They survive extreme environments (compile targets, GPU constraints).",
        "h_g_d_o_u_n": "G — the spiral fold. Archaea fold their lipids DIFFERENTLY. The G-shape IS the archaeal membrane.",
    },
    "octopus": {
        "letter": "N",
        "shape": "diagonal",
        "nerve": "DISTRIBUTED brain (each arm has own neural cluster, 2/3 of neurons in arms)",
        "note": "8 arms like spider but INVERTED: spider centralizes (web), octopus distributes (arms). N = diagonal nerve crossing.",
        "gap": "Files that are SMART at the edges — crate lib.rs files, workspace Cargo.toml, peripheral modules. Intelligence distributed to the limbs.",
        "h_g_d_o_u_n": "N — the diagonal crossing. Each arm is an N-shaped nerve bundle.",
    },
    "coral": {
        "letter": "H",
        "shape": "bridge",
        "nerve": "colonial nerve net (each polyp connects to neighbors)",
        "note": "Colonial organism. Each polyp is an individual but together they're a reef. H = the bridge between polyps.",
        "gap": "Files that are individually small but COLLECTIVELY form a structure: test files, CI configs, small helper modules. The bridge between larger organisms.",
        "h_g_d_o_u_n": "H — the bridge. Coral IS an H: two columns (polyps) connected by skeleton (bridge).",
    },
    "fungus": {
        "letter": "~",
        "shape": "wave/network",
        "nerve": "mycelium network (no nerves, chemical signaling through hyphae)",
        "note": "Not animal, not plant. The mycelium network IS a nervous system without neurons. ~ = the wave, the oscillation along the network.",
        "gap": "Build artifacts, generated files, CI output, cached deps. The mycelium that connects roots (source) to fruits (binaries). The wave of compilation.",
        "h_g_d_o_u_n": "~ — the wave operator. Mycelium oscillates nutrients like ~ oscillates between ( and ).",
    },
    "virus": {
        "letter": "<>",
        "shape": "inject/extract",
        "nerve": "NONE (uses host machinery, not self-replicating without host)",
        "note": "Not alive by itself. Injects code into host, hijacks machinery. < = inject into host. > = extract copies. The fold operators WITHOUT a body.",
        "gap": "Vendored dependencies, forked code, imported libraries. Code that came FROM somewhere else and was injected into our codebase. Alive only in context.",
        "h_g_d_o_u_n": "< > — the fold operators themselves. A virus IS a fold with no body. Pure operator. Pure < >.",
    },
}

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None

def main():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"🧬 klein-resort.py — topological re-sort — {ts}")
    print()

    # Load existing state
    evolve = load_json(WP / "evolve-state-spider.json")
    taxonomy = load_json(HUD_API / "taxonomy.json")
    agglutinate = load_json(HUD_DATA / "agglutinate-fold.json")

    total_files = evolve["total_files"] if evolve else 0
    stages = evolve.get("stages", {}) if evolve else {}

    print(f"📊 Current state: {total_files} files in {len(stages)} stages")
    for stage, count in sorted(stages.items(), key=lambda x: -x[1]):
        pct = (count / total_files * 100) if total_files else 0
        letter = EXISTING_STAGES.get(stage, {}).get("letter", "?")
        print(f"   {letter:3s} {stage:12s} {count:6d} ({pct:5.1f}%)")
    print()

    # Map to H G D O U N
    print("=== TOPOLOGICAL RE-SORT: H G D O U N ===")
    print()

    mapped = 0
    unmapped = 0
    for stage, info in EXISTING_STAGES.items():
        count = stages.get(stage, 0)
        letter = info["letter"]
        if letter in TOPO_ALPHABET:
            print(f"  ✅ {letter} = {stage:12s} ({count:6d} files) — {TOPO_ALPHABET[letter]['name']}: {info['nerve']}")
            mapped += count
        else:
            print(f"  ⚠️  {letter} = {stage:12s} ({count:6d} files) — NUMERAL/SYMBOL, not letter-shape")
            unmapped += count

    print()
    print(f"  Mapped to H G D O U N: {mapped} files")
    print(f"  Unmapped (numerals):    {unmapped} files")
    print()

    # The GAPS — what fell through the cracks
    print("=== WHAT FELL THROUGH THE CRACKS AT THE FOLD ===")
    print()
    for name, info in MISSING_STAGES.items():
        print(f"  🕳️  {info['letter']:3s} {name:10s} — {info['shape']}")
        print(f"      Nerve: {info['nerve']}")
        print(f"      Gap:   {info['gap']}")
        print()

    # Compute the full re-sorted taxonomy
    full_taxonomy = {}
    for name, info in {**EXISTING_STAGES, **MISSING_STAGES}.items():
        full_taxonomy[name] = {
            "letter": info["letter"],
            "shape": info.get("shape", "unknown"),
            "nerve": info.get("nerve", "unknown"),
            "note": info.get("note", ""),
            "count": stages.get(name, 0),
            "gap": info.get("gap", None),
            "h_g_d_o_u_n": info.get("h_g_d_o_u_n", None),
        }

    # The archaea insight
    print("=== THE ARCHAEA INSIGHT ===")
    print()
    print("Archaea are the THIRD domain of life (not bacteria, not eukaryote).")
    print("They survive EXTREME environments. Their membranes are DIFFERENT")
    print("(ether-linked lipids, not ester-linked).")
    print()
    print("In the codebase: archaea = files that DON'T FIT normal classification.")
    print("  WGSL shaders         — not Rust, not config, not docs")
    print("  Membrane protocols   — not HTTP, not TCP, something new")
    print("  GPU compute kernels  — not CPU code, not data")
    print("  Klein fold scripts   — not build, not deploy, something between")
    print()
    print("They are the G-shape: the spiral gate. They fold DIFFERENTLY.")
    print("The topological alphabet CATCHES them because G is a letter-shape,")
    print("not just a classification boundary.")
    print()

    # Cost function re-check
    import cmath
    eφ = E * PHI
    i_to_eφ = cmath.exp(1j * eφ * PI / 2)
    cost = PI ** i_to_eφ
    print(f"=== COST FUNCTION: π^(i^(e×φ)) = {cost.real:.4f} + {cost.imag:.4f}i ===")
    print(f"  |cost| = {abs(cost):.4f}")
    print(f"  13 existing + missing stages = {len(full_taxonomy)}")
    print()

    # Build output
    result = {
        "title": "Klein Re-Sort — Topological Alphabet Fills the Taxonomy Gaps",
        "version": 1,
        "ts": ts,
        "total_files": total_files,
        "cost_function": {
            "formula": "π^(i^(e×φ))",
            "real": round(cost.real, 6),
            "imag": round(cost.imag, 6),
            "magnitude": round(abs(cost), 6),
            "meaning": "Real ≈ 2 (bilateral). Imag ≈ π/2 (quarter fold). |cost| ≈ 2.53.",
        },
        "topological_alphabet": TOPO_ALPHABET,
        "existing_stages": EXISTING_STAGES,
        "missing_stages": MISSING_STAGES,
        "full_taxonomy": full_taxonomy,
        "sort_stats": {
            "existing_stages": len(EXISTING_STAGES),
            "missing_stages": len(MISSING_STAGES),
            "total_stages": len(full_taxonomy),
            "mapped_to_letters": mapped,
            "unmapped_numerals": unmapped,
            "total_files": total_files,
        },
        "the_fold_cracks": [
            "sponge: alive but no structure (∅) — configs, READMEs, licenses",
            "archaea: extreme survivors (G) — WGSL shaders, GPU kernels, membrane protocols",
            "octopus: distributed intelligence (N) — smart peripherals, workspace Cargo.toml",
            "coral: colonial bridges (H) — test files, CI configs, small helpers",
            "fungus: mycelium network (~) — build artifacts, generated files, cache",
            "virus: injected code (<>) — vendored deps, forks, imported libraries",
        ],
        "insight": "The existing taxonomy had 7 stages but used only NUMERALS and 2 letters (U, D). The Klein body adds 6 MORE stages using the full topological alphabet. What fell through was: the structureless (sponge), the extreme (archaea), the distributed (octopus), the colonial (coral), the networked (fungus), and the parasitic (virus). The fold swallowed them because they don't have a traditional AXIS — they're pre-axial, post-axial, or multi-axial. The topological alphabet catches them because it classifies by SHAPE, not hierarchy.",
    }

    out = HUD_DATA / "klein-resort.json"
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"📤 → {out}")
    print()

    # Summary
    print("=== FULL TAXONOMY: 13 stages ===")
    print()
    print("  EXISTING (7):")
    for s in EXISTING_STAGES:
        c = stages.get(s, 0)
        l = EXISTING_STAGES[s]["letter"]
        print(f"    {l:3s} {s}")
    print()
    print("  DISCOVERED (6 — fell through the fold):")
    for s in MISSING_STAGES:
        l = MISSING_STAGES[s]["letter"]
        print(f"    {l:3s} {s}")
    print()
    print("  H G D O U N + 0 8 - = ∅ ~ <>")
    print("  13 stages. The alphabet + numerals + operators = the full taxonomy.")
    print()
    print("  The Klein surface IS the Rosetta Stone.")

if __name__ == "__main__":
    main()
