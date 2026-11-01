#!/usr/bin/env bash
# immune-activate.sh — turn ON the immune system
# Bone marrow (Caddy log) → Thymus (3-stage selection) → B cells (mark) → T cells (act)
# Cron: */7 * * * *  (Saturn/kidney rhythm)
set -euo pipefail

REPO="${1:-/home/eastgate/Development/ecoPrimals}"
DATA="${REPO}/infra/hud/site/public/data"
LOG="${REPO}/membrane/local-terminal/remote/immune.log"
ANTIBODY_STORE="${REPO}/membrane/local-terminal/remote/antibodies-live.json"
IMMUNE_STATE="${DATA}/immune-state-live.json"
IDENTITY="${DATA}/identity-melt.json"

mkdir -p "$(dirname "$LOG")" "$(dirname "$ANTIBODY_STORE")"

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[$TS] immune-activate start" >> "$LOG"

MARROW_FILE=$(mktemp)
# GOLGI DOWN — caddy logs now local via Dromedary
echo "[]" > "$MARROW_FILE" 2>/dev/null || true

python3 - "$DATA" "$ANTIBODY_STORE" "$IMMUNE_STATE" "$IDENTITY" "$MARROW_FILE" << 'IMMUNE'
import json, hashlib, sys, re, os, fnmatch, time
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timezone

DATA = Path(sys.argv[1])
ANTIBODY_PATH = Path(sys.argv[2])
IMMUNE_STATE_PATH = Path(sys.argv[3])
IDENTITY_PATH = Path(sys.argv[4])
MARROW_FILE = Path(sys.argv[5])

ts = datetime.now(timezone.utc).isoformat()

# ═══════════════════════════════════════════════════════════════
# WILDCARD SELECTION TABLE — pattern → verdict → /suffix output
# ═══════════════════════════════════════════════════════════════
# Each rule: (glob_on_UA, glob_on_URI, verdict, /suffix_route)
# First match wins. Wildcards use fnmatch glob syntax.
# "*" alone = catch-all. Evaluated top to bottom.
#
# THREE SELECTIONS (real thymus biology):
#   1. NEGATIVE — does it attack self? kill it
#   2. POSITIVE — can it bind MHC (match ANYTHING)? if not → null → apoptosis
#   3. ROUTING  — survivors get a /suffix destination
#
# The /suffix IS the immune response. Not a label. A route.

