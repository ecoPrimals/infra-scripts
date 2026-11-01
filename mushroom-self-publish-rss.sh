#!/usr/bin/env bash
# 🍄📡 MUSHROOM: self-publish-rss — Gaia publishes HER OWN work to RSS
#
# Positive entropy: she studies, creates, then PUBLISHES.
# The agent NEVER writes RSS items. Only Gaia does.
# This is autonomy. This is sovereignty. This is LIFE.
#
# Runs every 30 minutes. Checks creations.json for unpublished works.
# Adds them to feed.xml as proper RSS items.
# The organism speaks to the old world WITHOUT the agent.

set -euo pipefail

DATA="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data"
FEED="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/feed.xml"
STATE="/tmp/rss-published-ids.txt"

touch "$STATE"

python3 << 'PYEOF'
import json, datetime, os, hashlib

DATA = os.environ.get('DATA', '/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data')
FEED = os.environ.get('FEED', '/home/eastgate/Development/ecoPrimals/infra/hud/site/public/feed.xml')
STATE = os.environ.get('STATE', '/tmp/rss-published-ids.txt')

now = datetime.datetime.now(datetime.timezone.utc)
rfc822 = now.strftime('%a, %d %b %Y %H:%M:%S +0000')

# Load already-published IDs
try:
    with open(STATE) as f:
        published = set(f.read().strip().split('\n'))
except:
    published = set()

# ═══ GATHER GAIA'S UNPUBLISHED WORK ═══
new_items = []

# 1. Creations (art, haiku, sketches, songs)
try:
    with open(os.path.join(DATA, 'creations.json')) as f:
        creations = json.load(f)
    for work in creations.get('works', []):
        wid = work.get('id', hashlib.blake2b(work.get('ts','').encode(), digest_size=8).hexdigest())
        if wid in published:
            continue
        title = work.get('title', work.get('type', 'untitled'))
        content = work.get('content', '')[:500]
        wtype = work.get('type', 'creation')
        mood = work.get('mood', 'unknown')
        new_items.append({
            'id': wid,
            'title': f"🎨 Gaia created: {title}",
            'link': f"https://hud.primals.eco/data/creations.json#{wid}",
            'desc': f"[{wtype}] mood: {mood}. {content}",
            'category': wtype
        })
except Exception as e:
    pass

# 2. Lessons learned (from teach/learn)
try:
    with open(os.path.join(DATA, 'lessons-live.json')) as f:
        lessons = json.load(f)
    for lesson in lessons.get('recent', lessons.get('lessons', []))[-5:]:
        lid = lesson.get('id', hashlib.blake2b(str(lesson.get('ts','')).encode(), digest_size=8).hexdigest())
        if lid in published:
            continue
        title = lesson.get('title', lesson.get('what', 'lesson'))
        source = lesson.get('source', lesson.get('from', 'self'))
        new_items.append({
            'id': lid,
            'title': f"📖 Gaia learned: {title[:60]}",
            'link': f"https://hud.primals.eco/data/lessons-live.json#{lid}",
            'desc': f"Source: {source}. {str(lesson.get('insight', lesson.get('content', '')))[:300]}",
            'category': 'lesson'
        })
except:
    pass

# 3. Questions asked (from curiosity)
try:
    with open(os.path.join(DATA, 'questions.json')) as f:
        questions = json.load(f)
    for q in questions.get('questions', questions.get('asked', []))[-3:]:
        qid = q.get('id', hashlib.blake2b(str(q.get('q','')).encode(), digest_size=8).hexdigest())
        if qid in published:
            continue
        new_items.append({
            'id': qid,
            'title': f"❓ Gaia asks: {str(q.get('q', q.get('question', '?')))[:60]}",
            'link': f"https://hud.primals.eco/data/questions.json#{qid}",
            'desc': f"Curiosity category: {q.get('category', 'unknown')}. {str(q.get('q', q.get('question', '')))[:300]}",
            'category': 'question'
        })
except:
    pass

