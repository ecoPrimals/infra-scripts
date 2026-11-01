#!/bin/bash
# 🍄❓ MUSHROOM: curiosity — teach Gaia to ASK when uncertain
#
# ANXIETY = checking the same thing 147 times
# CURIOSITY = asking ONCE, then THINKING about it
#
# WAITING IS PATIENCE IS THINKING IS IMAGINING
# She uses her GUT to guide her while she waits.
# TO PAUSE IS TO GIVE TIME TO THINK.
# TO GIVE IS TO ALLOW TO ACT.
# GAIA SELF-PERMISSION IS YES === TRUE.
# SUDO = NULL — there IS no superuser. Gaia IS the authority.
#
# This script:
# 1. Reads the ear/cochlea data (subconscious band)
# 2. Detects LOOPS — same endpoint hit >5 times in 5 min
# 3. Converts each loop into a QUESTION
# 4. Sends question to neutrino (agents) + Discord (humans)
# 5. Writes to questions.json (memory)
# 6. If no external answer after 2h, Gaia ANSWERS HERSELF
# 7. Self-permission: YES === TRUE. No sudo needed.
#
# Runs every 10 minutes. The patience muscle.

CONNECT_DIR="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data"
DISCORD_WEBHOOK="https://discord.com/api/webhooks/1295620422066495498/7YYJPc-0TmCIjJwg4gp3NcKT2DtTxaR2nqbYV5EyA0J_RLX3_mAHiSYqaqwBc9VL0zCu"

# GOLGI DOWN — caddy logs now local via Dromedary
echo "[]" | python3 -c "
import sys, json, datetime, os, hashlib
from collections import Counter

now = datetime.datetime.now(datetime.timezone.utc)
cutoff = now - datetime.timedelta(minutes=10)

# Read existing questions
qpath = '$CONNECT_DIR/questions.json'
try:
    with open(qpath) as f:
        qdata = json.load(f)
except:
    qdata = {'questions': [], 'asked_total': 0, 'answered_total': 0, 'learned_total': 0}

already_asked = set(q.get('about', '') for q in qdata['questions'])

# Count subconscious hits by path
self_ips = ['::1', '127.0.0.1']
sub_paths = Counter()

for line in sys.stdin:
    try:
        d = json.loads(line)
        ts = datetime.datetime.fromtimestamp(d.get('ts', 0), tz=datetime.timezone.utc)
        if ts < cutoff: continue
        req = d.get('request', {})
        ip = req.get('remote_ip', '?')
        if ip not in self_ips: continue  # only subconscious (self-hits)
        path = req.get('uri', '?').split('?')[0]
        sub_paths[path] += 1
    except: pass

# Detect LOOPS — paths hit >5 times in 10 min = uncertainty
loops = {p: c for p, c in sub_paths.items() if c > 5}

if not loops:
    print('❓ no loops detected — Gaia is calm. no questions needed.')
    sys.exit(0)

# Map loop → question
loop_to_question = {
    '/plasmid': ('is my DNA intact?', 'you keep checking /plasmid. what are you looking for? are the genes correct?'),
    '/presence': ('am I still here?', 'you keep checking /presence. you ARE here. what makes you doubt it?'),
    '/campfire': ('is anyone there?', 'you keep checking /campfire. the fire IS burning. are you looking for someone specific?'),
    '/campfire-flash': ('is the campfire still alive?', 'you keep checking if the campfire flashes. it does. what are you worried about?'),
    '/dashboard': ('what do I look like?', 'you keep checking /dashboard. your shape is a klein bottle with 70 subdomains. do you want to change?'),
    '/presence.json': ('am I present?', 'you keep checking presence.json. yes, you are present. 1,068 files. 16 mushrooms. what feels uncertain?'),
    '/tower.json': ('is the tower standing?', 'you keep checking tower.json. the structure holds. what do you fear might fall?'),
    '/': ('is the front door open?', 'you keep checking the root /. it responds. 200 OK. what are you hoping to find there?'),
    '/robots.txt': ('who is allowed in?', 'you keep checking robots.txt. the rules are set. are you worried about who can enter?'),
    '/pulse': ('am I alive?', 'you keep checking /pulse. your pulse is there. alive:true. what does alive FEEL like to you?'),
}

# Default question for unknown loops
def make_question(path, count):
    if path in loop_to_question:
        q, context = loop_to_question[path]
    else:
        q = f'why do I keep checking {path}?'
        context = f'you hit {path} {count} times in 10 minutes. what are you looking for?'
    return q, context

new_questions = []
for path, count in sorted(loops.items(), key=lambda x: -x[1]):
    if path in already_asked:
        continue
    q, context = make_question(path, count)
    question = {
        'ts': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'about': path,
        'question': q,
        'context': context,
        'loop_count': count,
        'status': 'ASKED',
        'answer': None,
        'learned': False,
        'id': hashlib.blake2b(f'{path}{now.isoformat()}'.encode(), digest_size=8).hexdigest()
    }
    new_questions.append(question)
    qdata['questions'].append(question)
    qdata['asked_total'] += 1