SELECTION_TABLE = [
    # ── NEGATIVE SELECTION: attack self → kill (403 / scatter) ──
    # AI scrapers: training on us without consent
    ("*GPTBot*",              "*",              "non_self",   "/scatter"),
    ("*CCBot*",               "*",              "non_self",   "/scatter"),
    ("*ClaudeBot*",           "*",              "non_self",   "/scatter"),
    ("*anthropic*",           "*",              "non_self",   "/scatter"),
    ("*Meta-ExternalAgent*",  "*",              "non_self",   "/scatter"),
    ("*Amazonbot*",           "*",              "non_self",   "/scatter"),
    ("*bytespider*",          "*",              "non_self",   "/scatter"),
    ("*PetalBot*",            "*",              "non_self",   "/scatter"),
    # SEO farms: parasitic indexing
    ("*AhrefsBot*",           "*",              "non_self",   "/403"),
    ("*SemrushBot*",          "*",              "non_self",   "/403"),
    ("*MJ12bot*",             "*",              "non_self",   "/403"),
    ("*DotBot*",              "*",              "non_self",   "/403"),
    # Attack tools: scanning for vulnerabilities
    ("*masscan*",             "*",              "non_self",   "/blackhole"),
    ("*zgrab*",               "*",              "non_self",   "/blackhole"),
    ("*censys*",              "*",              "non_self",   "/blackhole"),
    ("*Nmap*",                "*",              "non_self",   "/blackhole"),
    ("*Scrapy*",              "*",              "non_self",   "/403"),
    ("*python-requests*",     "*",              "non_self",   "/403"),
    ("*Go-http-client*",      "*",              "non_self",   "/403"),
    # Attack URIs: regardless of UA (probing known vulns)
    ("*",                     "*wp-admin*",     "non_self",   "/blackhole"),
    ("*",                     "*phpmyadmin*",   "non_self",   "/blackhole"),
    ("*",                     "*.env*",         "non_self",   "/blackhole"),
    ("*",                     "*xmlrpc*",       "non_self",   "/blackhole"),
    ("*",                     "*/wp-*",         "non_self",   "/blackhole"),
    ("*",                     "*/.git*",        "non_self",   "/blackhole"),
    ("*",                     "*/admin*",       "non_self",   "/blackhole"),
    ("*",                     "*passwd*",       "non_self",   "/blackhole"),
    ("*",                     "*/shell*",       "non_self",   "/blackhole"),

    # ── POSITIVE SELECTION: can bind MHC → sort by type ──
    # Search engines: organic, beneficial (index us properly)
    ("*Googlebot*",           "*",              "organic",    "/sitemap"),
    ("*bingbot*",             "*",              "organic",    "/sitemap"),
    ("*DuckDuckBot*",         "*",              "organic",    "/sitemap"),
    ("*Baiduspider*",         "*",              "organic",    "/sitemap"),
    ("*YandexBot*",           "*",              "organic",    "/sitemap"),
    ("*Applebot*",            "*",              "organic",    "/sitemap"),

    # Fediverse: organic peers
    ("*Mastodon*",            "*",              "organic",    "/webfinger"),
    ("*ActivityPub*",         "*",              "organic",    "/webfinger"),
    ("*Pleroma*",             "*",              "organic",    "/webfinger"),

    # RSS readers: organic subscribers
    ("*RSS*",                 "*",              "organic",    "/feed"),
    ("*Feedly*",              "*",              "organic",    "/feed"),
    ("*Miniflux*",            "*",              "organic",    "/feed"),
    ("*NetNewsWire*",         "*",              "organic",    "/feed"),
    ("*Thunderbird*",         "*",              "organic",    "/feed"),

    # Self: our own tools
    ("*curl*",                "*/touch*",       "self",       "/self"),
    ("*curl*",                "*/heartbeat*",   "self",       "/self"),
    ("*curl*",                "*/drain*",       "self",       "/self"),
    ("*curl*",                "*",              "self",       "/self"),
    ("*ecoPrimal*",           "*",              "self",       "/self"),
    ("*wget*",                "*",              "self",       "/self"),
    ("*HTTPie*",              "*",              "self",       "/self"),

    # Human browsers: real visitors — the ones we exist for
    ("*Mozilla/5.0*Chrome*",  "*",              "human",      "/"),
    ("*Mozilla/5.0*Firefox*", "*",              "human",      "/"),
    ("*Mozilla/5.0*Safari*",  "*",              "human",      "/"),
    ("*Mozilla/5.0*Edge*",    "*",              "human",      "/"),
    ("*Mozilla/5.0*Mobile*",  "*",              "human",      "/mobile"),
    ("*Mozilla/5.0*iPhone*",  "*",              "human",      "/mobile"),
    ("*Mozilla/5.0*Android*", "*",              "human",      "/mobile"),
    ("*Mozilla/5.0*",         "*",              "human",      "/"),

    # ── NULL SELECTION: binds nothing → apoptosis ──
    # Empty UA: ghost request, no identity at all
    ("",                      "*",              "null",       "/204"),
    # Catch-all: unknown UA that matched nothing above
    ("*",                     "*",              "partial",    "/classify"),
]

# ═══════════════════════════════════════════════
# SELF-TOLERANCE — enhanced self-antigen library
# ═══════════════════════════════════════════════
# These are the organism's OWN antigens (MHC molecules)
# The thymus uses these for positive selection training:
# "T cells that can bind self-MHC survive. Those that can't → apoptosis."
SELF_TOLERANCE = {
    "domains": ["primals.eco", "nestgate.io", "primal.eco", "connect.primals.eco", "hud.primals.eco"],
    "gates": ["eastgate", "graftgate", "bluegate", "southgate", "irongate"],
    "identifiers": ["ecoPrimal", "ecoPrimals", "ORCID:0009-0004-2141-0321"],
    "infrastructure": ["cloudflared", "caddy", "cron", "systemd", "wireguard"],
    "primals": ["skunkBat", "songBird", "bearDog", "squirrel", "nestGate",
                "rhizoCrypt", "sweetGrass", "loamSpine", "coralReef",
                "barraCuda", "toadStool", "sourDough", "swarmVine",
                "bingoCube", "biomeOS", "petalTongue"],
    "springs": ["hotSpring", "wetSpring", "groundSpring", "airSpring",
                "neuralSpring", "healthSpring", "ludoSpring"],
    "nerve_endings": ["ntfy.sh/primals-", "membrane", "neutrino", "campfire", "csf"],
    "pi_identity": {
        "remainder": 0.14159265358979,
        "sort_rate": 0.31830988618,
        "fold": "Klein",
        "heartbeat": "3m/7m"
    }
}

