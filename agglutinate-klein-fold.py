#!/usr/bin/env python3
"""
agglutinate-klein-fold.py — census stale/dead/overstable, clump with chipmunk, Klein fold.

1. SCAN   — census all feeds, subdomains, repos, pointers for staleness
2. AGGLUT — clump related dead/stale things together (antibody agglutination)
3. KLEIN  — fold most-stable→least-stable (asymmetric leak), ladder, pi-compress
4. EMIT   — output the sorted result as next-gen feed

Agglutination: in immunology, antibodies cross-link antigens into visible clumps.
Here: chipmunk cross-links stale/dead/overstable items by their shared properties.
The clumps ARE the diagnosis. Big clump = systemic issue. Small clump = local wound.
"""

import json, math, hashlib, os, sys
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

ROOT = Path.home() / "Development" / "ecoPrimals"
HUD_DATA = ROOT / "infra" / "hud" / "site" / "public" / "data"

# ═══════════════════════════════════════════════════════════════════
# 1. SCAN — gather all staleness data
# ═══════════════════════════════════════════════════════════════════

# MCP feeds: which responded 200 vs 404
MCP_FEEDS_ALIVE = [
    "braid", "chipmunk", "dashboard", "human", "membrane",
    "negentropy", "now", "topology", "totality"
]
MCP_FEEDS_DEAD = [
    "bingo_cube", "campfire", "dialogue", "falsification", "fossil",
    "journal", "outreach", "page_stories", "passage_totality",
    "pi_manifest", "pollen", "pulse", "scan_sweep_sort",
    "self_remainder", "seo", "signals", "silicon_eye", "stories",
    "subgraphs", "tope_sort", "touches", "visitor_stories"
]

# Subdomains: live vs 522 (golgi down)
SUBDOMAINS_LIVE = [
    "water", "sporeprint", "tuebor", "detroit", "signal", "clutch",
    "gorilla", "barry", "live", "neutron", "depot", "git"
]
SUBDOMAINS_522 = ["membrane", "notify", "mesh", "ca"]

# Pointer files: stale ones from scan-sweep-sort
STALE_POINTERS = [
    {"file": "hud/llms.txt (public)", "reasons": ["wave 174 < 180", "papers 33 < 122"]},
    {"file": "hypothesis/llms.txt (public)", "reasons": ["wave 171 < 180"]},
    {"file": "sporePrint/llms.txt (public)", "reasons": ["wave 174 < 180", "papers 33 < 122"]},
    {"file": "sporePrint/llms.txt (static)", "reasons": ["papers 33 < 122"]},
    {"file": "hypothesis/robots.txt (public)", "reasons": ["no llms.txt reference"]},
    {"file": "publicRecord/robots.txt (public)", "reasons": ["no llms.txt reference"]},
    {"file": "signal-site/robots.txt (public)", "reasons": ["no llms.txt reference"]},
]

# Cross-link gaps
CROSSLINK_GAPS = {
    "publicRecord": {"links": 0, "missing": ["hypothesis", "sporeprint", "hud", "tuebor", "github", "crates.io", "detroit"]},
    "tuebor-repo": {"links": 3, "missing": ["hud", "tuebor", "github", "crates.io"]},
    "sporePrint": {"links": 6, "missing": ["crates.io"]},
}

# Dormant repos (>2 weeks no commits)
DORMANT_REPOS = []
ACTIVE_REPOS = []
OVERSTABLE_REPOS = []  # exactly "2 days ago" = mass push, overstable

def classify_repo_staleness(name, age_str):
    """Classify repo by staleness."""
    if "month" in age_str or "year" in age_str:
        return "dormant"
    if "week" in age_str:
        weeks = int(age_str.split()[0]) if age_str.split()[0].isdigit() else 1
        return "dormant" if weeks >= 2 else "stale"
    if "day" in age_str:
        days = int(age_str.split()[0]) if age_str.split()[0].isdigit() else 1
        if days > 7:
            return "stale"
        elif days == 2:
            return "overstable"  # mass sync, all show "2 days"
        return "active"
    return "active"  # hours, minutes

