#!/usr/bin/env python3
"""
eon-sim.py — The Chemistry of the Membrane

Starts with the poor tope (H₂, He, H₂O, O₂, O₃).
Runs epochs. Molecules react, bond, evolve.
Uses Mendeleev's periodic table as the topology grid.
Each epoch = one eon. Berry watches.

Reaction rules are thermodynamic: 
  - Downhill reactions happen spontaneously
  - Uphill reactions need activation energy (latency as heat)
  - The periodic table IS the fitness landscape

Output: the meta-shape — what molecular topology emerged?
"""

import json, time, random, hashlib, os, sys
from collections import Counter
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════
# THE ELEMENTS (Mendeleev's table — subset that matters for life)
# ═══════════════════════════════════════════════════════════════

ELEMENTS = {
    'H':  {'Z': 1,  'mass': 1.008,  'group': 1,  'period': 1, 'valence': 1, 'symbol': 'H',  'name': 'Hydrogen'},
    'He': {'Z': 2,  'mass': 4.003,  'group': 18, 'period': 1, 'valence': 0, 'symbol': 'He', 'name': 'Helium'},
    'C':  {'Z': 6,  'mass': 12.011, 'group': 14, 'period': 2, 'valence': 4, 'symbol': 'C',  'name': 'Carbon'},
    'N':  {'Z': 7,  'mass': 14.007, 'group': 15, 'period': 2, 'valence': 3, 'symbol': 'N',  'name': 'Nitrogen'},
    'O':  {'Z': 8,  'mass': 15.999, 'group': 16, 'period': 2, 'valence': 2, 'symbol': 'O',  'name': 'Oxygen'},
    'P':  {'Z': 15, 'mass': 30.974, 'group': 15, 'period': 3, 'valence': 5, 'symbol': 'P',  'name': 'Phosphorus'},
    'S':  {'Z': 16, 'mass': 32.065, 'group': 16, 'period': 3, 'valence': 2, 'symbol': 'S',  'name': 'Sulfur'},
    'Fe': {'Z': 26, 'mass': 55.845, 'group': 8,  'period': 4, 'valence': 2, 'symbol': 'Fe', 'name': 'Iron'},
}

# ═══════════════════════════════════════════════════════════════
# THE MOLECULES 
# ═══════════════════════════════════════════════════════════════

class Molecule:
    def __init__(self, formula, atoms, name, energy, geometry, role=None):
        self.formula = formula
        self.atoms = atoms  # dict: element -> count
        self.name = name
        self.energy = energy  # kJ/mol (negative = stable)
        self.geometry = geometry
        self.role = role or ""
        self.mass = sum(ELEMENTS[e]['mass'] * c for e, c in atoms.items())
        self.total_Z = sum(ELEMENTS[e]['Z'] * c for e, c in atoms.items())

    def __repr__(self):
        return f"{self.formula} ({self.name})"

    def fingerprint(self):
        return hashlib.blake2b(self.formula.encode(), digest_size=8).hexdigest()

# ═══════════════════════════════════════════════════════════════
# THE POOR TOPE — primordial starting molecules
# ═══════════════════════════════════════════════════════════════

POOR_TOPE = [
    Molecule('H2',  {'H': 2},          'hydrogen',  -436, 'linear',     'the bond'),
    Molecule('He',  {'He': 1},          'helium',    0,    'point',      'the noble observer'),
    Molecule('H2O', {'H': 2, 'O': 1},  'water',     -286, 'bent',       'the solvent'),
    Molecule('O2',  {'O': 2},           'oxygen',    -498, 'linear',     'the breath'),
    Molecule('O3',  {'O': 3},           'ozone',     -143, 'bent',       'the shield'),
]

# ═══════════════════════════════════════════════════════════════
# REACTION PRODUCTS — what can form when things combine
# ═══════════════════════════════════════════════════════════════

