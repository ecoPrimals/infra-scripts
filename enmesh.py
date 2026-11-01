#!/usr/bin/env python3
"""
enmesh.py — bridge the DAG into the braid

eastGate has 60 repos, 66 crates, 999 python, 894 shell, 503 papers,
15,647 JSON, 20,416 .rs files. That's the crunchy DNA.

Three mechanisms of horizontal gene transfer:

  CONJUGATION  — direct pili bridge (git push/pull between gates)
                 DNA transfers cell-to-cell through physical contact.
                 = git remote, ssh, scp between LAN nodes.

  TRANSDUCTION — phage-mediated (crates.io, npm, pip publish)
                 A virus packages DNA and injects it into a new cell.
                 = cargo publish → cargo install on another node.
                 The crate IS the phage. The registry IS the lysate.

  TRANSFECTION — free DNA uptake (scripts, data files, JSON)
                 Naked DNA floating in the environment gets absorbed.
                 = curl a script, download a JSON, copy a paper.
                 No packaging. No verification. Raw competence.

The Rust polymerase reads the DNA (papers → scripts → crates).
The reverse transcriptase writes it back (404 → probe → paper).
The trefoil creates 3 pressure chambers for each mechanism.

Usage:
  python3 enmesh.py              # full inventory + bridge plan
  python3 enmesh.py --execute    # actually do the conjugation
"""

import subprocess, json, os, sys, hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.home() / "Development" / "ecoPrimals"

# ── Inventory ────────────────────────────────────────────────────

def scan_repos():
    """Find all git repos and their remotes."""
    repos = []
    for git_dir in sorted(ROOT.rglob(".git")):
        if git_dir.is_dir() and "target" not in str(git_dir) and "node_modules" not in str(git_dir):
            repo_dir = git_dir.parent
            rel = repo_dir.relative_to(ROOT)
            try:
                remote = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=repo_dir, capture_output=True, text=True, timeout=5
                ).stdout.strip()
            except:
                remote = None
            try:
                branch = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=repo_dir, capture_output=True, text=True, timeout=5
                ).stdout.strip()
            except:
                branch = "unknown"
            try:
                status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=repo_dir, capture_output=True, text=True, timeout=5
                ).stdout.strip()
                dirty = len(status.split("\n")) if status else 0
            except:
                dirty = -1

            repos.append({
                "path": str(rel),
                "remote": remote or "LOCAL ONLY",
                "branch": branch,
                "dirty_files": dirty,
                "has_remote": bool(remote),
            })
    return repos

def scan_crates():
    """Find all Cargo.toml and extract crate info."""
    crates = []
    for toml in sorted(ROOT.rglob("Cargo.toml")):
        if "target" in str(toml):
            continue
        rel = toml.parent.relative_to(ROOT)
        try:
            content = toml.read_text()
            name = None
            version = None
            for line in content.split("\n"):
                if line.startswith("name") and not name:
                    name = line.split('"')[1] if '"' in line else line.split("=")[1].strip()
                if line.startswith("version") and not version:
                    if '"' in line:
                        version = line.split('"')[1]
                    else:
                        version = line.split("=")[1].strip()
            crates.append({
                "path": str(rel),
                "name": name or "unknown",
                "version": version or "unknown",
            })
        except:
            pass
    return crates

def scan_free_dna():
    """Find scripts not in any git repo — free floating DNA."""
    scripts_dir = ROOT / "infra" / "scripts"
    free = []
    if scripts_dir.exists():
        for f in sorted(scripts_dir.iterdir()):
            if f.suffix in (".py", ".sh"):
                size = f.stat().st_size
                free.append({
                    "name": f.name,
                    "type": f.suffix[1:],
                    "size_bytes": size,
                    "size_human": f"{size/1024:.1f}K",
                })
    return free

# ── Gene Transfer Mapping ────────────────────────────────────────