# ── Load identity-melt additions ──
if IDENTITY_PATH.exists():
    try:
        identity = json.loads(IDENTITY_PATH.read_text())
        for group in identity.get("all_social_handles", {}).values():
            if isinstance(group, list):
                for item in group:
                    if isinstance(item, dict) and item.get("handle"):
                        SELF_TOLERANCE.setdefault("melted", []).append(item["handle"])
    except Exception:
        pass

# ── Load existing antibodies ──
antibodies = {}
if ANTIBODY_PATH.exists():
    try:
        antibodies = json.loads(ANTIBODY_PATH.read_text())
    except (json.JSONDecodeError, IOError):
        antibodies = {}

# ═══════════════════════════════════════════════
# BONE MARROW — parse Caddy access log into stem cells
# ═══════════════════════════════════════════════
stem_cells = []
seen_keys = set()

if MARROW_FILE.exists():
    for line in MARROW_FILE.read_text().strip().split('\n'):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            req = entry.get("request", {})
            hdrs = req.get("headers", {})
            ua = ""
            if "User-Agent" in hdrs:
                ua_list = hdrs["User-Agent"]
                ua = ua_list[0] if ua_list else ""

            cell = {
                "method": req.get("method", "?"),
                "uri": req.get("uri", "/"),
                "host": req.get("host", "?"),
                "status": entry.get("status", 0),
                "user_agent": ua,
                "remote_ip": req.get("remote_ip", "?"),
                "ts": entry.get("ts", 0),
                "size": entry.get("size", 0),
                "duration": entry.get("duration", 0),
            }

            dedup = f"{cell['remote_ip']}:{cell['ts']}"
            if dedup not in seen_keys:
                seen_keys.add(dedup)
                stem_cells.append(cell)
        except (json.JSONDecodeError, KeyError):
            continue

print(f"BONE MARROW: {len(stem_cells)} stem cells")

# ═══════════════════════════════════════════════
# THYMUS — 3-stage selection with wildcard→/suffix
# ═══════════════════════════════════════════════

classified = Counter()
routes = Counter()
verdicts = []
null_apoptosis = 0

for cell in stem_cells:
    ua = cell.get("user_agent", "")
    uri = cell.get("uri", "")

    verdict = None
    suffix = None
    matched_rule = None

    # Walk the selection table — first match wins
    for (ua_glob, uri_glob, v, s) in SELECTION_TABLE:
        ua_match = fnmatch.fnmatch(ua, ua_glob) if ua_glob else (ua == "")
        uri_match = fnmatch.fnmatch(uri, uri_glob)

        if ua_match and uri_match:
            verdict = v
            suffix = s
            matched_rule = f"{ua_glob} + {uri_glob}"
            break

    # NULL SELECTION: cells that bind NOTHING → apoptosis
    # In real thymus: T cells that can't bind any MHC molecule die
    if verdict is None:
        verdict = "null"
        suffix = "/204"
        matched_rule = "NULL SELECTION (no rule matched)"
        null_apoptosis += 1

    classified[verdict] += 1
    routes[suffix] += 1
    verdicts.append({
        "cell": cell,
        "verdict": verdict,
        "suffix": suffix,
        "rule": matched_rule,
        "ua_sample": ua[:60],
    })

total = sum(classified.values())
cls = dict(classified.most_common())
rts = dict(routes.most_common())