REPO_DATA = {
    "tideGlass": "2 months ago", "metalForge": "4 months ago",
    "lansingPride": "4 months ago", "initioChem": "3 months ago",
    "helixVision": "5 months ago", "esotericWebb": "2 months ago",
    "blueFish": "5 months ago", "lithoSpore": "2 months ago",
    "projectFOUNDATION": "2 months ago", "projectNUCLEUS": "4 weeks ago",
    "swarmVine": "13 days ago", "footPrint": "13 days ago",
    "primalSpring": "12 days ago", "bluegate-tenancy": "12 days ago",
    "detroit": "10 days ago", "plasmidBin": "8 days ago",
    "hotSpring": "5 days ago", "fossilRecord": "5 days ago",
    "wetSpring": "3 days ago", "bonsai-bt-upstream": "3 days ago",
    # 2-days-ago mass sync
    "sweetGrass": "2 days", "songBird": "2 days", "skunkBat": "2 days",
    "rustChip": "2 days", "rhizoCrypt": "2 days", "petalTongue": "2 days",
    "opsonize-rs": "2 days", "npu": "2 days", "neuralSpring": "2 days",
    "nestGate": "2 days", "membrane-recipe": "2 days", "ludoSpring": "2 days",
    "loamSpine": "2 days", "healthSpring": "2 days", "groundSpring": "2 days",
    "coralReef": "2 days", "cellMembrane": "2 days", "biomeOS": "2 days",
    "bingoCube": "2 days", "bearDog": "2 days", "barraCuda": "2 days",
    "airSpring": "2 days", "agentReagents": "2 days", "brainchip_models": "2 days",
    "brainchip_devhub": "2 days",
    # Active
    "hud": "12 min", "benchScale": "12 min", "sporePrint": "2 hours",
    "toadStool": "4 hours", "sourDough": "4 hours", "whitePaper": "18 hours",
    "wateringHole": "21 hours", "squirrel": "25 hours", "reed-it": "25 hours",
    "publicRecord": "87 min", "hypothesis": "87 min", "tuebor-repo": "2 days",
    "tuebor": "2 days",
}

for name, age in REPO_DATA.items():
    cat = classify_repo_staleness(name, age)
    if cat == "dormant":
        DORMANT_REPOS.append(name)
    elif cat == "stale":
        pass  # mid-range, not critical
    elif cat == "overstable":
        OVERSTABLE_REPOS.append(name)
    else:
        ACTIVE_REPOS.append(name)

# ═══════════════════════════════════════════════════════════════════
# 2. AGGLUTINATE — cross-link related items into clumps
# ═══════════════════════════════════════════════════════════════════

