#!/usr/bin/env python3
"""
info-mass.py — triangulation gave position. metabolism gives MASS.
c² is just π² (structurally).

Shannon entropy × stoichiometric weight × Landauer = PHYSICAL MASS.
Run it back through the sort. Information → size → mass.
"""
import json, math, hashlib, collections
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.home() / "Development" / "ecoPrimals"
DATA = ROOT / "infra" / "hud" / "site" / "public" / "data"
PI = math.pi
PI2 = PI * PI
C2 = 299792458.0 ** 2
K_B = 1.380649e-23
T = 300
LANDAUER = K_B * T * math.log(2)
PROTON = 1.67262192e-27

FILE_TYPES = {
    "rust":     (".rs",   "Fe", 55.845, "protein"),
    "python":   (".py",   "C",  12.011, "RNA"),
    "shell":    (".sh",   "N",  14.007, "regulatory"),
    "markdown": (".md",   "H",  1.008,  "substrate"),
    "json":     (".json", "O",  15.999, "nutrient"),
    "toml":     (".toml", "S",  32.06,  "bond"),
    "html":     (".html", "P",  30.974, "membrane"),
}

def shannon(data):
    if not data: return 0.0
    freq = collections.Counter(data)
    total = sum(freq.values())
    return -sum((c/total)*math.log2(c/total) for c in freq.values() if c>0)

def scan():
    print("📊 Shannon + stoichiometric scan...\n")
    results = {}
    total_bytes = 0; total_info = 0; total_stoich = 0
    for lang, (ext, elem, mass, role) in FILE_TYPES.items():
        files = [f for f in ROOT.rglob(f"*{ext}")
                 if f.is_file() and "target" not in str(f)
                 and ".git" not in str(f) and "node_modules" not in str(f)]
        if not files: continue
        lang_bytes = 0; entropy_sum = 0; n = 0
        for f in files[:300]:
            try:
                raw = f.read_bytes()
                H = shannon(raw)
                lang_bytes += len(raw)
                entropy_sum += H * len(raw)
                n += 1
            except: pass
        if n == 0: continue
        avg_H = entropy_sum / max(lang_bytes, 1)
        info_bits = lang_bytes * avg_H
        stoich = lang_bytes * mass * avg_H
        results[lang] = {
            "files": n, "total_files": len(files), "bytes": lang_bytes,
            "H": round(avg_H, 3), "info_bits": round(info_bits),
            "element": elem, "atomic_mass": mass, "role": role,
            "stoich_mass": round(stoich),
        }
        total_bytes += lang_bytes
        total_info += info_bits
        total_stoich += stoich
        print(f"  {elem:>2s} {lang:10s} {n:5d}/{len(files):<5d} {lang_bytes/1e6:7.1f}M  H={avg_H:.3f}  stoich={stoich/1e6:.1f}M")
    print(f"\n  TOTAL: {total_bytes/1e6:.0f}M bytes, {total_info/8/1e6:.1f}MB info, stoich={total_stoich:.0f}")
    return results, total_bytes, total_info, total_stoich

def compute_mass(total_bytes, total_info, total_stoich):
    print(f"\n⚖️  computing information mass...\n")
    raw_bits = total_bytes * 8
    E_info = total_info * LANDAUER
    E_raw = raw_bits * LANDAUER
    m_info = E_info / C2
    m_raw = E_raw / C2
    p_info = m_info / PROTON
    p_raw = m_raw / PROTON
    print(f"  Info bits:     {total_info:,.0f}")
    print(f"  Raw bits:      {raw_bits:,.0f}")
    print(f"  Compression:   {total_info/max(raw_bits,1):.4f}")
    print(f"  Landauer E:    {E_info:.3e} J")
    print(f"  Mass (E/c²):   {m_info:.3e} kg")
    print(f"  = {p_info:.2f} proton masses (information)")
    print(f"  = {p_raw:.2f} proton masses (raw)")
    return {"info_bits": round(total_info), "raw_bits": raw_bits,
            "energy_j": E_info, "mass_kg": m_info,
            "protons_info": round(p_info, 2), "protons_raw": round(p_raw, 2)}

def equivalence(total_stoich, landauer):
    print(f"\n{'═'*60}")
    print(f"  c² ≡ π²  (structural)")
    print(f"{'═'*60}\n")
    pi2_norm = total_stoich / PI2
    pi3_norm = total_stoich / (PI**3)
    print(f"  π²  = {PI2:.6f}")
    print(f"  c²  = {C2:.6e}")
    print(f"  1/π = {1/PI:.6f} (fold rate)")
    print(f"")
    print(f"  Stoich mass:       {total_stoich:>15.0f}")
    print(f"  ÷ π² (boundary):  {pi2_norm:>15.0f}")
    print(f"  ÷ π³ (trefoil):   {pi3_norm:>15.0f}")
    print(f"")
    print(f"  Landauer: {landauer['protons_info']:.2f} proton masses")
    print(f"")
    print(f"  WHY c² = π² STRUCTURALLY:")
    print(f"    c² converts mass ↔ energy   (interior ↔ radiation)")
    print(f"    π² converts area ↔ radius²  (surface ↔ interior)")
    print(f"    BOTH map inside to outside.")
    print(f"    The holographic principle: info ON surface = mass INSIDE.")
    print(f"    Surface area = πr². Interior mass = E/c².")
    print(f"    The π in the area IS the c in the energy.")
    print(f"    They're the same conversion on different manifolds.")
    print(f"")
    print(f"  THE CHAIN:")
    print(f"    Shannon bits → stoich mass (element-weighted)")
    print(f"    → ÷ π² (surface→interior)")
    print(f"    → ÷ π  (fold rate)")
    print(f"    → = π³ normalized mass")
    print(f"    → 3 crossings of π = trefoil")
    print(f"    → same as 3 GPS satellites = triangulation")
    print(f"    → same as KNN k=3 = classification")
    print(f"    → arithmetic → geometry → algebra → irreducibility")
    print(f"")
    print(f"  INFORMATION BACKTRACKS TO SIZE AND MASS:")
    print(f"    If you know the Shannon entropy, you know the info bits.")
    print(f"    If you know the info bits, you know the Landauer energy.")
    print(f"    If you know the energy, you know the mass (E/c²).")
    print(f"    c² is the conversion. π² is the same conversion")
    print(f"    for boundaries. The trefoil (π³) connects them.")
    return {"pi2_norm": round(pi2_norm), "pi3_norm": round(pi3_norm),
            "trefoil": "3 crossings × π = π³"}

def main():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\n⚖️  info-mass.py — c² is just π² — {ts}\n")
    results, total_bytes, total_info, total_stoich = scan()
    landauer = compute_mass(total_bytes, total_info, total_stoich)
    equiv = equivalence(total_stoich, landauer)
    result = {"ts": ts, "title": "Information Mass — c² is just π²",
              "shannon": {k: {"H": v["H"], "element": v["element"], "stoich": v["stoich_mass"]}
                          for k, v in results.items()},
              "landauer": landauer, "stoichiometric_mass": total_stoich,
              "equivalence": equiv,
              "digest": hashlib.sha256(str(total_info).encode()).hexdigest()[:16]}
    out = DATA / "info-mass.json"
    with open(out, "w") as f: json.dump(result, f, indent=2, default=str)
    print(f"\n⚖️  → {out}\n   digest: {result['digest']}")

if __name__ == "__main__":
    main()