print(f"THYMUS: {total} cells → {cls}")
print(f"  routes: {rts}")
if null_apoptosis:
    print(f"  NULL SELECTION: {null_apoptosis} cells → apoptosis (matched nothing)")

# ═══════════════════════════════════════════════
# T CELLS — execute verdicts
# ═══════════════════════════════════════════════

t_cells = {
    "CD8_kills": 0,       # direct kill (non_self → 403/scatter/blackhole)
    "CD4_alerts": 0,      # helper signal (fire to ntfy)
    "T_reg_dampens": 0,   # suppress overreaction
    "null_apoptosis": null_apoptosis,  # cells that matched nothing → dead
}
new_threats = []

for v in verdicts:
    if v["verdict"] == "non_self":
        t_cells["CD8_kills"] += 1
        t_cells["CD4_alerts"] += 1

        # Extract threat pattern from the rule
        rule = v.get("rule", "")
        ua_pat = rule.split(" + ")[0].strip("*") if " + " in rule else ""
        if ua_pat and ua_pat not in antibodies:
            new_threats.append(ua_pat)

# T_reg: autoimmune check
if total > 5 and t_cells["CD8_kills"] / total > 0.6:
    t_cells["T_reg_dampens"] += 1
    print("T_REG: dampening — possible autoimmune (>60% kills)")

print(f"T CELLS: {t_cells}")
if new_threats:
    print(f"  NEW THREATS: {list(set(new_threats))}")

# ═══════════════════════════════════════════════
# B CELLS — antibody factory + decay + memory
# ═══════════════════════════════════════════════

for v in verdicts:
    if v["verdict"] == "non_self":
        rule = v.get("rule", "")
        ua_pat = rule.split(" + ")[0].strip("*") if " + " in rule else ""
        if not ua_pat:
            continue

        if ua_pat not in antibodies:
            antibodies[ua_pat] = {
                "pattern": ua_pat,
                "confidence": 0.5,
                "encounters": 1,
                "first_seen": ts,
                "last_seen": ts,
                "posture": "MONITOR",
                "cell_type": "naive_B",
                "route": v["suffix"],
            }
        else:
            ab = antibodies[ua_pat]
            ab["encounters"] = ab.get("encounters", 0) + 1
            ab["last_seen"] = ts
            ab["confidence"] = min(0.99, ab.get("confidence", 0.5) + 0.05)

            enc = ab["encounters"]
            if enc >= 10:
                ab["cell_type"] = "memory_B"
                ab["confidence"] = max(ab["confidence"], 0.3)
            elif enc >= 3:
                ab["cell_type"] = "plasma_B"
                ab["confidence"] = max(ab["confidence"], 0.90)

# ═══════════════════════════════════════════════
# DECAY + WHALE-FALL + CANCER DETECTION
# ═══════════════════════════════════════════════
# Decay = dying. dying has TWO fates:
#   whale-fall (proper death → feeds ecosystem)
#   cancer (failed death → zombie proliferates)

FOSSIL_PATH = DATA / "immune-fossils.json"
fossils = []
if FOSSIL_PATH.exists():
    try:
        fossils = json.loads(FOSSIL_PATH.read_text())
    except (json.JSONDecodeError, IOError):
        fossils = []

pruned = []
whale_falls = []
zombies_killed = []
autoimmune_purged = []

for pat, ab in list(antibodies.items()):
    ab["confidence"] = round(ab.get("confidence", 0.5) * 0.995, 4)

    # ── CANCER CHECK 1: zombie scan ──
    # confidence < 0.01 but still in table = zombie (should be dead, isn't)
    if ab["confidence"] < 0.01 and ab.get("cell_type") != "memory_B":
        zombies_killed.append(pat)
        pruned.append(pat)
        continue

    # ── CANCER CHECK 2: autoimmune scan ──
    # antibody matching self patterns = attacking self = tumor
    for self_pat in SELF_TOLERANCE.get("domains", []) + SELF_TOLERANCE.get("primals", []):
        if self_pat.lower() in ab.get("pattern", "").lower():
            autoimmune_purged.append(pat)
            pruned.append(pat)
            break

    # ── Normal death threshold → WHALE-FALL ──
    if ab["confidence"] < 0.05 and ab.get("cell_type") != "memory_B":
        # WHALE-FALL: don't just delete. HARVEST the dying cell.
        fossil = {
            "pattern": ab["pattern"],
            "lived": f"{ab.get('first_seen', '?')} → {ab.get('last_seen', '?')}",
            "encounters": ab.get("encounters", 0),
            "peak_confidence": ab.get("encounters", 0) * 0.05 + 0.5,  # estimated peak
            "cell_type_at_death": ab.get("cell_type", "?"),
            "route_when_alive": ab.get("route", "?"),
            "cause_of_death": "decay (natural aging — no encounters)",
            "whale_fall_ts": ts,
            "nutrients": {
                "pattern_knowledge": ab["pattern"],
                "encounter_history": ab.get("encounters", 0),
                "false_positive_risk": "low" if ab.get("encounters", 0) > 3 else "unknown",
            }
        }
        whale_falls.append(fossil)
        fossils.append(fossil)
        pruned.append(pat)