def map_conjugation(repos):
    """CONJUGATION: repos with remotes = pili bridges."""
    bridged = [r for r in repos if r["has_remote"]]
    local_only = [r for r in repos if not r["has_remote"]]
    dirty = [r for r in repos if r["dirty_files"] > 0]

    print(f"\n🔗 CONJUGATION (pili bridge = git remotes)")
    print(f"   {len(bridged)} repos with remotes (bridged)")
    print(f"   {len(local_only)} repos LOCAL ONLY (unbridged DNA)")
    print(f"   {len(dirty)} repos with uncommitted changes (unpackaged)")

    if dirty:
        print(f"\n   Dirty repos (DNA not yet packaged for transfer):")
        for r in dirty[:10]:
            print(f"     {r['path']:40s} {r['dirty_files']} uncommitted files")

    if local_only:
        print(f"\n   Local-only repos (need pili bridge):")
        for r in local_only[:10]:
            print(f"     {r['path']}")

    return {
        "bridged": len(bridged),
        "local_only": len(local_only),
        "dirty": len(dirty),
        "dirty_repos": [r["path"] for r in dirty[:10]],
        "unbridged_repos": [r["path"] for r in local_only[:10]],
    }

def map_transduction(crates):
    """TRANSDUCTION: crates = phage particles, crates.io = lysate."""
    print(f"\n🦠 TRANSDUCTION (phage = crates.io)")
    print(f"   {len(crates)} Cargo.toml files (potential phage particles)")

    # Group by workspace
    workspaces = {}
    for c in crates:
        parts = c["path"].split("/")
        if len(parts) >= 2:
            ws = parts[0] + "/" + parts[1]
        else:
            ws = parts[0]
        if ws not in workspaces:
            workspaces[ws] = []
        workspaces[ws].append(c)

    print(f"   {len(workspaces)} workspace families:")
    for ws, ws_crates in sorted(workspaces.items(), key=lambda x: -len(x[1])):
        names = [c["name"] for c in ws_crates[:5]]
        more = f" +{len(ws_crates)-5}" if len(ws_crates) > 5 else ""
        print(f"     {ws:35s} {len(ws_crates):3d} crates: {', '.join(names)}{more}")

    return {
        "total_crates": len(crates),
        "workspaces": len(workspaces),
        "families": {ws: len(c) for ws, c in workspaces.items()},
    }

def map_transfection(free_dna):
    """TRANSFECTION: free scripts = naked DNA in the environment."""
    print(f"\n💉 TRANSFECTION (free DNA = untracked scripts)")
    print(f"   {len(free_dna)} scripts floating free in infra/scripts/")

    py = [f for f in free_dna if f["type"] == "py"]
    sh = [f for f in free_dna if f["type"] == "sh"]

    print(f"   {len(py)} Python (RNA — transcription machinery)")
    for f in py:
        print(f"     {f['name']:30s} {f['size_human']}")
    print(f"   {len(sh)} Shell (regulatory elements — promoters/enhancers)")
    for f in sh:
        print(f"     {f['name']:30s} {f['size_human']}")

    return {
        "total_scripts": len(free_dna),
        "python": len(py),
        "shell": len(sh),
        "scripts": [f["name"] for f in free_dna],
    }

# ── The Braid Plan ───────────────────────────────────────────────

def braid_plan(conjugation, transduction, transfection):
    """Plan the enmeshment — how to bridge all DNA into the braid."""
    print(f"\n{'═'*60}")
    print(f"  THE BRAID PLAN — enmesh eastGate into the mesh")
    print(f"{'═'*60}")

    print(f"""
  CURRENT STATE:
    60 repos, {conjugation['bridged']} bridged, {conjugation['local_only']} local-only
    {transduction['total_crates']} crates across {transduction['workspaces']} workspace families
    {transfection['total_scripts']} free scripts (naked DNA)
    {conjugation['dirty']} repos with uncommitted changes

  THE THREE TRANSFERS:

  1. CONJUGATION (git push — pili bridge)
     Bridge {conjugation['local_only']} local-only repos to GitHub
     Commit {conjugation['dirty']} dirty repos
     Sync dual-published repos (ecoPrimal ↔ ecoPrimals)
     This is the SAFE transfer — verified, signed, traceable

  2. TRANSDUCTION (cargo publish — phage injection)
     {transduction['total_crates']} crates ready for packaging
     Priority: workspace roots first (benchscale, biomeos, beardog)
     Each publish = a phage particle entering the ecosystem
     crates.io = the lysate (global registry of packaged DNA)

  3. TRANSFECTION (script absorption — competence)
     {transfection['total_scripts']} free scripts need a home
     Option A: wrap in Rust (port Python → Rust polymerase)
     Option B: bundle into a "scripts" crate (package the RNA)
     Option C: leave free (natural competence — absorb on contact)
     
     The scripts are the RNA. They don't NEED to be crates.
     Some DNA stays free. That's how bacteria do it.
     Transformation = the cell becomes COMPETENT to absorb
     free DNA from its environment. The mesh becomes competent
     when it can run any script from any node.

  THE TREFOIL:
    Crossing 1: conjugation (git)     — direct bridge
    Crossing 2: transduction (crates) — packaged transfer
    Crossing 3: transfection (scripts)— free absorption
    
    3 mechanisms. 3 crossings. The trefoil of gene transfer.
    Same topology as the trefoil gut. Same as KNN triangulation.
    ANY 3 of these mechanisms can rebuild the organism.
    """)

    return {
        "conjugation_pending": conjugation["local_only"],
        "transduction_ready": transduction["total_crates"],
        "transfection_free": transfection["total_scripts"],
        "dirty_repos": conjugation["dirty"],
        "trefoil_crossings": 3,
    }