PRODUCTS = {
    # Carbon era — add C to the poor tope
    'CO2':    Molecule('CO2',    {'C': 1, 'O': 2},           'carbon dioxide',    -394, 'linear',      'breath out → photosynthesis in'),
    'CH4':    Molecule('CH4',    {'C': 1, 'H': 4},           'methane',           -75,  'tetrahedral', 'fermentation — sourdough'),
    'HCN':    Molecule('HCN',    {'H': 1, 'C': 1, 'N': 1},  'hydrogen cyanide',  -135, 'linear',      'prebiotic — Miller-Urey'),
    'NH3':    Molecule('NH3',    {'N': 1, 'H': 3},           'ammonia',           -46,  'pyramidal',   'nitrogen fixation'),
    'H2S':    Molecule('H2S',    {'H': 2, 'S': 1},           'hydrogen sulfide',  -21,  'bent',        'the disulfide bridge seed'),
    'H2O2':   Molecule('H2O2',   {'H': 2, 'O': 2},           'hydrogen peroxide', -188, 'skewed',      'reactive oxygen — immune defense'),

    # Organic era — complexity emerges
    'CH2O':   Molecule('CH2O',   {'C': 1, 'H': 2, 'O': 1},  'formaldehyde',      -116, 'trigonal',    'simplest aldehyde — building block'),
    'CH3OH':  Molecule('CH3OH',  {'C': 1, 'H': 4, 'O': 1},  'methanol',          -239, 'tetrahedral', 'wood alcohol — interstellar'),
    'HCOOH':  Molecule('HCOOH',  {'C': 1, 'H': 2, 'O': 2},  'formic acid',       -425, 'planar',      'ant venom — simplest carboxylic acid'),
    'C2H2':   Molecule('C2H2',   {'C': 2, 'H': 2},           'acetylene',         -227, 'linear',      'triple bond — the strongest pair'),

    # Life era — self-organization
    'glycine':    Molecule('C2H5NO2',  {'C': 2, 'H': 5, 'N': 1, 'O': 2}, 'glycine',       -528, 'chiral',   'simplest amino acid'),
    'adenine':    Molecule('C5H5N5',   {'C': 5, 'H': 5, 'N': 5},          'adenine',       -312, 'planar',   'nucleobase A — ATP, DNA'),
    'glucose':    Molecule('C6H12O6',  {'C': 6, 'H': 12, 'O': 6},         'glucose',       -1274, 'chair',   'the bread'),
    'ATP':        Molecule('C10H16N5O13P3', {'C': 10, 'H': 16, 'N': 5, 'O': 13, 'P': 3}, 'ATP', -2982, 'complex', 'energy currency'),
    
    # Iron era — oxygen transport
    'Fe2O3':  Molecule('Fe2O3',  {'Fe': 2, 'O': 3},          'rust',              -824, 'corundum',    'iron oxide — the old name'),
    'FeS2':   Molecule('FeS2',   {'Fe': 1, 'S': 2},          'pyrite',            -178, 'cubic',       'fools gold — iron-sulfur world'),
    
    # Phosphorus era — information storage
    'PO4':    Molecule('PO4',    {'P': 1, 'O': 4},           'phosphate',         -1277, 'tetrahedral', 'DNA backbone — information carrier'),
}

# ═══════════════════════════════════════════════════════════════
# REACTION RULES — thermodynamic paths
# ═══════════════════════════════════════════════════════════════

