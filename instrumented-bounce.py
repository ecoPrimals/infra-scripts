#!/usr/bin/env python3
"""instrumented-bounce.py — galactic bounce using σ, uncanny valley, DK for v/a."""
import json, math, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "hud" / "site" / "public" / "data"

def sigmoid(x, mid=0.45, steep=6.0):
    z = max(-500, min(500, steep * (x - mid)))
    return 1.0 / (1.0 + math.exp(-z))

def anti_sigmoid(x, A=0.6, mu=0.85, width=0.08):
    s = sigmoid(x)
    return max(0.0, s - A * math.exp(-((x - mu) ** 2) / (2 * width ** 2)))

def dunning_kruger(c):
    c = max(0.0, min(1.0, c))
    mount = 0.85 * math.exp(-((c - 0.18) ** 2) / (2 * 0.07 ** 2))
    valley = 0.35 * math.exp(-((c - 0.42) ** 2) / (2 * 0.08 ** 2))
    slope = 0.15 + 0.85 * sigmoid(c, mid=0.55, steep=6)
    return max(0.05, min(1.0, slope + mount - valley - 0.2))

def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    cayley = json.loads((DATA / "galactic-cayley-bounce.json").read_text())
    kh = cayley["kingdom_health"]
    bump = 0.04
    if (DATA / "chew-dirt-mold.json").exists():
        kh["fungi"]["health_score"] = min(1.0, kh["fungi"]["health_score"] + bump)
    instruments = {}
    for name, h in kh.items():
        x = h["health_score"]
        s = sigmoid(x)
        uv = anti_sigmoid(x)
        competence = 1.0 if h.get("classified") else min(0.35, x * 0.5)
        if name == "fungi":
            competence = min(0.45, 0.12 + bump * 2)
        conf = dunning_kruger(competence)
        gap = conf - competence
        v = s * (1 - s) * 8
        unc = s - uv
        a = v * (0.5 - unc) - 0.3 * abs(gap)
        instruments[name] = {
            "health": round(x, 4), "sigma": round(s, 4), "anti_sigma_comfort": round(uv, 4),
            "uncanny_depth": round(unc, 4), "competence": round(competence, 4),
            "dk_confidence": round(conf, 4), "dk_gap": round(gap, 4),
            "velocity": round(v, 4), "acceleration": round(a, 4),
            "classified": h.get("classified", False),
        }
    path = ["animalia", "plantae", "fungi", "bacteria", "archaea", "protista", "animalia"]
    hops, total = [], 0.0
    for i in range(len(path) - 1):
        ia, ib = instruments[path[i]], instruments[path[i + 1]]
        unc = 0.5 * (ia["uncanny_depth"] + ib["uncanny_depth"])
        dkg = 0.5 * (abs(ia["dk_gap"]) + abs(ib["dk_gap"]))
        E = ia["sigma"] * ib["sigma"] * (1 - min(0.9, unc)) * (1 - 0.5 * min(1.0, dkg))
        hops.append({"from": path[i], "to": path[i + 1], "energy": round(E, 5),
                     "hop_velocity": round(0.5 * (ia["velocity"] + ib["velocity"]), 4),
                     "hop_acceleration": round(ib["velocity"] - ia["velocity"], 4)})
        total += E
    out = {
        "ts": now.isoformat(), "wave": 200, "type": "galactic-bounce-sort-live",
        "new_efficiency_pct": round(total / 6.0 * 100, 2),
        "total_energy": round(total, 5),
        "kingdom_instruments": instruments,
        "bounce_path": hops,
        "cron": True,
    }
    (DATA / "galactic-bounce-sort-live.json").write_text(json.dumps(out, indent=2))
    print(f"bounce efficiency={out['new_efficiency_pct']}%")

if __name__ == "__main__":
    main()
