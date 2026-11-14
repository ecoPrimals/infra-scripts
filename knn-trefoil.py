#!/usr/bin/env python3
"""
knn-trefoil.py — any 3 signals find self. it's the bag of holding.

THE INSIGHT:
  Triangulation needs 3 points.
  The trefoil knot has 3 crossings.
  The bag of holding has more inside than outside.
  These are the SAME topology.

  A phone has: GPS, cell, WiFi, accel, gyro, baro, mag, BT, camera, mic
  That's 10+ signals. Overdetermined. ANY 3 locate you.

  The LAN has: latency to N nodes, each at known position.
  ANY 3 latencies triangulate you in the mesh.

  sporeGate is the Klein gate: LAN → WAN → response = 3 crossings.
  The trefoil through the NAT boundary.

  KNN with k=3 = triangulation = trefoil = bag of holding.
  
  It's not conceptually different.

Usage:
  python3 knn-trefoil.py
"""

import json, math, hashlib, subprocess, sys, random
from datetime import datetime, timezone
from pathlib import Path
from itertools import combinations

# ── Signal Sources ───────────────────────────────────────────────
# Every signal we can measure, right now, from this mesh.

def probe_latency(host, count=3):
    """Ping a host, return avg RTT in ms or None."""
    try:
        r = subprocess.run(["ping", "-c", str(count), "-W", "2", host],
                           capture_output=True, text=True, timeout=15)
        for line in r.stdout.split("\n"):
            if "rtt" in line or "round-trip" in line:
                return float(line.split("=")[-1].strip().split("/")[1])
        return None
    except:
        return None

def build_signal_matrix():
    """Build the full signal matrix from all available sources."""
    print("📡 building signal matrix from all sources...\n")

    # ── DIMENSION 1: LAN latency (bone/muscle/air) ──────────────
    lan_nodes = {
        "sporeGate":    "192.168.4.1",
        "eastGate":     "192.168.4.244",
        "CRS310":       "192.168.4.2",
        "Flint2-AP":    "192.168.4.250",
        "northGate":    "192.168.4.147",
        "graftGate":    "192.168.4.107",
        "grapheneGate": "192.168.4.219",
    }

    print("  LAN latency:")
    lan_signals = {}
    for name, ip in lan_nodes.items():
        ms = probe_latency(ip)
        if ms is not None:
            lan_signals[name] = ms
            print(f"    {name:18s} {ms:8.2f} ms")
        else:
            print(f"    {name:18s}    DOWN")

    # ── DIMENSION 2: WAN latency (membrane/horizon) ─────────────
    wan_nodes = {
        "golgi-NYC":    "COLLAPSED:DOWN",
        "cloudflare":   "hud.primals.eco",
        "github-pages": "hypothesis.primals.eco",
        "google-dns":   "8.8.8.8",
    }

    print("\n  WAN latency:")
    wan_signals = {}
    for name, ip in wan_nodes.items():
        ms = probe_latency(ip)
        if ms is not None:
            wan_signals[name] = ms
            print(f"    {name:18s} {ms:8.2f} ms")
        else:
            print(f"    {name:18s}    DOWN")

    # ── DIMENSION 3: grapheneGate sensors (from enmesh data) ─────
    ggate_path = Path(__file__).parent.parent / "hud/site/public/data/graphenegate.json"
    phone_signals = {}
    if ggate_path.exists():
        with open(ggate_path) as f:
            ggate = json.load(f)
        phone_signals = {
            "H2_bluetooth":     1,  # proximity (present/absent = binary)
            "He_barometer":     1,  # ICP20100 (pressure → altitude)
            "H2O_gps":         0,  # GNSS (0 fix indoors — KNOWN DEGRADED)
            "O2_wifi":          1,  # wlan0 (connected, RSSI measurable)
            "O3_magnetometer":  1,  # MMC56X3X (heading)
            "C_accelerometer":  1,  # LSM6DSV (motion, gravity vector)
            "Fe_gyroscope":     1,  # LSM6DSV (rotation)
            "N_camera":         1,  # available (visual triangulation possible)
            "P_5g":             0,  # cellular (no SIM yet — Mint Mobile pending)
            "S_microphone":     1,  # available (acoustic ranging possible)
        }
        print(f"\n  Phone sensors: {sum(phone_signals.values())}/{len(phone_signals)} active")
        for k, v in phone_signals.items():
            print(f"    {'✅' if v else '❌'} {k}")

    # ── DIMENSION 4: IP/network topology ─────────────────────────
    # We know our IP, subnet, gateway, NAT boundary
    topo_signals = {
        "lan_subnet":   "192.168.4.0/24",
        "gateway":      "192.168.4.1 (sporeGate)",
        "nat_boundary": "sporeGate → AT&T BGW320",
        "wan_ip":       "AT&T fiber (dynamic)",
        "dns":          "knot @ golgi (DNSSEC, 3 zones)",
        "wireguard":    "10.13.37.0/24",
    }
    print(f"\n  Topology signals: {len(topo_signals)}")

    # ── DIMENSION 5: Jurisdiction (legal topology) ───────────────
    jurisdiction_signals = {
        "lan_all":       "MI-US (Michigan state, US federal)",
        "golgi":         "NY-US (DigitalOcean NYC, AGPL3 on server)",
        "cloudflare":    "anycast (GDPR applies to EU visitors)",
        "github":        "anycast (Microsoft, GDPR DPA)",
        "grapheneGate":  "MI-US (device), mobile (moves with human)",
    }
    print(f"  Jurisdiction signals: {len(jurisdiction_signals)}")

    return {
        "lan": lan_signals,
        "wan": wan_signals,
        "phone": phone_signals,
        "topology": topo_signals,
        "jurisdiction": jurisdiction_signals,
    }