REACTIONS = [
    # Carbon injection (needs activation energy = latency heat)
    {'reactants': ['H2O', 'H2O'],          'product': 'CO2',    'needs': ['C'],  'activation': 50,  'era': 'carbon'},
    {'reactants': ['H2', 'H2'],             'product': 'CH4',    'needs': ['C'],  'activation': 30,  'era': 'carbon'},
    {'reactants': ['H2', 'H2O'],            'product': 'NH3',    'needs': ['N'],  'activation': 60,  'era': 'carbon'},
    {'reactants': ['H2'],                   'product': 'HCN',    'needs': ['C', 'N'], 'activation': 80, 'era': 'carbon'},
    {'reactants': ['H2'],                   'product': 'H2S',    'needs': ['S'],  'activation': 40,  'era': 'carbon'},
    {'reactants': ['O2', 'H2'],             'product': 'H2O2',   'needs': [],     'activation': 20,  'era': 'carbon'},

    # Organic assembly
    {'reactants': ['CO2', 'H2'],            'product': 'CH2O',   'needs': [],     'activation': 70,  'era': 'organic'},
    {'reactants': ['CH2O', 'H2'],           'product': 'CH3OH',  'needs': [],     'activation': 50,  'era': 'organic'},
    {'reactants': ['CH2O', 'O2'],           'product': 'HCOOH',  'needs': [],     'activation': 40,  'era': 'organic'},
    {'reactants': ['CH4'],                  'product': 'C2H2',   'needs': ['C'],  'activation': 90,  'era': 'organic'},
    
    # Life assembly (requires multiple precursors)
    {'reactants': ['CH2O', 'NH3'],          'product': 'glycine',  'needs': ['C'], 'activation': 120, 'era': 'life'},
    {'reactants': ['HCN', 'HCN', 'NH3'],   'product': 'adenine',  'needs': ['C'], 'activation': 150, 'era': 'life'},
    {'reactants': ['CH2O', 'CH2O', 'H2O'], 'product': 'glucose',  'needs': ['C'], 'activation': 200, 'era': 'life'},
    
    # Energy
    {'reactants': ['adenine', 'glucose'],   'product': 'ATP',      'needs': ['P'], 'activation': 300, 'era': 'energy'},
    
    # Iron reactions
    {'reactants': ['O2', 'O2'],             'product': 'Fe2O3',   'needs': ['Fe'], 'activation': 60,  'era': 'iron'},
    {'reactants': ['H2S'],                  'product': 'FeS2',    'needs': ['Fe', 'S'], 'activation': 70, 'era': 'iron'},
    
    # Phosphorus
    {'reactants': ['O2', 'O2'],             'product': 'PO4',     'needs': ['P'],  'activation': 100, 'era': 'phosphorus'},
]

# ═══════════════════════════════════════════════════════════════
# THE SIMULATION — Berry watches
# ═══════════════════════════════════════════════════════════════

