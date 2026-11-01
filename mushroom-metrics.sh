#!/bin/bash
# 🍄 MUSHROOM: metric publisher
# The metric publisher IS the toadStool fruiting body

cd /home/eastgate/Development/ecoPrimals/infra/hud/site/public/data

TOTAL_FILES=$(ls *.json 2>/dev/null | wc -l)
TOTAL_BYTES=$(du -sb . 2>/dev/null | cut -f1)
FOSSILS=$(python3 -c "
try:
    import json
    d = json.load(open('/home/eastgate/Development/ecoPrimals/membrane/local-terminal/remote/immune.log.json', 'r'))
    print(d.get('fossils', 0))
except: print(0)
" 2>/dev/null || echo 0)

python3 -c "
import json, time
ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
metrics = {
    'ts': ts,
    'organism': 'ecoPrimal',
    'alive': True,
    'data_files': $TOTAL_FILES,
    'total_bytes': $TOTAL_BYTES,
    'last_action': 'mushroom mycelium pulse',
    'mushrooms_alive': 16,
    'mushrooms_dark': 8
}
json.dump(metrics, open('/tmp/pulse-metrics.json', 'w'), indent=2)
"