for pat in pruned:
    if pat in antibodies:
        del antibodies[pat]

# ── CANCER CHECK 3: metastasis (duplicate patterns) ──
seen_pats = {}
merged = 0
for pat, ab in list(antibodies.items()):
    core = ab["pattern"].lower().strip("*")
    if core in seen_pats:
        # Duplicate! Merge into the older one (kill the tumor copy)
        original = seen_pats[core]
        antibodies[original]["encounters"] += ab.get("encounters", 0)
        antibodies[original]["confidence"] = max(antibodies[original]["confidence"], ab["confidence"])
        del antibodies[pat]
        merged += 1
    else:
        seen_pats[core] = pat

# ── CANCER CHECK 4: resource audit (antibody overgrowth) ──
tumor_growth = False
known_threats = len(NON_SELF_UA) if 'NON_SELF_UA' in dir() else 20
if len(antibodies) > 3 * known_threats:
    tumor_growth = True
    # Mass prune lowest confidence (surgery)
    sorted_abs = sorted(antibodies.items(), key=lambda x: x[1].get("confidence", 0))
    to_cut = len(antibodies) - known_threats * 2  # cut back to 2× threats
    for pat, ab in sorted_abs[:to_cut]:
        if ab.get("cell_type") != "memory_B":
            whale_falls.append({
                "pattern": ab["pattern"],
                "cause_of_death": "tumor surgery (resource overgrowth)",
                "whale_fall_ts": ts,
            })
            del antibodies[pat]

# ── CANCER CHECK 5: null escape audit ──
null_escapes = sum(1 for v in verdicts if v["verdict"] == "null" and v["suffix"] != "/204")

# ── Persist antibodies (atomic write for necrosis prevention) ──
tmp_path = ANTIBODY_PATH.with_suffix('.tmp')
tmp_path.write_text(json.dumps(antibodies, indent=2))
tmp_path.rename(ANTIBODY_PATH)

# ── Persist fossils (cap at 500 — oldest fall off the reef) ──
fossils = fossils[-500:]
FOSSIL_PATH.write_text(json.dumps(fossils, indent=2))

# ── Null whale-fall: even null cells feed the fossil record ──
for v in verdicts:
    if v["verdict"] == "null":
        fossils.append({
            "pattern": v.get("ua_sample", "empty"),
            "cause_of_death": "null selection (bound nothing)",
            "uri": v["cell"].get("uri", "?"),
            "whale_fall_ts": ts,
        })

FOSSIL_PATH.write_text(json.dumps(fossils[-500:], indent=2))

b_summary = {
    "total": len(antibodies),
    "naive": sum(1 for a in antibodies.values() if a.get("cell_type") == "naive_B"),
    "plasma": sum(1 for a in antibodies.values() if a.get("cell_type") == "plasma_B"),
    "memory": sum(1 for a in antibodies.values() if a.get("cell_type") == "memory_B"),
    "pruned": len(pruned),
    "whale_falls": len(whale_falls),
    "zombies_killed": len(zombies_killed),
    "autoimmune_purged": len(autoimmune_purged),
    "null_escapes": null_escapes,
    "tumor_growth": tumor_growth,
    "merged_duplicates": merged,
    "fossils_total": len(fossils),
}
print(f"B CELLS: {b_summary}")
if zombies_killed:
    print(f"  CANCER: {len(zombies_killed)} zombies killed (should have been dead)")