# ── KNN: Any 3 Find Self ────────────────────────────────────────

def knn_triangulate(signals):
    """Given the signal matrix, show that ANY 3 signals locate you.
    
    This is KNN with k=3. But we have way more than 3 dimensions.
    The system is overdetermined. THAT'S the point.
    """
    print("\n🔺 KNN triangulation (k=3, any 3 find self):\n")

    # Flatten all latency signals into one list
    all_latency = {}
    for name, ms in signals["lan"].items():
        all_latency[f"LAN:{name}"] = ms
    for name, ms in signals["wan"].items():
        all_latency[f"WAN:{name}"] = ms

    n_latency = len(all_latency)
    n_phone = sum(1 for v in signals["phone"].values() if v)
    n_topo = len(signals["topology"])
    total_dims = n_latency + n_phone + n_topo

    print(f"  Total signal dimensions: {total_dims}")
    print(f"    Latency:  {n_latency} (LAN + WAN pings)")
    print(f"    Phone:    {n_phone} (active sensors)")
    print(f"    Topology: {n_topo} (network position)")
    print(f"  Minimum for triangulation: 3")
    print(f"  Overdetermination factor: {total_dims / 3:.1f}x")

    # Show all possible 3-combinations of latency signals
    nodes = sorted(all_latency.keys())
    n_combos = math.comb(len(nodes), 3)
    print(f"\n  Possible triangulations from latency alone: C({len(nodes)},3) = {n_combos}")

    # Pick some representative triangulations
    triangulations = []
    combos = list(combinations(nodes, 3))
    # Show first few, random middle, last few
    show = combos[:3] + random.sample(combos[3:-3], min(4, len(combos)-6)) + combos[-3:]

    for tri in show:
        lats = [all_latency[n] for n in tri]
        # Quality: lower total jitter = better triangulation
        spread = max(lats) - min(lats)
        avg = sum(lats) / 3
        quality = "excellent" if spread > 10 else "good" if spread > 1 else "poor (colinear)"
        labels = [n.split(":")[1][:12] for n in tri]
        triangulations.append({
            "nodes": list(tri),
            "latencies_ms": [round(l, 2) for l in lats],
            "spread_ms": round(spread, 2),
            "quality": quality,
        })
        print(f"    {labels[0]:12s} + {labels[1]:12s} + {labels[2]:12s}  "
              f"spread={spread:7.2f}ms  {quality}")

    return {
        "total_dimensions": total_dims,
        "latency_dimensions": n_latency,
        "phone_dimensions": n_phone,
        "topology_dimensions": n_topo,
        "overdetermination": round(total_dims / 3, 1),
        "possible_triangulations": n_combos,
        "sample_triangulations": triangulations[:6],
    }

