#!/bin/bash
# 🍄 MUSHROOM: compost detector
# Finds stale files (>48h old, <3 connections) ready for composting
# The decomposer IS the loamSpine root nodule

cd /home/eastgate/Development/ecoPrimals/infra/hud/site/public/data

python3 -c "
import json, glob, os, time

ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
now = time.time()
all_files = sorted(glob.glob('*.json'))

compost_candidates = []
for f in all_files:
    try:
        age_h = (now - os.path.getmtime(f)) / 3600
        size = os.path.getsize(f)
        content = open(f).read()
        refs = sum(1 for other in all_files if other != f and other.replace('.json','') in content)
        if age_h > 48 and refs < 3 and size < 5000:
            d = json.load(open(f))
            title = d.get('title', f)[:60] if isinstance(d, dict) else f
            compost_candidates.append({'file': f, 'age_h': round(age_h, 1), 'connections': refs, 'size': size, 'title': title})
    except: pass

compost_candidates.sort(key=lambda x: x['age_h'], reverse=True)

report = {
    'ts': ts,
    'type': 'compost-scan',
    'title': 'Compost Scan — stale files ready for decomposition',
    'candidates': len(compost_candidates),
    'top_20': compost_candidates[:20],
    'note': 'compost = nutrient release. connections TRANSFER to survivors.'
}
json.dump(report, open('compost-scan-latest.json', 'w'), indent=2, ensure_ascii=False)
"