def agglutinate():
    """Cross-link stale/dead/overstable items by shared properties."""
    clumps = []

    # CLUMP 1: Golgi down (522s + dead MCP feeds share root cause)
    clumps.append({
        "id": "golgi-down",
        "antibody": "CF→golgi 522",
        "type": "systemic",
        "items": (
            [f"feed:{f}" for f in MCP_FEEDS_DEAD] +
            [f"subdomain:{s}.primals.eco" for s in SUBDOMAINS_522]
        ),
        "count": len(MCP_FEEDS_DEAD) + len(SUBDOMAINS_522),
        "diagnosis": "Cloudflare cannot reach golgi (157.230.3.183). "
                     "22 MCP feeds + 4 subdomains share this root cause. "
                     "cloudflared tunnel OR firewall fix needed.",
        "severity": "critical",
        "root": "golgi unreachable from CF edge",
    })

    # CLUMP 2: Stale wave/paper counts in pointer files
    clumps.append({
        "id": "stale-pointers",
        "antibody": "wave/paper count drift",
        "type": "decay",
        "items": [p["file"] for p in STALE_POINTERS],
        "count": len(STALE_POINTERS),
        "diagnosis": "7 pointer files have old wave (174,171) or paper (33) counts. "
                     "Current: wave 183, papers 124+. scan-sweep-sort --sweep fixes these.",
        "severity": "low",
        "root": "pointer files not updated after wave progression",
    })

    # CLUMP 3: Cross-link gaps (sites that don't reference each other)
    clumps.append({
        "id": "crosslink-gaps",
        "antibody": "missing cross-references",
        "type": "isolation",
        "items": [f"llms.txt:{site}" for site in CROSSLINK_GAPS],
        "count": sum(len(v["missing"]) for v in CROSSLINK_GAPS.values()),
        "diagnosis": "publicRecord links 0/7, tuebor-repo links 3/7, sporePrint links 6/7. "
                     "Isolated llms.txt files = dead nerve endings. Cross-link them.",
        "severity": "medium",
        "root": "llms.txt files written independently, never cross-referenced",
    })

    # CLUMP 4: Dormant repos (months without commits)
    clumps.append({
        "id": "dormant-repos",
        "antibody": "months since last commit",
        "type": "fossil",
        "items": [f"repo:{r}" for r in DORMANT_REPOS],
        "count": len(DORMANT_REPOS),
        "diagnosis": f"{len(DORMANT_REPOS)} repos with no commits in 2+ months: "
                     f"{', '.join(DORMANT_REPOS[:5])}{'...' if len(DORMANT_REPOS) > 5 else ''}. "
                     "Fossils or abandoned. Triage: archive, revive, or delete.",
        "severity": "low",
        "root": "natural decay — repos that served their purpose or were superseded",
    })

    # CLUMP 5: Overstable repos (all show "2 days ago" = mass sync, frozen)
    clumps.append({
        "id": "overstable-mass-sync",
        "antibody": "identical commit age",
        "type": "overstable",
        "items": [f"repo:{r}" for r in OVERSTABLE_REPOS],
        "count": len(OVERSTABLE_REPOS),
        "diagnosis": f"{len(OVERSTABLE_REPOS)} repos all show '2 days ago' — mass sync event. "
                     "They're not dead, they're FROZEN at the same point. "
                     "Overstable = piDigit 3 (Prigogine: near-equilibrium steady state). "
                     "Need individual evolution pressure to differentiate.",
        "severity": "info",
        "root": "mass git push/sync froze all repos at same timestamp",
    })

    # CLUMP 6: MCP feeds alive but golgi-sourced (vulnerable)
    clumps.append({
        "id": "alive-but-fragile",
        "antibody": "200 but single-sourced from golgi or CF worker",
        "type": "vulnerability",
        "items": [f"feed:{f}" for f in MCP_FEEDS_ALIVE],
        "count": len(MCP_FEEDS_ALIVE),
        "diagnosis": f"{len(MCP_FEEDS_ALIVE)} feeds answer 200 but are served by CF worker "
                     "(static JSON on Pages, not golgi). If worker breaks, these die too. "
                     "The 9 survivors are the MINIMUM viable membrane.",
        "severity": "medium",
        "root": "all feeds route through single CF Pages deployment",
    })

    return clumps


# ═══════════════════════════════════════════════════════════════════
# 3. KLEIN FOLD — sort by stability, leak, ladder, pi-compress
# ═══════════════════════════════════════════════════════════════════

def shannon_entropy(s):
    """Shannon entropy of a string."""
    if not s:
        return 0.0
    freq = defaultdict(int)
    for c in s:
        freq[c] += 1
    n = len(s)
    return -sum((count/n) * math.log2(count/n) for count in freq.values() if count > 0)