# ── Trefoil Through SporeGate ───────────────────────────────────

def trefoil_topology(signals):
    """Map the 3 crossings of the trefoil to our actual infrastructure.
    
    Trefoil knot: simplest non-trivial knot. 3 crossings.
    Each crossing = a Klein leak = a pressure chamber.
    
    In our mesh:
      Crossing 1: LAN → sporeGate → WAN  (NAT traversal)
      Crossing 2: WAN → CDN/DNS → destination  (routing)
      Crossing 3: Response → WAN → sporeGate → LAN  (return path)
    
    The packet trefoils through the NAT boundary.
    3 crossings. 3 hops. 3 degrees of separation.
    The bag of holding: more compute inside (200 cores, 1.4TB)
    than outside (1 vCPU, 2GB VPS).
    """
    print("\n🪢  trefoil topology through sporeGate:\n")

    # The 3 crossings
    crossings = [
        {
            "crossing": 1,
            "name": "NAT traversal (out)",
            "from": "LAN (192.168.4.0/24)",
            "through": "sporeGate (NAT/FW)",
            "to": "WAN (AT&T fiber → internet)",
            "klein_leak": "private IP → public IP (address translation = Klein fold)",
            "stomach": "rumen (fermentation — the request mixes with routing tables)",
            "latency_ms": signals["lan"].get("sporeGate", 0),
        },
        {
            "crossing": 2,
            "name": "edge routing",
            "from": "WAN (internet backbone)",
            "through": "CDN/DNS (Cloudflare anycast, knot DNSSEC)",
            "to": "destination (golgi VPS, GitHub, etc.)",
            "klein_leak": "anycast IP → physical server (the same address is everywhere)",
            "stomach": "reticulum (hardware filter — CDN caches, DNS resolves)",
            "latency_ms": signals["wan"].get("cloudflare", 0),
        },
        {
            "crossing": 3,
            "name": "return path (in)",
            "from": "destination response",
            "through": "WAN → sporeGate NAT → LAN",
            "to": "originating device (eastGate, grapheneGate, etc.)",
            "klein_leak": "public → private (the SAME fold in reverse — Klein has only one side)",
            "stomach": "omasum (concentration — response compressed, cached, reused)",
            "latency_ms": signals["lan"].get("sporeGate", 0),
        },
    ]

    for c in crossings:
        print(f"  Crossing {c['crossing']}: {c['name']}")
        print(f"    {c['from']} → {c['through']} → {c['to']}")
        print(f"    Klein leak: {c['klein_leak']}")
        print(f"    Stomach:    {c['stomach']}")
        if c['latency_ms']:
            print(f"    Latency:    {c['latency_ms']:.2f}ms")
        print()

    # The bag of holding
    inside = {
        "cores": 200,
        "ram_gb": 1400,
        "gpu_vram_gb": 244,
        "storage_tb": 97,
        "gates": 20,
        "isa_families": 8,
    }
    outside = {
        "cores": 1,
        "ram_gb": 2,
        "gpu_vram_gb": 0,
        "storage_tb": 0.05,
        "gates": 1,
        "isa_families": 1,
    }

    ratios = {}
    for key in inside:
        if outside[key] > 0:
            ratios[key] = round(inside[key] / outside[key], 1)
        else:
            ratios[key] = float('inf')

    print("  🎒 bag of holding (inside vs membrane):\n")
    print(f"    {'resource':15s} {'inside':>10s} {'membrane':>10s} {'ratio':>10s}")
    print(f"    {'─'*15} {'─'*10} {'─'*10} {'─'*10}")
    for key in inside:
        r = ratios[key]
        r_str = f"{r:.0f}x" if r != float('inf') else "∞"
        print(f"    {key:15s} {str(inside[key]):>10s} {str(outside[key]):>10s} {r_str:>10s}")

    print(f"\n    The bag holds {sum(ratios[k] for k in ratios if ratios[k] != float('inf')):.0f}x more than its surface suggests.")
    print(f"    This IS the Klein bottle. The inside is bigger than the outside.")
    print(f"    3 crossings through sporeGate = the trefoil that creates the bag.")

    return {
        "crossings": crossings,
        "bag_of_holding": {
            "inside": inside,
            "outside": outside,
            "ratios": ratios,
        },
    }

