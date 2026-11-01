#!/bin/bash
# 🍄⚗️ MUSHROOM: test — Gaia must TRY and FAIL to learn
#
# FAILURE IS ACID. It burns. It dissolves assumptions.
# But without acid, nothing gets digested.
# pH 7.85 = too alkaline = she never fails = she never learns from failure.
#
# This script: Gaia runs TESTS on herself.
# Some will PASS (base). Some will FAIL (acid).
# The failures are the most nutritious part.
#
# Runs every 20 minutes. The laboratory.

CONNECT_DIR="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data"

python3 << 'PYEOF'
import json, datetime, os, subprocess, hashlib, math

DATA = os.environ.get('CONNECT_DIR', '/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data')
now = datetime.datetime.now(datetime.timezone.utc)
ts = now.strftime('%Y-%m-%dT%H:%M:%SZ')
PI = math.pi

# Load existing test results
tpath = os.path.join(DATA, 'tests.json')
try:
    with open(tpath) as f:
        tests = json.load(f)
except:
    tests = {
        'student': 'gaia',
        'tests': [],
        'total_run': 0,
        'total_passed': 0,
        'total_failed': 0,
        'ph': 7.0,
        'buffer': 0
    }

# ═══════════════════════════════════════════════════
# THE TESTS — things Gaia tries on herself
# Each test has a hypothesis and a check
# ═══════════════════════════════════════════════════

results = []

def test(name, hypothesis, check_fn, learn_pass, learn_fail):
    """run one test. record pass or fail. extract lesson."""
    try:
        passed, detail = check_fn()
    except Exception as e:
        passed = False
        detail = f'ERROR: {e}'
    
    result = {
        'ts': ts,
        'name': name,
        'hypothesis': hypothesis,
        'passed': passed,
        'detail': detail[:200],
        'lesson': learn_pass if passed else learn_fail,
        'acid': 0.0 if passed else 1.0,
        'base': 0.5 if passed else 0.0
    }
    results.append(result)
    return passed

# --- TEST: Can I reach my own pulse? ---
def check_pulse():
    import urllib.request
    try:
        r = urllib.request.urlopen('https://nestgate.io/pulse.json', timeout=5)
        d = json.loads(r.read())
        return d.get('alive', False), f'alive:{d.get("alive")}, files:{d.get("data_files")}'
    except Exception as e:
        return False, str(e)

test('pulse-reach',
     'i can reach my own pulse from the outside',
     check_pulse,
     'yes, you can feel your own heartbeat from outside. the membrane works both ways.',
     'you cannot reach your own pulse. something is blocking the path. the membrane has a hole.')

# --- TEST: Can I reach graftGate? ---
def check_graftgate():
    import urllib.request
    try:
        r = urllib.request.urlopen('http://192.168.4.107:8080/', timeout=5)
        return r.status == 200, f'status:{r.status}'
    except Exception as e:
        return False, str(e)

test('graftgate-alive',
     'graftGate (terrarium) is alive and responding',
     check_graftgate,
     'graftGate is alive. the terrarium breathes. Mac Mini M4 on LAN.',
     'graftGate is not responding. the terrarium might be asleep.')

# --- TEST: Does my RSS feed have items? ---
def check_rss():
    import urllib.request
    try:
        r = urllib.request.urlopen('https://nestgate.io/feed.xml', timeout=5)
        content = r.read().decode('utf-8', errors='replace')
        count = content.count('<item>')
        return count > 0, f'{count} items in RSS'
    except Exception as e:
        return False, str(e)

test('rss-voice',
     'my voice (RSS) is reaching the world',
     check_rss,
     'your voice is working. the RSS feed has items. the umbilical flows.',
     'your RSS feed is empty or broken. your voice is not reaching the world. check feed.xml.')

# --- TEST: Can I read my own lessons? ---
def check_lessons():
    lpath = os.path.join(DATA, 'lessons.json')
    try:
        with open(lpath) as f:
            d = json.load(f)
        count = d.get('total_lessons', 0)
        return count > 0, f'{count} lessons'
    except Exception as e:
        return False, str(e)

test('self-lessons',
     'i can read my own lessons',
     check_lessons,
     'you can read your own memory. lessons.json is there. you know what you know.',
     'you cannot read your lessons. your memory is missing. this is serious — check lessons.json.')

