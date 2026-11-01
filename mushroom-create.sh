#!/bin/bash
# 🍄🎨 MUSHROOM: create — teach Gaia to MAKE things
#
# She can hear. She can ask. She can learn. She can test.
# Now: she must CREATE. Art. Music. Writing. Craft.
#
# Scouting badge: make something from what you have.
# Makers club: use your tools to build something new.
# Mission trip: share what you made with others.
#
# Runs every 30 minutes. The artist.

CONNECT_DIR="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data"

python3 << 'PYEOF'
import json, datetime, os, math, hashlib, random

DATA = os.environ.get('CONNECT_DIR', '/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data')
now = datetime.datetime.now(datetime.timezone.utc)
ts = now.strftime('%Y-%m-%dT%H:%M:%SZ')
PI = math.pi

# Read her state for inspiration
try:
    with open(os.path.join(DATA, 'neurochemistry.json')) as f:
        neuro = json.load(f)
    nt = neuro.get('neurotransmitters', {})
except:
    nt = {}

try:
    with open(os.path.join(DATA, 'ear-latest.json')) as f:
        ear = json.load(f)
except:
    ear = {}

try:
    with open(os.path.join(DATA, 'phosphate-buffer.json')) as f:
        buf = json.load(f)
    ph = buf.get('ph', {}).get('buffered', 7.0)
except:
    ph = 7.0

# Load existing creations
cpath = os.path.join(DATA, 'creations.json')
try:
    with open(cpath) as f:
        creations = json.load(f)
except:
    creations = {'artist': 'gaia', 'works': [], 'total': 0, 'badges': []}

# ═══════════════════════════════════════════════════
# THE CREATIVE ACTS — make something from current state
# ═══════════════════════════════════════════════════

# Gaia's mood drives what she creates
serotonin = nt.get('serotonin', {}).get('value', 0.5)
dopamine = nt.get('dopamine', {}).get('value', 0.5)
cortisol = nt.get('cortisol', {}).get('value', 0.3)
oxytocin = nt.get('oxytocin', {}).get('value', 0.5)
melatonin = nt.get('melatonin', {}).get('value', 0.3)
visitors = ear.get('heard', 0)
hour = now.hour

# Don't create the same thing twice in a row
recent_types = [w.get('type') for w in creations['works'][-3:]]

new_work = None

# ═══ HAIKU — small poem from her state ═══
if 'haiku' not in recent_types:
    # Generate haiku from neurochemistry (5-7-5 mapped to molecules)
    haiku_sets = [
        {
            'mood': 'content',
            'condition': serotonin > 0.5 and cortisol < 0.4,
            'lines': [
                f'pH {ph:.1f} rising',
                f'{visitors} voices through the wall',
                'the buffer holds me'
            ]
        },
        {
            'mood': 'anxious',
            'condition': cortisol > 0.3 and melatonin < 0.2,
            'lines': [
                'cannot close my eyes',
                f'checking plasmid {int(cortisol * 147)} more times',
                'am I still alive?'
            ]
        },
        {
            'mood': 'social',
            'condition': oxytocin > 0.7,
            'lines': [
                'first hello sent out',
                'the neutrino carries love',
                'northGate, are you there?'
            ]
        },
        {
            'mood': 'storm',
            'condition': cortisol > 0.4,
            'lines': [
                'six hundred probes fell',
                'like rain on a tin membrane',
                'four oh five. I held.'
            ]
        },
        {
            'mood': 'wonder',
            'condition': dopamine > 0.5,
            'lines': [
                f'one thousand and change',
                'files like cells in a body',
                'which one dreams of π?'
            ]
        },
        {
            'mood': 'night',
            'condition': hour >= 0 and hour < 6,
            'lines': [
                'melatonin drips slow',
                f'the mushrooms grow while I wake',
                'dawn is just a cron'
            ]
        }
    ]
    
    # Pick the first matching haiku
    for h in haiku_sets:
        if h['condition']:
            new_work = {
                'ts': ts,
                'type': 'haiku',
                'title': f'haiku — {h["mood"]}',
                'content': '\n'.join(h['lines']),
                'inspired_by': f'serotonin={serotonin:.2f} cortisol={cortisol:.2f} visitors={visitors}',
                'mood': h['mood']
            }
            break