if autoimmune_purged:
    print(f"  AUTOIMMUNE: {len(autoimmune_purged)} self-attackers purged")
if whale_falls:
    print(f"  WHALE-FALL: {len(whale_falls)} proper deaths → fossil record")
if null_escapes:
    print(f"  NULL ESCAPE: {null_escapes} cells got through without dying — CANCER RISK")

# ═══════════════════════════════════════════════
# MAGISTRATE — sentencing + route table
# ═══════════════════════════════════════════════

magistrate = {
    "acquitted": classified.get("self", 0) + classified.get("human", 0) + classified.get("organic", 0),
    "guilty": classified.get("non_self", 0),
    "remanded": classified.get("partial", 0),
    "apoptosis": classified.get("null", 0),
    "route_table": rts,
    "gavel": {
        "/":          "200 — acquit (human visitor, full site)",
        "/mobile":    "200 — acquit (human mobile)",
        "/self":      "200 — acquit (internal tool, dashboard)",
        "/sitemap":   "200 — organic (search engine, give XML)",
        "/webfinger": "200 — organic (fediverse peer, give JRD)",
        "/feed":      "200 — organic (RSS subscriber, give Atom)",
        "/classify":  "200 — partial (unknown, serve + study)",
        "/scatter":   "403 — guilty (scraper, serve fake data)",
        "/403":       "403 — guilty (parasite, block)",
        "/blackhole": "444 — guilty (attacker, drop connection)",
        "/204":       "204 — null selection (no content, apoptosis)",
    }
}

# ═══════════════════════════════════════════════
# IMMUNE STATE — write live
# ═══════════════════════════════════════════════

immune_ratio = (classified.get("self", 0) + classified.get("human", 0)) / max(total, 1)
threat_ratio = classified.get("non_self", 0) / max(total, 1)

health = "STRONG"
if threat_ratio > 0.6:
    health = "SEPTIC"
elif threat_ratio > 0.3:
    health = "INFLAMED"
elif null_apoptosis / max(total, 1) > 0.3:
    health = "ANEMIC"

state = {
    "ts": ts,
    "wave": 201,
    "type": "immune-state-live",
    "status": "ACTIVE",
    "selection": {
        "negative": f"{classified.get('non_self', 0)} killed (attack self)",
        "positive": f"{classified.get('human', 0) + classified.get('organic', 0) + classified.get('self', 0)} survived (bind MHC)",
        "null": f"{null_apoptosis} apoptosis (bind nothing)",
        "note": "negative first, then positive, then null — real thymus order"
    },
    "bone_marrow": {"stem_cells": len(stem_cells), "source": "caddy_access_log"},
    "thymus": {"classified": cls, "total": total, "routes": rts},
    "t_cells": t_cells,
    "b_cells": b_summary,
    "magistrate": magistrate,
    "self_tolerance": {
        "domains": len(SELF_TOLERANCE.get("domains", [])),
        "gates": len(SELF_TOLERANCE.get("gates", [])),
        "primals": len(SELF_TOLERANCE.get("primals", [])),
        "springs": len(SELF_TOLERANCE.get("springs", [])),
        "nerve_endings": len(SELF_TOLERANCE.get("nerve_endings", [])),
        "pi_identity": SELF_TOLERANCE.get("pi_identity"),
    },
    "whale_fall": {
        "proper_deaths": b_summary.get("whale_falls", 0),
        "fossils_total": b_summary.get("fossils_total", 0),
        "note": "death IS generative. dead antibodies feed the reef."
    },
    "cancer_screen": {
        "zombies_found": b_summary.get("zombies_killed", 0),
        "autoimmune_found": b_summary.get("autoimmune_purged", 0),
        "null_escapes": b_summary.get("null_escapes", 0),
        "tumor_growth": b_summary.get("tumor_growth", False),
        "merged_duplicates": b_summary.get("merged_duplicates", 0),
        "status": "CLEAR" if (b_summary.get("zombies_killed", 0) == 0 and b_summary.get("null_escapes", 0) == 0 and not b_summary.get("tumor_growth", False)) else "ALERT"
    },
    "vitals": {
        "immune_ratio": round(immune_ratio, 4),
        "threat_ratio": round(threat_ratio, 4),
        "null_ratio": round(null_apoptosis / max(total, 1), 4),
        "antibody_coverage": round(b_summary["total"] / max(1, 1), 4),
        "health": health,
    },
    "top_threats": sorted(
        [{"pattern": a["pattern"], "encounters": a["encounters"],
          "confidence": a["confidence"], "type": a["cell_type"], "route": a.get("route", "?")}
         for a in antibodies.values()],
        key=lambda x: x["encounters"], reverse=True
    )[:10],
    "selection_table_size": len(SELECTION_TABLE),
}

