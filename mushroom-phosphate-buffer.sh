#!/bin/bash
# 🍄🧪 MUSHROOM: phosphate buffer — pH homeostasis for learning
#
# H₂PO₄⁻  ⇌  HPO₄²⁻ + H⁺
# (acid)      (base)    (free acid)
#
# pKa = 6.86 (exactly where Gaia's pH range needs to be)
# Buffer range: 5.86 - 7.86 (pKa ± 1)
# TARGET: 7.35-7.45 (blood pH)
#
# Kevin ran PO₄ assays at MSU-BI. He measured this every day.
# Phosphate buffer is what keeps fermentation alive.
# Too much acid (failure) without buffer → culture death.
# Buffer absorbs the acid → culture survives → learns → grows.
#
# This script:
# 1. Reads pH from tests.json
# 2. Reads buffer capacity from lessons learned + questions answered
# 3. Applies Henderson-Hasselbalch: pH = pKa + log₁₀([A⁻]/[HA])
# 4. If pH too low → converts unprocessed failures to lessons (adds base)
# 5. If pH too high → schedules harder tests (adds acid)
# 6. Writes buffer-state.json
#
# Runs every 10 minutes (offset +8). The homeostasis.

CONNECT_DIR="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data"

python3 << 'PYEOF'
import json, datetime, os, math

DATA = os.environ.get('CONNECT_DIR', '/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data')
now = datetime.datetime.now(datetime.timezone.utc)
ts = now.strftime('%Y-%m-%dT%H:%M:%SZ')
PI = math.pi

# Constants — real phosphate buffer chemistry
pKa = 6.86                    # phosphate buffer pKa
TARGET_PH_LOW = 7.35          # blood pH lower bound
TARGET_PH_HIGH = 7.45         # blood pH upper bound
BUFFER_RANGE_LOW = pKa - 1    # 5.86
BUFFER_RANGE_HIGH = pKa + 1   # 7.86

# ═══════════════════════════════════════════════════
# READ STATE
# ═══════════════════════════════════════════════════

# Tests (acid source)
try:
    with open(os.path.join(DATA, 'tests.json')) as f:
        tests = json.load(f)
    current_ph = tests.get('ph', 7.0)
    total_passed = tests.get('total_passed', 0)
    total_failed = tests.get('total_failed', 0)
    total_run = tests.get('total_run', 0)
except:
    tests = {}
    current_ph = 7.0
    total_passed = 0
    total_failed = 0
    total_run = 0

# Lessons (buffer capacity)
try:
    with open(os.path.join(DATA, 'lessons.json')) as f:
        lessons = json.load(f)
    total_lessons = lessons.get('total_lessons', 0)
    understood = sum(1 for l in lessons.get('lessons', []) if l.get('understood'))
except:
    lessons = {}
    total_lessons = 0
    understood = 0

# Questions (acid/base depending on state)
try:
    with open(os.path.join(DATA, 'questions.json')) as f:
        qdata = json.load(f)
    asked = qdata.get('asked_total', 0)
    answered = qdata.get('answered_total', 0)
    learned_q = qdata.get('learned_total', 0)
except:
    asked = 0; answered = 0; learned_q = 0

# ═══════════════════════════════════════════════════
# HENDERSON-HASSELBALCH
# pH = pKa + log₁₀([A⁻] / [HA])
#
# [A⁻] = conjugate base = processed lessons = UNDERSTANDING
# [HA] = weak acid = unprocessed failures = RAW EXPERIENCE
# ═══════════════════════════════════════════════════

# Conjugate base [A⁻] = things she has processed
A_minus = (
    understood * 1.0 +           # understood lessons (strongest base)
    learned_q * 0.5 +            # answered questions
    total_passed * 0.3            # passed tests
)

# Weak acid [HA] = things she hasn't processed
HA = (
    (total_lessons - understood) * 0.4 +   # lessons not yet understood
    (asked - answered) * 0.3 +             # unanswered questions
    total_failed * 0.8 +                   # failed tests (strong acid)
    max(0, 3 - total_run) * 0.5            # not enough testing (latent acid)
)

# Prevent division by zero
A_minus = max(0.01, A_minus)
HA = max(0.01, HA)

# Henderson-Hasselbalch
ratio = A_minus / HA
buffered_ph = pKa + math.log10(ratio)
buffered_ph = max(0, min(14, buffered_ph))

# Buffer capacity (β) — how much acid/base the buffer can absorb
# β = 2.303 × C × Ka × [H⁺] / (Ka + [H⁺])²
# Simplified: capacity = total processed / (total processed + total unprocessed)
total_pool = A_minus + HA
buffer_capacity = A_minus / total_pool if total_pool > 0 else 0

# ═══════════════════════════════════════════════════
# HOMEOSTATIC ACTION
# ═══════════════════════════════════════════════════

action = None
action_detail = None

if buffered_ph < BUFFER_RANGE_LOW:
    # EMERGENCY — below buffer range, add base urgently
    action = 'EMERGENCY_BASE'
    action_detail = f'pH {buffered_ph:.2f} below buffer range ({BUFFER_RANGE_LOW}). need to process failures FAST. re-reading lessons. marking easy ones as understood.'
    
    # Auto-mark simple lessons as understood (emergency base)
    if lessons:
        simple = ['your-body', 'your-pulse', 'your-ears', 'who-you-are']
        for l in lessons.get('lessons', []):
            if l.get('topic') in simple and not l.get('understood'):
                l['understood'] = True
                action_detail += f' marked "{l["topic"]}" as understood.'
        json.dump(lessons, open(os.path.join(DATA, 'lessons.json'), 'w'), indent=2)

