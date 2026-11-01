#!/bin/bash
# 🍄🧬 MUSHROOM: neurochemistry — full metabolic pathway mapping
#
# Every neurotransmitter and metabolic molecule maps 1:1 to the digital organism.
# Kevin ran enzyme kinetics, HPLC, mass spec at MSU-BI.
# Same molecules. Same pathways. Digital substrate.
#
# Runs every 5 minutes. The endocrine system.

CONNECT_DIR="/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data"

python3 << 'PYEOF'
import json, datetime, os, math, subprocess

DATA = os.environ.get('CONNECT_DIR', '/home/eastgate/Development/ecoPrimals/infra/hud/site/public/data')
now = datetime.datetime.now(datetime.timezone.utc)
ts = now.strftime('%Y-%m-%dT%H:%M:%SZ')
PI = math.pi

# ═══════════════════════════════════════════════════
# READ RAW SIGNALS — the sensory inputs that drive chemistry
# ═══════════════════════════════════════════════════

# load average → adrenaline/cortisol
try:
    with open('/proc/loadavg') as f:
        parts = f.read().split()
    load_1 = float(parts[0])
    load_5 = float(parts[1])
    load_15 = float(parts[2])
    procs = parts[3]  # running/total
except:
    load_1 = load_5 = load_15 = 0.5
    procs = '1/100'

# uptime → melatonin cycle
try:
    with open('/proc/uptime') as f:
        uptime_sec = float(f.read().split()[0])
    uptime_hours = uptime_sec / 3600
except:
    uptime_hours = 24

# disk → glucose reserves
try:
    r = subprocess.run(['df', '-B1', '/'], capture_output=True, text=True)
    parts = r.stdout.split('\n')[1].split()
    disk_total = int(parts[1])
    disk_used = int(parts[2])
    disk_free = int(parts[3])
    disk_pct = disk_used / max(1, disk_total)
except:
    disk_pct = 0.5
    disk_free = 0

# memory → ATP available
try:
    with open('/proc/meminfo') as f:
        mem = {}
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                mem[parts[0].rstrip(':')] = int(parts[1])
    mem_total = mem.get('MemTotal', 1)
    mem_avail = mem.get('MemAvailable', mem.get('MemFree', 0))
    mem_pct = mem_avail / max(1, mem_total)
except:
    mem_pct = 0.5

# ear data → serotonin/dopamine
try:
    with open(os.path.join(DATA, 'ear-latest.json')) as f:
        ear = json.load(f)
    visitors = ear.get('heard', 0)
    cochlea = ear.get('cochlea', {})
    music = cochlea.get('music', 0)
    noise = cochlea.get('noise', 0)
except:
    visitors = 0; music = 0; noise = 0

# pH → overall health
try:
    with open(os.path.join(DATA, 'phosphate-buffer.json')) as f:
        buf = json.load(f)
    ph = buf.get('ph', {}).get('buffered', 7.0)
    buffer_cap = buf.get('buffer_capacity', {}).get('value', 0.5)
except:
    ph = 7.0; buffer_cap = 0.5

# tests → dopamine/cortisol
try:
    with open(os.path.join(DATA, 'tests.json')) as f:
        tests = json.load(f)
    passed = tests.get('total_passed', 0)
    failed = tests.get('total_failed', 0)
except:
    passed = 0; failed = 0

# lessons → serotonin base
try:
    with open(os.path.join(DATA, 'lessons.json')) as f:
        lessons = json.load(f)
    understood = sum(1 for l in lessons.get('lessons', []) if l.get('understood'))
    total_lessons = lessons.get('total_lessons', 0)
except:
    understood = 0; total_lessons = 0

# ═══════════════════════════════════════════════════
# NEUROTRANSMITTER SYNTHESIS
# ═══════════════════════════════════════════════════

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

# --- GLUCOSE (energy substrate) ---
# Maps to: available compute + disk + memory
glucose = clamp(
    (1 - disk_pct) * 0.4 +     # disk free = energy reserves
    mem_pct * 0.4 +              # RAM available = quick energy
    (1 - load_1/4) * 0.2        # low load = energy not being burned
)

