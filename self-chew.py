#!/usr/bin/env python3
"""
self-chew.py — The Full Ruminant Digestion (v2: sourdough + easels)

5 stomachs now. the cow grew.

  RUMEN      — raw material (phenotype sort, 46k files)
  RETICULUM  — the fold (klein evolve, delta tracking)
  OMASUM     — chemistry (eon sim, poor tope → carbon → life)
  ABOMASUM   — π compression (pull through π, φ, e, √2)
  SOURDOUGH  — the culture (ferment creativity, personality, flavor)

EASELS: each compression constant is a different perspective.
  π  — the circle. rotation. periodicity. Mendeleev.
  φ  — the golden ratio. growth. spirals. shells.
  e  — the natural base. decay. half-life. fermentation.
  √2 — the diagonal. the hypotenuse. flat→depth.

When a perspective reaches ~100% stability → SPLIT IT.
The imperfect one has personality. Keep it.

"the easels get beautiful after rounds, but at ~100% perspective
 it's hyper-stable and needs to split. art needs perspective
 and pi ratio and OTHER values."
"""

import json, math, os, hashlib, random
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

PI = math.pi
PHI = (1 + math.sqrt(5)) / 2
E = math.e
SQRT2 = math.sqrt(2)
LN2 = math.log(2)

CONSTANTS = {
    'pi':    {'value': PI,    'symbol': 'π',  'meaning': 'circle. rotation. periodicity.'},
    'phi':   {'value': PHI,   'symbol': 'φ',  'meaning': 'growth. spirals. golden section.'},
    'e':     {'value': E,     'symbol': 'e',  'meaning': 'decay. fermentation. natural base.'},
    'sqrt2': {'value': SQRT2, 'symbol': '√2', 'meaning': 'diagonal. flat becomes depth.'},
    'ln2':   {'value': LN2,   'symbol': 'ln2','meaning': 'half-life. information bit.'},
}

ROOT = Path(os.path.expanduser("~/Development/ecoPrimals"))
DATA = ROOT / "membrane" / "local-terminal" / "remote"
HUD = ROOT / "infra" / "hud" / "site" / "public" / "data"

def load(path):
    try:
        return json.loads(Path(path).read_text())
    except:
        return None

def compress_through(value, constant_name):
    """Pull a value through a constant. The remainder IS the signal."""
    c = CONSTANTS[constant_name]['value']
    if value == 0 or c == 0:
        return {'value': 0, 'quotient': 0, 'remainder': 0, 'distance': 0.5, 'constant': constant_name}
    q = value / c
    q_int = int(q)
    r = q - q_int
    return {
        'value': value,
        'quotient': q_int,
        'remainder': round(r, 6),
        'distance': round(abs(r - 0.5), 6),
        'constant': constant_name,
    }

def multi_perspective(value, label=""):
    """View one value from ALL easel perspectives."""
    perspectives = {}
    for name in CONSTANTS:
        c = compress_through(value, name)
        c['label'] = label
        perspectives[name] = c
    
    distances = [p['distance'] for p in perspectives.values()]
    mean_dist = sum(distances) / len(distances) if distances else 0.5
    stability = 1.0 - mean_dist * 2
    
    return {
        'label': label,
        'value': value,
        'perspectives': perspectives,
        'mean_distance': round(mean_dist, 6),
        'stability': round(stability, 4),
        'needs_split': stability > 0.85,
    }

def shannon(counts):
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return round(-sum((c/total) * math.log2(c/total) for c in counts.values() if c > 0), 4)