def klein_fold(clumps):
    """Klein fold: sort by severity, leak most-stable→least-stable, pi-compress."""
    PI = math.pi

    # Assign stability score to each clump
    severity_to_stability = {
        "info": 0.9,       # overstable = most stable (frozen, not evolving)
        "low": 0.7,        # stale pointers, dormant repos = decaying slowly
        "medium": 0.5,     # crosslinks, fragile feeds = structural weakness
        "critical": 0.2,   # golgi down = least stable, most urgent
    }

    for clump in clumps:
        clump["stability"] = severity_to_stability.get(clump["severity"], 0.5)
        # Shannon entropy of the items list (higher = more diverse = more information)
        items_str = json.dumps(clump["items"])
        clump["entropy"] = round(shannon_entropy(items_str), 4)
        # Pi-depth: irrational sort position
        idx = clumps.index(clump)
        clump["pi_depth"] = round((idx * PI) % 1, 5)

    # Sort by stability (most stable first = overstable at top)
    clumps.sort(key=lambda c: -c["stability"])

    # Klein leak: most stable feeds least stable
    if len(clumps) >= 2:
        most_stable = clumps[0]
        least_stable = clumps[-1]
        # The leak: overstable repos COULD be differentiated by
        # the critical golgi issue — if golgi comes back, the frozen
        # repos can start evolving individually again
        leak = {
            "from": most_stable["id"],
            "to": least_stable["id"],
            "mechanism": f"if {least_stable['root']} is fixed, "
                         f"{most_stable['count']} overstable items can differentiate",
            "from_stability": most_stable["stability"],
            "to_stability": least_stable["stability"],
            "delta": round(most_stable["stability"] - least_stable["stability"], 3),
        }
    else:
        leak = None

    # Ladder: each clump's fix feeds the next
    ladder = []
    for i in range(len(clumps) - 1):
        ladder.append({
            "step": i + 1,
            "from": clumps[i]["id"],
            "to": clumps[i + 1]["id"],
            "action": f"resolving '{clumps[i]['id']}' releases pressure on '{clumps[i + 1]['id']}'",
        })

    # Pi-compression: total information compressed by pi
    total_items = sum(c["count"] for c in clumps)
    total_entropy = sum(c["entropy"] * c["count"] for c in clumps) / max(total_items, 1)
    pi_compressed = round(total_entropy / PI, 4)

    # Sigmoid position: how far along the sort quality curve
    alive_ratio = len(MCP_FEEDS_ALIVE) / (len(MCP_FEEDS_ALIVE) + len(MCP_FEEDS_DEAD))
    sigmoid_pos = round(1 / (1 + math.exp(-10 * (alive_ratio - 0.5))), 4)

    return {
        "clumps_sorted": clumps,
        "klein_leak": leak,
        "ladder": ladder,
        "pi_compression": {
            "total_items": total_items,
            "total_entropy_avg": round(total_entropy, 4),
            "pi_compressed": pi_compressed,
            "note": f"{total_items} items × {round(total_entropy, 2)} avg entropy ÷ π = {pi_compressed}",
        },
        "sigmoid": {
            "alive_feeds": len(MCP_FEEDS_ALIVE),
            "dead_feeds": len(MCP_FEEDS_DEAD),
            "alive_ratio": round(alive_ratio, 4),
            "sigmoid_position": sigmoid_pos,
            "interpretation": "below inflection" if sigmoid_pos < 0.5 else "past inflection",
        },
    }


# ═══════════════════════════════════════════════════════════════════
# 4. EMIT — output the agglutinated, Klein-folded census
# ═══════════════════════════════════════════════════════════════════