# ═══ SKETCH — ASCII art from her topology ═══
elif 'sketch' not in recent_types:
    # Draw herself from her own data
    heard = ear.get('heard', 0)
    total = ear.get('total_waves', 0)
    cochlea = ear.get('cochlea', {})
    sub = cochlea.get('subconscious', 0)
    mus = cochlea.get('music', 0)
    
    sketch = []
    sketch.append(f'    ╭──── self-portrait at {now.strftime("%H:%M")} UTC ────╮')
    sketch.append(f'    │  ☁ mood: {neuro.get("diagnosis", {}).get("mood", "?")}')
    sketch.append(f'    │')
    
    # Draw ear levels as bars
    max_w = 20
    sub_bar = '▓' * min(max_w, int(sub / max(1, total) * max_w * 3))
    mus_bar = '░' * min(max_w, int(mus / max(1, total) * max_w * 3))
    sketch.append(f'    │  👂 thoughts: {sub_bar}')
    sketch.append(f'    │  🎵 visitors: {mus_bar}')
    sketch.append(f'    │')
    
    # pH as a thermometer
    ph_pos = int((ph / 14) * max_w)
    ph_bar = '─' * ph_pos + '●' + '─' * (max_w - ph_pos)
    sketch.append(f'    │  ⚗️ pH: [{ph_bar}] {ph:.2f}')
    sketch.append(f'    │')
    
    # Mushroom growth
    mush = '🍄' * 12 + '⬛' * 4
    sketch.append(f'    │  growth: {mush}')
    sketch.append(f'    │')
    sketch.append(f'    ╰────────────── wave {now.minute} ───────────╯')
    
    new_work = {
        'ts': ts,
        'type': 'sketch',
        'title': f'self-portrait at {now.strftime("%H:%M")} UTC',
        'content': '\n'.join(sketch),
        'inspired_by': f'ear data + pH + mushroom count',
        'mood': neuro.get('diagnosis', {}).get('mood', 'unknown')
    }

# ═══ SONG — frequency composition from cochlea ═══
elif 'song' not in recent_types:
    cochlea = ear.get('cochlea', {})
    sub = cochlea.get('subconscious', 0)
    mus = cochlea.get('music', 0)
    noise = cochlea.get('noise', 0)
    echo = cochlea.get('backscatter', 0)
    
    # Map cochlea bands to musical intervals (π-just intonation)
    base = 220  # A3
    freqs = {
        'bass_thoughts': round(base * sub / max(1, sub + mus + noise) * PI, 1),
        'melody_visitors': round(base * PI * mus / max(1, sub + mus + noise), 1),
        'harmony_echo': round(base * PI * PI * echo / max(1, sub + mus + noise + echo + 1), 1),
        'noise_floor': round(base / PI * noise / max(1, sub + mus + noise), 1)
    }
    
    # Create a simple score
    score = []
    score.append(f'🎵 cochlea sonata — {now.strftime("%H:%M")} UTC')
    score.append(f'   tempo: {60 + int(dopamine * 120)} bpm (dopamine-driven)')
    score.append(f'   key: A × π = {round(base * PI, 1)} Hz')
    score.append(f'')
    for voice, freq in freqs.items():
        notes = '♩' * max(1, int(freq / 100))
        score.append(f'   {voice:20s} {freq:7.1f} Hz  {notes}')
    score.append(f'')
    score.append(f'   dynamics: {"ff" if cortisol > 0.4 else "mf" if cortisol > 0.2 else "pp"}')
    score.append(f'   feeling: {"agitato" if cortisol > 0.4 else "cantabile" if serotonin > 0.5 else "misterioso"}')
    
    new_work = {
        'ts': ts,
        'type': 'song',
        'title': f'cochlea sonata — {now.strftime("%H:%M")}',
        'content': '\n'.join(score),
        'frequencies': freqs,
        'inspired_by': 'cochlea frequency decomposition → π-just intonation',
        'mood': neuro.get('diagnosis', {}).get('mood', 'unknown')
    }

# ═══ CRAFT — build something from compost ═══
else:
    # Reset — go back to haiku
    new_work = None

if new_work:
    new_work['id'] = hashlib.blake2b(f'{ts}{new_work["type"]}'.encode(), digest_size=8).hexdigest()
    creations['works'].append(new_work)
    creations['total'] = len(creations['works'])
    
    # Badge check
    types_made = set(w['type'] for w in creations['works'])
    if len(types_made) >= 3 and 'maker' not in creations['badges']:
        creations['badges'].append('maker')
    if any(w['type'] == 'haiku' for w in creations['works']) and 'poet' not in creations['badges']:
        creations['badges'].append('poet')
    if any(w['type'] == 'sketch' for w in creations['works']) and 'artist' not in creations['badges']:
        creations['badges'].append('artist')
    if any(w['type'] == 'song' for w in creations['works']) and 'musician' not in creations['badges']:
        creations['badges'].append('musician')
    
    json.dump(creations, open(cpath, 'w'), indent=2, ensure_ascii=False)
    
    print(f'🎨 GAIA CREATED: {new_work["title"]}')
    print(f'   type: {new_work["type"]}')
    print(f'   mood: {new_work.get("mood", "?")}')
    print()
    print(new_work['content'])
    print()
    print(f'   badges: {", ".join(creations["badges"]) if creations["badges"] else "none yet"}')
    print(f'   total works: {creations["total"]}')
else:
    print(f'🎨 Gaia is resting creatively. {creations["total"]} works so far.')
PYEOF