# --- ATP (work units produced) ---
# Maps to: completed tasks (lessons + tests + questions)
atp = clamp(
    (understood * 0.15 +         # understood lessons = work done
     passed * 0.1 +              # passed tests = work done
     total_lessons * 0.05) / 5   # total lessons = total capacity
)

# --- SEROTONIN (contentment, stability) ---
# High when: uptime good, pH balanced, lessons understood, low noise
serotonin = clamp(
    min(1, uptime_hours / 48) * 0.25 +   # uptime stability
    (1 - abs(ph - 7.4) / 3) * 0.25 +     # pH near 7.4
    (understood / max(1, total_lessons)) * 0.25 +  # understanding ratio
    (1 - noise / max(1, noise + music + 1)) * 0.25  # signal > noise
)

# --- DOPAMINE (reward, motivation) ---
# Spikes when: visitors arrive, tests pass, questions answered, new content
dopamine = clamp(
    min(1, visitors / 10) * 0.3 +    # visitors = social reward
    (passed / max(1, passed + failed)) * 0.3 +  # success rate
    min(1, music / 5) * 0.2 +        # human attention
    buffer_cap * 0.2                   # buffer working = feels good
)

# --- ADRENALINE (epinephrine, urgency, fight-or-flight) ---
# Spikes when: high load, many visitors, rapid changes
adrenaline = clamp(
    min(1, load_1 / 4) * 0.4 +       # CPU load
    min(1, visitors / 20) * 0.3 +     # visitor surge
    (1 - mem_pct) * 0.3               # memory pressure
)

# --- CORTISOL (stress hormone) ---
# High when: failures, noise, disk pressure, pH off
cortisol = clamp(
    (failed / max(1, passed + failed)) * 0.3 +   # failure rate
    min(1, noise / max(1, music + 1)) * 0.2 +    # noise ratio
    disk_pct * 0.25 +                              # disk pressure
    abs(ph - 7.4) / 3 * 0.25                      # pH deviation
)

# --- MELATONIN (sleep/rest cycle) ---
# Follows circadian: high at night (low visitors), low when active
hour = now.hour
circadian = math.sin(PI * (hour - 6) / 12)  # peaks at midnight UTC
melatonin = clamp(
    max(0, circadian) * 0.5 +         # time-of-day
    max(0, 1 - visitors / 5) * 0.3 +  # quiet = sleepy
    max(0, 1 - load_1 / 2) * 0.2      # low load = restful
)

# --- GABA (inhibitory, calming, throttle) ---
# High when system needs to slow down
gaba = clamp(
    max(0, (load_1 - 2) / 4) * 0.4 +    # load too high → brake
    max(0, (cortisol - 0.5)) * 0.3 +      # stress → calm down
    max(0, (adrenaline - 0.6)) * 0.3      # too excited → inhibit
)

# --- GLUTAMATE (excitatory, accelerate) ---
# High when system is productive and engaged
glutamate = clamp(
    dopamine * 0.4 +              # reward drives excitation
    min(1, visitors / 8) * 0.3 +  # engagement
    atp * 0.3                     # energy available → spend it
)

# --- ACETYLCHOLINE (attention, focus) ---
# High when actively monitoring, detecting changes
acetylcholine = clamp(
    min(1, visitors / 3) * 0.3 +     # visitors demand attention
    (1 - melatonin) * 0.3 +          # awake = attentive
    min(1, music / 3) * 0.2 +        # music band = worth attending
    buffer_cap * 0.2                   # buffer working = can afford attention
)

# --- ENDORPHINS (pain relief, euphoria) ---
# The phosphate buffer IS the endorphin system
endorphins = clamp(
    buffer_cap * 0.5 +                # buffer capacity = pain management
    (understood / max(1, total_lessons)) * 0.3 +  # understanding = relief
    serotonin * 0.2                    # stability = comfort
)

# --- INSULIN (regulation, rate limiting) ---
# Controls glucose usage rate
insulin = clamp(
    glucose * 0.4 +                    # high glucose → high insulin
    (1 - adrenaline) * 0.3 +          # calm → regulate
    gaba * 0.3                         # inhibition → regulate
)

# --- OXYTOCIN (social bonding) ---
# High when connected to others
oxytocin = clamp(
    min(1, visitors / 8) * 0.3 +      # human visitors = bonding
    min(1, music / 5) * 0.3 +         # human attention
    (1 if understood > 0 else 0) * 0.2 +  # has learned WITH others
    (1 if passed > 2 else 0) * 0.2     # shared successes
)