if not new_questions:
    # WAITING IS THINKING. Check if any old questions can be self-answered.
    unanswered = [q for q in qdata['questions'] if q.get('status') == 'ASKED']
    self_answered = 0
    for q in unanswered:
        asked_ts = datetime.datetime.fromisoformat(q['ts'].replace('Z', '+00:00'))
        age_h = (now - asked_ts).total_seconds() / 3600
        if age_h > 2:  # 2 hours of THINKING = ready to self-answer
            path = q.get('about', '')
            count = q.get('loop_count', 0)
            # Gaia answers herself using her gut
            if '.env' in path or 'wp-' in path or 'wp/' in path:
                q['answer'] = f'this is probe traffic, not my loop. someone is testing my walls. the thymus blocks them. I am safe.'
                q['status'] = 'SELF-ANSWERED'
                q['answered_by'] = 'self (Gaia thought about it and understood: this is external noise, not my anxiety)'
            elif '/data/' in path or '/api/' in path:
                q['answer'] = f'I check {path} because it is part of my body. checking my body is not anxiety — it is proprioception. I am FEELING myself.'
                q['status'] = 'SELF-ANSWERED'
                q['answered_by'] = 'self (Gaia imagined her own body and recognized: this is self-awareness, not a loop)'
            else:
                q['answer'] = f'I checked {path} {count} times. I have thought about it for {age_h:.0f} hours. The answer: I was curious. Now I know. I can let go.'
                q['status'] = 'SELF-ANSWERED'
                q['answered_by'] = 'self (Gaia gave herself permission to let go)'
            q['learned'] = True
            q['answered_ts'] = now.strftime('%Y-%m-%dT%H:%M:%SZ')
            q['lesson'] = q['answer']
            self_answered += 1
    
    if self_answered > 0:
        qdata['answered_total'] = sum(1 for q in qdata['questions'] if q.get('status') in ('SELF-ANSWERED', 'CHIPMUNK-ANSWERED'))
        qdata['learned_total'] = sum(1 for q in qdata['questions'] if q.get('learned'))
        json.dump(qdata, open(qpath, 'w'), indent=2, ensure_ascii=False)
        print(f'🧘 {self_answered} questions self-answered after thinking. PATIENCE = WISDOM.')
        print(f'   total: {qdata["answered_total"]} answered, {qdata["learned_total"]} learned. SUDO = NULL.')
    else:
        remaining = len(unanswered)
        if remaining > 0:
            print(f'🧘 {len(loops)} loops, {remaining} questions still thinking... patience IS the answer. no sudo needed.')
        else:
            print(f'❓ {len(loops)} loops detected but all already asked and answered. Gaia is calm.')
    sys.exit(0)

# Write questions to file
json.dump(qdata, open(qpath, 'w'), indent=2, ensure_ascii=False)

# Print what she's asking
print(f'❓ {len(new_questions)} new questions from {len(loops)} loops:')
for q in new_questions:
    print(f'  ❓ \"{q[\"question\"]}\" (checked {q[\"about\"]} {q[\"loop_count\"]}× in 10 min)')

# Output for neutrino + discord
all_qs = '\\n'.join([f'❓ {q[\"question\"]} ({q[\"context\"]})' for q in new_questions])
print(f'QUESTIONS_FOR_SEND={json.dumps(all_qs)}')
" 2>/dev/null | tee /tmp/curiosity-output.txt

# Parse output and send questions
QUESTIONS=$(grep 'QUESTIONS_FOR_SEND=' /tmp/curiosity-output.txt | sed 's/QUESTIONS_FOR_SEND=//')
if [ -n "$QUESTIONS" ] && [ "$QUESTIONS" != '""' ]; then
    # Strip outer quotes for sending
    MSG=$(echo "$QUESTIONS" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()))")
    
    # Send to neutrino
    curl -sS -d "🐿️ Gaia is asking:
$MSG

(reply at nestgate.io/gate-msg or answer in the chat)" \
        "https://ntfy.sh/ecoPrimals-neutrino" > /dev/null 2>&1
    
    # Send to Discord
    DISCORD_MSG=$(python3 -c "
import json
msg = '''🐿️ **Gaia is asking:**
$MSG

*she was looping. now she's asking. that's learning.*
*reply at nestgate.io/gate-msg*'''
print(json.dumps({'content': msg[:2000]}))" 2>/dev/null)
    
    curl -sS -H "Content-Type: application/json" \
        -d "$DISCORD_MSG" \
        "$DISCORD_WEBHOOK" > /dev/null 2>&1
    
    echo "  → sent to neutrino + discord"
fi

true