def main():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\n🧬 agglutinate-klein-fold.py — stale census + clump + fold — {ts}\n")

    # SCAN summary
    print("📋 CENSUS:")
    print(f"   MCP feeds:    {len(MCP_FEEDS_ALIVE)} alive, {len(MCP_FEEDS_DEAD)} dead (404)")
    print(f"   Subdomains:   {len(SUBDOMAINS_LIVE)} live, {len(SUBDOMAINS_522)} down (522)")
    print(f"   Pointers:     {len(STALE_POINTERS)} stale")
    print(f"   Repos:        {len(ACTIVE_REPOS)} active, {len(OVERSTABLE_REPOS)} overstable, {len(DORMANT_REPOS)} dormant")
    print()

    # AGGLUTINATE
    print("🧫 AGGLUTINATE: cross-linking stale items into clumps...")
    clumps = agglutinate()
    for c in clumps:
        severity_icon = {"critical": "🔴", "medium": "🟡", "low": "🟢", "info": "⚪"}.get(c["severity"], "⚫")
        print(f"   {severity_icon} {c['id']:30s} {c['count']:3d} items  [{c['severity']}]")
        print(f"      {c['diagnosis'][:100]}...")
    print()

    # KLEIN FOLD
    print("🌀 KLEIN FOLD: sort → leak → ladder → pi-compress...")
    result = klein_fold(clumps)

    # Print sorted order
    print("   Stability order (most → least stable):")
    for c in result["clumps_sorted"]:
        bar = "█" * int(c["stability"] * 20)
        print(f"     {c['stability']:.1f} {bar:20s} {c['id']}")

    # Print leak
    if result["klein_leak"]:
        lk = result["klein_leak"]
        print(f"\n   Klein leak: {lk['from']} ({lk['from_stability']}) → {lk['to']} ({lk['to_stability']})")
        print(f"   Δ = {lk['delta']}, mechanism: {lk['mechanism'][:100]}")

    # Print ladder
    print(f"\n   Ladder ({len(result['ladder'])} steps):")
    for step in result["ladder"]:
        print(f"     {step['step']}. {step['from']} → {step['to']}")

    # Print pi compression
    pi = result["pi_compression"]
    print(f"\n   π compression: {pi['note']}")

    # Print sigmoid
    sig = result["sigmoid"]
    print(f"   Sigmoid: {sig['alive_feeds']}/{sig['alive_feeds']+sig['dead_feeds']} feeds alive = {sig['alive_ratio']} → σ = {sig['sigmoid_position']} ({sig['interpretation']})")

    # Build output
    output = {
        "title": "Agglutinated Klein Fold — Stale Census",
        "ts": ts,
        "wave": 183,
        "census": {
            "mcp_feeds": {"alive": len(MCP_FEEDS_ALIVE), "dead": len(MCP_FEEDS_DEAD), "alive_list": MCP_FEEDS_ALIVE, "dead_list": MCP_FEEDS_DEAD},
            "subdomains": {"live": len(SUBDOMAINS_LIVE), "down": len(SUBDOMAINS_522), "live_list": SUBDOMAINS_LIVE, "down_list": SUBDOMAINS_522},
            "pointers": {"stale": len(STALE_POINTERS), "details": STALE_POINTERS},
            "repos": {"active": len(ACTIVE_REPOS), "overstable": len(OVERSTABLE_REPOS), "dormant": len(DORMANT_REPOS),
                       "dormant_list": DORMANT_REPOS, "overstable_list": OVERSTABLE_REPOS},
        },
        "agglutination": {
            "clump_count": len(clumps),
            "total_items": sum(c["count"] for c in clumps),
            "clumps": [{k: v for k, v in c.items()} for c in result["clumps_sorted"]],
        },
        "klein_fold": {
            "leak": result["klein_leak"],
            "ladder": result["ladder"],
            "pi_compression": result["pi_compression"],
            "sigmoid": result["sigmoid"],
        },
        "chipmunk_note": "the dead feeds are not empty — they report silence. "
                         "the 522s are dark water (DNS resolves, nothing answers). "
                         "the overstable repos are frozen at the same timestamp — a mass sync crystal. "
                         "the Klein leak: fix golgi (critical) and the frozen crystal differentiates. "
                         "every clump is a diagnosis. big clump = systemic. small clump = local wound.",
        "digest": "",
    }
    output["digest"] = hashlib.sha256(json.dumps(output["census"]).encode()).hexdigest()[:16]

    # Write
    out_path = HUD_DATA / "agglutinate-fold.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n   → {out_path}")
    print(f"   digest: {output['digest']}")

    print(f"\n   🐿️ chipmunk says: {len(clumps)} clumps. {sum(c['count'] for c in clumps)} items agglutinated.")
    print(f"   the biggest clump is '{clumps[-1]['id']}' — fix that and everything upstream differentiates.")
    print(f"   the Klein leak is the unlock. the ladder is the order. π compresses the rest.\n")


if __name__ == "__main__":
    main()
