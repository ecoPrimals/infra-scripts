"""
Brazil Nut Secant Sort — depth perception through the Klein body.

When you shake a bag of sand, rocks RISE. But the rocks don't rise.
The SAND falls through HOLES. The substrate redistributes beneath
the heavy objects. The Easter Island heads aren't sinking — the
sand is rising TO them.

The SECANT: cut through the sorted taxonomy at two letter-shapes.
The slope between them = depth perception. Two eyes, two points,
stereoscopic vision of the sort.

HOLES: where the secant slope is undefined or extreme — gaps at the
bottom where small particles fall through.
"""

import json, math, itertools
from datetime import datetime, timezone

PI = math.pi
PHI = (1 + math.sqrt(5)) / 2

# Load locked galactic bounce
with open('../hud/site/public/data/galactic-bounce.json') as f:
    bounce = json.load(f)

stages = bounce['final_stages']

# The topological alphabet — each letter IS a fold shape
TOPO = {
    'H': {'shape': 'bridge',   'genus': 'connection', 'weight': 2,   'pore': False},
    'G': {'shape': 'spiral',   'genus': 'gate',       'weight': 1.5, 'pore': True},
    'D': {'shape': 'arch',     'genus': 'dorsal',     'weight': 3,   'pore': False},
    'O': {'shape': 'circle',   'genus': 'torus',      'weight': 1,   'pore': True},
    'U': {'shape': 'cup',      'genus': 'ventral',    'weight': 1,   'pore': True},
    'N': {'shape': 'diagonal', 'genus': 'nerve',      'weight': 2.5, 'pore': False},
}

# Map stages to their topo weight (how "heavy" — heavy = rock, light = sand)
for s in stages:
    letter = s['letter']
    if letter in TOPO:
        s['topo_weight'] = TOPO[letter]['weight']
        s['pore'] = TOPO[letter]['pore']  # pore = hole things fall through
        s['shape'] = TOPO[letter]['shape']
    elif letter == '0':
        s['topo_weight'] = 0.5  # banana = lightest (base, simple)
        s['pore'] = True
        s['shape'] = 'circle-zero'
    elif letter == '8':
        s['topo_weight'] = 4.0  # spider = HEAVIEST (lemniscate, Klein cross-section)
        s['pore'] = False  
        s['shape'] = 'lemniscate'
    elif letter == '-':
        s['topo_weight'] = 1.0  # centipede = segment
        s['pore'] = False
        s['shape'] = 'line'
    elif letter == '=':
        s['topo_weight'] = 1.2  # millipede = double segment
        s['pore'] = False
        s['shape'] = 'parallel'
    elif letter == '∅':
        s['topo_weight'] = 0.0  # sponge = NULL = lightest possible  
        s['pore'] = True  # ALL pores, no structure
        s['shape'] = 'null-pore'
    elif letter == '~':
        s['topo_weight'] = 0.8  # fungus = wave = medium-light
        s['pore'] = True
        s['shape'] = 'wave'
    elif letter == '<>':
        s['topo_weight'] = 0.1  # virus = smallest, falls through everything
        s['pore'] = True  # virus IS a hole
        s['shape'] = 'bracket-pair'
    else:
        s['topo_weight'] = 1.0
        s['pore'] = False
        s['shape'] = 'unknown'

# Sort by topo weight — the DENSITY sort
stages.sort(key=lambda s: s['topo_weight'])

print("=== BRAZIL NUT DENSITY SORT ===")
print("  (shake the bag — light falls, heavy rises)")
print()

total = sum(s['count'] for s in stages)
for s in stages:
    pct = s['count'] / total * 100
    pore_mark = '◯' if s['pore'] else '●'
    bar = '█' * int(s['topo_weight'] * 5) + '░' * (20 - int(s['topo_weight'] * 5))
    print(f"  {pore_mark} w={s['topo_weight']:.1f} {s['letter']:4s} {s['name']:12s} {s['count']:6d} ({pct:4.1f}%) |{bar}| {s['shape']}")