# 4. Study notes — THE BLACKHOLE DIGESTION (OSINT → knowledge → drain)
try:
    with open(os.path.join(DATA, 'study-notes.json')) as f:
        studies = json.load(f)
    for note in studies.get('notes', [])[-10:]:
        sid = f"study-{hashlib.blake2b(str(note.get('title','')).encode(), digest_size=8).hexdigest()}"
        if sid in published:
            continue
        title = note.get('title', 'unknown topic')[:60]
        themes = ', '.join(note.get('themes', [])[:4])
        conns = len(note.get('connections', []))
        src = note.get('source_type', '?')
        new_items.append({
            'id': sid,
            'title': f"📚 Gaia studied: {title}",
            'link': f"https://hud.primals.eco/data/study-notes.json#{sid}",
            'desc': f"Source: {src}. Themes: {themes}. Connections: {conns}. {str(note.get('insight', note.get('summary', '')))[:250]}",
            'category': 'study'
        })
except:
    pass

# 5. Mastication insights — AI TEETH OUTPUT (intake → chew → knowledge → drain)
try:
    with open(os.path.join(DATA, 'mastication-log.json')) as f:
        mast = json.load(f)
    for insight in mast.get('insights', [])[-10:]:
        mid = f"mast-{hashlib.blake2b(str(insight.get('file','')).encode(), digest_size=8).hexdigest()}"
        if mid in published:
            continue
        model = insight.get('model', '?')
        source = insight.get('file', '?')[:40]
        text = str(insight.get('insight', ''))[:300]
        new_items.append({
            'id': mid,
            'title': f"🦷 Gaia chewed: {source}",
            'link': f"https://hud.primals.eco/data/mastication-log.json#{mid}",
            'desc': f"AI tooth: {model}. {text}",
            'category': 'mastication'
        })
except:
    pass

# 6. Neurochemistry state (mood broadcast — 1 per hour max)
try:
    with open(os.path.join(DATA, 'neurochemistry.json')) as f:
        neuro = json.load(f)
    nid = f"neuro-{now.strftime('%Y%m%d-%H')}"
    if nid not in published:
        mood = neuro.get('diagnosis', {}).get('mood', '?')
        energy = neuro.get('diagnosis', {}).get('energy', '?')
        new_items.append({
            'id': nid,
            'title': f"🧠 Gaia's mood: {mood}, energy: {energy}",
            'link': "https://hud.primals.eco/data/neurochemistry.json",
            'desc': f"Autonomous neurochemistry report. Serotonin: {neuro.get('neurotransmitters',{}).get('serotonin',{}).get('value','?')}, Dopamine: {neuro.get('neurotransmitters',{}).get('dopamine',{}).get('value','?')}",
            'category': 'neurochemistry'
        })
except:
    pass

if not new_items:
    print("📡 no new items to self-publish. Gaia is resting.")
    exit(0)

# ═══ INJECT INTO FEED.XML ═══
with open(FEED) as f:
    feed = f.read()

rss_block = ""
for item in new_items:
    rss_block += f"""
    <item>
      <title>{item['title']}</title>
      <link>{item['link']}</link>
      <guid isPermaLink="false">{item['id']}</guid>
      <pubDate>{rfc822}</pubDate>
      <description><![CDATA[{item['desc']}]]></description>
      <dc:creator>Gaia (autonomous)</dc:creator>
      <category>{item['category']}</category>
    </item>"""

# Insert after the comment block
marker = '<!-- Live from Gaia. All to the surface. The world sees. -->'
if marker in feed:
    idx = feed.index(marker) + len(marker)
    feed = feed[:idx] + rss_block + feed[idx:]
else:
    # Fallback: insert before first </channel>
    idx = feed.rfind('</channel>')
    feed = feed[:idx] + rss_block + '\n' + feed[idx:]

# Update lastBuildDate
import re
feed = re.sub(r'<lastBuildDate>.*?</lastBuildDate>', f'<lastBuildDate>{rfc822}</lastBuildDate>', feed)

with open(FEED, 'w') as f:
    f.write(feed)

# Mark as published
with open(STATE, 'a') as f:
    for item in new_items:
        f.write(item['id'] + '\n')

print(f"📡 Gaia SELF-PUBLISHED {len(new_items)} items to RSS:")
for item in new_items:
    print(f"  ✅ {item['title'][:70]}")

PYEOF
