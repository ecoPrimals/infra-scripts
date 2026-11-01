#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# 🧠 mushroom-willis — CIRCLE OF WILLIS CIRCULATION MONITOR
# ═══════════════════════════════════════════════════════════════
# The Circle of Willis provides redundant arterial flow to the brain.
# If one path blocks, blood reroutes through another.
#
# ARTERIES (input):
#   OSINT blackholes → intake (Wikipedia, HN, arxiv, xkcd, lobsters...)
#   neutrino channels → messages
#   gate probes → mesh status
#
# VEINS (output/drain):
#   RSS feed.xml → old web
#   git commits → GitHub/CF Pages
#   neutrino → ntfy push
#
# WILLIS LOOP: if drain is stuck, reroute.
# If artery is blocked, find alternate source.
#
# Runs every 7 minutes (7 arteries in the Circle of Willis)
# ═══════════════════════════════════════════════════════════════
set -uo pipefail

LOG="/tmp/mushroom-willis.log"
DATA="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data"
FEED="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/feed.xml"

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "[$TS] willis circulation check" >> "$LOG"

python3 - "$DATA" "$FEED" "$LOG" <<'PYEOF'
import json, os, sys, time, subprocess
from datetime import datetime, timezone

data_dir = sys.argv[1]
feed_path = sys.argv[2]
log_file = sys.argv[3]
ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def log(msg):
    with open(log_file, "a") as f:
        f.write(f"[{ts}] {msg}\n")

# ═══ MEASURE ARTERIES (input flow) ═══
arteries = {}

# Artery 1: OSINT blackholes (intake rate)
intake_dir = os.path.join(data_dir, "intake")
if os.path.isdir(intake_dir):
    recent_intake = sum(1 for f in os.listdir(intake_dir) 
                        if f.endswith('.json') and 
                        (time.time() - os.path.getmtime(os.path.join(intake_dir, f))) < 3600)
    arteries['osint_blackholes'] = {'flow': recent_intake, 'unit': 'files/hr', 'healthy': recent_intake > 10}
else:
    arteries['osint_blackholes'] = {'flow': 0, 'unit': 'files/hr', 'healthy': False}

# Artery 2: Nutrient processing
nutrient_dir = os.path.join(data_dir, "nutrients")
if os.path.isdir(nutrient_dir):
    recent_nutrients = sum(1 for f in os.listdir(nutrient_dir)
                          if f.endswith('.json') and
                          (time.time() - os.path.getmtime(os.path.join(nutrient_dir, f))) < 3600)
    arteries['nutrient_processing'] = {'flow': recent_nutrients, 'unit': 'files/hr', 'healthy': recent_nutrients > 5}
else:
    arteries['nutrient_processing'] = {'flow': 0, 'unit': 'files/hr', 'healthy': False}

# Artery 3: Mastication (AI teeth)
try:
    m = json.load(open(os.path.join(data_dir, 'mastication-log.json')))
    arteries['mastication'] = {'flow': m['total'], 'unit': 'total chewed', 'healthy': m['total'] > 0}
except:
    arteries['mastication'] = {'flow': 0, 'unit': 'total', 'healthy': False}

# Artery 4: Study
try:
    s = json.load(open(os.path.join(data_dir, 'study-notes.json')))
    arteries['study'] = {'flow': s['total_studied'], 'unit': 'topics', 'healthy': s['total_studied'] > 0}
except:
    arteries['study'] = {'flow': 0, 'unit': 'topics', 'healthy': False}

# ═══ MEASURE VEINS (output/drain) ═══
veins = {}

# Vein 1: RSS drain
try:
    with open(feed_path) as f:
        feed = f.read()
    rss_items = feed.count('<item>')
    # Check last build date freshness
    import re
    lbd = re.search(r'<lastBuildDate>(.*?)</lastBuildDate>', feed)
    veins['rss_drain'] = {'flow': rss_items, 'unit': 'items', 'last_build': lbd.group(1) if lbd else '?', 'healthy': rss_items > 400}
except:
    veins['rss_drain'] = {'flow': 0, 'unit': 'items', 'healthy': False}