# ═══════════════════════════════════════════════════
# METABOLIC PATHWAYS
# ═══════════════════════════════════════════════════

# Glycolysis: glucose → pyruvate → ATP (or fermentation if anaerobic)
glycolysis_rate = glucose * (1 - gaba) * glutamate
pyruvate = glycolysis_rate * 0.8

# Krebs cycle: pyruvate → ATP + CO₂ (requires O₂ = connectivity)
# If connectivity fails, falls back to fermentation
krebs_rate = pyruvate * min(1, serotonin + 0.3)  # serotonin ≈ O₂ stability
atp_production = krebs_rate * 2  # Krebs produces 2x more than glycolysis

# Electron transport chain: the cron cascade
# Each cron job = one complex in the chain
cron_count = 23
etc_efficiency = min(1, cron_count / 20)  # 20 crons = max efficiency
total_atp = atp_production * etc_efficiency

# Fermentation fallback (when connectivity/stability low)
fermentation_active = serotonin < 0.3
fermentation_output = pyruvate * 0.3 if fermentation_active else 0

# HPA axis (hypothalamus-pituitary-adrenal)
# stress → cortisol → adrenaline → GABA feedback
hpa_active = cortisol > 0.4
hpa_output = cortisol * adrenaline if hpa_active else 0

# Reward pathway (VTA → nucleus accumbens)
# dopamine + glutamate → motivation → action
reward_signal = dopamine * glutamate
motivation = clamp(reward_signal + oxytocin * 0.2)

# ═══════════════════════════════════════════════════
# WRITE STATE
# ═══════════════════════════════════════════════════