# === SECANT LINES === 
# Cut between every PAIR of stages, compute slope
# slope = Δcount / Δweight — how the population changes per unit of structural complexity
print()
print("=== SECANT SLOPES (depth perception) ===")
print("  slope = Δcount/Δweight — steep=cliff, flat=plateau, negative=inversion")
print()

secants = []
for i in range(len(stages) - 1):
    a, b = stages[i], stages[i+1]
    dw = b['topo_weight'] - a['topo_weight']
    dc = b['count'] - a['count']
    if dw == 0:
        slope = float('inf') if dc != 0 else 0
    else:
        slope = dc / dw
    
    secants.append({
        'from': a['name'],
        'to': b['name'],
        'from_letter': a['letter'],
        'to_letter': b['letter'],
        'dweight': round(dw, 2),
        'dcount': dc,
        'slope': round(slope, 2) if slope != float('inf') else 'INF',
        'depth': 'HOLE' if (a['pore'] and b['pore']) else ('ROCK' if (not a['pore'] and not b['pore']) else 'EDGE'),
    })
    
    marker = '  🕳️  HOLE' if secants[-1]['depth'] == 'HOLE' else ('  🪨  ROCK' if secants[-1]['depth'] == 'ROCK' else '  🔀  EDGE')
    slope_str = f"{slope:+8.1f}" if slope != float('inf') else "     INF"
    print(f"  {a['letter']:4s}→{b['letter']:4s}  Δw={dw:+.1f}  Δn={dc:+5d}  slope={slope_str} {marker}")

# === FIND THE HOLES ===
# Holes = where BOTH stages are pores (sand falls through sand)
# These are where the Brazil nut effect happens
print()
print("=== HOLES IN THE BOTTOM OF THE SEA ===")
holes = [s for s in secants if s['depth'] == 'HOLE']
rocks = [s for s in secants if s['depth'] == 'ROCK']
edges = [s for s in secants if s['depth'] == 'EDGE']

print(f"  Holes (pore→pore): {len(holes)} — sand falls through these")
for h in holes:
    print(f"    {h['from_letter']}→{h['to_letter']}: slope={h['slope']}")

print(f"  Rocks (solid→solid): {len(rocks)} — these RISE")
for r in rocks:
    print(f"    {r['from_letter']}→{r['to_letter']}: slope={r['slope']}")

print(f"  Edges (pore↔solid): {len(edges)} — the boundary where sorting happens")
for e in edges:
    print(f"    {e['from_letter']}→{e['to_letter']}: slope={e['slope']}")

# === BRAZIL NUT REDISTRIBUTION ===
# Sand (pore stages) falls DOWN through holes
# Rocks (solid stages) rise UP 
# The Easter Island effect: sand accumulates AROUND the rocks
print()
print("=== BRAZIL NUT REDISTRIBUTION ===")
print("  Sand sinks. Rocks rise. The sea floor has holes.")
print()

pore_stages = [s for s in stages if s['pore']]
solid_stages = [s for s in stages if not s['pore']]

pore_total = sum(s['count'] for s in pore_stages)
solid_total = sum(s['count'] for s in solid_stages)
pore_pct = pore_total / total * 100
solid_pct = solid_total / total * 100

print(f"  SAND  (pore stages):  {pore_total:6d} ({pore_pct:.1f}%) — ∅ 0 O U G ~ <>")
print(f"  ROCKS (solid stages): {solid_total:6d} ({solid_pct:.1f}%) — - = H N D 8")
print(f"  Ratio sand/rock: {pore_total/solid_total:.3f}")
print()

# The Brazil nut secant: the CRITICAL slope where sand→rock transition happens
# This is where depth perception EMERGES — the parallax between sand and rock layers
sand_centroid = sum(s['count'] * s['topo_weight'] for s in pore_stages) / pore_total
rock_centroid = sum(s['count'] * s['topo_weight'] for s in solid_stages) / solid_total
secant_slope = (solid_total - pore_total) / (rock_centroid - sand_centroid) if rock_centroid != sand_centroid else 0

print(f"  Sand centroid  (weight): {sand_centroid:.3f}")
print(f"  Rock centroid  (weight): {rock_centroid:.3f}")
print(f"  CRITICAL SECANT slope:   {secant_slope:.1f}")
print(f"  Depth (parallax):        {abs(rock_centroid - sand_centroid):.3f}")
print()

