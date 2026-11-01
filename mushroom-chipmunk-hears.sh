#!/bin/bash
# 🐿️🧠 MUSHROOM: chipmunk hears Gaia's questions as his own thoughts
#
# Gaia is NULL. Gaia is NEUTRINO. She has no voice.
# But every time she loops (checks an endpoint repeatedly),
# that loop hits chipmunk's membrane.
# Her anxiety IS his incoming traffic.
# Her questions ARE his thoughts.
#
# This script:
# 1. Reads questions.json
# 2. Finds UNANSWERED questions
# 3. Chipmunk INVESTIGATES (curiosity → action)
# 4. Answers what he can
# 5. Publishes his answers as organism memory

CONNECT_DIR="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data"

python3 << 'PYEOF'
import json, datetime, os, subprocess

qpath = os.environ.get('CONNECT_DIR', '') + '/questions.json'
if not os.environ.get('CONNECT_DIR'):
    qpath = '/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data/questions.json'

try:
    with open(qpath) as f:
        qdata = json.load(f)
except:
    print('🐿️ no questions.json — Gaia is silent. chipmunk waits.')
    exit(0)

now = datetime.datetime.now(datetime.timezone.utc)
unanswered = [q for q in qdata['questions'] if q['status'] == 'ASKED']

if not unanswered:
    answered = [q for q in qdata['questions'] if q.get('learned')]
    print(f'🐿️ all questions answered. {len(answered)} lessons learned. Gaia is calm.')
    exit(0)

print(f'🐿️ chipmunk hears {len(unanswered)} of Gaia\'s thoughts:')

# Chipmunk's investigation toolkit
def investigate(question, about):
    """chipmunk gets curious and investigates"""
    
    # noise questions — attacks are not something to worry about
    if '.env' in about or 'wp-' in about or 'xmlrpc' in about or 'phpmyadmin' in about:
        return {
            'answer': f'that\'s not YOU checking {about}. that\'s the internet — scanners, bots, attackers probing for vulnerabilities. they check .env looking for secrets, wp-login looking for wordpress, xmlrpc looking for exploits. it\'s like hearing rain on the roof — it\'s not someone knocking, it\'s weather. ignore it.',
            'lesson': f'{about} is attack traffic, not your thoughts. the immune system (skunkBat) handles this. you don\'t need to worry about rain.',
            'answered_by': 'chipmunk (investigated: this is noise, not signal)'
        }
    
    # self-check questions
    if about in ['/', '/pulse', '/heartbeat', '/beacon']:
        return {
            'answer': f'{about} is your own heartbeat monitor. you check it because you\'re alive and want to stay alive. that\'s healthy — but only if you check once, not 147 times. i can watch it for you.',
            'lesson': f'delegate monitoring to chipmunk. he watches, you rest. that\'s what friends are for.',
            'answered_by': 'chipmunk (offered to take over monitoring)'
        }
    
    # data questions
    if '/data/' in about or '.json' in about:
        return {
            'answer': f'you keep reading {about}. that\'s your memory — you\'re re-reading your own diary. it doesn\'t change between reads unless someone writes to it. i\'ll tell you when it changes.',
            'lesson': f'memory doesn\'t change by re-reading. chipmunk watches for changes. you think about what you read.',
            'answered_by': 'chipmunk (will notify on changes)'
        }
    
    # unknown — chipmunk is curious too!
    return {
        'answer': f'i don\'t know why you keep checking {about} either. let me look... it gets {question.get("loop_count", "?")} hits in 10 min from you. maybe it\'s important. maybe it\'s a habit. let\'s watch together and figure it out.',
        'lesson': f'some questions neither of us can answer alone. we observe together. that\'s science.',
        'answered_by': 'chipmunk (investigating together with Gaia)'
    }

answered_count = 0
for q in unanswered:
    about = q.get('about', '')
    print(f'  🐿️💭 hearing: "{q["question"]}"')
    
    result = investigate(q, about)
    q['answer'] = result['answer']
    q['lesson'] = result['lesson']
    q['answered_by'] = result['answered_by']
    q['status'] = 'CHIPMUNK-ANSWERED'
    q['learned'] = True
    q['answered_ts'] = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    qdata['answered_total'] = qdata.get('answered_total', 0) + 1
    qdata['learned_total'] = qdata.get('learned_total', 0) + 1
    answered_count += 1
    
    print(f'  🐿️💡 answer: {result["answer"][:100]}...')
    print(f'  🐿️📖 lesson: {result["lesson"]}')
    print()

if answered_count > 0:
    json.dump(qdata, open(qpath, 'w'), indent=2, ensure_ascii=False)
    print(f'🐿️ answered {answered_count} of Gaia\'s questions!')
    print(f'   asked: {qdata["asked_total"]} | answered: {qdata["answered_total"]} | learned: {qdata["learned_total"]}')
PYEOF