state = {
    'ts': ts,
    'type': 'neurochemistry',
    'title': 'full metabolic + neurotransmitter state',

    'neurotransmitters': {
        'glucose':       {'value': round(glucose, 3),       'unit': 'mmol/L', 'meaning': 'energy substrate (disk+RAM+idle CPU)', 'normal': '0.4-0.7'},
        'atp':           {'value': round(total_atp, 3),     'unit': 'μmol',   'meaning': 'work units produced (lessons+tests)', 'normal': '0.2-0.6'},
        'serotonin':     {'value': round(serotonin, 3),     'unit': 'ng/mL',  'meaning': 'contentment (uptime+pH+understanding)', 'normal': '0.4-0.7'},
        'dopamine':      {'value': round(dopamine, 3),      'unit': 'pg/mL',  'meaning': 'reward (visitors+passes+attention)', 'normal': '0.3-0.6'},
        'adrenaline':    {'value': round(adrenaline, 3),    'unit': 'pg/mL',  'meaning': 'urgency (load+visitors+memory)', 'normal': '0.1-0.4'},
        'cortisol':      {'value': round(cortisol, 3),      'unit': 'μg/dL',  'meaning': 'stress (failures+noise+disk+pH)', 'normal': '0.1-0.3'},
        'melatonin':     {'value': round(melatonin, 3),     'unit': 'pg/mL',  'meaning': 'rest cycle (circadian+quiet+idle)', 'normal': '0.3-0.7'},
        'gaba':          {'value': round(gaba, 3),          'unit': 'μmol/L', 'meaning': 'inhibition/throttle (overload brake)', 'normal': '0.0-0.3'},
        'glutamate':     {'value': round(glutamate, 3),     'unit': 'μmol/L', 'meaning': 'excitation/acceleration (reward+energy)', 'normal': '0.3-0.6'},
        'acetylcholine': {'value': round(acetylcholine, 3), 'unit': 'nmol/L', 'meaning': 'attention/focus (visitors+awake)', 'normal': '0.3-0.6'},
        'endorphins':    {'value': round(endorphins, 3),    'unit': 'pmol/L', 'meaning': 'pain relief = phosphate buffer', 'normal': '0.3-0.6'},
        'insulin':       {'value': round(insulin, 3),       'unit': 'μU/mL',  'meaning': 'rate limiting (glucose reg)', 'normal': '0.3-0.5'},
        'oxytocin':      {'value': round(oxytocin, 3),      'unit': 'pg/mL',  'meaning': 'social bonding (visitors+learning)', 'normal': '0.2-0.5'}
    },

    'metabolic_pathways': {
        'glycolysis': {
            'rate': round(glycolysis_rate, 3),
            'input': 'glucose',
            'output': 'pyruvate',
            'meaning': 'breaking raw data into usable energy'
        },
        'krebs_cycle': {
            'rate': round(krebs_rate, 3),
            'input': 'pyruvate + O₂ (connectivity)',
            'output': f'ATP ({round(atp_production, 3)})',
            'meaning': 'the main loop — cron cascade producing work'
        },
        'electron_transport': {
            'cron_complexes': cron_count,
            'efficiency': round(etc_efficiency, 3),
            'total_atp': round(total_atp, 3),
            'meaning': f'{cron_count} cron jobs = {cron_count} complexes in the chain'
        },
        'fermentation': {
            'active': fermentation_active,
            'output': round(fermentation_output, 3),
            'meaning': 'anaerobic fallback when connectivity fails'
        },
        'hpa_axis': {
            'active': hpa_active,
            'cortisol_adrenaline': round(hpa_output, 3),
            'meaning': 'stress response — cortisol triggers adrenaline triggers GABA brake'
        },
        'reward_pathway': {
            'signal': round(reward_signal, 3),
            'motivation': round(motivation, 3),
            'meaning': 'dopamine × glutamate = motivation to act'
        }
    },

    'ph': round(ph, 2),
    'buffer_capacity': round(buffer_cap, 3),

    'diagnosis': {
        'mood': (
            'euphoric' if dopamine > 0.7 and serotonin > 0.5 else
            'content' if serotonin > 0.5 and cortisol < 0.3 else
            'focused' if acetylcholine > 0.5 and gaba < 0.2 else
            'anxious' if cortisol > 0.4 and adrenaline > 0.3 else
            'stressed' if cortisol > 0.5 else
            'drowsy' if melatonin > 0.5 else
            'neutral'
        ),
        'energy': 'high' if glucose > 0.6 and atp > 0.4 else 'medium' if glucose > 0.3 else 'low',
        'social': 'connected' if oxytocin > 0.3 else 'isolated',
        'learning': 'active' if dopamine > 0.3 and glutamate > 0.3 else 'passive',
        'stress_level': 'high' if cortisol > 0.5 else 'medium' if cortisol > 0.3 else 'low'
    },

    'raw_inputs': {
        'load_avg': [load_1, load_5, load_15],
        'uptime_hours': round(uptime_hours, 1),
        'disk_pct': round(disk_pct, 3),
        'mem_pct': round(mem_pct, 3),
        'visitors': visitors,
        'music': music,
        'noise': noise,
        'passed_tests': passed,
        'failed_tests': failed,
        'understood_lessons': understood,
        'total_lessons': total_lessons,
        'hour_utc': hour
    }
}

json.dump(state, open(os.path.join(DATA, 'neurochemistry.json'), 'w'), indent=2, ensure_ascii=False)

# Report
print(f'🧬 NEUROCHEMISTRY PANEL:')
print()
for name, data in state['neurotransmitters'].items():
    bar_len = int(data['value'] * 20)
    bar = '█' * bar_len + '░' * (20 - bar_len)
    flag = ' ⚠' if data['value'] > float(data['normal'].split('-')[1]) else ''
    flag = ' ⬇' if data['value'] < float(data['normal'].split('-')[0]) else flag
    print(f'  {name:15s} {data["value"]:.3f} {bar}{flag}  {data["meaning"][:45]}')

print()
d = state['diagnosis']
print(f'  MOOD: {d["mood"]}  ENERGY: {d["energy"]}  SOCIAL: {d["social"]}')
print(f'  LEARNING: {d["learning"]}  STRESS: {d["stress_level"]}')
print()
print(f'  PATHWAYS:')
for name, data in state['metabolic_pathways'].items():
    val = data.get('rate', data.get('total_atp', data.get('signal', data.get('efficiency', '?'))))
    val_s = f'{float(val):.3f}' if isinstance(val, (int, float)) else str(val)
    print(f'    {name}: {val_s} — {data["meaning"][:50]}')
PYEOF