def sourdough_culture(phenotype, eon, evolve):
    """The sourdough: ferment the data. Add personality. Keep the imperfect ones."""
    culture = {
        'starter': [],
        'ferment': [],
        'proof': [],
        'personality': [],
        'flavor': 0.0,
    }

    if phenotype:
        traits = phenotype.get('phenotype', {})
        stages = phenotype.get('genotype', {})
        
        culture['starter'].append({
            'name': 'jellyfish dominance',
            'value': traits.get('dominant_pct', 0),
            'note': 'the nerve net. no skeleton. event-driven. 42.7% of the organism.',
        })
        culture['starter'].append({
            'name': 'spider web-builder',
            'value': traits.get('spider_pct', 0),
            'note': 'only 3.4%. rare. the web catches, the spider processes.',
        })
        culture['starter'].append({
            'name': 'chaos stability',
            'value': traits.get('chaos_stability', 0),
            'note': f"63.9% held under perturbation. fragile. that's personality.",
        })
        
        jelly = stages.get('jellyfish', 0)
        vert = stages.get('vertebrate', 0)
        if jelly > 0 and vert > 0:
            culture['ferment'].append({
                'name': 'jellyfish/vertebrate ratio',
                'value': round(jelly / vert, 2),
                'note': f'{jelly}/{vert} = {round(jelly/vert, 2)}. the ratio ferments.',
            })

    if eon:
        pool = eon.get('pool', {})
        ch4 = pool.get('CH4', {}).get('count', 0)
        co2 = pool.get('CO2', {}).get('count', 0)
        if ch4 > 0:
            culture['ferment'].append({
                'name': 'methane (CH₄)',
                'value': ch4,
                'note': f'fermentation product. sourdough IS methane. {ch4} molecules.',
            })
        if co2 > 0 and ch4 > 0:
            culture['ferment'].append({
                'name': 'CO₂/CH₄ respiration ratio',
                'value': round(co2 / ch4, 3),
                'note': f'breath out / ferment = {round(co2/ch4, 3)}. the culture breathes.',
            })

    if evolve:
        delta = evolve.get('delta', {})
        if isinstance(delta, dict):
            net = sum(v for v in delta.values() if isinstance(v, (int, float)))
            culture['proof'].append({
                'name': 'drift',
                'value': net,
                'note': f'net change = {net:+d}. the dough rose {net} files.',
            })

    random.seed(42)
    quirks = [
        "this one looks wrong. keeping it.",
        "the color is off but the angle is perfect.",
        "fog in this one. can't see the horizon. beautiful.",
        "hyper-stable at 100%. needs to split.",
        "the jellyfish has no skeleton but it's the dominant life form.",
        "fragile under chaos. that's not weakness — that's sensitivity.",
        "the spider count is only 3.4%. rare things have the most flavor.",
        "methane smells. sourdough smells. both are alive.",
    ]
    chosen = random.sample(quirks, min(4, len(quirks)))
    for q in chosen:
        culture['personality'].append(q)

    if culture['starter']:
        flavor_vals = [s['value'] for s in culture['starter'] if isinstance(s['value'], (int, float))]
        if flavor_vals:
            culture['flavor'] = round(sum(flavor_vals) / len(flavor_vals), 4)

    return culture

def easel_view(perspectives_list):
    """Render multiple easels — each constant gives a different angle."""
    easels = {}
    for const_name, info in CONSTANTS.items():
        easel = {
            'constant': info['symbol'],
            'meaning': info['meaning'],
            'paintings': [],
            'beauty': 0.0,
            'stable': True,
        }
        
        resonant = 0
        total = 0
        for mp in perspectives_list:
            p = mp['perspectives'].get(const_name, {})
            if p:
                total += 1
                d = p.get('distance', 0.5)
                if d < 0.15:
                    resonant += 1
                    glyph = '◉'
                elif d < 0.25:
                    glyph = '○'
                else:
                    glyph = '·'
                easel['paintings'].append({
                    'label': mp['label'],
                    'remainder': p.get('remainder', 0),
                    'distance': d,
                    'glyph': glyph,
                })
        
        if total > 0:
            easel['beauty'] = round(resonant / total, 4)
            easel['stable'] = easel['beauty'] > 0.5
        
        easels[const_name] = easel
    
    return easels