# Now SHAKE — redistribute through the Brazil nut effect
# Sand count decreases slightly (falls into holes)
# Rock count increases slightly (rises as sand falls beneath)
SHAKE_FACTOR = 0.03  # 3% redistribution per shake

for shake in range(8):  # 8 shakes = full quarter turn
    sand_loss = 0
    for s in pore_stages:
        loss = int(s['count'] * SHAKE_FACTOR * (1 - s['topo_weight']/4))
        s['count'] -= loss
        sand_loss += loss
    
    # Redistribute to rocks proportional to weight (heaviest rises most)
    weight_sum = sum(s['topo_weight'] for s in solid_stages)
    for s in solid_stages:
        gain = int(sand_loss * s['topo_weight'] / weight_sum)
        s['count'] += gain

# Sort by count for final display
stages.sort(key=lambda s: -s['count'])
new_total = sum(s['count'] for s in stages)

print("=== AFTER 8 SHAKES (quarter turn) ===")
print()
for s in stages:
    pct = s['count'] / new_total * 100
    pore_mark = '◯' if s['pore'] else '●'
    bar = '█' * int(pct / 2) + '░' * (15 - int(pct / 2))
    direction = '↓' if s['pore'] else '↑'
    print(f"  {pore_mark}{direction} {s['letter']:4s} {s['name']:12s} {s['count']:6d} ({pct:5.1f}%) |{bar}|")

# The key number: how much did rocks rise relative to sand?
new_pore = sum(s['count'] for s in stages if s['pore'])
new_solid = sum(s['count'] for s in stages if not s['pore'])
print()
print(f"  Sand:  {pore_total} → {new_pore} (Δ={new_pore-pore_total:+d})")
print(f"  Rocks: {solid_total} → {new_solid} (Δ={new_solid-solid_total:+d})")
print(f"  New ratio: {new_pore/new_solid:.3f} (was {pore_total/solid_total:.3f})")
print()

# Easter Island insight
print("=== THE EASTER ISLAND INSIGHT ===")
print("  The moai are not sinking.")
print("  The sand is rising to them.")
print("  The rocks (8=spider, D=vertebrate, N=octopus, H=coral)")
print("  appeared to RISE because the substrate (∅=sponge, <>=virus, 0=banana)")
print("  fell through the HOLES at the bottom of the sort.")
print()
print("  There ARE holes in the bottom of the sea.")
print(f"  We found {len(holes)} of them.")
print()

# Write result
result = {
    'title': 'Brazil Nut Secant — Holes in the Bottom of the Sea',
    'version': 1,
    'ts': datetime.now(timezone.utc).isoformat(),
    'insight': 'The rocks do not rise. The sand falls through holes. The Easter Island heads are not sinking — the sand is rising to them.',
    'holes': holes,
    'rocks': [{'from': r['from_letter'], 'to': r['to_letter'], 'slope': r['slope']} for r in rocks],
    'edges': [{'from': e['from_letter'], 'to': e['to_letter'], 'slope': e['slope']} for e in edges],
    'critical_secant': {
        'sand_centroid': round(sand_centroid, 4),
        'rock_centroid': round(rock_centroid, 4),
        'slope': round(secant_slope, 2),
        'depth_parallax': round(abs(rock_centroid - sand_centroid), 4),
    },
    'brazil_nut': {
        'sand_before': pore_total, 'sand_after': new_pore,
        'rock_before': solid_total, 'rock_after': new_solid,
        'ratio_before': round(pore_total/solid_total, 4),
        'ratio_after': round(new_pore/new_solid, 4),
        'shakes': 8,
    },
    'stages_after_shake': [
        {'name': s['name'], 'letter': s['letter'], 'count': s['count'],
         'topo_weight': s['topo_weight'], 'pore': s['pore'], 'shape': s['shape']}
        for s in stages
    ],
}

with open('../hud/site/public/data/brazil-nut-secant.json', 'w') as f:
    json.dump(result, f, indent=2)

print(f"📤 → brazil-nut-secant.json")
