#!/usr/bin/env python3
"""
scan-sweep-sort.py — census all pointer files, redistribute, feed next gen.

Every llms.txt, robots.txt, sitemap.xml is a pointer ELSEWHERE.
They ARE the membrane surface — the markers that let outsiders find us.
Every edit is an edit we should feed the next generation of self.

THE CYCLE:
  1. SCAN  — find all pointer files, check staleness
  2. SWEEP — update stale ones to current wave/counts
  3. SORT  — cross-link everything, ensure consistency
  4. FEED  — output a manifest that IS the next generation's input

Usage:
  python3 scan-sweep-sort.py              # scan only
  python3 scan-sweep-sort.py --sweep      # scan + update files
"""

import json, os, sys, re, hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.home() / "Development" / "ecoPrimals"
WAVE = 180
HYPOTHESES = 18
PAPERS = 122
CRATES = 680
CRATE_FAMILIES = 46
FORMULA = "Fe₃₁O₂₃P₁₈C₁₀S₉N₈H₁"
SITES = {
    "hypothesis.primals.eco": "18 hypotheses — gAIa university, start here",
    "sporeprint.primals.eco": "122+ papers — science, evidence, methodology",
    "hud.primals.eco":        "live membrane dashboard — observation surface",
    "detroit.primals.eco":    "civic data — public records, analysis",
    "tuebor.primals.eco":     "legal analysis — evidence, defense",
    "github.com/ecoPrimal":   "source code — 60 repos, AGPL-3.0",
    "crates.io/users/ecoPrimal": "Rust crates — 5 published, 680 ready",
}

def scan_pointer_files():
    """Find all llms.txt, robots.txt, sitemap.xml and check freshness."""
    pointers = []
    for name in ["llms.txt", "robots.txt", "sitemap.xml"]:
        for f in sorted(ROOT.rglob(name)):
            if "target" in str(f) or "node_modules" in str(f):
                continue
            is_static = "/static/" in str(f)
            is_public = "/public/" in str(f)
            rel = str(f.relative_to(ROOT))
            site = rel.split("/")[1] if len(rel.split("/")) > 1 else "root"
            try:
                content = f.read_text(errors='replace')
                lines = len(content.split("\n"))
                # Check staleness indicators
                wave_match = re.search(r'[Ww]ave\s*(\d+)', content)
                found_wave = int(wave_match.group(1)) if wave_match else None
                has_hypothesis = "hypothesis" in content.lower()
                has_gaia = "gaia" in content.lower() or "gAIa" in content
                has_tale = "tale of two" in content.lower()
                has_ptolemy = "ptolemy" in content.lower()
                paper_match = re.search(r'(\d+)\s*papers', content)
                found_papers = int(paper_match.group(1)) if paper_match else None

                stale_reasons = []
                if found_wave and found_wave < WAVE:
                    stale_reasons.append(f"wave {found_wave} < {WAVE}")
                if found_papers and found_papers < PAPERS:
                    stale_reasons.append(f"papers {found_papers} < {PAPERS}")
                if name == "llms.txt" and not has_gaia:
                    stale_reasons.append("missing gAIa reference")
                if name == "robots.txt" and "llms" not in content.lower():
                    stale_reasons.append("no llms.txt reference in robots.txt")

                pointers.append({
                    "file": rel,
                    "name": name,
                    "site": site,
                    "source": "static" if is_static else "public" if is_public else "other",
                    "lines": lines,
                    "wave": found_wave,
                    "papers": found_papers,
                    "has_gaia": has_gaia,
                    "has_hypothesis": has_hypothesis,
                    "stale": bool(stale_reasons),
                    "stale_reasons": stale_reasons,
                })
            except Exception as e:
                pointers.append({
                    "file": rel, "name": name, "site": site,
                    "error": str(e), "stale": True,
                    "stale_reasons": [f"error: {e}"],
                })
    return pointers

def sweep_robots(pointers, dry_run=True):
    """Update robots.txt files to include llms.txt reference."""
    updated = []
    for p in pointers:
        if p["name"] != "robots.txt" or p.get("source") != "static":
            continue
        if "no llms.txt reference" in " ".join(p.get("stale_reasons", [])):
            filepath = ROOT / p["file"]
            content = filepath.read_text()
            if "llms" not in content.lower():
                # Determine the site's base URL
                if "hypothesis" in p["site"]:
                    base = "https://hypothesis.primals.eco"
                elif "publicRecord" in p["site"]:
                    base = "https://detroit.primals.eco"
                elif "signal" in p["file"]:
                    base = "https://signal.primals.eco"
                else:
                    continue
                addition = f"\n# AI context document\n# See {base}/llms.txt for full site context\n"
                if not dry_run:
                    filepath.write_text(content.rstrip() + addition + "\n")
                updated.append(p["file"])
    return updated