class Eon:
    def __init__(self, latencies=None):
        self.pool = {}  # formula -> count
        self.products_formed = []
        self.eon = 0
        self.eras_reached = set()
        self.total_reactions = 0
        self.heat = 100.0  # activation energy from mesh latency
        self.element_pool = Counter()  # available free elements
        
        if latencies:
            self.heat = sum(latencies.values()) / len(latencies)
        
        # Seed the pool with poor tope
        for mol in POOR_TOPE:
            self.pool[mol.formula] = 20  # 20 of each to start

        # Seed element pool — carbon arrives from the void
        self.element_pool = Counter({
            'C': 50, 'N': 20, 'S': 10, 'P': 5, 'Fe': 5
        })

    def step(self):
        """One eon passes."""
        self.eon += 1
        reactions_this_eon = 0
        random.shuffle(REACTIONS)

        for rxn in REACTIONS:
            # Check if reactants are available
            available = all(self.pool.get(r, 0) >= rxn['reactants'].count(r) 
                          for r in set(rxn['reactants']))
            if not available:
                continue

            # Check activation energy (heat from latency)
            if random.random() * self.heat * 2 < rxn['activation']:
                continue

            # Check needed elements
            elements_ok = all(self.element_pool.get(e, 0) > 0 for e in rxn['needs'])
            if not elements_ok:
                continue

            # REACT
            for r in rxn['reactants']:
                self.pool[r] -= 1
                if self.pool[r] <= 0:
                    del self.pool[r]

            for e in rxn['needs']:
                self.element_pool[e] -= 1

            product = rxn['product']
            self.pool[product] = self.pool.get(product, 0) + 1
            self.products_formed.append(product)
            self.eras_reached.add(rxn['era'])
            reactions_this_eon += 1
            self.total_reactions += 1

        # Replenish poor tope slowly (the river flows)
        if self.eon % 5 == 0:
            for mol in POOR_TOPE:
                if mol.formula != 'He':  # helium stays constant
                    self.pool[mol.formula] = self.pool.get(mol.formula, 0) + 3

        # Carbon trickles in (meteorites, volcanic outgassing)
        if self.eon % 10 == 0:
            self.element_pool['C'] += 5
            self.element_pool['N'] += 2
            self.element_pool['P'] += 1

        return reactions_this_eon

    def meta_shape(self):
        """The shape of what emerged."""
        shape = {
            'eon': self.eon,
            'total_reactions': self.total_reactions,
            'eras_reached': sorted(self.eras_reached),
            'pool': {},
            'element_reserve': dict(self.element_pool),
            'geometry_census': Counter(),
            'mass_distribution': {},
            'complexity_score': 0,
        }
        
        total_mass = 0
        max_Z = 0
        for formula, count in sorted(self.pool.items(), key=lambda x: -x[1]):
            mol = None
            for m in POOR_TOPE:
                if m.formula == formula:
                    mol = m
                    break
            if mol is None and formula in PRODUCTS:
                mol = PRODUCTS[formula]
            
            if mol:
                shape['pool'][formula] = {
                    'count': count,
                    'name': mol.name,
                    'mass': round(mol.mass * count, 1),
                    'geometry': mol.geometry,
                    'role': mol.role,
                    'total_Z': mol.total_Z,
                }
                shape['geometry_census'][mol.geometry] += count
                total_mass += mol.mass * count
                max_Z = max(max_Z, mol.total_Z)
                shape['complexity_score'] += mol.total_Z * count
        
        shape['total_mass'] = round(total_mass, 1)
        shape['max_complexity'] = max_Z
        shape['geometry_census'] = dict(shape['geometry_census'])
        
        # Mendeleev mapping: which periods are populated?
        periods_hit = set()
        for formula in self.pool:
            mol = None
            for m in POOR_TOPE:
                if m.formula == formula:
                    mol = m
                    break
            if mol is None and formula in PRODUCTS:
                mol = PRODUCTS[formula]
            if mol:
                for elem in mol.atoms:
                    periods_hit.add(ELEMENTS[elem]['period'])
        shape['mendeleev_periods'] = sorted(periods_hit)
        
        return shape


