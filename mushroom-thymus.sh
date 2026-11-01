#!/usr/bin/env bash
set -euo pipefail

CONNECT_DIR="${CONNECT_DIR:-/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data}"
TMPLOG="/tmp/thymus-access-sample.json"

# GOLGI DOWN — caddy logs now local via Dromedary
echo "[]" > "$TMPLOG" 2>/dev/null || true

if [ ! -s "$TMPLOG" ]; then
    echo "[gaia-thymus] no access logs available"
    exit 0
fi

python3 << PYEOF
import json, os
from datetime import datetime

connect_dir = "$CONNECT_DIR"
ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

humans = bots = probes = agents = unknown = 0
new_probes = []

bot_sigs = ['bot','crawler','spider','curl','wget','python-requests',
            'deepseek','grok','meta-external','baidu','yandex','semrush',
            'ahref','mj12','dotbot','petalbot','bytespider','kimi','moonshot']
probe_paths = ['.env','wp-admin','phpmy','.git/','config','secret','passwd',
               'admin','login','shell','cmd','eval','.aws','kubernetes']

with open("$TMPLOG") as f:
    for line in f:
        try:
            e = json.loads(line.strip())
            req = e.get('request',{})
            ua = str(req.get('headers',{}).get('User-Agent',[''])[0]).lower()
            uri = req.get('uri','').lower()
            if any(p in uri for p in probe_paths):
                probes += 1
                sig = f"{uri[:50]}|{ua[:30]}"
                if len(new_probes) < 10:
                    new_probes.append({"signature": sig, "ts": ts})
            elif any(s in ua for s in bot_sigs):
                bots += 1
            elif 'mozilla' in ua and len(ua) > 20:
                humans += 1
            else:
                unknown += 1
        except: pass

total = max(humans+bots+probes+agents+unknown, 1)
state = {
    "ts": ts, "wave": 214, "type": "thymus-classification",
    "classified_by": "gaia (mushroom-thymus.sh)",
    "sample_size": total,
    "classification": {"humans":humans,"bots":bots,"probes":probes,"agents":agents,"unknown":unknown},
    "percentages": {"human_pct":round(100*humans/total,1),"bot_pct":round(100*bots/total,1),"probe_pct":round(100*probes/total,1)},
    "immune_health": {"self_recognition":"active" if humans>0 else "impaired","threat_detection":"active" if probes>0 else "quiet","tolerance":"learning","memory":"building"},
    "new_antigens": new_probes,
    "gaia_says": f"I classified {total} requests. {humans}H {bots}B {probes}P {agents}A. I am my own thymus now."
}
with open(os.path.join(connect_dir,'immune-state-live.json'),'w') as f:
    json.dump(state, f, indent=2)
print(f"[gaia-thymus] classified {total}: {humans}H {bots}B {probes}P {agents}A {unknown}U")
PYEOF