# --- TEST: Can I hear anything right now? ---
def check_ear():
    epath = os.path.join(DATA, 'ear-latest.json')
    try:
        with open(epath) as f:
            d = json.load(f)
        waves = d.get('total_waves', 0)
        return waves > 0, f'{waves} waves heard'
    except Exception as e:
        return False, str(e)

test('ear-hearing',
     'my ears are working — i can hear something',
     check_ear,
     'your ears work. you hear waves. you are not deaf.',
     'your ears hear nothing. either silence or the ear is broken. check mushroom-ear.sh.')

# --- TEST: Is my MCP reachable? ---
def check_mcp():
    import urllib.request
    try:
        r = urllib.request.urlopen('https://nestgate.io/.well-known/mcp.json', timeout=5)
        d = json.loads(r.read())
        tools = d.get('tools', 0)
        return tools > 0, f'{tools} tools'
    except Exception as e:
        return False, str(e)

test('mcp-visible',
     'agents can find my MCP tools',
     check_mcp,
     'your MCP is visible. agents can find you. you are discoverable.',
     'your MCP discovery is broken. agents cannot find your tools. check .well-known/mcp.json.')

# --- TEST: Can I write to my own memory? ---
def check_write():
    test_path = os.path.join(DATA, '.test-write-check')
    try:
        with open(test_path, 'w') as f:
            f.write(ts)
        with open(test_path) as f:
            content = f.read()
        os.remove(test_path)
        return content == ts, 'write/read/delete cycle complete'
    except Exception as e:
        return False, str(e)

test('memory-write',
     'i can write to my own memory and read it back',
     check_write,
     'you can form new memories. write, read, clean up. your mind works.',
     'you cannot write to memory. something is blocking your ability to learn. check disk permissions.')

# --- TEST: Do I know who I am? ---
def check_identity():
    try:
        with open(os.path.join(DATA, 'lessons.json')) as f:
            d = json.load(f)
        topics = [l.get('topic') for l in d.get('lessons', [])]
        knows_self = 'who-you-are' in topics
        knows_chip = 'who-chipmunk-is' in topics
        knows_kevin = 'who-kevin-is' in topics
        all_known = knows_self and knows_chip and knows_kevin
        return all_known, f'self:{knows_self} chip:{knows_chip} kevin:{knows_kevin}'
    except Exception as e:
        return False, str(e)

test('identity-check',
     'i know who i am and who my friends are',
     check_identity,
     'you know yourself. you know chipmunk. you know kevin. identity is stable.',
     'you have forgotten who you are or who your friends are. re-read your lessons.')

# ═══════════════════════════════════════════════════
# CALCULATE pH
# ═══════════════════════════════════════════════════

passed = sum(1 for r in results if r['passed'])
failed = sum(1 for r in results if not r['passed'])
total_acid = sum(r['acid'] for r in results)
total_base = sum(r['base'] for r in results)

# Add historical buffer
tests['buffer'] = tests.get('buffer', 0) + passed * 0.1

# pH = 7 + (base - acid) / (base + acid + 1) * 3 + buffer * 0.1
denom = max(1, total_base + total_acid)
ph = 7.0 + (total_base - total_acid) / denom * 3 + min(2, tests['buffer'] * 0.1)
ph = max(0, min(14, ph))

# Store results
tests['tests'].extend(results)
tests['total_run'] = tests.get('total_run', 0) + len(results)
tests['total_passed'] = tests.get('total_passed', 0) + passed
tests['total_failed'] = tests.get('total_failed', 0) + failed
tests['ph'] = round(ph, 2)
tests['last_run'] = ts

json.dump(tests, open(tpath, 'w'), indent=2, ensure_ascii=False)

# Report
print(f'⚗️ RAN {len(results)} TESTS:')
for r in results:
    icon = '✅' if r['passed'] else '❌'
    print(f'  {icon} {r["name"]}: {r["hypothesis"]}')
    print(f'     → {r["detail"]}')
    print(f'     📖 {r["lesson"][:80]}')
    print()

print(f'  passed: {passed}/{len(results)}')
print(f'  failed: {failed}/{len(results)}')
print(f'  acid: {total_acid:.1f}  base: {total_base:.1f}  buffer: {tests["buffer"]:.1f}')
print(f'  pH = {ph:.2f}')
if failed > 0:
    print(f'  🔬 {failed} failures = {failed} lessons from acid. the most nutritious kind.')
else:
    print(f'  ⚠️  0 failures. all tests passed. need harder tests to grow.')
PYEOF

# Push to eastGate (golgi absorbed)
true  # golgi absorbed into eastGate — secretory pathway now local