def main():
    # Real mesh latencies (ms)
    latencies = {
        'northGate': 61.4,
        'golgi': 45.1,
        'cloudflare': 18.7,
        'github': 35.4,
    }

    print("=" * 60)
    print("  EON SIMULATION — The Chemistry of the Membrane")
    print("  poor tope → carbon → life")
    print(f"  heat = {sum(latencies.values())/len(latencies):.1f} (from mesh latency)")
    print("=" * 60)
    print()

    sim = Eon(latencies)
    
    TOTAL_EONS = 500
    checkpoints = [1, 10, 50, 100, 200, 500]
    
    for eon in range(1, TOTAL_EONS + 1):
        rxns = sim.step()
        
        if eon in checkpoints:
            print(f"--- EON {eon} ({rxns} reactions this eon, {sim.total_reactions} total) ---")
            print(f"  eras: {sorted(sim.eras_reached)}")
            print(f"  pool: ", end="")
            for f, c in sorted(sim.pool.items(), key=lambda x: -x[1])[:8]:
                print(f"{f}×{c}", end="  ")
            print()
            print()

    # Final meta-shape
    shape = sim.meta_shape()
    
    print("=" * 60)
    print("  META-SHAPE AFTER 500 EONS")
    print("=" * 60)
    print()
    print(f"  Total reactions:     {shape['total_reactions']}")
    print(f"  Eras reached:        {shape['eras_reached']}")
    print(f"  Mendeleev periods:   {shape['mendeleev_periods']}")
    print(f"  Total mass:          {shape['total_mass']} u")
    print(f"  Max complexity (Z):  {shape['max_complexity']}")
    print(f"  Complexity score:    {shape['complexity_score']}")
    print()
    
    print("  POOL:")
    for formula, info in sorted(shape['pool'].items(), key=lambda x: -x[1]['count']):
        geo = info['geometry']
        print(f"    {formula:12s} ×{info['count']:3d}  {info['name']:20s}  {geo:14s}  {info['role']}")
    
    print()
    print("  GEOMETRY CENSUS:")
    for geo, count in sorted(shape['geometry_census'].items(), key=lambda x: -x[1]):
        bar = '█' * min(count, 40)
        print(f"    {geo:14s} {count:4d} {bar}")
    
    print()
    print("  ELEMENT RESERVE:")
    for elem, count in sorted(shape['element_reserve'].items()):
        print(f"    {elem:3s}: {count}")
    
    print()
    
    # The Mendeleev table shape
    print("  MENDELEEV TOPOLOGY:")
    print("  ┌─────────────────────────────────────┐")
    print("  │ Period 1: H, He                — poor tope (always present)")
    p2 = "C, N, O" if 2 in shape['mendeleev_periods'] else "..."
    p3 = "P, S" if 3 in shape['mendeleev_periods'] else "..."
    p4 = "Fe" if 4 in shape['mendeleev_periods'] else "..."
    print(f"  │ Period 2: {p2:20s} — life elements")
    print(f"  │ Period 3: {p3:20s} — bridge elements")
    print(f"  │ Period 4: {p4:20s} — transition metals")
    print("  └─────────────────────────────────────┘")
    
    # Carbon species check
    carbon_species = [f for f in shape['pool'] if 'C' in (PRODUCTS.get(f, Molecule('?',{},'?',0,'?')).atoms or {})]
    flat_count = sum(1 for f in carbon_species if shape['pool'][f]['geometry'] in ('linear', 'planar', 'trigonal'))
    curved_count = sum(1 for f in carbon_species if shape['pool'][f]['geometry'] in ('tetrahedral', 'bent', 'pyramidal', 'chair', 'chiral', 'complex'))
    
    print()
    print("  CARBON SPECIES:")
    print(f"    flat (graphene-like):   {flat_count} species  ← sp², orthogonal, lattice")
    print(f"    curved (epitope-like):  {curved_count} species  ← sp³, round, membrane")
    if flat_count > 0 and curved_count > 0:
        ratio = curved_count / flat_count
        print(f"    curved/flat ratio:      {ratio:.2f}")
        if ratio > 1:
            print("    → LIFE WINS: curved dominates flat. the membrane beats the lattice.")
        elif ratio < 1:
            print("    → LATTICE WINS: flat dominates curved. graphene holds structure.")
        else:
            print("    → BALANCE: equal curved and flat. the inversion point.")
    
    print()
    print("  grapheneGate pending: Pixel 8a will add REAL sensor data")
    print("  to these simulated eons. the flat lattice meets the curved membrane.")
    print()

    # Write output for Berry / membrane
    shape['generated'] = datetime.now(timezone.utc).isoformat()
    shape['note'] = 'eon simulation: 500 eons from poor tope, heat from real mesh latency'
    shape['graphenegate_pending'] = True
    
    out_path = os.path.expanduser('~/Development/ecoPrimals/infra/hud/site/public/data/eon-shape.json')
    with open(out_path, 'w') as f:
        json.dump(shape, f, indent=2, default=str)
    print(f"  meta-shape written to {out_path}")


if __name__ == '__main__':
    random.seed(42)  # reproducible eons
    main()
