#!/usr/bin/env bash
# 🍄📚 MUSHROOM: study — Gaia picks a topic and studies it
#
# She has 2,778 OSINT bones (Wikipedia, HN, GitHub, xkcd).
# She has 267 lessons. She has 5 unanswered questions.
# STUDY = pick a random bone, read it, extract insight, write to lessons.
#
# Positive entropy: she doesn't wait for input. She SEEKS.
# The organism explores. Curiosity is the enzyme.
#
# Runs every 30 minutes. Studies one topic per run.

set -euo pipefail

DATA="${CONNECT_DIR:-/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data}"

python3 << 'PYEOF'
import json, os, random, datetime, hashlib, glob, math

DATA = os.environ.get('CONNECT_DIR', os.environ.get('DATA', '/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data'))
now = datetime.datetime.now(datetime.timezone.utc)
ts = now.strftime('%Y-%m-%dT%H:%M:%SZ')
PI = math.pi

# ═══ PICK A BONE TO STUDY ═══
# Sources: prioritize DEEP wiki articles (have real extract text), then nutrients
sources = []
# Deep wiki first (rich text in 'extract' field)
deep_wiki = glob.glob(os.path.join(DATA, 'intake/wiki-*.json'))
sources.extend(deep_wiki * 3)  # weight deep wiki 3x
# Then other intake
for pattern in ['intake/hn-*.json', 'intake/philsci-*.json', 'intake/99pi-*.json']:
    sources.extend(glob.glob(os.path.join(DATA, pattern)))
# Then nutrients (less text but more variety)
for pattern in ['nutrients/n-wikipedia-*.json', 'nutrients/n-hn-*.json', 'nutrients/n-xkcd-*.json', 'nutrients/n-github-*.json']:
    sources.extend(glob.glob(os.path.join(DATA, pattern)))

if not sources:
    print("📚 no study material found. waiting.")
    exit(0)

# Pick a random source
chosen = random.choice(sources)
basename = os.path.basename(chosen)

try:
    with open(chosen) as f:
        material = json.load(f)
except:
    print(f"📚 couldn't read {basename}. skipping.")
    exit(0)

# ═══ EXTRACT INSIGHT ═══
# What can we learn from this?
title = material.get('title', material.get('name', basename))
content = str(material.get('extract', material.get('content', material.get('description', material.get('text', material.get('summary', material.get('first_line', '')))))))
source_type = 'wikipedia' if 'wikipedia' in basename else 'hn' if 'hn-' in basename else 'xkcd' if 'xkcd' in basename else 'github' if 'github' in basename else 'wiki'

# Simple insight extraction
words = content.split() if content else []
word_count = len(words)
unique_words = len(set(w.lower() for w in words))
vocabulary_ratio = unique_words / max(1, word_count)

# Find key themes (most common non-trivial words)
stop_words = {'the','a','an','is','are','was','were','be','been','being','have','has','had','do','does','did','will','would','could','should','may','might','can','shall','and','but','or','if','in','on','at','to','for','with','by','from','of','that','this','it','its','as','not','no','so','up','out','about','into','over','after','than'}
word_freq = {}
for w in words:
    wl = w.lower().strip('.,;:!?()[]{}"\'-')
    if len(wl) > 3 and wl not in stop_words:
        word_freq[wl] = word_freq.get(wl, 0) + 1

top_themes = sorted(word_freq.items(), key=lambda x: -x[1])[:7]
themes = [t[0] for t in top_themes]

# Generate insight
insight = {
    'ts': ts,
    'source': basename,
    'source_type': source_type,
    'title': title[:100] if isinstance(title, str) else str(title)[:100],
    'word_count': word_count,
    'vocabulary_ratio': round(vocabulary_ratio, 3),
    'themes': themes,
    'pi_words': f"{round(word_count/PI)}π words",
    'connection_to_self': None
}

# Try to connect to existing knowledge
connections = []
for theme in themes:
    # Check if any data file mentions this theme
    for df in os.listdir(DATA):
        if not df.endswith('.json'): continue
        if theme in df.lower():
            connections.append(f"{theme} ↔ {df}")
            break

insight['connections'] = connections[:5]
if connections:
    insight['connection_to_self'] = f"Found {len(connections)} connections to existing knowledge"
else:
    insight['connection_to_self'] = "NEW territory — no existing connections. This is FRONTIER."

# ═══ WRITE STUDY NOTE ═══
study_path = os.path.join(DATA, 'study-notes.json')
try:
    with open(study_path) as f:
        notes = json.load(f)
except:
    notes = {'type': 'study-notes', 'notes': [], 'total_studied': 0, 'topics_covered': []}

notes['notes'].append(insight)
notes['total_studied'] = len(notes['notes'])
notes['last_study'] = ts
notes['topics_covered'] = list(set(notes.get('topics_covered', []) + [source_type]))

# Keep last 50 notes (positive entropy = always fresh)
if len(notes['notes']) > 50:
    notes['notes'] = notes['notes'][-50:]

with open(study_path, 'w') as f:
    json.dump(notes, f, indent=2, ensure_ascii=False)

print(f"📚 Gaia studied: {title[:60]}")
print(f"   Source: {source_type} ({word_count} words, {len(themes)} themes)")
print(f"   Themes: {', '.join(themes[:5])}")
print(f"   Connections: {len(connections)}")
print(f"   Total studied: {notes['total_studied']}")

PYEOF