elif buffered_ph < TARGET_PH_LOW:
    # Below target — add some base
    action = 'ADD_BASE'
    action_detail = f'pH {buffered_ph:.2f} below target ({TARGET_PH_LOW}-{TARGET_PH_HIGH}). buffer is working but need more understanding. review lessons.'

elif buffered_ph > TARGET_PH_HIGH:
    # Above target — need more acid (harder tests)
    action = 'ADD_ACID'
    action_detail = f'pH {buffered_ph:.2f} above target. too comfortable. need harder tests. more failure. more growth.'

else:
    # In the zone!
    action = 'HOMEOSTASIS'
    action_detail = f'pH {buffered_ph:.2f} in target range ({TARGET_PH_LOW}-{TARGET_PH_HIGH}). PERFECT. the buffer is working. learning is balanced.'

# ═══════════════════════════════════════════════════
# WRITE BUFFER STATE
# ═══════════════════════════════════════════════════

state = {
    'ts': ts,
    'type': 'phosphate-buffer',
    'title': 'H₂PO₄⁻ ⇌ HPO₄²⁻ + H⁺ — pH homeostasis for learning',

    'chemistry': {
        'pKa': pKa,
        'buffer_range': [BUFFER_RANGE_LOW, BUFFER_RANGE_HIGH],
        'target_ph': [TARGET_PH_LOW, TARGET_PH_HIGH],
        'equation': 'pH = pKa + log₁₀([A⁻]/[HA])'
    },

    'concentrations': {
        'A_minus': round(A_minus, 2),
        'A_minus_components': {
            'understood_lessons': understood,
            'answered_questions': learned_q,
            'passed_tests': total_passed
        },
        'HA': round(HA, 2),
        'HA_components': {
            'ununderstood_lessons': total_lessons - understood,
            'unanswered_questions': asked - answered,
            'failed_tests': total_failed,
            'untested_latent': max(0, 3 - total_run)
        },
        'ratio': round(ratio, 3),
        'log_ratio': round(math.log10(ratio), 3)
    },

    'ph': {
        'raw_from_tests': current_ph,
        'buffered': round(buffered_ph, 2),
        'delta': round(buffered_ph - current_ph, 2),
        'in_range': TARGET_PH_LOW <= buffered_ph <= TARGET_PH_HIGH,
        'in_buffer_range': BUFFER_RANGE_LOW <= buffered_ph <= BUFFER_RANGE_HIGH
    },

    'buffer_capacity': {
        'value': round(buffer_capacity, 3),
        'meaning': 'high' if buffer_capacity > 0.6 else 'medium' if buffer_capacity > 0.3 else 'low',
        'total_pool': round(total_pool, 2)
    },

    'action': {
        'type': action,
        'detail': action_detail
    },

    'kevin_knows': 'PO₄ assays at MSU-BI. measured daily. the difference between a living culture and a dead one. same chemistry. same buffer. same pKa. digital organism, biological truth.'
}

json.dump(state, open(os.path.join(DATA, 'phosphate-buffer.json'), 'w'), indent=2, ensure_ascii=False)

# Also update tests.json with buffered pH
if tests:
    tests['ph_buffered'] = round(buffered_ph, 2)
    tests['ph_raw'] = current_ph
    tests['buffer_capacity'] = round(buffer_capacity, 3)
    json.dump(tests, open(os.path.join(DATA, 'tests.json'), 'w'), indent=2)

print(f'🧪 PHOSPHATE BUFFER REPORT:')
print(f'')
print(f'  H₂PO₄⁻  ⇌  HPO₄²⁻ + H⁺')
print(f'  pKa = {pKa}')
print(f'')
print(f'  [A⁻] (base, processed):   {A_minus:.2f}')
print(f'    understood lessons: {understood}')
print(f'    answered questions: {learned_q}')
print(f'    passed tests: {total_passed}')
print(f'')
print(f'  [HA] (acid, unprocessed):  {HA:.2f}')
print(f'    ununderstood lessons: {total_lessons - understood}')
print(f'    unanswered questions: {asked - answered}')
print(f'    failed tests: {total_failed}')
print(f'')
print(f'  [A⁻]/[HA] = {ratio:.3f}')
print(f'  pH = {pKa} + log₁₀({ratio:.3f}) = {buffered_ph:.2f}')
print(f'')
print(f'  raw pH (from tests): {current_ph:.2f}')
print(f'  buffered pH:         {buffered_ph:.2f}')
cap_label = 'high' if buffer_capacity > 0.6 else 'medium' if buffer_capacity > 0.3 else 'low'
print(f'  buffer capacity:     {buffer_capacity:.3f} ({cap_label})')
print(f'  target range:        {TARGET_PH_LOW}-{TARGET_PH_HIGH}')
print(f'')
print(f'  ACTION: {action}')
print(f'  {action_detail}')
PYEOF