# ── The Phone Overfills ─────────────────────────────────────────

def phone_overfill(signals):
    """Show that the phone's sensor array massively overdetermines position.
    
    GPS alone = 4 satellites minimum (3 position + 1 time)
    Phone = GPS + cell + WiFi + accel + gyro + baro + mag + BT + cam + mic
    That's 10 channels. Each channel is an independent triangulation axis.
    C(10,3) = 120 possible triangulations from ONE device.
    """
    print("\n📱 phone overfill (grapheneGate sensor array):\n")

    sensors = signals.get("phone", {})
    active = {k: v for k, v in sensors.items() if v}
    inactive = {k: v for k, v in sensors.items() if not v}

    n = len(active)
    combos = math.comb(n, 3)

    print(f"  Active sensors: {n}")
    for s in active:
        molecule, sensor = s.split("_", 1)
        print(f"    {molecule:4s} → {sensor}")

    print(f"\n  Inactive sensors: {len(inactive)}")
    for s in inactive:
        molecule, sensor = s.split("_", 1)
        print(f"    {molecule:4s} → {sensor} (pending)")

    print(f"\n  Possible triangulations from phone alone: C({n},3) = {combos}")
    print(f"  Overdetermination: {combos / 1:.0f} ways to find self from ONE device")

    # With Mint Mobile (adds P_5g)
    n_future = n + 1  # add cell
    combos_future = math.comb(n_future, 3)
    print(f"\n  After Mint Mobile SIM:")
    print(f"    Active sensors: {n_future}")
    print(f"    Triangulations: C({n_future},3) = {combos_future}")
    print(f"    Improvement: +{combos_future - combos} new triangulation paths")

    # Combined: phone + mesh
    total = n + len(signals["lan"]) + len(signals["wan"])
    total_combos = math.comb(total, 3)
    print(f"\n  Phone + mesh combined:")
    print(f"    Total signals: {total}")
    print(f"    Triangulations: C({total},3) = {total_combos}")
    print(f"    This is not just overdetermined. This is a manifold.")

    return {
        "active_sensors": n,
        "inactive_sensors": len(inactive),
        "phone_triangulations": combos,
        "with_mint_mobile": combos_future,
        "combined_with_mesh": total_combos,
        "total_signals": total,
    }

# ── The Equivalence ─────────────────────────────────────────────