def sort_crosslinks(pointers):
    """Check cross-linking between sites."""
    llms_files = [p for p in pointers if p["name"] == "llms.txt" and p.get("source") == "static"]
    crosslinks = {}
    for p in llms_files:
        filepath = ROOT / p["file"]
        content = filepath.read_text(errors='replace')
        links_to = []
        for site_url in SITES:
            if site_url in content:
                links_to.append(site_url)
        crosslinks[p["site"]] = {
            "file": p["file"],
            "links_to": links_to,
            "missing": [s for s in SITES if s not in links_to],
        }
    return crosslinks

def feed_manifest(pointers, crosslinks):
    """Output the manifest that IS the next generation's input."""
    stale = [p for p in pointers if p.get("stale")]
    fresh = [p for p in pointers if not p.get("stale")]

    manifest = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "title": "Scan Sweep Sort — Census of All Pointers",
        "wave": WAVE,
        "current_state": {
            "hypotheses": HYPOTHESES,
            "papers": PAPERS,
            "crates": CRATES,
            "crate_families": CRATE_FAMILIES,
            "formula": FORMULA,
            "sites": list(SITES.keys()),
        },
        "pointers": {
            "total": len(pointers),
            "stale": len(stale),
            "fresh": len(fresh),
            "by_type": {
                "llms_txt": len([p for p in pointers if p["name"] == "llms.txt"]),
                "robots_txt": len([p for p in pointers if p["name"] == "robots.txt"]),
                "sitemap_xml": len([p for p in pointers if p["name"] == "sitemap.xml"]),
            },
        },
        "stale_files": [{"file": p["file"], "reasons": p.get("stale_reasons", [])} for p in stale],
        "crosslinks": crosslinks,
        "next_generation": {
            "note": "every edit is an edit we should feed the next generation to solve",
            "inputs": [
                "this manifest (scan-sweep-sort.json)",
                "all llms.txt files (the pointers)",
                "all robots.txt files (the permissions)",
                "all sitemap.xml files (the maps)",
                "the yggdrasil-cascade.json (the tree)",
                "the enmesh.json (the DAG)",
                "the metabolize.json (the cycle)",
            ],
            "outputs": [
                "updated llms.txt across all sites",
                "cross-linked sitemap references",
                "consistent wave/paper/hypothesis counts",
                "the NEXT scan-sweep-sort.json (the fold)",
            ],
            "the_fold": "this manifest IS the sourdough starter for the next generation. feed it back.",
        },
        "digest": "",
    }
    manifest["digest"] = hashlib.sha256(json.dumps(manifest["pointers"]).encode()).hexdigest()[:16]
    return manifest

def main():
    sweep = "--sweep" in sys.argv
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\n🔍 scan-sweep-sort.py — census all pointers — {ts}\n")

    # 1. SCAN
    print("📋 SCAN: finding all pointer files...")
    pointers = scan_pointer_files()
    stale = [p for p in pointers if p.get("stale")]
    fresh = [p for p in pointers if not p.get("stale")]

    print(f"   {len(pointers)} pointer files found")
    print(f"   {len(fresh)} fresh, {len(stale)} stale\n")

    for p in pointers:
        status = "✅" if not p.get("stale") else "⚠️ "
        reasons = ", ".join(p.get("stale_reasons", []))
        print(f"   {status} {p['name']:15s} {p.get('source','?'):7s} {p['site']:25s} {reasons}")

    # 2. SORT (check cross-links)
    print(f"\n🔗 SORT: checking cross-links...")
    crosslinks = sort_crosslinks(pointers)
    for site, info in crosslinks.items():
        n_links = len(info["links_to"])
        n_missing = len(info["missing"])
        print(f"   {site:25s} links to {n_links}/{len(SITES)} sites", end="")
        if n_missing:
            print(f"  MISSING: {', '.join(info['missing'][:3])}")
        else:
            print(" ✅ fully linked")

    # 3. SWEEP (update if --sweep)
    if sweep:
        print(f"\n🧹 SWEEP: updating stale files...")
        updated = sweep_robots(pointers, dry_run=False)
        for u in updated:
            print(f"   updated: {u}")
    else:
        print(f"\n   (pass --sweep to update stale files)")

    # 4. FEED (output manifest)
    print(f"\n📤 FEED: writing manifest for next generation...")
    manifest = feed_manifest(pointers, crosslinks)
    out = ROOT / "infra" / "hud" / "site" / "public" / "data" / "scan-sweep-sort.json"
    with open(out, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"   → {out}")
    print(f"   digest: {manifest['digest']}")
    print(f"\n   This manifest IS the sourdough starter for the next generation.")
    print(f"   Feed it back. Every edit feeds the fold.")

if __name__ == "__main__":
    main()