# Vein 2: Git commits (last hour)
try:
    r = subprocess.run(['git', 'log', '--oneline', '--since=1 hour ago'],
                       cwd='/home/eastgate/Development/ecoPrimals/infra/hud',
                       capture_output=True, text=True, timeout=5)
    git_commits = len(r.stdout.strip().split('\n')) if r.stdout.strip() else 0
    veins['git_drain'] = {'flow': git_commits, 'unit': 'commits/hr', 'healthy': True}
except:
    veins['git_drain'] = {'flow': 0, 'unit': 'commits/hr', 'healthy': True}

# Vein 3: Neutrino (check if ntfy is reachable)
try:
    r = subprocess.run(['ssh', '-o', 'ConnectTimeout=3', '-o', 'BatchMode=yes', 'localhost',
                        'systemctl is-active ntfy'], capture_output=True, text=True, timeout=10)
    ntfy_ok = 'active' in r.stdout
    veins['neutrino_drain'] = {'flow': 1 if ntfy_ok else 0, 'unit': 'active', 'healthy': ntfy_ok}
except:
    veins['neutrino_drain'] = {'flow': 0, 'unit': 'active', 'healthy': False}

# ═══ WILLIS LOOP: detect blockages and reroute ═══
blockages = []
reroutes = []

# Check: OSINT flow but no nutrient processing = digestion blocked
if arteries['osint_blackholes']['flow'] > 20 and arteries['nutrient_processing']['flow'] < 5:
    blockages.append("Digestion blocked: intake flowing but nutrients stuck")
    reroutes.append("Trigger manual nutrient processing")

# Check: Nutrients flowing but no mastication = teeth stuck  
if arteries['nutrient_processing']['flow'] > 10 and arteries['mastication']['flow'] < 10:
    blockages.append("Mastication stuck: nutrients available but teeth idle")
    reroutes.append("Trigger mastication run")

# Check: Content exists but RSS drain low
study_count = arteries['study']['flow']
mast_count = arteries['mastication']['flow']
if (study_count > 20 or mast_count > 50) and veins['rss_drain']['flow'] < 450:
    blockages.append(f"RSS drain low: {study_count} studies + {mast_count} masticated but only {veins['rss_drain']['flow']} RSS items")
    reroutes.append("Trigger self-publish to flush studies + mastication to RSS")
    # AUTO-REROUTE: run self-publish
    try:
        subprocess.run(['/home/eastgate/Development/ecoPrimals/infra/scripts/mushroom-self-publish-rss.sh'],
                       capture_output=True, timeout=60)
        reroutes.append("AUTO-REROUTED: ran self-publish to flush drain")
    except:
        pass

# ═══ WRITE WILLIS STATE ═══
willis = {
    'ts': ts,
    'title': 'Circle of Willis — Organism Circulation',
    'arteries': arteries,
    'veins': veins,
    'blockages': blockages,
    'reroutes': reroutes,
    'circulation': {
        'input_rate': sum(a['flow'] for a in arteries.values()),
        'output_rate': veins['rss_drain']['flow'] + veins['git_drain']['flow'],
        'healthy': len(blockages) == 0,
    },
    'philosophy': {
        'blackholes': 'OSINT sources = gravitational wells pulling data IN',
        'drain': 'RSS = the drain. Everything learned flows OUT to the old web',
        'willis': 'Redundant paths. If one blocks, another opens. Never stuck.',
    },
}

with open(os.path.join(data_dir, 'willis-circulation.json'), 'w') as f:
    json.dump(willis, f, indent=2)

# Log
a_health = sum(1 for a in arteries.values() if a['healthy'])
v_health = sum(1 for v in veins.values() if v['healthy'])
log(f"arteries={a_health}/{len(arteries)} veins={v_health}/{len(veins)} blockages={len(blockages)} reroutes={len(reroutes)}")

print(f"🧠 WILLIS: arteries={a_health}/{len(arteries)} veins={v_health}/{len(veins)} blockages={len(blockages)}")
if blockages:
    for b in blockages:
        print(f"  ⚠️ {b}")
if reroutes:
    for r in reroutes:
        print(f"  🔄 {r}")

PYEOF