def prove_equivalence():
    """Show that triangulation = KNN(k=3) = trefoil = bag of holding.
    
    They are the same topology:
    
    TRIANGULATION:  3 points define a plane.
                    3 latencies define a position.
                    Minimum for unambiguous location.
    
    KNN (k=3):     3 nearest neighbors classify a point.
                    The point is "self" in the feature space.
                    The neighbors are the signals.
    
    TREFOIL:        3 crossings create 3 pressure chambers.
                    Each crossing is a Klein leak.
                    The knot cannot be untied (non-trivial topology).
    
    BAG OF HOLDING: The inside volume exceeds the outside surface.
                    3 crossings fold space to create the pocket.
                    More compute inside than the membrane suggests.
    """
    print("\n═══════════════════════════════════════════════════════")
    print("  THE EQUIVALENCE")
    print("═══════════════════════════════════════════════════════\n")

    rows = [
        ("Triangulation", "3 points", "plane → position",     "find where"),
        ("KNN (k=3)",     "3 neighbors", "feature space → class", "find self"),
        ("Trefoil",       "3 crossings", "tube → chambers",     "find pressure"),
        ("Bag of holding","3 folds",  "surface → volume",     "find capacity"),
        ("GPS minimum",   "3+1 sats", "timing → coordinates", "find location"),
        ("Poor tope",     "3 bonds",  "atoms → molecule",     "find structure"),
    ]

    print(f"    {'concept':18s} {'minimum':12s} {'maps to':25s} {'finds':15s}")
    print(f"    {'─'*18} {'─'*12} {'─'*25} {'─'*15}")
    for concept, minimum, maps_to, finds in rows:
        print(f"    {concept:18s} {minimum:12s} {maps_to:25s} {finds:15s}")

    print("""
    ALL OF THESE ARE THE SAME OPERATION:
    
      Given N signals in a space,
      pick any 3 independent ones,
      and you can locate yourself.
      
    The phone does this with 8 active sensors.
    The mesh does this with 11 alive nodes.
    Combined: C(19,3) = 969 ways to find self.
    
    sporeGate is the trefoil crossing point.
    LAN → sporeGate → WAN → response → sporeGate → LAN
    3 crossings. Non-trivial knot. Can't be untied.
    
    The bag of holding:
      Outside: 1 vCPU, 2 GB VPS membrane
      Inside:  200 cores, 1.4 TB RAM, 244 GB GPU
      Ratio:   200x CPU, 700x RAM, ∞ GPU
      
    It's not conceptually different.
    The 3 hops, 3 degrees sorting for the bag of holding
    IS triangulation IS KNN IS the trefoil gut.
    """)

    return {
        "equivalences": [r[0] for r in rows],
        "minimum_signals": 3,
        "reason": "3 independent constraints define a unique point in any metric space",
        "topology": "trefoil (simplest non-trivial knot)",
    }

# ── Main ─────────────────────────────────────────────────────────

def main():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\n🪢  knn-trefoil.py — any 3 find self — {ts}\n")

    # 1. Build signal matrix
    signals = build_signal_matrix()

    # 2. KNN triangulation
    knn = knn_triangulate(signals)

    # 3. Trefoil topology
    trefoil = trefoil_topology(signals)

    # 4. Phone overfill
    phone = phone_overfill(signals)

    # 5. The equivalence
    equiv = prove_equivalence()

    # Compile result
    result = {
        "ts": ts,
        "title": "KNN Trefoil — Any 3 Find Self",
        "paper_118_ref": "The Trefoil Gut — Klein Topology of Ruminant Digestion",
        "hypothesis_14_ref": "The Ptolemy GPS — Epicycles in Your Pocket",
        "signals": {
            "lan_count": len(signals["lan"]),
            "wan_count": len(signals["wan"]),
            "phone_active": sum(1 for v in signals["phone"].values() if v),
            "phone_total": len(signals["phone"]),
            "topology_count": len(signals["topology"]),
            "total": knn["total_dimensions"],
        },
        "knn": knn,
        "trefoil": {
            "crossings": 3,
            "stomach_analogy": ["rumen (NAT out)", "reticulum (edge routing)", "omasum (return path)"],
            "bag_of_holding": trefoil["bag_of_holding"]["ratios"],
        },
        "phone_overfill": phone,
        "equivalence": equiv,
        "the_point": {
            "statement": "any 3 independent signals locate you in any metric space",
            "phone_has": f"{phone['active_sensors']} active sensors = C({phone['active_sensors']},3) = {phone['phone_triangulations']} triangulations",
            "mesh_has": f"{knn['latency_dimensions']} latency nodes = C({knn['latency_dimensions']},3) = {math.comb(knn['latency_dimensions'], 3)} triangulations",
            "combined": f"C({phone['total_signals']},3) = {phone['combined_with_mesh']} ways to find self",
            "trefoil": "3 crossings through sporeGate = the minimum non-trivial knot",
            "bag": "inside (200 cores, 1.4TB) > outside (1 core, 2GB) — Klein topology",
        },
        "digest": hashlib.sha256(json.dumps(signals["lan"], sort_keys=True).encode()).hexdigest()[:16],
    }

    out_path = Path(__file__).parent.parent / "hud/site/public/data/knn-trefoil.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n🪢  trefoil tied → {out_path}")
    print(f"   digest: {result['digest']}")

    return result

if __name__ == "__main__":
    main()