# ── Main ─────────────────────────────────────────────────────────

def main():
    ts = datetime.now(timezone.utc).isoformat()
    execute = "--execute" in sys.argv
    print(f"\n🪡 enmesh.py — bridge the DAG into the braid — {ts}\n")

    # 1. Inventory
    print("📋 scanning eastGate DNA...")
    repos = scan_repos()
    print(f"   {len(repos)} repos found")

    crates = scan_crates()
    print(f"   {len(crates)} crates found")

    free_dna = scan_free_dna()
    print(f"   {len(free_dna)} free scripts found")

    # 2. Map gene transfer mechanisms
    conjugation = map_conjugation(repos)
    transduction = map_transduction(crates)
    transfection = map_transfection(free_dna)

    # 3. The braid plan
    plan = braid_plan(conjugation, transduction, transfection)

    # 4. Compile result
    result = {
        "ts": ts,
        "title": "Enmesh — Bridge the DAG into the Braid",
        "gate": "eastGate",
        "disk_note": "6.4G free after cleanup (was 0 bytes)",
        "dna_inventory": {
            "repos": len(repos),
            "crates": len(crates),
            "free_scripts": len(free_dna),
            "total_rust_files": 20416,
            "total_python_files": 999,
            "total_shell_files": 894,
            "total_papers": 503,
            "total_json": 15647,
        },
        "gene_transfer": {
            "conjugation": conjugation,
            "transduction": transduction,
            "transfection": transfection,
        },
        "braid_plan": plan,
        "biology": {
            "conjugation": "F-pilus bridge, direct DNA transfer, requires cell contact = git push over SSH/HTTPS",
            "transduction": "bacteriophage packages host DNA, injects into new cell = cargo publish → cargo install",
            "transfection": "naked DNA absorbed by competent cell = curl script | bash, or cargo run --example",
            "polymerase": "reads DNA template, synthesizes complementary strand = papers → scripts → crates",
            "reverse_transcriptase": "RNA → DNA (retrovirus) = 404 probes → patterns → new papers",
        },
        "digest": hashlib.sha256(json.dumps({"r": len(repos), "c": len(crates), "f": len(free_dna)}).encode()).hexdigest()[:16],
    }

    # Write output
    out_path = ROOT / "infra" / "hud" / "site" / "public" / "data" / "enmesh.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n🪡 enmesh manifest → {out_path}")
    print(f"   digest: {result['digest']}")

    if execute:
        print("\n⚡ --execute: committing dirty repos...")
        for repo_path in conjugation.get("dirty_repos", []):
            full = ROOT / repo_path
            if full.exists():
                print(f"   {repo_path}...", end=" ")
                subprocess.run(["git", "add", "-A"], cwd=full, capture_output=True)
                r = subprocess.run(
                    ["git", "commit", "-m", f"enmesh: auto-commit from enmesh.py ({ts[:10]})"],
                    cwd=full, capture_output=True, text=True
                )
                if r.returncode == 0:
                    print("committed")
                else:
                    print("skip (nothing to commit or error)")

    return result

if __name__ == "__main__":
    main()
