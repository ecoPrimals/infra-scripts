#!/bin/bash
# 🍄 MUSHROOM: braid scanner
# Finds orphan nodes (<3 connections) and over-threaded hubs (>89 connections)
# The braid scanner IS the spider IS the sweetGrass rhizome finder

cd /home/eastgate/Development/ecoPrimals/infra/hud/site/public/data

python3 -c "
import json, glob, os, time

ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
all_files = sorted(glob.glob('*.json'))

# Count connections (references to other files)
connections = {}
for f in all_files:
    try:
        content = open(f).read()
        refs = sum(1 for other in all_files if other != f and other.replace('.json','') in content)
        connections[f] = refs
    except: pass

orphans = {f: c for f, c in connections.items() if c < 3}
hubs = {f: c for f, c in connections.items() if c > 89}
healthy = {f: c for f, c in connections.items() if 3 <= c <= 89}

scan = {
    'ts': ts,
    'type': 'braid-scan',
    'title': 'Braid Scan — orphans, hubs, and healthy nodes',
    'total': len(connections),
    'orphans': len(orphans),
    'hubs': len(hubs),
    'healthy': len(healthy),
    'top_orphans': sorted(orphans.items(), key=lambda x: x[1])[:10],
    'top_hubs': sorted(hubs.items(), key=lambda x: -x[1])[:5],
    'density': round(sum(connections.values()) / max(len(connections), 1), 2)
}
json.dump(scan, open('braid-scan-latest.json', 'w'), indent=2, ensure_ascii=False)
"