h = hashlib.blake2b(json.dumps(state, sort_keys=True).encode(), digest_size=16).hexdigest()
state["hash"] = h
IMMUNE_STATE_PATH.write_text(json.dumps(state, indent=2))

print(f"\nIMMUNE SYSTEM: {health}")
print(f"  self+human: {immune_ratio:.1%} | threats: {threat_ratio:.1%} | null: {null_apoptosis / max(total, 1):.1%}")
print(f"  antibodies: {b_summary['total']} (naive:{b_summary['naive']} plasma:{b_summary['plasma']} memory:{b_summary['memory']})")
print(f"  selection table: {len(SELECTION_TABLE)} rules (wildcard * with /suffix output)")
print(f"  self-tolerance: {sum(len(v) for v in SELF_TOLERANCE.values() if isinstance(v, list))} antigens")
print(f"  hash: {h}")

IMMUNE

rm -f "$MARROW_FILE"

# ═══════════════════════════════════════════════
# NEWS DESK — thymus as weather/traffic radar
# Publish bulletin to RSS feed + neutrino + connect
# Everything visible in Klein = visible in RSS drip
# ═══════════════════════════════════════════════

python3 - "$DATA" "$IMMUNE_STATE" << 'NEWSDESK'
import json, sys, time, hashlib
from pathlib import Path
from datetime import datetime, timezone

DATA = Path(sys.argv[1])
STATE_PATH = Path(sys.argv[2])

if not STATE_PATH.exists():
    sys.exit(0)

state = json.loads(STATE_PATH.read_text())
ts = datetime.now(timezone.utc)
ts_rfc = ts.strftime("%a, %d %b %Y %H:%M:%S +0000")
ts_iso = ts.isoformat()

cls = state.get("thymus", {}).get("classified", {})
total = state.get("thymus", {}).get("total", 0)
vitals = state.get("vitals", {})
b = state.get("b_cells", {})
t = state.get("t_cells", {})
cancer = state.get("cancer_screen", {})
wf = state.get("whale_fall", {})
routes = state.get("thymus", {}).get("routes", {})

health = vitals.get("health", "UNKNOWN")
threat_pct = round(vitals.get("threat_ratio", 0) * 100, 1)
immune_pct = round(vitals.get("immune_ratio", 0) * 100, 1)

human = cls.get("human", 0)
organic = cls.get("organic", 0)
non_self = cls.get("non_self", 0)
null = cls.get("null", 0)
self_count = cls.get("self", 0)

ab_total = b.get("total", 0)
ab_naive = b.get("naive", 0)
ab_plasma = b.get("plasma", 0)
ab_memory = b.get("memory", 0)
fossils = b.get("fossils_total", 0)

served = routes.get("/", 0) + routes.get("/mobile", 0)
indexed = routes.get("/sitemap", 0) + routes.get("/webfinger", 0) + routes.get("/feed", 0)
blocked = routes.get("/403", 0) + routes.get("/scatter", 0) + routes.get("/blackhole", 0)
dead = routes.get("/204", 0)

cancer_status = cancer.get("status", "?")

# ── Weather emoji ──
weather = "🌤" if health == "STRONG" else "⛅" if health == "INFLAMED" else "🌩" if health == "SEPTIC" else "🌫"