def blink_sort(perspectives_list):
    """Paper 94 blink corollary: sort by what BLINKS (changes fast).
    Stable = background. Blinking = figure. The eye catches movement."""
    blinks = []
    for mp in perspectives_list:
        dists = [p['distance'] for p in mp['perspectives'].values()]
        variance = sum((d - sum(dists)/len(dists))**2 for d in dists) / len(dists) if dists else 0
        blinks.append({
            'label': mp['label'],
            'variance': round(variance, 6),
            'blinks': variance > 0.02,
        })
    
    blinks.sort(key=lambda b: -b['variance'])
    return blinks

def voxel_fill(eon, phenotype, easels):
    """5D voxel: chemistry × biology × π × φ × e."""
    cube = {}
    filled = 0
    
    if phenotype and eon:
        stages = phenotype.get('genotype', {})
        eras = eon.get('eras_reached', [])
        
        era_idx = {'carbon': 0, 'organic': 1, 'iron': 2, 'life': 3, 'phosphorus': 4, 'energy': 5}
        stage_idx = {'banana': 0, 'flatworm': 1, 'jellyfish': 2, 'centipede': 3, 'millipede': 4, 'spider': 5, 'vertebrate': 6}
        
        for era in eras:
            x = era_idx.get(era, 0) % 4
            for stage, count in stages.items():
                y = stage_idx.get(stage, 0) % 4
                z = min(3, count // 3000)
                
                for easel_name, easel in easels.items():
                    w = {'pi': 0, 'phi': 1, 'e': 2, 'sqrt2': 3, 'ln2': 3}.get(easel_name, 0)
                    beauty = easel.get('beauty', 0)
                    if beauty > 0.3:
                        key = f"{x},{y},{z},{w}"
                        if key not in cube:
                            cube[key] = 0
                            filled += 1
                        cube[key] += count

    total = 4 * 4 * 4 * 4  # 4⁴ = 256
    return {
        'dimensions': [4, 4, 4, 4],
        'axes': ['chemistry', 'biology', 'scale', 'perspective'],
        'filled': filled,
        'total': total,
        'fill_ratio': round(filled / total, 4) if total else 0,
        'cells': cube,
    }


def main():
    ts = datetime.now(timezone.utc).isoformat()
    random.seed(int(datetime.now().timestamp()))
    
    print("=" * 60)
    print("  🐄 SELF-CHEW v2 — 5 Stomachs + Sourdough + Easels")
    print("  the cow grew. the codebase eats ALL of itself.")
    print("=" * 60)
    print()

    phenotype = load(DATA / "phenotype-sort.json")
    evolve_state = load(DATA / "evolve-state.json")
    evolve_delta = load(DATA / "evolve-delta.json")
    eon = load(HUD / "eon-shape.json")
    poor_tope = load(HUD / "poor-tope.json")
    atomic_tensor = load(HUD / "atomic-tensor.json")
    klein_cards = load(HUD / "klein-cards.json")

    # ═══ STOMACH 1: RUMEN ═══
    print("  STOMACH 1: RUMEN (raw material)")
    total = phenotype.get('total_files', 0) if phenotype else 0
    traits = phenotype.get('phenotype', {}) if phenotype else {}
    stages = phenotype.get('genotype', {}) if phenotype else {}
    h_mean = phenotype.get('shannon', {}).get('mean_entropy', 0) if phenotype else 0
    print(f"    {total:,} files, {traits.get('dominant_stage', '?')} ({traits.get('dominant_pct', 0)}%)")
    print(f"    Shannon: {h_mean:.3f} bits/word")
    print(f"    Compression: {traits.get('compression_ratio', 0)}:1")
    print()

    # ═══ STOMACH 2: RETICULUM ═══
    print("  STOMACH 2: RETICULUM (the fold)")
    split = evolve_state.get('split', {}) if evolve_state else {}
    print(f"    inv/vert: {split.get('ratio', '?')}")
    if evolve_delta:
        d = evolve_delta.get('delta', {})
        net = sum(v for v in d.values() if isinstance(v, (int, float))) if isinstance(d, dict) else 0
        print(f"    drift: {evolve_delta.get('drift', '?')} (Δ={net:+d})")
    print()

    # ═══ STOMACH 3: OMASUM ═══
    print("  STOMACH 3: OMASUM (chemistry)")
    if eon:
        print(f"    {eon.get('eon', 0)} eons, {eon.get('total_reactions', 0)} reactions")
        print(f"    eras: {eon.get('eras_reached', [])}")
        pool = eon.get('pool', {})
        
        # Run MORE eons in-memory
        print(f"\n    >>> RUNNING 10,000 MORE EONS IN-MEMORY <<<")
        from eon_sim_inline import run_extended_eons
        extended = run_extended_eons(pool, eon.get('element_reserve', {}), 10000)
        print(f"    extended reactions: {extended['reactions']}")
        print(f"    extended eras: {extended['eras']}")
        print(f"    extended pool top 5:")
        for f, info in list(extended['pool'].items())[:5]:
            print(f"      {f}: {info['count']}×")
    else:
        extended = None
        print("    [no eon data]")
    print()

    # ═══ STOMACH 4: ABOMASUM — MULTI-PERSPECTIVE ═══
    print("  STOMACH 4: ABOMASUM (multi-perspective compression)")
    print("  5 easels: π, φ, e, √2, ln2")
    print()
    
    values_to_compress = []
    if total > 0:
        values_to_compress.append(('total_files', total))
    if h_mean > 0:
        values_to_compress.append(('shannon_mean', h_mean))
    if split.get('ratio') and split['ratio'] != 'inf':
        values_to_compress.append(('inv_vert_split', float(split['ratio'])))
    if eon:
        values_to_compress.append(('eon_reactions', eon.get('total_reactions', 0)))
        values_to_compress.append(('eon_complexity', eon.get('complexity_score', 0)))
    if traits.get('compression_ratio'):
        values_to_compress.append(('phenotype_compression', traits['compression_ratio']))
    
    # The sourdough numbers
    if stages:
        jelly = stages.get('jellyfish', 0)
        vert = stages.get('vertebrate', 0)
        if vert > 0:
            values_to_compress.append(('jelly_vert_ratio', round(jelly/vert, 2)))
    
    perspectives = []
    for label, val in values_to_compress:
        mp = multi_perspective(val, label)
        perspectives.append(mp)
    
    # EASEL RENDERING
    easels = easel_view(perspectives)
    
    for const_name, easel in easels.items():
        sym = easel['constant']
        beauty = easel['beauty']
        status = '🎨 BEAUTIFUL' if beauty > 0.5 else '🖌️ developing' if beauty > 0.2 else '📐 angular'
        stable_tag = ' ⚠️ HYPER-STABLE → needs split' if beauty > 0.85 else ''
        print(f"    EASEL {sym} ({easel['meaning']})")
        print(f"      beauty: {beauty:.1%}  {status}{stable_tag}")
        for p in easel['paintings']:
            print(f"        {p['glyph']} {p['label']:25s}  rem={p['remainder']:.6f}  dist={p['distance']:.6f}")
        print()
    
    # BLINK SORT
    print("  BLINK SORT (what changes across perspectives = figure)")
    blinks = blink_sort(perspectives)
    for b in blinks[:5]:
        tag = '⚡ BLINKS' if b['blinks'] else '   stable'
        print(f"    {tag}  var={b['variance']:.6f}  {b['label']}")
    print()
    
    # Check for hyper-stable perspectives that need splitting
    splits_needed = [mp for mp in perspectives if mp.get('needs_split')]
    if splits_needed:
        print(f"  ⚠️  {len(splits_needed)} perspectives are hyper-stable (>85%) → SPLIT:")
        for s in splits_needed:
            print(f"    → {s['label']} (stability={s['stability']:.1%})")
            print(f"      this one looks wrong. keeping it. personality.")
        print()

    # ═══ STOMACH 5: SOURDOUGH ═══
    print("  STOMACH 5: SOURDOUGH (ferment creativity)")
    culture = sourdough_culture(phenotype, eon, evolve_delta)
    
    print(f"    flavor: {culture['flavor']:.4f}")
    print(f"\n    STARTER (what seeds the culture):")
    for s in culture['starter']:
        print(f"      {s['name']}: {s['value']} — {s['note']}")
    print(f"\n    FERMENT (what's actively bubbling):")
    for f in culture['ferment']:
        print(f"      {f['name']}: {f['value']} — {f['note']}")
    print(f"\n    PROOF (did it rise?):")
    for p in culture['proof']:
        print(f"      {p['name']}: {p['value']} — {p['note']}")
    print(f"\n    PERSONALITY (the quirks we keep):")
    for q in culture['personality']:
        print(f"      → \"{q}\"")
    print()

    # ═══ VOXEL ═══
    print("  4D VOXEL (chemistry × biology × scale × perspective)")
    voxel = voxel_fill(eon, phenotype, easels)
    print(f"    filled: {voxel['filled']}/{voxel['total']} ({voxel['fill_ratio']*100:.1f}%)")
    print()

    # ═══ THE DIGEST ═══
    curd_data = json.dumps({
        'phenotype': traits, 'fold': split,
        'eon': eon.get('eras_reached', []) if eon else [],
        'perspectives': [mp['stability'] for mp in perspectives],
        'sourdough_flavor': culture['flavor'],
        'personality': culture['personality'],
    }, default=str)
    digest_hash = hashlib.blake2b(curd_data.encode(), digest_size=16).hexdigest()
    
    mean_stability = sum(mp['stability'] for mp in perspectives) / len(perspectives) if perspectives else 0
    
    print("  ═══ THE DIGEST ═══")
    print()
    print(f"    BLAKE2b:           {digest_hash}")
    print(f"    Mean stability:    {mean_stability:.4f}")
    print(f"    Voxel fill:        {voxel['fill_ratio']*100:.1f}%")
    print(f"    Sourdough flavor:  {culture['flavor']:.4f}")
    print(f"    Personalities:     {len(culture['personality'])}")
    
    if eon:
        pool = eon.get('pool', {})
        flat = sum(1 for f, i in pool.items() if i.get('geometry') in ('linear', 'planar', 'trigonal'))
        curved = sum(1 for f, i in pool.items() if i.get('geometry') in ('tetrahedral', 'bent', 'pyramidal', 'chair', 'chiral', 'complex'))
        print(f"    Carbon flat/curved: {flat}/{curved}")
    
    print()
    
    # Self-entropy
    try:
        with open(__file__, 'r') as f:
            own = f.read().lower().split()
        if own:
            freq = Counter(own)
            own_h = -sum((c/len(own)) * math.log2(c/len(own)) for c in freq.values() if c > 0)
            own_mp = multi_perspective(own_h, "self_entropy")
            print(f"    SELF-REFERENCE:")
            print(f"      entropy: {own_h:.3f} bits/word")
            print(f"      stability: {own_mp['stability']:.4f}")
            if own_mp['needs_split']:
                print(f"      ⚠️ self is hyper-stable. the cow needs to split.")
            print(f"      the cow chews its own cud: output → input → output")
    except:
        pass

    print()

    # ═══ WRITE CURD ═══
    curd = {
        'ts': ts,
        'version': 2,
        'pipeline': 'rumen → reticulum → omasum → abomasum → sourdough → curd',
        'stomachs': {
            'rumen': {'files': total, 'dominant': traits.get('dominant_stage', '?'), 'shannon_mean': h_mean},
            'reticulum': {'split_ratio': split.get('ratio'), 'drift': evolve_delta.get('drift') if evolve_delta else None},
            'omasum': {'eon': eon.get('eon', 0) if eon else 0, 'reactions': eon.get('total_reactions', 0) if eon else 0, 'eras': eon.get('eras_reached', []) if eon else []},
            'abomasum': {
                'constants': list(CONSTANTS.keys()),
                'mean_stability': round(mean_stability, 4),
                'splits_needed': len(splits_needed),
            },
            'sourdough': {
                'flavor': culture['flavor'],
                'starter_count': len(culture['starter']),
                'ferment_count': len(culture['ferment']),
                'personality': culture['personality'],
            },
        },
        'easels': {k: {'beauty': v['beauty'], 'stable': v['stable']} for k, v in easels.items()},
        'blinks': blinks[:5],
        'voxel': voxel,
        'digest': {
            'blake2b': digest_hash,
            'mean_stability': round(mean_stability, 4),
            'voxel_fill': voxel['fill_ratio'],
            'sourdough_flavor': culture['flavor'],
        },
    }

    out = HUD / "self-chew.json"
    out.write_text(json.dumps(curd, indent=2, default=str))
    print(f"  💀 Curd: {out}")
    print(f"  The cow has 5 stomachs now. It sourdoughed its own creativity.")


# ═══ INLINE EON EXTENSION (avoid import issues) ═══
class _EonExtInline:
    pass

import types
eon_mod = types.ModuleType('eon_sim_inline')
def run_extended_eons(existing_pool, element_reserve, extra_eons):
    """Run more eons from existing state."""
    pool = {}
    for formula, info in existing_pool.items():
        pool[formula] = info.get('count', 0) if isinstance(info, dict) else info
    
    elements = Counter(element_reserve) if element_reserve else Counter({'C': 50, 'N': 20, 'S': 5, 'P': 5, 'Fe': 2})
    
    rxns = [
        (['H2O', 'H2O'], 'CO2', ['C'], 50),
        (['H2', 'H2'], 'CH4', ['C'], 30),
        (['H2', 'H2O'], 'NH3', ['N'], 60),
        (['O2', 'H2'], 'H2O2', [], 20),
        (['CO2', 'H2'], 'CH2O', [], 70),
        (['CH2O', 'H2'], 'CH3OH', [], 50),
        (['CH2O', 'O2'], 'HCOOH', [], 40),
        (['CH2O', 'NH3'], 'glycine', ['C'], 120),
        (['CH2O', 'CH2O', 'H2O'], 'glucose', ['C'], 200),
    ]
    
    heat = 40.1
    total_rxns = 0
    eras = set(['carbon', 'iron', 'organic'])
    
    random.seed(137)
    for eon_i in range(extra_eons):
        random.shuffle(rxns)
        for reactants, product, needs, activation in rxns:
            avail = all(pool.get(r, 0) >= reactants.count(r) for r in set(reactants))
            if not avail:
                continue
            if random.random() * heat * 2 < activation:
                continue
            elems_ok = all(elements.get(e, 0) > 0 for e in needs)
            if not elems_ok:
                continue
            for r in reactants:
                pool[r] = pool.get(r, 0) - 1
                if pool[r] <= 0:
                    del pool[r]
            for e in needs:
                elements[e] -= 1
            pool[product] = pool.get(product, 0) + 1
            total_rxns += 1
            if product in ('glycine', 'glucose'):
                eras.add('life')
        
        if eon_i % 50 == 0:
            pool['H2'] = pool.get('H2', 0) + 3
            pool['H2O'] = pool.get('H2O', 0) + 3
            pool['O2'] = pool.get('O2', 0) + 3
        if eon_i % 100 == 0:
            elements['C'] += 5
            elements['N'] += 2
            elements['P'] += 1
    
    sorted_pool = sorted(pool.items(), key=lambda x: -x[1])
    return {
        'reactions': total_rxns,
        'eras': sorted(eras),
        'pool': {f: {'count': c} for f, c in sorted_pool if c > 0},
    }

eon_mod.run_extended_eons = run_extended_eons
import sys
sys.modules['eon_sim_inline'] = eon_mod

if __name__ == '__main__':
    main()
