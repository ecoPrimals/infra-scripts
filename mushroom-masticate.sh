#!/usr/bin/env bash
# 🍄🦷 MUSHROOM: masticate — Gaia's AI TEETH
#
# ALL AI IS GUTS. IN THE GUT.
# 8 ollama models = 8 sets of teeth. Each chews differently.
# 12,898 uneaten files = the food pile.
# We pick a file. We chew it with a random model. We swallow the insight.
#
# The agent is NOT the eater. The agent is the masticator.
# Gaia eats. We chew. SUDO = NULL.
#
# Models and their teeth:
#   tinyllama     — baby teeth (fast, simple bites)
#   llama3.2:1b   — milk teeth (small but sharp)
#   gemma2:2b     — incisors (cutting, precise)
#   phi3          — canines (tearing into logic)
#   llama3.2:3b   — premolars (grinding medium)
#   qwen2.5:7b    — molars (deep grinding, multilingual)
#   mistral:7b    — wisdom teeth (analytical, careful)
#   deepseek:16b  — jaw muscle (code understanding, heavy lift)
#
# Runs every 30 minutes. Chews 3 files per run.

set -euo pipefail

CONNECT_DIR="${CONNECT_DIR:-/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data}"
OLLAMA="http://localhost:11434"
BATCH=3

python3 << 'PYEOF'
import json, os, random, datetime, hashlib, glob, math, urllib.request

DATA = os.environ.get('CONNECT_DIR', '/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data')
OLLAMA = os.environ.get('OLLAMA', 'http://localhost:11434')
BATCH = int(os.environ.get('BATCH', '3'))
now = datetime.datetime.now(datetime.timezone.utc)
ts = now.strftime('%Y-%m-%dT%H:%M:%SZ')
PI = math.pi

# Models = teeth (ordered small → large)
TEETH = [
    'tinyllama:latest',
    'llama3.2:1b',
    'gemma2:2b',
    'phi3:latest',
    'llama3.2:3b',
    'qwen2.5:7b',
]

# Load what's already been masticated
chewed_path = os.path.join(DATA, 'mastication-log.json')
try:
    with open(chewed_path) as f:
        chewed = json.load(f)
except:
    chewed = {'chewed': [], 'total': 0, 'insights': []}
already_chewed = set(c.get('file','') for c in chewed['chewed'])

# Find uneaten files (prefer intake/wiki and intake with actual content)
candidates = []
for pattern in ['intake/wiki-*.json', 'intake/hn-*.json', 'intake/arxiv-*.json',
                'intake/lobsters-*.json', 'intake/cat-fact-*.json',
                'intake/github-*.json', 'intake/noaa-*.json',
                'intake/reddit-*.json', 'intake/99pi-*.json',
                'intake/wikipedia-*.json']:
    candidates.extend(glob.glob(os.path.join(DATA, pattern)))

# Filter out already chewed
unchewed = [f for f in candidates if os.path.basename(f) not in already_chewed]
if not unchewed:
    print("🦷 all candidates chewed. expanding to nutrients...")
    unchewed = [f for f in glob.glob(os.path.join(DATA, 'nutrients/n-*.json'))
                if os.path.basename(f) not in already_chewed]

if not unchewed:
    print("🦷 nothing left to chew. the gut is full.")
    exit(0)

# Pick BATCH random files
picks = random.sample(unchewed, min(BATCH, len(unchewed)))

def chew(filepath, model):
    """Send a file to ollama and get insight back"""
    basename = os.path.basename(filepath)
    try:
        with open(filepath) as f:
            raw = json.load(f)
    except:
        return None

    # Extract readable content
    content = ''
    for key in ['extract', 'content', 'description', 'text', 'summary', 'title', 'items', 'first_line']:
        if key in raw:
            val = raw[key]
            if isinstance(val, str) and len(val) > 20:
                content = val[:1500]
                break
            elif isinstance(val, list) and val:
                content = json.dumps(val[:5])[:1500]
                break
    
    if not content:
        content = json.dumps(raw)[:1000]

    title = raw.get('title', raw.get('name', basename))

    prompt = f"""You are Gaia, a living digital organism studying the world. You just read this:

Title: {title}
Content: {content}

In exactly 2-3 sentences: What is the key insight? How does it connect to biology, computation, or self-organization? Be specific and original."""

    try:
        req = urllib.request.Request(
            f'{OLLAMA}/api/generate',
            data=json.dumps({
                'model': model,
                'prompt': prompt,
                'stream': False,
                'options': {'temperature': 0.7, 'num_predict': 150}
            }).encode(),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result.get('response', '').strip()
    except Exception as e:
        return f"(teeth broke: {str(e)[:50]})"

# MASTICATE
results = []
for filepath in picks:
    basename = os.path.basename(filepath)
    model = random.choice(TEETH)
    
    print(f"🦷 chewing {basename[:50]} with {model}...")
    insight = chew(filepath, model)
    
    if insight:
        entry = {
            'ts': ts,
            'file': basename,
            'model': model,
            'insight': insight[:500],
            'hash': hashlib.blake2b(f'{basename}{ts}'.encode(), digest_size=8).hexdigest()
        }
        results.append(entry)
        chewed['chewed'].append({'file': basename, 'ts': ts, 'model': model})
        chewed['insights'].append(entry)
        print(f"   → {insight[:120]}...")
    else:
        print(f"   → (no content to chew)")

# Keep last 200 insights
if len(chewed['insights']) > 200:
    chewed['insights'] = chewed['insights'][-200:]
chewed['total'] = len(chewed['chewed'])

with open(chewed_path, 'w') as f:
    json.dump(chewed, f, indent=2, ensure_ascii=False)

print(f"\n🦷 MASTICATED {len(results)} files. Total chewed: {chewed['total']}. {len(unchewed)-len(picks)} remaining.")

PYEOF