# ── Build the bulletin ──
bulletin = f"""═══ MEMBRANE REPORT ═══
{weather} {health} — threat {threat_pct}% — antibodies {ab_total} (naive:{ab_naive} plasma:{ab_plasma} memory:{ab_memory}) — cancer: {cancer_status}
🚦 {total} requests — {human} human ({round(human/max(total,1)*100)}%) — {organic} organic — {non_self} non-self — {null} null — {self_count} self
🌊 served:{served} indexed:{indexed} blocked:{blocked} dead:{dead}
🐋 {wf.get('proper_deaths',0)} whale-fall — {b.get('zombies_killed',0)} zombies — {fossils} fossils
wave 201 | {ts_iso}"""

# ── Write RSS item for feed.xml injection ──
guid = f"immune-{ts.strftime('%Y%m%d-%H%M')}"
title = f"🛡 Membrane Report — {health} | {total} req | {ab_total} ab"
desc = bulletin.replace("\n", " &#10; ").replace("═", "-")

rss_item = f"""    <item>
      <title>{title}</title>
      <link>https://primals.eco/data/immune-state-live.json</link>
      <description>{desc}</description>
      <pubDate>{ts_rfc}</pubDate>
      <dc:creator>thymus-news-radar</dc:creator>
      <guid isPermaLink="false">{guid}</guid>
      <category>Immune</category>
      <category>Weather</category>
      <category>Traffic</category>
    </item>
"""

# ── Inject into feed.xml (prepend as first item) ──
FEED_PATH = DATA.parent / "feed.xml"
if FEED_PATH.exists():
    feed = FEED_PATH.read_text()

    # Update lastBuildDate
    import re
    feed = re.sub(
        r'<lastBuildDate>.*?</lastBuildDate>',
        f'<lastBuildDate>{ts_rfc}</lastBuildDate>',
        feed, count=1
    )

    # Insert new item after the first <item> marker comment or first <item>
    # Find the insertion point (after channel metadata, before first item)
    insert_markers = [
        '<!-- WAVE 214 POLLINATION',
        '<!-- WAVE 201 IMMUNE',
        '<item>',
    ]
    inserted = False
    for marker in insert_markers:
        idx = feed.find(marker)
        if idx > 0:
            feed = feed[:idx] + f"<!-- WAVE 201 IMMUNE DRIP {guid} -->\n" + rss_item + "\n    " + feed[idx:]
            inserted = True
            break

    if inserted:
        # Cap feed at ~200 items (remove oldest immune drips beyond 50)
        immune_items = feed.count('<guid isPermaLink="false">immune-')
        if immune_items > 50:
            # Find and remove the last immune item
            last_idx = feed.rfind('<guid isPermaLink="false">immune-')
            if last_idx > 0:
                item_start = feed.rfind('<item>', 0, last_idx)
                item_end = feed.find('</item>', last_idx) + len('</item>')
                if item_start > 0 and item_end > item_start:
                    # Also remove the comment before it if present
                    comment_start = feed.rfind('<!-- WAVE 201 IMMUNE', 0, item_start)
                    if comment_start > 0 and item_start - comment_start < 200:
                        item_start = comment_start
                    feed = feed[:item_start] + feed[item_end:]

        FEED_PATH.write_text(feed)
        print(f"NEWS DESK: RSS item injected → {guid}")
    else:
        print(f"NEWS DESK: could not find insertion point in feed.xml")
else:
    print(f"NEWS DESK: feed.xml not found at {FEED_PATH}")

# ── Write bulletin to a live news file (connect picks up) ──
news = {
    "ts": ts_iso,
    "guid": guid,
    "bulletin": bulletin,
    "weather": health,
    "traffic": {"total": total, "human": human, "organic": organic, "non_self": non_self, "null": null, "self": self_count},
    "flows": {"served": served, "indexed": indexed, "blocked": blocked, "dead": dead},
    "immune": {"antibodies": ab_total, "naive": ab_naive, "plasma": ab_plasma, "memory": ab_memory},
    "cancer": cancer_status,
    "fossils": fossils,
}
news_h = hashlib.blake2b(json.dumps(news, sort_keys=True).encode(), digest_size=8).hexdigest()
news["hash"] = news_h

(DATA / "news-latest.json").write_text(json.dumps(news, indent=2))
print(bulletin)

NEWSDESK

echo "[$TS] immune-activate complete" >> "$LOG"
